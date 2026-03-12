"""
InterviewMe Interview Models

This module defines the core interview-related database models:
- Interview: Main interview session with CV/JD analysis
- Turn: Individual question-answer pairs within an interview

Engineering decisions:
- UUID primary keys for distributed system compatibility
- JSONB columns for structured AI analysis data (queryable + flexible)
- Enum-based status tracking for clear state management
- Proper foreign key relationships with cascade behavior
- Indexed fields for common query patterns
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, Float, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ============================================================
# ENUMS FOR TYPE SAFETY
# ============================================================

class InterviewStatus(str, Enum):
    """
    Interview lifecycle states.
    
    Flow: PENDING → PROCESSING_CV → READY → IN_PROGRESS → COMPLETED
    Error states: FAILED (can occur from any state)
    """
    PENDING = "pending"                    # Just created, no processing yet
    PROCESSING_CV = "processing_cv"        # AI is analyzing CV/JD
    READY = "ready"                        # Analysis complete, ready to start
    IN_PROGRESS = "in_progress"            # WebSocket session active
    COMPLETED = "completed"                # Interview finished
    FAILED = "failed"                      # Processing or interview failed


class InterviewPhase(str, Enum):
    """
    Interview phases for structured progression.
    
    Each phase has different question types and evaluation criteria.
    """
    INTRO = "intro"                        # Opening question, get to know candidate
    BEHAVIORAL = "behavioral"              # STAR-format situational questions
    TECHNICAL = "technical"                # Domain-specific technical questions
    DEEP_DIVE = "deep_dive"               # Follow-up probes on strengths/weaknesses
    CLOSING = "closing"                    # Candidate questions, wrap-up


# ============================================================
# INTERVIEW MODEL
# ============================================================

class Interview(Base):
    """
    Main interview session model.
    
    Stores the complete interview context including:
    - Original CV and JD text
    - AI-generated structured analysis
    - Interview configuration and progress
    - Relationships to turns and feedback
    """
    
    __tablename__ = "interviews"
    
    # ============================================================
    # CORE FIELDS
    # ============================================================
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this interview"
    )
    
    status: Mapped[InterviewStatus] = mapped_column(
        String(20),
        default=InterviewStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current interview state"
    )
    
    # ============================================================
    # CV PROCESSING
    # ============================================================
    
    cv_raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original extracted CV text"
    )
    
    cv_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured CV analysis from AI (skills, experience, etc.)"
    )
    
    # ============================================================
    # JOB DESCRIPTION PROCESSING
    # ============================================================
    
    jd_raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original job description text"
    )
    
    jd_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured JD analysis from AI (requirements, level, etc.)"
    )
    
    # ============================================================
    # INTERVIEW CONFIGURATION
    # ============================================================
    
    interview_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Interview settings (phases, question counts, difficulty)"
    )
    
    target_role: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Job title extracted from JD"
    )
    
    target_company: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Company name if specified"
    )
    
    # ============================================================
    # INTERVIEW SESSION STATE
    # ============================================================
    
    session_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Current interview session state (for crash recovery)"
    )
    
    current_phase: Mapped[Optional[InterviewPhase]] = mapped_column(
        String(20),
        nullable=True,
        comment="Current interview phase"
    )
    
    current_turn: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current turn number (0 = not started)"
    )
    
    # ============================================================
    # COMPLETION TRACKING
    # ============================================================
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the interview was completed"
    )
    
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Total interview duration in seconds"
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Many-to-one: Interview belongs to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="interviews",
        lazy="select"
    )
    
    # One-to-many: Interview has many Turns
    turns: Mapped[List["Turn"]] = relationship(
        "Turn",
        back_populates="interview",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Turn.turn_number"
    )
    
    # One-to-one: Interview has one Feedback
    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback",
        back_populates="interview",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False
    )
    
    # ============================================================
    # INDEXES FOR PERFORMANCE
    # ============================================================
    
    __table_args__ = (
        # Composite index for user's interviews by status
        Index("idx_interview_user_status", "user_id", "status"),
        
        # Index for finding interviews by role
        Index("idx_interview_role", "target_role"),
        
        # Index for completed interviews
        Index("idx_interview_completed", "completed_at"),
    )
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Interview(id={self.id}, user_id={self.user_id}, status={self.status}, role={self.target_role})>"
    
    @property
    def is_ready_to_start(self) -> bool:
        """Check if interview is ready to begin"""
        return self.status == InterviewStatus.READY
    
    @property
    def is_in_progress(self) -> bool:
        """Check if interview is currently active"""
        return self.status == InterviewStatus.IN_PROGRESS
    
    @property
    def is_completed(self) -> bool:
        """Check if interview is finished"""
        return self.status == InterviewStatus.COMPLETED
    
    @property
    def has_cv_analysis(self) -> bool:
        """Check if CV has been analyzed"""
        return self.cv_analysis is not None
    
    @property
    def has_jd_analysis(self) -> bool:
        """Check if JD has been analyzed"""
        return self.jd_analysis is not None
    
    def get_cv_skills(self) -> List[str]:
        """Extract technical skills from CV analysis"""
        if not self.cv_analysis:
            return []
        return self.cv_analysis.get("skills", {}).get("technical", [])
    
    def get_jd_requirements(self) -> List[str]:
        """Extract required skills from JD analysis"""
        if not self.jd_analysis:
            return []
        return self.jd_analysis.get("required_skills", [])
    
    def get_skill_gap_analysis(self) -> Dict[str, List[str]]:
        """Compare CV skills vs JD requirements"""
        cv_skills = set(skill.lower() for skill in self.get_cv_skills())
        jd_requirements = set(req.lower() for req in self.get_jd_requirements())
        
        return {
            "matching_skills": list(cv_skills & jd_requirements),
            "missing_skills": list(jd_requirements - cv_skills),
            "additional_skills": list(cv_skills - jd_requirements)
        }
    
    def to_dict(self, include_analysis: bool = False) -> Dict[str, Any]:
        """
        Convert interview to dictionary for API responses.
        
        Args:
            include_analysis: Whether to include full CV/JD analysis data
        """
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "status": self.status.value,
            "target_role": self.target_role,
            "target_company": self.target_company,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "current_turn": self.current_turn,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_seconds": self.total_duration_seconds,
            "turn_count": len(self.turns) if self.turns else 0,
            "has_feedback": self.feedback is not None,
        }
        
        if include_analysis:
            data.update({
                "cv_analysis": self.cv_analysis,
                "jd_analysis": self.jd_analysis,
                "interview_config": self.interview_config,
                "skill_gap_analysis": self.get_skill_gap_analysis(),
            })
        
        return data


# ============================================================
# TURN MODEL
# ============================================================

class Turn(Base):
    """
    Individual question-answer pair within an interview.
    
    Each turn represents one exchange:
    1. AI asks a question
    2. User provides an answer
    3. AI evaluates the answer
    """
    
    __tablename__ = "turns"
    
    # ============================================================
    # CORE FIELDS
    # ============================================================
    
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Interview this turn belongs to"
    )
    
    turn_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential turn number (1, 2, 3...)"
    )
    
    phase: Mapped[InterviewPhase] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Interview phase when this turn occurred"
    )
    
    # ============================================================
    # QUESTION & ANSWER
    # ============================================================
    
    ai_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The AI's question to the candidate"
    )
    
    user_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Candidate's transcribed answer"
    )
    
    # ============================================================
    # EVALUATION & METADATA
    # ============================================================
    
    evaluation: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="AI evaluation of the answer (relevance, depth, clarity)"
    )
    
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="How long the candidate took to answer"
    )
    
    difficulty_level: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Question difficulty (0.0 = easy, 1.0 = hard)"
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Many-to-one: Turn belongs to Interview
    interview: Mapped["Interview"] = relationship(
        "Interview",
        back_populates="turns",
        lazy="select"
    )
    
    # ============================================================
    # INDEXES FOR PERFORMANCE
    # ============================================================
    
    __table_args__ = (
        # Composite index for interview turns
        Index("idx_turn_interview_number", "interview_id", "turn_number"),
        
        # Index for turns by phase
        Index("idx_turn_phase", "phase"),
        
        # Unique constraint: one turn number per interview
        Index("idx_turn_unique", "interview_id", "turn_number", unique=True),
    )
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Turn(id={self.id}, interview_id={self.interview_id}, turn={self.turn_number}, phase={self.phase})>"
    
    @property
    def has_answer(self) -> bool:
        """Check if user has provided an answer"""
        return self.user_answer is not None and len(self.user_answer.strip()) > 0
    
    @property
    def has_evaluation(self) -> bool:
        """Check if answer has been evaluated"""
        return self.evaluation is not None
    
    def get_evaluation_score(self, metric: str) -> Optional[float]:
        """Get specific evaluation metric score"""
        if not self.evaluation:
            return None
        return self.evaluation.get(metric)
    
    def get_overall_score(self) -> Optional[float]:
        """Calculate overall score from evaluation metrics"""
        if not self.evaluation:
            return None
        
        # Average of relevance, depth, and clarity
        metrics = ["relevance", "depth", "clarity"]
        scores = [self.evaluation.get(metric) for metric in metrics if self.evaluation.get(metric) is not None]
        
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def to_dict(self, include_evaluation: bool = True) -> Dict[str, Any]:
        """
        Convert turn to dictionary for API responses.
        
        Args:
            include_evaluation: Whether to include evaluation data
        """
        data = {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "turn_number": self.turn_number,
            "phase": self.phase.value,
            "ai_question": self.ai_question,
            "user_answer": self.user_answer,
            "duration_seconds": self.duration_seconds,
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at.isoformat(),
            "has_answer": self.has_answer,
            "has_evaluation": self.has_evaluation,
        }
        
        if include_evaluation and self.evaluation:
            data.update({
                "evaluation": self.evaluation,
                "overall_score": self.get_overall_score(),
            })
        
        return data