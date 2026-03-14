"""
InterviewMe Interview Schemas

This module defines Pydantic schemas for interview-related API requests and responses.
These schemas provide type safety, validation, and automatic API documentation.

Engineering decisions:
- Separate request and response schemas for clear API contracts
- Optional fields with sensible defaults
- Comprehensive validation rules
- Nested schemas for complex data structures
- Consistent naming conventions
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
import uuid

from app.models.interview import InterviewStatus, InterviewPhase


def _enum_or_str(value: Any) -> Any:
    """Return enum value when available, otherwise return the original value."""
    return value.value if hasattr(value, "value") else value


def _loaded_attr(obj: Any, attr_name: str) -> Any:
    """Get relationship attribute only if already loaded, else return None."""
    state_dict = getattr(obj, "__dict__", {})
    if attr_name in state_dict:
        return state_dict.get(attr_name)
    return None


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateInterviewRequest(BaseModel):
    """Request schema for creating a new interview."""
    
    jd_text: str = Field(
        ...,
        min_length=100,
        max_length=10000,
        description="Job description text content"
    )
    
    target_company: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional company name override"
    )
    
    @validator('jd_text')
    def validate_jd_text(cls, v):
        """Validate job description text content."""
        if not v.strip():
            raise ValueError("Job description cannot be empty")
        return v.strip()
    
    @validator('target_company')
    def validate_target_company(cls, v):
        """Validate company name."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class UpdateInterviewRequest(BaseModel):
    """Request schema for updating interview metadata."""
    
    target_company: Optional[str] = Field(
        None,
        max_length=255,
        description="Company name"
    )
    
    @validator('target_company')
    def validate_target_company(cls, v):
        """Validate company name."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class InterviewActionRequest(BaseModel):
    """Request schema for interview actions (start, complete, etc.)."""
    
    action: str = Field(
        ...,
        description="Action to perform: 'start', 'complete', 'pause'"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional action metadata"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action type."""
        allowed_actions = ['start', 'complete', 'pause']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class InterviewSummaryResponse(BaseModel):
    """Summary response schema for interview list items."""
    
    id: str
    user_id: str
    status: str
    target_role: Optional[str]
    target_company: Optional[str]
    current_phase: Optional[str]
    current_turn: int
    created_at: datetime
    completed_at: Optional[datetime]
    total_duration_seconds: Optional[float]
    turn_count: int
    has_feedback: bool
    
    class Config:
        from_attributes = True


class SkillAnalysisResponse(BaseModel):
    """Schema for skill analysis data."""
    
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ExperienceItemResponse(BaseModel):
    """Schema for experience item."""
    
    role: str
    company: str
    duration: str
    key_achievements: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)


class CVAnalysisResponse(BaseModel):
    """Schema for CV analysis data."""
    
    candidate_name: str
    years_of_experience: int
    current_role: str
    seniority_level: str
    skills: SkillAnalysisResponse
    experience: List[ExperienceItemResponse] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    notable_points: List[str] = Field(default_factory=list)
    potential_gaps: List[str] = Field(default_factory=list)
    interview_focus_areas: List[str] = Field(default_factory=list)


class JDAnalysisResponse(BaseModel):
    """Schema for job description analysis data."""
    
    role_title: str
    company: Optional[str]
    seniority_level: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    technical_requirements: List[str] = Field(default_factory=list)
    interview_focus_areas: List[str] = Field(default_factory=list)
    required_experience: Dict[str, Any] = Field(default_factory=dict)
    company_culture: Dict[str, Any] = Field(default_factory=dict)


class SkillGapAnalysisResponse(BaseModel):
    """Schema for skill gap analysis."""
    
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)
    match_percentage: float = 0.0


class InterviewDetailResponse(BaseModel):
    """Detailed response schema for individual interview."""
    
    id: str
    user_id: str
    status: str
    target_role: Optional[str]
    target_company: Optional[str]
    current_phase: Optional[str]
    current_turn: int
    created_at: datetime
    completed_at: Optional[datetime]
    total_duration_seconds: Optional[float]
    turn_count: int
    has_feedback: bool
    
    # Analysis data (optional, included when requested)
    cv_analysis: Optional[CVAnalysisResponse] = None
    jd_analysis: Optional[JDAnalysisResponse] = None
    skill_gap_analysis: Optional[SkillGapAnalysisResponse] = None
    
    class Config:
        from_attributes = True


