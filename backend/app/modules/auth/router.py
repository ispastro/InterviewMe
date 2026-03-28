from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.core.exceptions import DatabaseError


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    display_name: str
    oauth_provider: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserStatsResponse(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: Optional[float]
    last_interview_date: Optional[datetime]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user.to_dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if update_data.name is not None:
            current_user.name = update_data.name.strip() or None
        await db.commit()
        await db.refresh(current_user)
        return UserResponse.model_validate(current_user.to_dict())
    except Exception as e:
        await db.rollback()
        raise DatabaseError("Failed to update user profile", str(e))


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from sqlalchemy import select, func
        from app.models.interview import Interview, InterviewStatus
        from app.models.feedback import Feedback

        total = (await db.execute(select(func.count(Interview.id)).where(Interview.user_id == current_user.id))).scalar() or 0
        completed = (await db.execute(select(func.count(Interview.id)).where(Interview.user_id == current_user.id, Interview.status == InterviewStatus.COMPLETED))).scalar() or 0
        avg_score = (await db.execute(select(func.avg(Feedback.overall_score)).join(Interview, Feedback.interview_id == Interview.id).where(Interview.user_id == current_user.id))).scalar()
        last_date = (await db.execute(select(func.max(Interview.created_at)).where(Interview.user_id == current_user.id))).scalar()

        return UserStatsResponse(
            total_interviews=total,
            completed_interviews=completed,
            average_score=round(avg_score, 1) if avg_score else None,
            last_interview_date=last_date,
        )
    except Exception as e:
        raise DatabaseError("Failed to get user statistics", str(e))


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        current_user.is_active = False
        await db.commit()
        return {"message": "Account deactivated successfully"}
    except Exception as e:
        await db.rollback()
        raise DatabaseError("Failed to deactivate account", str(e))


@router.post("/validate")
async def validate_token(current_user: User = Depends(get_current_user)):
    return {"valid": True, "user": UserResponse.model_validate(current_user.to_dict())}


@router.get("/health")
async def auth_health_check():
    return {"status": "healthy", "service": "auth"}
