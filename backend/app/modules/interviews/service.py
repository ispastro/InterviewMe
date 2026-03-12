"""
InterviewMe Interview Service

This module provides business logic for interview management including:
- Interview creation with CV/JD processing
- Status management and state transitions
- CRUD operations with proper validation
- Integration with AI processing modules

Engineering decisions:
- Service layer pattern for business logic separation
- Async operations for non-blocking processing
- Comprehensive error handling and validation
- Status-based state machine for interview lifecycle
- Integration with AI processors for analysis
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Interview, Turn, Feedback, InterviewStatus, InterviewPhase
from app.modules.ai.cv_processor import analyze_cv_with_ai
from app.modules.ai.jd_processor import analyze_jd_with_ai, compare_cv_to_jd, generate_interview_strategy
from app.core.exceptions import NotFoundError, ValidationError, InterviewStateError, AIServiceError


# ============================================================
# INTERVIEW CREATION
# ============================================================

async def create_interview(
    db: AsyncSession,
    user: User,
    cv_text: str,
    jd_text: str,
    cv_metadata: Dict[str, Any] = None,
    target_company: str = None
) -> Interview:
    """
    Create a new interview with CV and JD processing.
    
    Args:
        db: Database session
        user: User creating the interview
        cv_text: Extracted CV text content
        jd_text: Job description text
        cv_metadata: Metadata from file extraction
        target_company: Optional company name override
        
    Returns:
        Created interview object
        
    Raises:
        ValidationError: If input validation fails
        AIServiceError: If AI processing fails
    """
    # Validate inputs
    if not cv_text or len(cv_text.strip()) < 50:
        raise ValidationError("CV text is too short for analysis")
    
    if not jd_text or len(jd_text.strip()) < 100:
        raise ValidationError("Job description text is too short for analysis")
    
    # Create interview record with PENDING status
    interview = Interview(
        user_id=user.id,
        status=InterviewStatus.PENDING,
        cv_raw_text=cv_text,
        jd_raw_text=jd_text,
        target_company=target_company
    )
    
    db.add(interview)
    await db.flush()  # Get the ID without committing
    
    try:
        # Update status to PROCESSING_CV
        interview.status = InterviewStatus.PROCESSING_CV
        await db.flush()
        
        # Process CV with AI
        cv_analysis = await analyze_cv_with_ai(cv_text)
        cv_analysis["_metadata"]["processed_at"] = datetime.now(timezone.utc).isoformat()
        if cv_metadata:
            cv_analysis["_metadata"]["file_info"] = cv_metadata
        
        # Process JD with AI
        jd_analysis = await analyze_jd_with_ai(jd_text)
        jd_analysis["_metadata"]["processed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Generate interview strategy
        interview_strategy = generate_interview_strategy(jd_analysis)
        
        # Compare CV to JD for gap analysis
        comparison_analysis = compare_cv_to_jd(cv_analysis, jd_analysis)
        
        # Update interview with analysis results
        interview.cv_analysis = cv_analysis
        interview.jd_analysis = jd_analysis
        interview.target_role = jd_analysis.get("role_title", "Software Engineer")
        interview.target_company = target_company or jd_analysis.get("company", interview.target_company)
        
        # Create interview configuration
        interview.interview_config = {
            "strategy": interview_strategy,
            "comparison": comparison_analysis,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }
        
        # Update status to READY
        interview.status = InterviewStatus.READY
        
        await db.commit()
        await db.refresh(interview)
        
        return interview
        
    except Exception as e:
        # Mark interview as FAILED
        interview.status = InterviewStatus.FAILED
        await db.commit()
        
        # Re-raise the original exception
        if isinstance(e, (ValidationError, AIServiceError)):
            raise
        else:
            raise AIServiceError(f"Interview creation failed: {str(e)}")


# ============================================================
# INTERVIEW RETRIEVAL
# ============================================================

async def get_interview_by_id(
    db: AsyncSession,
    interview_id: uuid.UUID,
    user: User,
    include_turns: bool = False,
    include_feedback: bool = False
) -> Interview:
    """
    Get interview by ID with user ownership validation.
    
    Args:
        db: Database session
        interview_id: Interview UUID
        user: User requesting the interview
        include_turns: Whether to load turns
        include_feedback: Whether to load feedback
        
    Returns:
        Interview object
        
    Raises:
        NotFoundError: If interview not found or not owned by user
    """
    # Build query with optional eager loading
    query = select(Interview).where(
        and_(
            Interview.id == interview_id,
            Interview.user_id == user.id
        )
    )
    
    if include_turns:
        query = query.options(selectinload(Interview.turns))
    
    if include_feedback:
        query = query.options(selectinload(Interview.feedback))
    
    result = await db.execute(query)
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise NotFoundError(f"Interview {interview_id} not found")
    
    return interview


async def list_user_interviews(
    db: AsyncSession,
    user: User,
    status: Optional[InterviewStatus] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Interview], int]:
    """
    List interviews for a user with optional filtering.
    
    Args:
        db: Database session
        user: User whose interviews to list
        status: Optional status filter
        limit: Maximum number of interviews to return
        offset: Number of interviews to skip
        
    Returns:
        Tuple of (interviews, total_count)
    """
    # Build base query
    query = select(Interview).where(Interview.user_id == user.id)
    
    if status:
        query = query.where(Interview.status == status)
    
    # Get total count
    count_query = select(Interview.id).where(Interview.user_id == user.id)
    if status:
        count_query = count_query.where(Interview.status == status)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.all())
    
    # Get paginated results
    query = query.order_by(Interview.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    interviews = result.scalars().all()
    
    return list(interviews), total_count


# ============================================================
# INTERVIEW STATUS MANAGEMENT
# ============================================================

async def start_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    user: User
) -> Interview:
    """
    Start an interview session (transition to IN_PROGRESS).
    
    Args:
        db: Database session
        interview_id: Interview UUID
        user: User starting the interview
        
    Returns:
        Updated interview object
        
    Raises:
        NotFoundError: If interview not found
        InterviewStateError: If interview not ready to start
    """
    interview = await get_interview_by_id(db, interview_id, user)
    
    if interview.status != InterviewStatus.READY:
        raise InterviewStateError(
            f"Cannot start interview in status {interview.status}. Must be READY."
        )
    
    # Update status and initialize session state
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_phase = InterviewPhase.INTRO
    interview.current_turn = 0
    interview.session_state = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "current_phase": InterviewPhase.INTRO.value,
        "phase_history": [],
        "difficulty_level": interview.interview_config.get("strategy", {}).get("difficulty_level", 0.5),
        "identified_strengths": [],
        "identified_weaknesses": []
    }
    
    await db.commit()
    await db.refresh(interview)
    
    return interview


async def complete_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    user: User,
    total_duration_seconds: Optional[float] = None
) -> Interview:
    """
    Complete an interview session (transition to COMPLETED).
    
    Args:
        db: Database session
        interview_id: Interview UUID
        user: User completing the interview
        total_duration_seconds: Total interview duration
        
    Returns:
        Updated interview object
        
    Raises:
        NotFoundError: If interview not found
        InterviewStateError: If interview not in progress
    """
    interview = await get_interview_by_id(db, interview_id, user, include_turns=True)
    
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise InterviewStateError(
            f"Cannot complete interview in status {interview.status}. Must be IN_PROGRESS."
        )
    
    # Update status and completion info
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.now(timezone.utc)
    interview.total_duration_seconds = total_duration_seconds
    
    # Update session state
    if interview.session_state:
        interview.session_state["completed_at"] = interview.completed_at.isoformat()
        interview.session_state["total_duration_seconds"] = total_duration_seconds
    
    await db.commit()
    await db.refresh(interview)
    
    return interview


# ============================================================
# INTERVIEW DELETION
# ============================================================

async def delete_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    user: User
) -> None:
    """
    Delete an interview and all related data.
    
    Args:
        db: Database session
        interview_id: Interview UUID
        user: User deleting the interview
        
    Raises:
        NotFoundError: If interview not found
        InterviewStateError: If interview is currently in progress
    """
    interview = await get_interview_by_id(db, interview_id, user)
    
    # Prevent deletion of in-progress interviews
    if interview.status == InterviewStatus.IN_PROGRESS:
        raise InterviewStateError("Cannot delete interview that is currently in progress")
    
    # Delete the interview (cascades to turns and feedback)
    await db.delete(interview)
    await db.commit()


# ============================================================
# INTERVIEW ANALYTICS
# ============================================================

async def get_user_interview_stats(
    db: AsyncSession,
    user: User
) -> Dict[str, Any]:
    """
    Get comprehensive interview statistics for a user.
    
    Args:
        db: Database session
        user: User to get stats for
        
    Returns:
        Dictionary with interview statistics
    """
    # Get all user interviews
    interviews_query = select(Interview).where(Interview.user_id == user.id)
    result = await db.execute(interviews_query)
    interviews = result.scalars().all()
    
    if not interviews:
        return {
            "total_interviews": 0,
            "completed_interviews": 0,
            "in_progress_interviews": 0,
            "average_score": None,
            "completion_rate": 0,
            "total_time_minutes": 0,
            "most_recent_interview": None,
            "skill_trends": {},
            "role_distribution": {}
        }
    
    # Calculate basic stats
    total_interviews = len(interviews)
    completed_interviews = len([i for i in interviews if i.status == InterviewStatus.COMPLETED])
    in_progress_interviews = len([i for i in interviews if i.status == InterviewStatus.IN_PROGRESS])
    
    # Calculate average score (need to get feedback)
    feedback_query = select(Feedback).join(Interview).where(Interview.user_id == user.id)
    feedback_result = await db.execute(feedback_query)
    feedbacks = feedback_result.scalars().all()
    
    average_score = None
    if feedbacks:
        average_score = sum(f.overall_score for f in feedbacks) / len(feedbacks)
    
    # Calculate total time
    total_time_seconds = sum(
        i.total_duration_seconds or 0 
        for i in interviews 
        if i.total_duration_seconds
    )
    total_time_minutes = total_time_seconds / 60
    
    # Get most recent interview
    most_recent = max(interviews, key=lambda i: i.created_at) if interviews else None
    
    # Analyze role distribution
    role_distribution = {}
    for interview in interviews:
        role = interview.target_role or "Unknown"
        role_distribution[role] = role_distribution.get(role, 0) + 1
    
    # Analyze skill trends (from CV analyses)
    skill_trends = {}
    for interview in interviews:
        if interview.cv_analysis and interview.cv_analysis.get("skills", {}).get("technical"):
            for skill in interview.cv_analysis["skills"]["technical"]:
                skill_trends[skill] = skill_trends.get(skill, 0) + 1
    
    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_interviews,
        "in_progress_interviews": in_progress_interviews,
        "failed_interviews": len([i for i in interviews if i.status == InterviewStatus.FAILED]),
        "completion_rate": (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0,
        "average_score": round(average_score, 1) if average_score else None,
        "total_time_minutes": round(total_time_minutes, 1),
        "most_recent_interview": {
            "id": str(most_recent.id),
            "target_role": most_recent.target_role,
            "status": most_recent.status if isinstance(most_recent.status, str) else most_recent.status.value,
            "created_at": most_recent.created_at.isoformat()
        } if most_recent else None,
        "role_distribution": dict(sorted(role_distribution.items(), key=lambda x: x[1], reverse=True)[:5]),
        "top_skills": dict(sorted(skill_trends.items(), key=lambda x: x[1], reverse=True)[:10])
    }