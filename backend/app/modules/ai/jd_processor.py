"""
InterviewMe Job Description Processor

This module processes job description text using Groq AI to extract structured
information including requirements, responsibilities, and interview focus areas.

Engineering decisions:
- Single AI call for complete JD analysis (efficient token usage)
- Structured JSON output for interview strategy generation
- Seniority level detection for appropriate question difficulty
- Company culture analysis for behavioral question context
- Integration with CV analysis for gap identification
"""

import json
import re
from typing import Dict, Any, Optional, List
from groq import AsyncGroq

from app.config import settings
from app.core.exceptions import AIServiceError, ValidationError


# ============================================================
# GROQ CLIENT SETUP
# ============================================================

# Use the same client as CV processor
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)


# ============================================================
# JD ANALYSIS PROMPT
# ============================================================

JD_ANALYSIS_PROMPT = """You are an expert technical recruiter analyzing a job description. Your task is to extract structured information that will be used to conduct a tailored technical interview.

IMPORTANT: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Analyze the following job description and extract information in this exact JSON structure:

{{
  "role_title": "Exact job title from the posting",
  "company": "Company name if mentioned",
  "department": "Department or team if specified",
  "seniority_level": "junior|mid|senior|lead|principal|executive",
  "employment_type": "full-time|part-time|contract|internship",
  "location": "Work location or remote",
  "salary_range": "Salary information if mentioned",
  "required_skills": ["Must-have technical skills", "Programming languages", "Frameworks", "Tools"],
  "preferred_skills": ["Nice-to-have skills", "Bonus qualifications"],
  "required_experience": {{
    "years_minimum": 0,
    "years_preferred": 0,
    "specific_domains": ["Industry experience", "Specific technology experience"]
  }},
  "key_responsibilities": ["Primary job duties", "What they'll be doing day-to-day"],
  "technical_requirements": ["Specific technical tasks", "System design needs", "Architecture requirements"],
  "soft_skills": ["Communication", "Leadership", "Collaboration", "Problem-solving"],
  "education_requirements": ["Degree requirements", "Certifications", "Educational preferences"],
  "company_culture": {{
    "values": ["Company values mentioned"],
    "work_style": "collaborative|independent|hybrid",
    "pace": "fast-paced|steady|flexible",
    "size": "startup|small|medium|large|enterprise"
  }},
  "benefits": ["Compensation and benefits mentioned"],
  "growth_opportunities": ["Career development", "Learning opportunities"],
  "interview_focus_areas": ["Detailed list of technical topics, concepts, and behavioral traits to assess. Be as specific as possible (e.g., 'Distributed Systems Consistency' instead of 'System Design')"],
  "question_categories": {{
    "technical": ["Specific technical topics to cover"],
    "behavioral": ["Behavioral scenarios relevant to role"],
    "system_design": ["System design topics if applicable"],
    "coding": ["Programming challenges if applicable"]
  }},
  "role_complexity_nuance": "A brief description of what makes this specific role unique or particularly challenging (e.g. 'requires balancing legacy migration with greenfield development' or 'heavy focus on low-latency optimization')",
  "red_flags_to_watch": ["Potential concerns based on role requirements"],
  "success_metrics": ["How success will be measured in this role"]
}}

ANALYSIS GUIDELINES:
1. Infer seniority level from responsibilities, requirements, and language used
2. Extract both explicit and implied requirements
3. Identify the most critical skills vs nice-to-have
4. Suggest interview focus areas based on role criticality
5. Consider company culture for behavioral question context
6. If information is missing, use null or empty arrays
7. Be specific about technical requirements vs general business skills

JOB DESCRIPTION TEXT TO ANALYZE:
{jd_text}"""


# ============================================================
# JD PROCESSING FUNCTIONS
# ============================================================

