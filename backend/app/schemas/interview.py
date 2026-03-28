from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import uuid

from app.models.interview import InterviewStatus, InterviewPhase


def _enum_or_str(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _loaded_attr(obj: Any, attr_name: str) -> Any:
    state_dict = getattr(obj, "__dict__", {})
    return state_dict.get(attr_name) if attr_name in state_dict else None


class CreateInterviewRequest(BaseModel):
    jd_text: str = Field(..., min_length=100, max_length=10000)
    target_company: Optional[str] = Field(None, max_length=255)

    @validator('jd_text')
    def validate_jd_text(cls, v):
        if not v.strip():
            raise ValueError("Job description cannot be empty")
        return v.strip()

    @validator('target_company')
    def validate_target_company(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class UpdateInterviewRequest(BaseModel):
    target_company: Optional[str] = Field(None, max_length=255)

    @validator('target_company')
    def validate_target_company(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class InterviewActionRequest(BaseModel):
    action: str = Field(...)
    metadata: Optional[Dict[str, Any]] = None

    @validator('action')
    def validate_action(cls, v):
        if v not in ['start', 'complete', 'pause']:
            raise ValueError("Action must be one of: start, complete, pause")
        return v


class InterviewSummaryResponse(BaseModel):
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
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ExperienceItemResponse(BaseModel):
    role: str
    company: str
    duration: str
    key_achievements: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)


class CVAnalysisResponse(BaseModel):
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
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)
    match_percentage: float = 0.0


class InterviewDetailResponse(BaseModel):
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
    cv_analysis: Optional[CVAnalysisResponse] = None
    jd_analysis: Optional[JDAnalysisResponse] = None
    skill_gap_analysis: Optional[SkillGapAnalysisResponse] = None

    class Config:
        from_attributes = True


class TurnResponse(BaseModel):
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
    interviews: List[InterviewSummaryResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class InterviewStatsResponse(BaseModel):
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


class FileUploadResponse(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int
    text_length: int
    word_count: int
    processing_time_seconds: float
    extracted_text_preview: str


class FileInfoResponse(BaseModel):
    filename: Optional[str]
    file_type: str
    content_type: Optional[str]
    is_supported: bool
    max_allowed_size_mb: int
    estimated_processing_time_seconds: Optional[float] = None


class InterviewErrorResponse(BaseModel):
    error: str
    message: str
    interview_id: Optional[str] = None
    current_status: Optional[str] = None
    allowed_actions: List[str] = Field(default_factory=list)


def create_interview_summary_response(interview) -> InterviewSummaryResponse:
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
        has_feedback=loaded_feedback is not None,
    )


def create_interview_detail_response(interview, include_analysis: bool = False) -> InterviewDetailResponse:
    loaded_turns = _loaded_attr(interview, 'turns')
    loaded_feedback = _loaded_attr(interview, 'feedback')
    data = {
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
        "has_feedback": loaded_feedback is not None,
    }
    if include_analysis:
        if interview.cv_analysis:
            cv = interview.cv_analysis.copy()
            data["cv_analysis"] = CVAnalysisResponse(
                candidate_name=cv.get("candidate_name", "Unknown"),
                years_of_experience=cv.get("years_of_experience", 0),
                current_role=cv.get("current_role", "Not specified"),
                seniority_level=cv.get("seniority_level", "junior"),
                skills=SkillAnalysisResponse(technical=cv.get("skills", {}).get("technical", []), soft=cv.get("skills", {}).get("soft", [])),
                experience=[ExperienceItemResponse(**e) for e in cv.get("experience", [])],
                education=cv.get("education", []),
                projects=cv.get("projects", []),
                certifications=cv.get("certifications", []),
                notable_points=cv.get("notable_points", []),
                potential_gaps=cv.get("potential_gaps", []),
                interview_focus_areas=cv.get("interview_focus_areas", []),
            )
        if interview.jd_analysis:
            jd = interview.jd_analysis.copy()
            data["jd_analysis"] = JDAnalysisResponse(
                role_title=jd.get("role_title", "Software Engineer"),
                company=jd.get("company"),
                seniority_level=jd.get("seniority_level", "mid"),
                required_skills=jd.get("required_skills", []),
                preferred_skills=jd.get("preferred_skills", []),
                key_responsibilities=jd.get("key_responsibilities", []),
                technical_requirements=jd.get("technical_requirements", []),
                interview_focus_areas=jd.get("interview_focus_areas", []),
                required_experience=jd.get("required_experience", {}),
                company_culture=jd.get("company_culture", {}),
            )
        if hasattr(interview, 'get_skill_gap_analysis'):
            data["skill_gap_analysis"] = SkillGapAnalysisResponse(**interview.get_skill_gap_analysis())
    return InterviewDetailResponse(**data)
