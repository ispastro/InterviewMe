import json
import re
from typing import Dict, Any, List
import logging

from app.config import settings
from app.core.exceptions import AIServiceError, ValidationError
from app.modules.llm.gateway import llm_gateway

logger = logging.getLogger(__name__)

JD_ANALYSIS_PROMPT = """You are an expert technical recruiter analyzing a job description. Extract structured information for a tailored technical interview.

IMPORTANT: Respond with ONLY valid JSON. No explanations, no markdown, no additional text.

{{{{"role_title": "","company": null,"seniority_level": "junior|mid|senior|lead|principal","required_skills": [],"preferred_skills": [],"required_experience": {{"years_minimum": 0,"years_preferred": 0,"specific_domains": []}},"key_responsibilities": [],"technical_requirements": [],"soft_skills": [],"company_culture": {{"values": [],"work_style": "","pace": "","size": ""}},"interview_focus_areas": [],"question_categories": {{"technical": [],"behavioral": [],"system_design": [],"coding": []}},"role_complexity_nuance": "","red_flags_to_watch": [],"success_metrics": []}}}}

JD TEXT:
{jd_text}"""


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


async def analyze_jd_with_ai(jd_text: str) -> Dict[str, Any]:
    if not jd_text or len(jd_text.strip()) < 100:
        raise ValidationError("Job description text is too short for analysis")
    try:
        # Use LLM Gateway for automatic caching and retry logic
        content = await llm_gateway.completion_json(
            prompt=JD_ANALYSIS_PROMPT.format(jd_text=jd_text),
            temperature=0.3,
            max_tokens=settings.GROQ_MAX_TOKENS,
            use_cache=True,
            cache_ttl=7200  # Cache JD analysis for 2 hours
        )
        
        jd_analysis = content

        for field in ["role_title", "seniority_level", "required_skills", "key_responsibilities"]:
            if field not in jd_analysis:
                jd_analysis[field] = _get_jd_default(field)

        if not isinstance(jd_analysis.get("required_experience"), dict):
            jd_analysis["required_experience"] = {"years_minimum": 0, "years_preferred": 0, "specific_domains": []}
        if not isinstance(jd_analysis.get("company_culture"), dict):
            jd_analysis["company_culture"] = {"values": [], "work_style": "collaborative", "pace": "steady", "size": "medium"}
        if not isinstance(jd_analysis.get("question_categories"), dict):
            jd_analysis["question_categories"] = {"technical": [], "behavioral": [], "system_design": [], "coding": []}

        jd_analysis["_metadata"] = {
            "processed_at": "2024-01-01T00:00:00Z",
            "ai_model": settings.GROQ_MODEL,
            "text_length": len(jd_text),
            "word_count": len(jd_text.split()),
        }
        return jd_analysis

    except (AIServiceError, ValidationError):
        if settings.is_development:
            return _fallback_jd_analysis(jd_text, "AI error")
        raise
    except Exception as e:
        if settings.is_development:
            return _fallback_jd_analysis(jd_text, str(e))
        raise AIServiceError(f"JD analysis failed: {str(e)}")


def _fallback_jd_analysis(jd_text: str, error: str) -> Dict[str, Any]:
    lowered = jd_text.lower()
    role_match = re.search(r"(senior|junior|lead|principal)?\s*(software|backend|frontend|full stack)\s*engineer", lowered)
    role_title = role_match.group(0).title() if role_match else "Software Engineer"
    tech = ["python","javascript","typescript","java","go","react","node","fastapi","django","postgresql","redis","docker","kubernetes","aws"]
    required = [s for s in tech if re.search(rf"\b{re.escape(s)}\b", lowered)]
    years_match = re.search(r"(\d+)\s*\+?\s*(years?|yrs?)", lowered)
    years = int(years_match.group(1)) if years_match else 0
    return {
        "role_title": role_title, "company": None, "seniority_level": "senior" if "senior" in lowered else "mid",
        "required_skills": required, "preferred_skills": [],
        "required_experience": {"years_minimum": years, "years_preferred": max(years, 0), "specific_domains": []},
        "key_responsibilities": [], "technical_requirements": required[:5],
        "soft_skills": ["Communication", "Collaboration", "Problem-solving"],
        "company_culture": {"values": [], "work_style": "collaborative", "pace": "steady", "size": "medium"},
        "interview_focus_areas": ["Core technical fundamentals", "Communication"],
        "question_categories": {"technical": required[:6], "behavioral": ["Conflict handling", "Collaboration"], "system_design": ["Scalability"] if years >= 3 else [], "coding": ["Problem solving"]},
        "red_flags_to_watch": [], "success_metrics": [],
        "_metadata": {"processed_at": "2024-01-01T00:00:00Z", "ai_model": f"fallback:{settings.GROQ_MODEL}", "text_length": len(jd_text), "word_count": len(jd_text.split()), "fallback": True, "fallback_reason": error[:300]},
    }


def _get_jd_default(field: str):
    return {"role_title": "Software Engineer", "company": "Not specified", "seniority_level": "mid",
            "required_skills": [], "preferred_skills": [], "key_responsibilities": [],
            "technical_requirements": [], "soft_skills": [], "interview_focus_areas": [],
            "question_categories": {"technical": [], "behavioral": [], "system_design": [], "coding": []}}.get(field)


def extract_critical_skills(jd_analysis: Dict[str, Any]) -> List[str]:
    skills = list(jd_analysis.get("required_skills", []))
    skills.extend(jd_analysis.get("preferred_skills", [])[:3])
    return list(dict.fromkeys(skills))


