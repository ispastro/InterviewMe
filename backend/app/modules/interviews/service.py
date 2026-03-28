import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Interview, Turn, Feedback, InterviewStatus, InterviewPhase
from app.modules.ai.cv_processor import analyze_cv_with_ai
from app.modules.ai.jd_processor import analyze_jd_with_ai, compare_cv_to_jd, generate_interview_strategy
from app.core.exceptions import NotFoundError, ValidationError, InterviewStateError, AIServiceError


async def create_interview(
    db: AsyncSession, user: User, cv_text: str, jd_text: str,
    cv_metadata: Dict[str, Any] = None, target_company: str = None,
) -> Interview:
    if not cv_text or len(cv_text.strip()) < 50:
        raise ValidationError("CV text is too short for analysis")
    if not jd_text or len(jd_text.strip()) < 100:
        raise ValidationError("Job description text is too short for analysis")

    interview = Interview(user_id=user.id, status=InterviewStatus.PENDING, cv_raw_text=cv_text, jd_raw_text=jd_text, target_company=target_company)
    db.add(interview)
    await db.flush()

    try:
        interview.status = InterviewStatus.PROCESSING_CV
        await db.flush()

        cv_analysis = await analyze_cv_with_ai(cv_text)
        cv_analysis["_metadata"]["processed_at"] = datetime.now(timezone.utc).isoformat()
        if cv_metadata:
            cv_analysis["_metadata"]["file_info"] = cv_metadata

        jd_analysis = await analyze_jd_with_ai(jd_text)
        jd_analysis["_metadata"]["processed_at"] = datetime.now(timezone.utc).isoformat()

        interview_strategy = generate_interview_strategy(jd_analysis)
        comparison_analysis = compare_cv_to_jd(cv_analysis, jd_analysis)

        interview.cv_analysis = cv_analysis
        interview.jd_analysis = jd_analysis
        interview.target_role = jd_analysis.get("role_title", "Software Engineer")
        interview.target_company = target_company or jd_analysis.get("company", interview.target_company)
        interview.interview_config = {
            "strategy": interview_strategy,
            "comparison": comparison_analysis,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
        }
        interview.status = InterviewStatus.READY

        await db.commit()
        await db.refresh(interview)
        return interview

    except Exception as e:
        interview.status = InterviewStatus.FAILED
        await db.commit()
        if isinstance(e, (ValidationError, AIServiceError)):
            raise
        raise AIServiceError(f"Interview creation failed: {str(e)}")


async def get_interview_by_id(
    db: AsyncSession, interview_id: uuid.UUID, user: User,
    include_turns: bool = False, include_feedback: bool = False,
) -> Interview:
    query = select(Interview).where(and_(Interview.id == interview_id, Interview.user_id == user.id))
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
    db: AsyncSession, user: User, status: Optional[InterviewStatus] = None,
    limit: int = 20, offset: int = 0,
) -> Tuple[List[Interview], int]:
    query = select(Interview).where(Interview.user_id == user.id)
    count_query = select(Interview.id).where(Interview.user_id == user.id)
    if status:
        query = query.where(Interview.status == status)
        count_query = count_query.where(Interview.status == status)
    total_count = len((await db.execute(count_query)).all())
    interviews = (await db.execute(query.order_by(Interview.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return list(interviews), total_count


async def start_interview(db: AsyncSession, interview_id: uuid.UUID, user: User) -> Interview:
    interview = await get_interview_by_id(db, interview_id, user)
    if interview.status != InterviewStatus.READY:
        raise InterviewStateError(f"Cannot start interview in status {interview.status}. Must be READY.")
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_phase = InterviewPhase.INTRO
    interview.current_turn = 0
    interview.session_state = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "current_phase": InterviewPhase.INTRO.value,
        "phase_history": [],
        "difficulty_level": interview.interview_config.get("strategy", {}).get("difficulty_level", 0.5),
        "identified_strengths": [],
        "identified_weaknesses": [],
    }
    await db.commit()
    await db.refresh(interview)
    return interview


async def complete_interview(
    db: AsyncSession, interview_id: uuid.UUID, user: User,
    total_duration_seconds: Optional[float] = None,
) -> Interview:
    interview = await get_interview_by_id(db, interview_id, user, include_turns=True)
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise InterviewStateError(f"Cannot complete interview in status {interview.status}. Must be IN_PROGRESS.")
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.now(timezone.utc)
    interview.total_duration_seconds = total_duration_seconds
    if interview.session_state:
        interview.session_state["completed_at"] = interview.completed_at.isoformat()
        interview.session_state["total_duration_seconds"] = total_duration_seconds
    await db.commit()
    await db.refresh(interview)
    return interview


async def delete_interview(db: AsyncSession, interview_id: uuid.UUID, user: User) -> None:
    interview = await get_interview_by_id(db, interview_id, user)
    if interview.status == InterviewStatus.IN_PROGRESS:
        raise InterviewStateError("Cannot delete interview that is currently in progress")
    await db.delete(interview)
    await db.commit()


async def get_user_interview_stats(db: AsyncSession, user: User) -> Dict[str, Any]:
    result = await db.execute(select(Interview).where(Interview.user_id == user.id))
    interviews = result.scalars().all()

    if not interviews:
        return {
            "total_interviews": 0, "completed_interviews": 0, "in_progress_interviews": 0,
            "failed_interviews": 0, "average_score": None, "completion_rate": 0,
            "total_time_minutes": 0, "most_recent_interview": None, "skill_trends": {}, "role_distribution": {},
        }

    total = len(interviews)
    completed = len([i for i in interviews if i.status == InterviewStatus.COMPLETED])
    in_progress = len([i for i in interviews if i.status == InterviewStatus.IN_PROGRESS])
    failed = len([i for i in interviews if i.status == InterviewStatus.FAILED])

    feedbacks = (await db.execute(select(Feedback).join(Interview).where(Interview.user_id == user.id))).scalars().all()
    average_score = sum(f.overall_score for f in feedbacks) / len(feedbacks) if feedbacks else None

    total_time_minutes = sum(i.total_duration_seconds or 0 for i in interviews if i.total_duration_seconds) / 60
    most_recent = max(interviews, key=lambda i: i.created_at)

    role_distribution = {}
    for i in interviews:
        role = i.target_role or "Unknown"
        role_distribution[role] = role_distribution.get(role, 0) + 1

    skill_trends = {}
    for i in interviews:
        if i.cv_analysis and i.cv_analysis.get("skills", {}).get("technical"):
            for skill in i.cv_analysis["skills"]["technical"]:
                skill_trends[skill] = skill_trends.get(skill, 0) + 1

    return {
        "total_interviews": total,
        "completed_interviews": completed,
        "in_progress_interviews": in_progress,
        "failed_interviews": failed,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "average_score": round(average_score, 1) if average_score else None,
        "total_time_minutes": round(total_time_minutes, 1),
        "most_recent_interview": {
            "id": str(most_recent.id),
            "target_role": most_recent.target_role,
            "status": most_recent.status if isinstance(most_recent.status, str) else most_recent.status.value,
            "created_at": most_recent.created_at.isoformat(),
        },
        "role_distribution": dict(sorted(role_distribution.items(), key=lambda x: x[1], reverse=True)[:5]),
        "top_skills": dict(sorted(skill_trends.items(), key=lambda x: x[1], reverse=True)[:10]),
    }
