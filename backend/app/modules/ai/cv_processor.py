"""
InterviewMe CV Processor

This module processes CV text using Groq AI to extract structured information
including skills, experience, education, and potential gaps.

Engineering decisions:
- Single AI call for complete CV analysis (efficient token usage)
- Structured JSON output for queryable data storage
- Comprehensive prompt engineering for consistent results
- Error handling for AI service failures
- Token counting and optimization
"""

import json
import re
from typing import Dict, Any, Optional
from groq import AsyncGroq

from app.config import settings
from app.core.exceptions import AIServiceError, ValidationError


# ============================================================
# GROQ CLIENT SETUP
# ============================================================

# Initialize async Groq client
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)


# ============================================================
# CV ANALYSIS PROMPT
# ============================================================

CV_ANALYSIS_PROMPT = """You are an expert HR professional and career coach analyzing a candidate's CV. Your task is to extract structured information that will be used to conduct a tailored technical interview.

IMPORTANT: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Analyze the following CV text and extract information in this exact JSON structure:

{{
  "candidate_name": "Full name of the candidate",
  "years_of_experience": 0,
  "current_role": "Most recent job title",
  "seniority_level": "junior|mid|senior|lead|principal",
  "skills": {{
    "technical": ["List of technical skills, programming languages, frameworks, tools"],
    "soft": ["Communication", "Leadership", "Problem-solving", etc.]
  }},
  "experience": [
    {{
      "role": "Job title",
      "company": "Company name",
      "duration": "Time period (e.g., '2 years', '6 months')",
      "key_achievements": ["Notable accomplishments", "Quantified results"],
      "technologies_used": ["Tech stack used in this role"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "School/University name",
      "year": "Graduation year or 'ongoing'",
      "relevant_coursework": ["Relevant courses if mentioned"]
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech stack used"],
      "achievements": ["Key outcomes or metrics"]
    }}
  ],
  "certifications": ["List of professional certifications"],
  "notable_points": ["Unique achievements", "Publications", "Awards", "Open source contributions"],
  "potential_gaps": ["Areas where experience might be lacking", "Skills not mentioned but typically expected"],
  "interview_focus_areas": ["Areas to probe deeper", "Strengths to validate", "Gaps to explore"]
}}

ANALYSIS GUIDELINES:
1. Be thorough but concise
2. Infer seniority level from experience and responsibilities
3. Extract both explicitly mentioned and implied skills
4. Identify potential red flags or gaps
5. Suggest interview focus areas based on the role level
6. If information is missing, use null or empty arrays, don't make assumptions
7. For years_of_experience, calculate total professional experience

CV TEXT TO ANALYZE:
{cv_text}"""


# ============================================================
# CV PROCESSING FUNCTIONS
# ============================================================