def get_interview_difficulty_level(jd_analysis: Dict[str, Any]) -> float:
    adjustments = {"junior": -0.2, "mid": 0.0, "senior": 0.2, "lead": 0.3, "principal": 0.4, "executive": 0.4}
    difficulty = 0.5 + adjustments.get(jd_analysis.get("seniority_level", "mid"), 0.0)
    required_count = len(jd_analysis.get("required_skills", []))
    if required_count > 10: difficulty += 0.1
    elif required_count < 5: difficulty -= 0.1
    min_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0)
    if min_years > 5: difficulty += 0.1
    elif min_years < 2: difficulty -= 0.1
    return max(0.0, min(1.0, difficulty))


def generate_interview_strategy(jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
    seniority = jd_analysis.get("seniority_level", "mid")
    difficulty = get_interview_difficulty_level(jd_analysis)
    counts = {
        "junior": {"intro": 1, "behavioral": 2, "technical": 3, "deep_dive": 2, "closing": 1},
        "mid": {"intro": 1, "behavioral": 3, "technical": 4, "deep_dive": 2, "closing": 1},
        "senior": {"intro": 1, "behavioral": 3, "technical": 4, "deep_dive": 3, "closing": 1},
        "lead": {"intro": 1, "behavioral": 4, "technical": 3, "deep_dive": 3, "closing": 1},
        "principal": {"intro": 1, "behavioral": 4, "technical": 3, "deep_dive": 4, "closing": 1},
    }
    base_counts = counts.get(seniority, counts["mid"])
    nuance = jd_analysis.get("role_complexity_nuance", "").lower()
    if any(w in nuance for w in ["complex", "high-scale", "critical", "optimized", "architect"]):
        base_counts["technical"] += 1
        base_counts["deep_dive"] += 1
    return {
        "difficulty_level": difficulty,
        "total_duration_minutes": 45 if seniority in ["junior", "mid"] else 60,
        "question_counts": base_counts,
        "focus_areas": jd_analysis.get("interview_focus_areas", []),
        "critical_skills": extract_critical_skills(jd_analysis),
        "role_nuance": nuance,
        "behavioral_context": {"company_culture": jd_analysis.get("company_culture", {}), "key_responsibilities": jd_analysis.get("key_responsibilities", [])[:3]},
        "technical_depth": {
            "system_design_required": seniority in ["senior", "lead", "principal"] or "system design" in nuance,
            "coding_required": "coding" in jd_analysis.get("question_categories", {}),
            "architecture_focus": seniority in ["lead", "principal"] or "architecture" in nuance,
        },
    }


def compare_cv_to_jd(cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
    cv_skills = set(s.lower() for s in cv_analysis.get("skills", {}).get("technical", []))
    required = set(s.lower() for s in jd_analysis.get("required_skills", []))
    preferred = set(s.lower() for s in jd_analysis.get("preferred_skills", []))

    req_matches = cv_skills & required
    pref_matches = cv_skills & preferred
    cv_years = cv_analysis.get("years_of_experience", 0)
    req_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0) or 0
    pref_years = jd_analysis.get("required_experience", {}).get("years_preferred", 0) or 0

    levels = ["junior", "mid", "senior", "lead", "principal"]
    cv_lvl = levels.index(cv_analysis.get("seniority_level", "junior")) if cv_analysis.get("seniority_level") in levels else 0
    jd_lvl = levels.index(jd_analysis.get("seniority_level", "mid")) if jd_analysis.get("seniority_level") in levels else 1

    skill_score = (len(req_matches) / len(required) * 60 if required else 30) + (len(pref_matches) / len(preferred) * 20 if preferred else 10)
    exp_score = min(20, (cv_years / max(req_years, 1)) * 20)
    sen_score = max(0, 20 - abs(cv_lvl - jd_lvl) * 5)
    fit_score = min(100, skill_score + exp_score + sen_score)

    return {
        "overall_fit_score": fit_score,
        "skill_analysis": {
            "required_skills_match": list(req_matches),
            "preferred_skills_match": list(pref_matches),
            "missing_required_skills": list(required - cv_skills),
            "missing_preferred_skills": list(preferred - cv_skills),
            "additional_skills": list(cv_skills - required - preferred),
            "required_match_percentage": len(req_matches) / len(required) * 100 if required else 0,
        },
        "experience_analysis": {
            "cv_years": cv_years, "required_years": req_years, "preferred_years": pref_years,
            "experience_fit": "over-qualified" if cv_years > pref_years else "qualified" if cv_years >= req_years else "under-qualified",
        },
        "seniority_analysis": {
            "cv_level": cv_analysis.get("seniority_level"), "jd_level": jd_analysis.get("seniority_level"),
            "level_fit": "match" if cv_lvl == jd_lvl else "higher" if cv_lvl > jd_lvl else "lower",
        },
        "interview_recommendations": _generate_recommendations(cv_analysis, jd_analysis, fit_score),
    }


def _generate_recommendations(cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any], fit_score: float) -> List[str]:
    recs = []
    if fit_score >= 80: recs.append("Strong candidate — focus on cultural fit and advanced scenarios")
    elif fit_score >= 60: recs.append("Good candidate — validate key skills and assess learning ability")
    else: recs.append("Assess potential and growth mindset")
    cv_years = cv_analysis.get("years_of_experience", 0)
    req_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0)
    if cv_years < req_years: recs.append("Probe depth of experience — quality over quantity")
    elif cv_years > req_years * 2: recs.append("Assess motivation — avoid overqualification concerns")
    missing = set(s.lower() for s in jd_analysis.get("required_skills", [])) - set(s.lower() for s in cv_analysis.get("skills", {}).get("technical", []))
    if missing: recs.append(f"Explore learning approach for: {', '.join(list(missing)[:3])}")
    return recs
