import uuid
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Text, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    strengths: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    suggestions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    phase_scores: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    skill_assessment: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    detailed_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="feedback", lazy="select")

    __table_args__ = (
        Index("idx_feedback_score", "overall_score"),
        Index("idx_feedback_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, interview_id={self.interview_id}, score={self.overall_score})>"

    @property
    def performance_level(self) -> str:
        if self.overall_score >= 90:
            return "excellent"
        elif self.overall_score >= 80:
            return "good"
        elif self.overall_score >= 70:
            return "satisfactory"
        elif self.overall_score >= 60:
            return "needs_improvement"
        return "poor"

    @property
    def top_strengths(self) -> List[str]:
        if not self.strengths:
            return []
        sorted_strengths = sorted(self.strengths, key=lambda x: x.get("score", 0), reverse=True)
        return [s.get("area", "") for s in sorted_strengths[:3]]

    @property
    def top_weaknesses(self) -> List[str]:
        if not self.weaknesses:
            return []
        sorted_weaknesses = sorted(self.weaknesses, key=lambda x: x.get("score", 100))
        return [w.get("area", "") for w in sorted_weaknesses[:3]]

    @property
    def high_priority_suggestions(self) -> List[str]:
        if not self.suggestions:
            return []
        high = [s.get("action", "") for s in self.suggestions if s.get("priority", "").lower() == "high"]
        return high if high else [s.get("action", "") for s in self.suggestions[:3]]

    def get_phase_score(self, phase: str) -> Optional[float]:
        return self.phase_scores.get(phase)

    def get_skill_score(self, skill: str) -> Optional[float]:
        if not self.skill_assessment:
            return None
        return self.skill_assessment.get(skill, {}).get("score")

    def to_dict(self, include_detailed: bool = True) -> Dict[str, Any]:
        data = {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "overall_score": self.overall_score,
            "performance_level": self.performance_level,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "phase_scores": self.phase_scores,
            "top_strengths": self.top_strengths,
            "top_weaknesses": self.top_weaknesses,
            "high_priority_suggestions": self.high_priority_suggestions,
            "created_at": self.created_at.isoformat(),
        }
        if include_detailed:
            data.update({
                "skill_assessment": self.skill_assessment,
                "detailed_analysis": self.detailed_analysis,
                "generation_metadata": self.generation_metadata,
            })
        return data

    @classmethod
    def create_from_analysis(
        cls,
        interview_id: uuid.UUID,
        overall_score: float,
        strengths: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]],
        phase_scores: Dict[str, float],
        summary: str = None,
        detailed_analysis: str = None,
        skill_assessment: Dict[str, Any] = None,
        generation_metadata: Dict[str, Any] = None,
    ) -> "Feedback":
        return cls(
            interview_id=interview_id,
            overall_score=overall_score,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            phase_scores=phase_scores,
            skill_assessment=skill_assessment,
            detailed_analysis=detailed_analysis,
            generation_metadata=generation_metadata,
        )