async def analyze_jd_with_ai(jd_text: str) -> Dict[str, Any]:
    """
    Analyze job description text using Groq AI to extract structured information.
    
    Args:
        jd_text: Raw job description text content
        
    Returns:
        Structured JD analysis as dictionary
        
    Raises:
        AIServiceError: If AI processing fails
        ValidationError: If JD text is invalid
    """
    if not jd_text or len(jd_text.strip()) < 100:
        raise ValidationError("Job description text is too short for meaningful analysis")
    
    try:
        # Prepare the prompt
        prompt = JD_ANALYSIS_PROMPT.format(jd_text=jd_text)
        
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
        try:
            jd_analysis = json.loads(ai_response)
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
                    ai_response = ai_response[json_start:json_end].strip()
                    jd_analysis = json.loads(ai_response)
                else:
                    raise AIServiceError(f"Failed to parse AI response as JSON: {e}")
            else:
                raise AIServiceError(f"Failed to parse AI response as JSON: {e}")
        
        # Validate and set defaults for required fields
        required_fields = ["role_title", "seniority_level", "required_skills", "key_responsibilities"]
        for field in required_fields:
            if field not in jd_analysis:
                jd_analysis[field] = get_jd_default_value(field)
        
        # Ensure required_experience has proper structure
        if "required_experience" not in jd_analysis or not isinstance(jd_analysis["required_experience"], dict):
            jd_analysis["required_experience"] = {
                "years_minimum": 0,
                "years_preferred": 0,
                "specific_domains": []
            }
        
        # Ensure company_culture has proper structure
        if "company_culture" not in jd_analysis or not isinstance(jd_analysis["company_culture"], dict):
            jd_analysis["company_culture"] = {
                "values": [],
                "work_style": "collaborative",
                "pace": "steady",
                "size": "medium"
            }
        
        # Ensure question_categories has proper structure
        if "question_categories" not in jd_analysis or not isinstance(jd_analysis["question_categories"], dict):
            jd_analysis["question_categories"] = {
                "technical": [],
                "behavioral": [],
                "system_design": [],
                "coding": []
            }
        
        # Add metadata
        jd_analysis["_metadata"] = {
            "processed_at": "2024-01-01T00:00:00Z",  # Will be set by caller
            "ai_model": settings.GROQ_MODEL,
            "text_length": len(jd_text),
            "word_count": len(jd_text.split()),
        }
        
        return jd_analysis
        
    except AIServiceError as e:
        if settings.is_development:
            return build_fallback_jd_analysis(jd_text, str(e))
        raise
    except ValidationError:
        raise
    except Exception as e:
        if settings.is_development:
            return build_fallback_jd_analysis(jd_text, str(e))
        raise AIServiceError(f"Job description analysis failed: {str(e)}")


def build_fallback_jd_analysis(jd_text: str, error_detail: str) -> Dict[str, Any]:
    """Generate deterministic JD analysis when AI is unavailable in development."""
    lowered = jd_text.lower()

    role_title = "Software Engineer"
    role_match = re.search(r"(senior|junior|lead|principal)?\s*(software|backend|frontend|full stack)\s*engineer", lowered)
    if role_match:
        role_title = role_match.group(0).title()

    tech_candidates = [
        "python", "javascript", "typescript", "java", "go", "react", "node",
        "fastapi", "django", "postgresql", "redis", "docker", "kubernetes", "aws"
    ]
    required = [skill for skill in tech_candidates if re.search(rf"\b{re.escape(skill)}\b", lowered)]

    years_match = re.search(r"(\d+)\s*\+?\s*(years?|yrs?)", lowered)
    years_minimum = int(years_match.group(1)) if years_match else 0

    return {
        "role_title": role_title,
        "company": None,
        "department": None,
        "seniority_level": "senior" if "senior" in lowered else "mid",
        "employment_type": "full-time",
        "location": None,
        "salary_range": None,
        "required_skills": required,
        "preferred_skills": [],
        "required_experience": {
            "years_minimum": years_minimum,
            "years_preferred": max(years_minimum, 0),
            "specific_domains": [],
        },
        "key_responsibilities": [],
        "technical_requirements": required[:5],
        "soft_skills": ["Communication", "Collaboration", "Problem-solving"],
        "education_requirements": [],
        "company_culture": {
            "values": [],
            "work_style": "collaborative",
            "pace": "steady",
            "size": "medium",
        },
        "benefits": [],
        "growth_opportunities": [],
        "interview_focus_areas": ["Core technical fundamentals", "Communication"],
        "question_categories": {
            "technical": required[:6],
            "behavioral": ["Conflict handling", "Collaboration"],
            "system_design": ["Scalability"] if years_minimum >= 3 else [],
            "coding": ["Problem solving"],
        },
        "red_flags_to_watch": [],
        "success_metrics": [],
        "_metadata": {
            "processed_at": "2024-01-01T00:00:00Z",
            "ai_model": f"fallback:{settings.GROQ_MODEL}",
            "text_length": len(jd_text),
            "word_count": len(jd_text.split()),
            "fallback": True,
            "fallback_reason": error_detail[:300],
        },
    }


