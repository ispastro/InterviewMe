"""
InterviewMe Feedback Model

This module defines the Feedback model for storing comprehensive
post-interview analysis and recommendations.

Engineering decisions:
- One-to-one relationship with Interview (unique constraint)
- JSONB columns for structured feedback data (strengths, weaknesses, suggestions)
- Separate overall score and phase-specific scores
- Rich text field for detailed narrative analysis
- Indexed fields for analytics and reporting
"""

import uuid
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Text, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ============================================================
# FEEDBACK MODEL
# ============================================================

class Feedback(Base):
    """
    Post-interview feedback and analysis model.
    
    Generated after interview completion, contains:
    - Overall performance score and summary
    - Detailed strengths and weaknesses analysis
    - Actionable improvement suggestions
    - Phase-by-phase score breakdown
    - Comprehensive narrative feedback
    """
    
    __tablename__ = "feedback"
    
    # ============================================================
    # CORE FIELDS
    # ============================================================
    
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One feedback per interview
        index=True,
        comment="Interview this feedback belongs to"
    )
    
    # ============================================================
    # OVERALL ASSESSMENT
    # ============================================================
    
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Overall interview score (0-100)"
    )
    
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Brief summary of performance"
    )
    
    # ============================================================
    # STRUCTURED FEEDBACK
    # ============================================================
    
    strengths: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of identified strengths with evidence"
    )
    
    weaknesses: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of identified weaknesses with evidence"
    )
    
    suggestions: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Actionable improvement suggestions"
    )
    
    # ============================================================
    # DETAILED ANALYSIS
    # ============================================================
    
    phase_scores: Mapped[Dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Score breakdown by interview phase"
    )
    
    skill_assessment: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Assessment of specific skills mentioned in JD"
    )
    
    detailed_analysis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full narrative feedback analysis"
    )
    
    # ============================================================
    # METADATA
    # ============================================================
    
    generation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Metadata about feedback generation (AI model, tokens used, etc.)"
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # One-to-one: Feedback belongs to Interview
    interview: Mapped["Interview"] = relationship(
        "Interview",
        back_populates="feedback",
        lazy="select"
    )
    
    # ============================================================
    # INDEXES FOR PERFORMANCE
    # ============================================================
    
    __table_args__ = (
        # Index for score-based queries
        Index("idx_feedback_score", "overall_score"),
        
        # Index for feedback creation time
        Index("idx_feedback_created", "created_at"),
    )
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Feedback(id={self.id}, interview_id={self.interview_id}, score={self.overall_score})>"
    
    @property
    def performance_level(self) -> str:
        """Get performance level based on overall score"""
        if self.overall_score >= 90:
            return "excellent"
        elif self.overall_score >= 80:
            return "good"
        elif self.overall_score >= 70:
            return "satisfactory"
        elif self.overall_score >= 60:
            return "needs_improvement"
        else:
            return "poor"
    
    @property
    def top_strengths(self) -> List[str]:
        """Get top 3 strengths"""
        if not self.strengths:
            return []
        
        # Sort by score if available, otherwise take first 3
        sorted_strengths = sorted(
            self.strengths,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        return [strength.get("area", "") for strength in sorted_strengths[:3]]
    
    @property
    def top_weaknesses(self) -> List[str]:
        """Get top 3 areas for improvement"""
        if not self.weaknesses:
            return []
        
        # Sort by score (lower is worse), take first 3
        sorted_weaknesses = sorted(
            self.weaknesses,
            key=lambda x: x.get("score", 100)  # Default high score if not specified
        )
        
        return [weakness.get("area", "") for weakness in sorted_weaknesses[:3]]
    
    @property
    def high_priority_suggestions(self) -> List[str]:
        """Get high priority improvement suggestions"""
        if not self.suggestions:
            return []
        
        # Filter for high priority suggestions
        high_priority = [
            suggestion.get("action", "")
            for suggestion in self.suggestions
            if suggestion.get("priority", "").lower() == "high"
        ]
        
        # If no high priority, return first 3
        if not high_priority:
            return [suggestion.get("action", "") for suggestion in self.suggestions[:3]]
        
        return high_priority
    
    def get_phase_score(self, phase: str) -> Optional[float]:
        """Get score for specific interview phase"""
        return self.phase_scores.get(phase)
    
    def get_skill_score(self, skill: str) -> Optional[float]:
        """Get assessment score for specific skill"""
        if not self.skill_assessment:
            return None
        return self.skill_assessment.get(skill, {}).get("score")
    
    def to_dict(self, include_detailed: bool = True) -> Dict[str, Any]:
        """
        Convert feedback to dictionary for API responses.
        
        Args:
            include_detailed: Whether to include full detailed analysis
        """
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
    
    # ============================================================
    # CLASS METHODS FOR FEEDBACK CREATION
    # ============================================================
    
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
        generation_metadata: Dict[str, Any] = None
    ) -> "Feedback":
        """
        Create feedback from AI analysis results.
        
        This is the main factory method for creating feedback objects
        from the structured output of the AI feedback generation process.
        """
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
            generation_metadata=generation_metadata
        )