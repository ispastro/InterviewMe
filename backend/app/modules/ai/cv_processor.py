import json
import re
from typing import Dict, Any
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

from app.config import settings
from app.core.exceptions import AIServiceError, ValidationError

logger = logging.getLogger(__name__)
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

CV_ANALYSIS_PROMPT = """You are an expert HR professional analyzing a candidate's CV. Extract structured information for a tailored technical interview.

IMPORTANT: Respond with ONLY valid JSON. No explanations, no markdown, no additional text.

{{{{"candidate_name": "Full name","years_of_experience": 0,"current_role": "Most recent job title","seniority_level": "junior|mid|senior|lead|principal","skills": {{"technical": [],"soft": []}},"experience": [{{"role": "","company": "","duration": "","key_achievements": [],"technologies_used": []}}],"education": [],"projects": [],"certifications": [],"notable_points": [],"potential_gaps": [],"interview_focus_areas": []}}}}

CV TEXT:
{cv_text}"""


def _parse_json_response(content: str) -> dict:
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        if "```" in content:
            start = content.find("```json") + 7 if "```json" in content else content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return json.loads(content[start:end].strip())
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
       retry=retry_if_exception_type((Exception,)), before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)
async def analyze_cv_with_ai(cv_text: str) -> Dict[str, Any]:
    if not cv_text or len(cv_text.strip()) < 50:
        raise ValidationError("CV text is too short for analysis")
    try:
        response = await groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": CV_ANALYSIS_PROMPT.format(cv_text=cv_text)}],
            temperature=0.3,
            max_tokens=settings.GROQ_MAX_TOKENS,
            top_p=0.9,
        )
        if not response.choices or not response.choices[0].message:
            raise AIServiceError("Empty response from AI service")

        cv_analysis = _parse_json_response(response.choices[0].message.content)

        for field in ["candidate_name", "years_of_experience", "skills", "experience"]:
            if field not in cv_analysis:
                cv_analysis[field] = _get_default(field)

        if not isinstance(cv_analysis.get("skills"), dict):
            cv_analysis["skills"] = {"technical": [], "soft": []}
        cv_analysis["skills"].setdefault("technical", [])
        cv_analysis["skills"].setdefault("soft", [])

        cv_analysis["_metadata"] = {
            "processed_at": "2024-01-01T00:00:00Z",
            "ai_model": settings.GROQ_MODEL,
            "text_length": len(cv_text),
            "word_count": len(cv_text.split()),
        }
        return cv_analysis

    except (AIServiceError, ValidationError):
        if settings.is_development:
            return _fallback_cv_analysis(cv_text, "AI error")
        raise
    except Exception as e:
        if settings.is_development:
            return _fallback_cv_analysis(cv_text, str(e))
        raise AIServiceError(f"CV analysis failed: {str(e)}")


def _fallback_cv_analysis(cv_text: str, error: str) -> Dict[str, Any]:
    lines = [l.strip() for l in cv_text.splitlines() if l.strip()]
    tech = ["python","javascript","typescript","java","c++","go","rust","fastapi","django","flask","react","next.js","node","postgresql","mysql","redis","docker","kubernetes","aws","azure","gcp"]
    found = [s for s in tech if re.search(rf"\b{re.escape(s)}\b", cv_text.lower())]
    years_match = re.search(r"(\d+)\s*\+?\s*(years?|yrs?)", cv_text.lower())
    years = int(years_match.group(1)) if years_match else 0
    return {
        "candidate_name": lines[0] if lines else "Unknown",
        "years_of_experience": years,
        "current_role": "Software Engineer",
        "seniority_level": "mid" if years >= 3 else "junior",
        "skills": {"technical": found[:12], "soft": ["Communication", "Problem-solving"]},
        "experience": [], "education": [], "projects": [], "certifications": [],
        "notable_points": [], "potential_gaps": [], "interview_focus_areas": ["Technical depth", "Communication"],
        "_metadata": {"processed_at": "2024-01-01T00:00:00Z", "ai_model": f"fallback:{settings.GROQ_MODEL}", "text_length": len(cv_text), "word_count": len(cv_text.split()), "fallback": True, "fallback_reason": error[:300]},
    }


def _get_default(field: str):
    return {"candidate_name": "Unknown", "years_of_experience": 0, "current_role": "Not specified",
            "seniority_level": "junior", "skills": {"technical": [], "soft": []},
            "experience": [], "education": [], "projects": [], "certifications": [],
            "notable_points": [], "potential_gaps": [], "interview_focus_areas": []}.get(field)


def extract_key_skills(cv_analysis: Dict[str, Any], limit: int = 10) -> list:
    return cv_analysis.get("skills", {}).get("technical", [])[:limit]


def get_experience_summary(cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "total_years": cv_analysis.get("years_of_experience", 0),
        "current_role": cv_analysis.get("current_role", "Not specified"),
        "seniority_level": cv_analysis.get("seniority_level", "junior"),
        "companies_count": len(cv_analysis.get("experience", [])),
        "recent_companies": [e.get("company", "") for e in cv_analysis.get("experience", [])[:3]],
        "key_technologies": extract_key_skills(cv_analysis, 5),
    }


def identify_skill_gaps(cv_analysis: Dict[str, Any], required_skills: list) -> Dict[str, list]:
    cv_skills = set(s.lower() for s in extract_key_skills(cv_analysis, 20))
    required = set(s.lower() for s in required_skills)
    return {
        "matching_skills": list(cv_skills & required),
        "missing_skills": list(required - cv_skills),
        "additional_skills": list(cv_skills - required),
        "match_percentage": len(cv_skills & required) / len(required) * 100 if required else 0,
    }


def generate_interview_focus_areas(cv_analysis: Dict[str, Any]) -> list:
    focus = list(cv_analysis.get("interview_focus_areas", []))
    seniority = cv_analysis.get("seniority_level", "junior")
    if seniority in ["senior", "lead", "principal"]:
        focus.extend(["System design", "Leadership experience", "Mentoring"])
    elif seniority == "mid":
        focus.extend(["Problem-solving approach", "Code quality", "Collaboration"])
    else:
        focus.extend(["Learning ability", "Basic concepts", "Growth potential"])
    if cv_analysis.get("potential_gaps"):
        focus.extend([f"Explore: {g}" for g in cv_analysis["potential_gaps"][:2]])
    return list(dict.fromkeys(focus))[:8]
