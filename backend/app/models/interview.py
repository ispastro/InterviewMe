import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, Float, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterviewStatus(str, Enum):
    PENDING = "pending"
    PROCESSING_CV = "processing_cv"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewPhase(str, Enum):
    INTRO = "intro"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    DEEP_DIVE = "deep_dive"
    CLOSING = "closing"


class Interview(Base):
    __tablename__ = "interviews"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[InterviewStatus] = mapped_column(
        String(20),
        default=InterviewStatus.PENDING,
        nullable=False,
        index=True,
    )

    cv_raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cv_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    jd_raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jd_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    interview_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    target_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    target_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    session_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    current_phase: Mapped[Optional[InterviewPhase]] = mapped_column(String(20), nullable=True)
    current_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="interviews", lazy="select")

    turns: Mapped[List["Turn"]] = relationship(
        "Turn",
        back_populates="interview",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Turn.turn_number",
    )

    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback",
        back_populates="interview",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_interview_user_status", "user_id", "status"),
        Index("idx_interview_role", "target_role"),
        Index("idx_interview_completed", "completed_at"),
    )

    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, user_id={self.user_id}, status={self.status}, role={self.target_role})>"

    @property
    def is_ready_to_start(self) -> bool:
        return self.status == InterviewStatus.READY

    @property
    def is_in_progress(self) -> bool:
        return self.status == InterviewStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        return self.status == InterviewStatus.COMPLETED

    @property
    def has_cv_analysis(self) -> bool:
        return self.cv_analysis is not None

    @property
    def has_jd_analysis(self) -> bool:
        return self.jd_analysis is not None

    def get_cv_skills(self) -> List[str]:
        if not self.cv_analysis:
            return []
        if not isinstance(self.cv_analysis, dict):
            return []
        skills = self.cv_analysis.get("skills", {})
        if not isinstance(skills, dict):
            return []
        return skills.get("technical", [])

    def get_jd_requirements(self) -> List[str]:
        if not self.jd_analysis:
            return []
        if not isinstance(self.jd_analysis, dict):
            return []
        return self.jd_analysis.get("required_skills", [])

    def get_skill_gap_analysis(self) -> Dict[str, List[str]]:
        cv_skills = set(skill.lower() for skill in self.get_cv_skills())
        jd_requirements = set(req.lower() for req in self.get_jd_requirements())
        return {
            "matching_skills": list(cv_skills & jd_requirements),
            "missing_skills": list(jd_requirements - cv_skills),
            "additional_skills": list(cv_skills - jd_requirements),
        }

    def to_dict(self, include_analysis: bool = False) -> Dict[str, Any]:
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


class Turn(Base):
    __tablename__ = "turns"

    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[InterviewPhase] = mapped_column(String(20), nullable=False, index=True)

    ai_question: Mapped[str] = mapped_column(Text, nullable=False)
    user_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evaluation: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    difficulty_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="turns", lazy="select")

    __table_args__ = (
        Index("idx_turn_interview_number", "interview_id", "turn_number"),
        Index("idx_turn_phase", "phase"),
        Index("idx_turn_unique", "interview_id", "turn_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Turn(id={self.id}, interview_id={self.interview_id}, turn={self.turn_number}, phase={self.phase})>"

    @property
    def has_answer(self) -> bool:
        return self.user_answer is not None and len(self.user_answer.strip()) > 0

    @property
    def has_evaluation(self) -> bool:
        return self.evaluation is not None

    def get_evaluation_score(self, metric: str) -> Optional[float]:
        if not self.evaluation:
            return None
        return self.evaluation.get(metric)

    def get_overall_score(self) -> Optional[float]:
        if not self.evaluation:
            return None
        
        # Try to get overall_score directly if it exists
        if "overall_score" in self.evaluation:
            try:
                return float(self.evaluation["overall_score"])
            except (ValueError, TypeError):
                pass
        
        # Calculate from metrics
        metrics = ["relevance", "depth", "clarity"]
        scores = []
        for m in metrics:
            val = self.evaluation.get(m)
            if val is not None:
                try:
                    scores.append(float(val))
                except (ValueError, TypeError):
                    continue
        
        if not scores:
            return None
        return sum(scores) / len(scores)

    def to_dict(self, include_evaluation: bool = True) -> Dict[str, Any]:
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