class TurnResponse(BaseModel):
    """Response schema for interview turn."""
    
    id: str
    interview_id: str
    turn_number: int
    phase: str
    ai_question: str
    user_answer: Optional[str]
    duration_seconds: Optional[float]
    difficulty_level: Optional[float]
    created_at: datetime
    has_answer: bool
    has_evaluation: bool
    evaluation: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class InterviewListResponse(BaseModel):
    """Response schema for interview list with pagination."""
    
    interviews: List[InterviewSummaryResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class InterviewStatsResponse(BaseModel):
    """Response schema for user interview statistics."""
    
    total_interviews: int
    completed_interviews: int
    in_progress_interviews: int
    failed_interviews: int
    completion_rate: float
    average_score: Optional[float]
    total_time_minutes: float
    most_recent_interview: Optional[Dict[str, Any]]
    role_distribution: Dict[str, int]
    top_skills: Dict[str, int]


# ============================================================
# FILE UPLOAD SCHEMAS
# ============================================================

class FileUploadResponse(BaseModel):
    """Response schema for file upload operations."""
    
    filename: str
    file_type: str
    file_size_bytes: int
    text_length: int
    word_count: int
    processing_time_seconds: float
    extracted_text_preview: str = Field(
        description="First 200 characters of extracted text"
    )


class FileInfoResponse(BaseModel):
    """Response schema for file information."""
    
    filename: Optional[str]
    file_type: str
    content_type: Optional[str]
    is_supported: bool
    max_allowed_size_mb: int
    estimated_processing_time_seconds: Optional[float] = None


# ============================================================
# ERROR SCHEMAS
# ============================================================

class InterviewErrorResponse(BaseModel):
    """Response schema for interview-specific errors."""
    
    error: str
    message: str
    interview_id: Optional[str] = None
    current_status: Optional[str] = None
    allowed_actions: List[str] = Field(default_factory=list)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def create_interview_summary_response(interview) -> InterviewSummaryResponse:
    """Create interview summary response from model."""
    loaded_turns = _loaded_attr(interview, 'turns')
    loaded_feedback = _loaded_attr(interview, 'feedback')

    return InterviewSummaryResponse(
        id=str(interview.id),
        user_id=str(interview.user_id),
        status=_enum_or_str(interview.status),
        target_role=interview.target_role,
        target_company=interview.target_company,
        current_phase=_enum_or_str(interview.current_phase) if interview.current_phase else None,
        current_turn=interview.current_turn,
        created_at=interview.created_at,
        completed_at=interview.completed_at,
        total_duration_seconds=interview.total_duration_seconds,
        turn_count=len(loaded_turns) if loaded_turns else 0,
        has_feedback=loaded_feedback is not None
    )


def create_interview_detail_response(
    interview, 
    include_analysis: bool = False
) -> InterviewDetailResponse:
    """Create detailed interview response from model."""
    loaded_turns = _loaded_attr(interview, 'turns')
    loaded_feedback = _loaded_attr(interview, 'feedback')

    response_data = {
        "id": str(interview.id),
        "user_id": str(interview.user_id),
        "status": _enum_or_str(interview.status),
        "target_role": interview.target_role,
        "target_company": interview.target_company,
        "current_phase": _enum_or_str(interview.current_phase) if interview.current_phase else None,
        "current_turn": interview.current_turn,
        "created_at": interview.created_at,
        "completed_at": interview.completed_at,
        "total_duration_seconds": interview.total_duration_seconds,
        "turn_count": len(loaded_turns) if loaded_turns else 0,
        "has_feedback": loaded_feedback is not None
    }
    
    if include_analysis:
        # Add CV analysis
        if interview.cv_analysis:
            cv_data = interview.cv_analysis.copy()
            response_data["cv_analysis"] = CVAnalysisResponse(
                candidate_name=cv_data.get("candidate_name", "Unknown"),
                years_of_experience=cv_data.get("years_of_experience", 0),
                current_role=cv_data.get("current_role", "Not specified"),
                seniority_level=cv_data.get("seniority_level", "junior"),
                skills=SkillAnalysisResponse(
                    technical=cv_data.get("skills", {}).get("technical", []),
                    soft=cv_data.get("skills", {}).get("soft", [])
                ),
                experience=[
                    ExperienceItemResponse(**exp) for exp in cv_data.get("experience", [])
                ],
                education=cv_data.get("education", []),
                projects=cv_data.get("projects", []),
                certifications=cv_data.get("certifications", []),
                notable_points=cv_data.get("notable_points", []),
                potential_gaps=cv_data.get("potential_gaps", []),
                interview_focus_areas=cv_data.get("interview_focus_areas", [])
            )
        
        # Add JD analysis
        if interview.jd_analysis:
            jd_data = interview.jd_analysis.copy()
            response_data["jd_analysis"] = JDAnalysisResponse(
                role_title=jd_data.get("role_title", "Software Engineer"),
                company=jd_data.get("company"),
                seniority_level=jd_data.get("seniority_level", "mid"),
                required_skills=jd_data.get("required_skills", []),
                preferred_skills=jd_data.get("preferred_skills", []),
                key_responsibilities=jd_data.get("key_responsibilities", []),
                technical_requirements=jd_data.get("technical_requirements", []),
                interview_focus_areas=jd_data.get("interview_focus_areas", []),
                required_experience=jd_data.get("required_experience", {}),
                company_culture=jd_data.get("company_culture", {})
            )
        
        # Add skill gap analysis
        if hasattr(interview, 'get_skill_gap_analysis'):
            gap_analysis = interview.get_skill_gap_analysis()
            response_data["skill_gap_analysis"] = SkillGapAnalysisResponse(**gap_analysis)
    
    return InterviewDetailResponse(**response_data)