async def analyze_cv_with_ai(cv_text: str) -> Dict[str, Any]:
    """
    Analyze CV text using Groq AI to extract structured information.
    
    Args:
        cv_text: Raw CV text content
        
    Returns:
        Structured CV analysis as dictionary
        
    Raises:
        AIServiceError: If AI processing fails
        ValidationError: If CV text is invalid
    """
    if not cv_text or len(cv_text.strip()) < 50:
        raise ValidationError("CV text is too short for meaningful analysis")
    
    try:
        # Prepare the prompt
        prompt = CV_ANALYSIS_PROMPT.format(cv_text=cv_text)
        
        # Make API call to Groq
        response = await groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent structured output
            max_tokens=settings.GROQ_MAX_TOKENS,
            top_p=0.9,
        )
        
        # Extract response content
        if not response.choices or not response.choices[0].message:
            raise AIServiceError("Empty response from AI service")
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        cv_analysis = None
        try:
            cv_analysis = json.loads(ai_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response if it's wrapped in markdown
            if "```" in ai_response:
                # Handle both ```json and ``` formats
                if "```json" in ai_response:
                    json_start = ai_response.find("```json") + 7
                else:
                    json_start = ai_response.find("```") + 3
                
                json_end = ai_response.find("```", json_start)
                if json_end > json_start:
                    json_content = ai_response[json_start:json_end].strip()
                    try:
                        cv_analysis = json.loads(json_content)
                    except json.JSONDecodeError as e2:
                        raise AIServiceError(f"Failed to parse extracted JSON: {e2}. Content: {json_content[:100]}...")
                else:
                    raise AIServiceError(f"Failed to find closing markdown: {e}. Content: {ai_response[:100]}...")
            else:
                raise AIServiceError(f"Failed to parse AI response as JSON: {e}. Content: {ai_response[:100]}...")
        
        if cv_analysis is None:
            raise AIServiceError("Failed to parse CV analysis from AI response")
        
        # Validate required fields
        required_fields = ["candidate_name", "years_of_experience", "skills", "experience"]
        for field in required_fields:
            if field not in cv_analysis:
                cv_analysis[field] = get_default_value(field)
        
        # Ensure skills has required structure
        if "skills" in cv_analysis and not isinstance(cv_analysis["skills"], dict):
            cv_analysis["skills"] = {"technical": [], "soft": []}
        elif "skills" in cv_analysis:
            if "technical" not in cv_analysis["skills"]:
                cv_analysis["skills"]["technical"] = []
            if "soft" not in cv_analysis["skills"]:
                cv_analysis["skills"]["soft"] = []
        
        # Add metadata
        cv_analysis["_metadata"] = {
            "processed_at": "2024-01-01T00:00:00Z",  # Will be set by caller
            "ai_model": settings.GROQ_MODEL,
            "text_length": len(cv_text),
            "word_count": len(cv_text.split()),
        }
        
        return cv_analysis
        
    except AIServiceError as e:
        if settings.is_development:
            return build_fallback_cv_analysis(cv_text, str(e))
        raise
    except ValidationError:
        raise
    except Exception as e:
        if settings.is_development:
            return build_fallback_cv_analysis(cv_text, str(e))
        raise AIServiceError(f"CV analysis failed: {str(e)}")


def build_fallback_cv_analysis(cv_text: str, error_detail: str) -> Dict[str, Any]:
    """Generate a minimal deterministic CV analysis when AI is unavailable in development."""
    lines = [line.strip() for line in cv_text.splitlines() if line.strip()]
    candidate_name = lines[0] if lines else "Unknown"

    tech_candidates = [
        "python", "javascript", "typescript", "java", "c++", "go", "rust",
        "fastapi", "django", "flask", "react", "next.js", "node", "postgresql",
        "mysql", "redis", "docker", "kubernetes", "aws", "azure", "gcp"
    ]
    found_skills = []
    lowered = cv_text.lower()
    for skill in tech_candidates:
        if re.search(rf"\b{re.escape(skill)}\b", lowered):
            found_skills.append(skill)

    years_match = re.search(r"(\d+)\s*\+?\s*(years?|yrs?)", lowered)
    years_of_experience = int(years_match.group(1)) if years_match else 0

    return {
        "candidate_name": candidate_name,
        "years_of_experience": years_of_experience,
        "current_role": "Software Engineer",
        "seniority_level": "mid" if years_of_experience >= 3 else "junior",
        "skills": {
            "technical": found_skills[:12],
            "soft": ["Communication", "Problem-solving"],
        },
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "notable_points": [],
        "potential_gaps": [],
        "interview_focus_areas": ["Technical depth", "Communication clarity"],
        "_metadata": {
            "processed_at": "2024-01-01T00:00:00Z",
            "ai_model": f"fallback:{settings.GROQ_MODEL}",
            "text_length": len(cv_text),
            "word_count": len(cv_text.split()),
            "fallback": True,
            "fallback_reason": error_detail[:300],
        },
    }


def get_default_value(field: str) -> Any:
    """Get default value for missing CV analysis fields."""
    defaults = {
        "candidate_name": "Unknown",
        "years_of_experience": 0,
        "current_role": "Not specified",
        "seniority_level": "junior",
        "skills": {"technical": [], "soft": []},
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "notable_points": [],
        "potential_gaps": [],
        "interview_focus_areas": []
    }
    return defaults.get(field, None)


# ============================================================
# CV ANALYSIS UTILITIES
# ============================================================

def extract_key_skills(cv_analysis: Dict[str, Any], limit: int = 10) -> list[str]:
    """
    Extract top technical skills from CV analysis.
    
    Args:
        cv_analysis: Structured CV analysis
        limit: Maximum number of skills to return
        
    Returns:
        List of key technical skills
    """
    if not cv_analysis.get("skills", {}).get("technical"):
        return []
    
    technical_skills = cv_analysis["skills"]["technical"]
    
    # Return up to limit skills
    return technical_skills[:limit]


def get_experience_summary(cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate experience summary from CV analysis.
    
    Args:
        cv_analysis: Structured CV analysis
        
    Returns:
        Experience summary dictionary
    """
    experience = cv_analysis.get("experience", [])
    
    return {
        "total_years": cv_analysis.get("years_of_experience", 0),
        "current_role": cv_analysis.get("current_role", "Not specified"),
        "seniority_level": cv_analysis.get("seniority_level", "junior"),
        "companies_count": len(experience),
        "recent_companies": [exp.get("company", "") for exp in experience[:3]],
        "key_technologies": extract_key_skills(cv_analysis, 5),
    }


def identify_skill_gaps(cv_analysis: Dict[str, Any], required_skills: list[str]) -> Dict[str, list[str]]:
    """
    Compare CV skills against required skills to identify gaps.
    
    Args:
        cv_analysis: Structured CV analysis
        required_skills: List of required skills from job description
        
    Returns:
        Dictionary with matching and missing skills
    """
    cv_skills = set(skill.lower() for skill in extract_key_skills(cv_analysis, 20))
    required_skills_lower = set(skill.lower() for skill in required_skills)
    
    return {
        "matching_skills": list(cv_skills & required_skills_lower),
        "missing_skills": list(required_skills_lower - cv_skills),
        "additional_skills": list(cv_skills - required_skills_lower),
        "match_percentage": len(cv_skills & required_skills_lower) / len(required_skills_lower) * 100 if required_skills_lower else 0
    }


def generate_interview_focus_areas(cv_analysis: Dict[str, Any]) -> list[str]:
    """
    Generate suggested interview focus areas based on CV analysis.
    
    Args:
        cv_analysis: Structured CV analysis
        
    Returns:
        List of suggested focus areas for the interview
    """
    focus_areas = []
    
    # Add predefined focus areas from analysis
    if cv_analysis.get("interview_focus_areas"):
        focus_areas.extend(cv_analysis["interview_focus_areas"])
    
    # Add areas based on experience level
    seniority = cv_analysis.get("seniority_level", "junior")
    if seniority in ["senior", "lead", "principal"]:
        focus_areas.extend(["System design", "Leadership experience", "Mentoring"])
    elif seniority == "mid":
        focus_areas.extend(["Problem-solving approach", "Code quality", "Collaboration"])
    else:
        focus_areas.extend(["Learning ability", "Basic concepts", "Growth potential"])
    
    # Add areas based on potential gaps
    if cv_analysis.get("potential_gaps"):
        focus_areas.extend([f"Explore: {gap}" for gap in cv_analysis["potential_gaps"][:2]])
    
    # Remove duplicates and limit
    return list(dict.fromkeys(focus_areas))[:8]