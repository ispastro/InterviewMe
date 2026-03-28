from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import time

from app.database import get_db
from app.models import User
from app.modules.auth.dependencies import get_current_user
from app.modules.interviews import service as interview_service
from app.schemas.interview import (
    InterviewSummaryResponse,
    InterviewDetailResponse,
    InterviewListResponse,
    InterviewStatsResponse,
    FileUploadResponse,
    FileInfoResponse,
    TurnResponse,
    UpdateInterviewRequest,
    create_interview_summary_response,
    create_interview_detail_response,
)
from app.utils.text_extraction import extract_text_from_file, get_file_info
from app.core.exceptions import NotFoundError, ValidationError, InterviewStateError, AIServiceError
from app.models.interview import InterviewStatus


router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.post("/upload-cv", response_model=FileUploadResponse)
async def upload_cv_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    start_time = time.time()
    try:
        extracted_text, metadata = await extract_text_from_file(file)
        processing_time = time.time() - start_time
        return FileUploadResponse(
            filename=metadata["filename"],
            file_type=metadata["file_type"],
            file_size_bytes=metadata["file_size_bytes"],
            text_length=metadata["text_length"],
            word_count=metadata["word_count"],
            processing_time_seconds=round(processing_time, 2),
            extracted_text_preview=extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File processing failed: {str(e)}")


@router.get("/file-info")
async def get_upload_file_info(
    filename: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    class MockUploadFile:
        def __init__(self, filename):
            self.filename = filename
            self.content_type = None
    return FileInfoResponse(**get_file_info(MockUploadFile(filename)))


@router.post("", response_model=InterviewDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    cv_file: UploadFile = File(...),
    target_company: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cv_text, cv_metadata = await extract_text_from_file(cv_file)
        resolved_jd_text = jd_text.strip() if jd_text else None
        if jd_file is not None:
            resolved_jd_text, _ = await extract_text_from_file(jd_file)
        if not resolved_jd_text:
            raise ValidationError("Provide either jd_text or jd_file")
        interview = await interview_service.create_interview(
            db=db, user=current_user, cv_text=cv_text, jd_text=resolved_jd_text,
            cv_metadata=cv_metadata, target_company=target_company,
        )
        return create_interview_detail_response(interview, include_analysis=True)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Interview creation failed: {str(e)}")


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        status_enum = None
        if status_filter:
            try:
                status_enum = InterviewStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid status: {status_filter}")
        offset = (page - 1) * page_size
        interviews, total_count = await interview_service.list_user_interviews(
            db=db, user=current_user, status=status_enum, limit=page_size, offset=offset,
        )
        return InterviewListResponse(
            interviews=[create_interview_summary_response(i) for i in interviews],
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total_count,
            has_previous=page > 1,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list interviews: {str(e)}")


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
async def get_interview(
    interview_id: uuid.UUID,
    include_analysis: bool = Query(False),
    include_turns: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        interview = await interview_service.get_interview_by_id(db, interview_id, current_user, include_turns=include_turns)
        return create_interview_detail_response(interview, include_analysis=include_analysis)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interview: {str(e)}")


@router.put("/{interview_id}", response_model=InterviewDetailResponse)
async def update_interview(
    interview_id: uuid.UUID,
    update_data: UpdateInterviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        interview = await interview_service.get_interview_by_id(db, interview_id, current_user)
        if update_data.target_company is not None:
            interview.target_company = update_data.target_company
        await db.commit()
        await db.refresh(interview)
        return create_interview_detail_response(interview)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update interview: {str(e)}")


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await interview_service.delete_interview(db, interview_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except InterviewStateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete interview: {str(e)}")


@router.post("/{interview_id}/start", response_model=InterviewDetailResponse)
async def start_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        interview = await interview_service.start_interview(db, interview_id, current_user)
        return create_interview_detail_response(interview)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except InterviewStateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/{interview_id}/complete", response_model=InterviewDetailResponse)
async def complete_interview(
    interview_id: uuid.UUID,
    total_duration_seconds: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        interview = await interview_service.complete_interview(db, interview_id, current_user, total_duration_seconds)
        return create_interview_detail_response(interview)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except InterviewStateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete interview: {str(e)}")


@router.get("/{interview_id}/turns", response_model=List[TurnResponse])
async def get_interview_turns(
    interview_id: uuid.UUID,
    include_evaluation: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        interview = await interview_service.get_interview_by_id(db, interview_id, current_user, include_turns=True)
        if not interview.turns:
            return []
        return [
            TurnResponse(
                id=str(t.id), interview_id=str(t.interview_id), turn_number=t.turn_number,
                phase=t.phase.value, ai_question=t.ai_question, user_answer=t.user_answer,
                duration_seconds=t.duration_seconds, difficulty_level=t.difficulty_level,
                created_at=t.created_at, has_answer=t.has_answer, has_evaluation=t.has_evaluation,
                evaluation=t.evaluation if include_evaluation else None,
                overall_score=t.get_overall_score() if include_evaluation else None,
            )
            for t in interview.turns
        ]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get turns: {str(e)}")


@router.get("/stats/summary", response_model=InterviewStatsResponse)
async def get_interview_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        stats = await interview_service.get_user_interview_stats(db, current_user)
        return InterviewStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health")
async def interview_service_health():
    return {"status": "healthy", "service": "interviews"}