def get_jd_default_value(field: str) -> Any:
    """Get default value for missing JD analysis fields."""
    defaults = {
        "role_title": "Software Engineer",
        "company": "Not specified",
        "seniority_level": "mid",
        "employment_type": "full-time",
        "required_skills": [],
        "preferred_skills": [],
        "key_responsibilities": [],
        "technical_requirements": [],
        "soft_skills": [],
        "interview_focus_areas": [],
        "question_categories": {
            "technical": [],
            "behavioral": [],
            "system_design": [],
            "coding": []
        }
    }
    return defaults.get(field, None)


# ============================================================
# JD ANALYSIS UTILITIES
# ============================================================

def extract_critical_skills(jd_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract the most critical skills from JD analysis.
    
    Args:
        jd_analysis: Structured JD analysis
        
    Returns:
        List of critical skills (required + top preferred)
    """
    critical_skills = []
    
    # Add all required skills
    if jd_analysis.get("required_skills"):
        critical_skills.extend(jd_analysis["required_skills"])
    
    # Add top 3 preferred skills
    if jd_analysis.get("preferred_skills"):
        critical_skills.extend(jd_analysis["preferred_skills"][:3])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(critical_skills))


def get_interview_difficulty_level(jd_analysis: Dict[str, Any]) -> float:
    """
    Determine interview difficulty level based on JD analysis.
    
    Args:
        jd_analysis: Structured JD analysis
        
    Returns:
        Difficulty level (0.0 = easy, 1.0 = hard)
    """
    base_difficulty = 0.5  # Default medium difficulty
    
    # Adjust based on seniority level
    seniority_adjustments = {
        "junior": -0.2,
        "mid": 0.0,
        "senior": 0.2,
        "lead": 0.3,
        "principal": 0.4,
        "executive": 0.4
    }
    
    seniority = jd_analysis.get("seniority_level", "mid")
    difficulty = base_difficulty + seniority_adjustments.get(seniority, 0.0)
    
    # Adjust based on required skills count
    required_skills_count = len(jd_analysis.get("required_skills", []))
    if required_skills_count > 10:
        difficulty += 0.1
    elif required_skills_count < 5:
        difficulty -= 0.1
    
    # Adjust based on experience requirements
    min_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0)
    if min_years > 5:
        difficulty += 0.1
    elif min_years < 2:
        difficulty -= 0.1
    
    # Clamp to valid range
    return max(0.0, min(1.0, difficulty))


def generate_interview_strategy(jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate interview strategy based on JD analysis.
    
    Args:
        jd_analysis: Structured JD analysis
        
    Returns:
        Interview strategy configuration
    """
    seniority = jd_analysis.get("seniority_level", "mid")
    difficulty = get_interview_difficulty_level(jd_analysis)
    
    # Base question counts by seniority
    question_counts = {
        "junior": {"intro": 1, "behavioral": 2, "technical": 3, "deep_dive": 2, "closing": 1},
        "mid": {"intro": 1, "behavioral": 3, "technical": 4, "deep_dive": 2, "closing": 1},
        "senior": {"intro": 1, "behavioral": 3, "technical": 4, "deep_dive": 3, "closing": 1},
        "lead": {"intro": 1, "behavioral": 4, "technical": 3, "deep_dive": 3, "closing": 1},
        "principal": {"intro": 1, "behavioral": 4, "technical": 3, "deep_dive": 4, "closing": 1},
    }
    
    base_counts = question_counts.get(seniority, question_counts["mid"])
    
    # Increase question counts for complex roles
    role_nuance = jd_analysis.get("role_complexity_nuance", "").lower()
    if any(word in role_nuance for word in ["complex", "high-scale", "critical", "optimized", "architect"]):
        base_counts["technical"] += 1
        base_counts["deep_dive"] += 1
    
    return {
        "difficulty_level": difficulty,
        "total_duration_minutes": 45 if seniority in ["junior", "mid"] else 60,
        "question_counts": base_counts,
        "focus_areas": jd_analysis.get("interview_focus_areas", []),
        "critical_skills": extract_critical_skills(jd_analysis),
        "role_nuance": role_nuance,
        "behavioral_context": {
            "company_culture": jd_analysis.get("company_culture", {}),
            "key_responsibilities": jd_analysis.get("key_responsibilities", [])[:3],
        },
        "technical_depth": {
            "system_design_required": seniority in ["senior", "lead", "principal"] or "system design" in role_nuance,
            "coding_required": "coding" in jd_analysis.get("question_categories", {}),
            "architecture_focus": seniority in ["lead", "principal"] or "architecture" in role_nuance,
        }
    }


def compare_cv_to_jd(cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare CV analysis against JD requirements to identify fit and gaps.
    
    Args:
        cv_analysis: Structured CV analysis
        jd_analysis: Structured JD analysis
        
    Returns:
        Comparison analysis with fit score and recommendations
    """
    # Extract skills for comparison
    cv_skills = set(skill.lower() for skill in cv_analysis.get("skills", {}).get("technical", []))
    required_skills = set(skill.lower() for skill in jd_analysis.get("required_skills", []))
    preferred_skills = set(skill.lower() for skill in jd_analysis.get("preferred_skills", []))
    
    # Calculate skill matches
    required_matches = cv_skills & required_skills
    preferred_matches = cv_skills & preferred_skills
    missing_required = required_skills - cv_skills
    missing_preferred = preferred_skills - cv_skills
    
    # Calculate experience fit
    cv_years = cv_analysis.get("years_of_experience", 0)
    required_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0) or 0
    preferred_years = jd_analysis.get("required_experience", {}).get("years_preferred", 0) or 0
    
    # Calculate seniority fit
    cv_seniority = cv_analysis.get("seniority_level", "junior")
    jd_seniority = jd_analysis.get("seniority_level", "mid")
    
    seniority_levels = ["junior", "mid", "senior", "lead", "principal"]
    cv_level_index = seniority_levels.index(cv_seniority) if cv_seniority in seniority_levels else 0
    jd_level_index = seniority_levels.index(jd_seniority) if jd_seniority in seniority_levels else 1
    
    # Calculate overall fit score (0-100)
    skill_score = (len(required_matches) / len(required_skills) * 60) if required_skills else 30
    skill_score += (len(preferred_matches) / len(preferred_skills) * 20) if preferred_skills else 10
    
    experience_score = min(20, (cv_years / max(required_years, 1)) * 20)
    
    seniority_score = max(0, 20 - abs(cv_level_index - jd_level_index) * 5)
    
    overall_fit_score = skill_score + experience_score + seniority_score
    
    return {
        "overall_fit_score": min(100, overall_fit_score),
        "skill_analysis": {
            "required_skills_match": list(required_matches),
            "preferred_skills_match": list(preferred_matches),
            "missing_required_skills": list(missing_required),
            "missing_preferred_skills": list(missing_preferred),
            "additional_skills": list(cv_skills - required_skills - preferred_skills),
            "required_match_percentage": len(required_matches) / len(required_skills) * 100 if required_skills else 0,
        },
        "experience_analysis": {
            "cv_years": cv_years,
            "required_years": required_years,
            "preferred_years": preferred_years,
            "experience_fit": "over-qualified" if cv_years > preferred_years else "qualified" if cv_years >= required_years else "under-qualified"
        },
        "seniority_analysis": {
            "cv_level": cv_seniority,
            "jd_level": jd_seniority,
            "level_fit": "match" if cv_seniority == jd_seniority else "higher" if cv_level_index > jd_level_index else "lower"
        },
        "interview_recommendations": generate_interview_recommendations(cv_analysis, jd_analysis, overall_fit_score)
    }


def generate_interview_recommendations(cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any], fit_score: float) -> List[str]:
    """Generate specific interview recommendations based on CV-JD comparison."""
    recommendations = []
    
    # Based on fit score
    if fit_score >= 80:
        recommendations.append("Strong candidate - focus on cultural fit and advanced technical scenarios")
    elif fit_score >= 60:
        recommendations.append("Good candidate - validate key skills and assess learning ability")
    else:
        recommendations.append("Assess potential and growth mindset - may need additional training")
    
    # Based on experience level
    cv_years = cv_analysis.get("years_of_experience", 0)
    required_years = jd_analysis.get("required_experience", {}).get("years_minimum", 0)
    
    if cv_years < required_years:
        recommendations.append("Probe depth of experience - quality over quantity")
    elif cv_years > required_years * 2:
        recommendations.append("Assess motivation for this role level - avoid overqualification concerns")
    
    # Based on skill gaps
    cv_skills = set(skill.lower() for skill in cv_analysis.get("skills", {}).get("technical", []))
    required_skills = set(skill.lower() for skill in jd_analysis.get("required_skills", []))
    missing_skills = required_skills - cv_skills
    
    if missing_skills:
        recommendations.append(f"Explore learning approach for: {', '.join(list(missing_skills)[:3])}")
    
    return recommendations