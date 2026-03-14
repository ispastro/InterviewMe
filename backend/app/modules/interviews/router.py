"""
InterviewMe Interview Router

This module provides REST API endpoints for interview management including:
- Interview creation with CV upload and JD processing
- Interview retrieval and listing with pagination
- Interview status management (start, complete, delete)
- File upload and text extraction
- User interview statistics

Engineering decisions:
- RESTful API design with proper HTTP methods and status codes
- File upload with streaming for memory efficiency
- Comprehensive error handling and validation
- Pagination for list endpoints
- Optional data inclusion via query parameters
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.modules.auth.dependencies import get_current_user
from app.modules.interviews import service as interview_service
from app.schemas.interview import (
    CreateInterviewRequest,
    UpdateInterviewRequest,
    InterviewActionRequest,
    InterviewSummaryResponse,
    InterviewDetailResponse,
    InterviewListResponse,
    InterviewStatsResponse,
    FileUploadResponse,
    FileInfoResponse,
    TurnResponse,
    create_interview_summary_response,
    create_interview_detail_response
)
from app.utils.text_extraction import extract_text_from_file, get_file_info
from app.core.exceptions import NotFoundError, ValidationError, InterviewStateError, AIServiceError
from app.models.interview import InterviewStatus
import uuid
import time


# ============================================================
# ROUTER SETUP
# ============================================================
router = APIRouter(
    prefix="/api/interviews",
    tags=["Interviews"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"},
        404: {"description": "Interview not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================
# FILE UPLOAD ENDPOINTS
# ============================================================

@router.post("/upload-cv", response_model=FileUploadResponse)
async def upload_cv_file(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, or TXT)"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and extract text from CV file.
    
    Supports PDF, DOCX, and TXT files up to 5MB.
    Returns extracted text and metadata for interview creation.
    """
    start_time = time.time()
    
    try:
        # Extract text from file
        extracted_text, metadata = await extract_text_from_file(file)
        
        processing_time = time.time() - start_time
        
        return FileUploadResponse(
            filename=metadata["filename"],
            file_type=metadata["file_type"],
            file_size_bytes=metadata["file_size_bytes"],
            text_length=metadata["text_length"],
            word_count=metadata["word_count"],
            processing_time_seconds=round(processing_time, 2),
            extracted_text_preview=extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.get("/file-info")
async def get_upload_file_info(
    filename: str = Query(..., description="Filename to check"),
    current_user: User = Depends(get_current_user)
):
    """
    Get information about a file before upload.
    
    Returns file type support, size limits, and estimated processing time.
    """
    # Create a mock UploadFile object for validation
    class MockUploadFile:
        def __init__(self, filename: str):
            self.filename = filename
            self.content_type = None
    
    mock_file = MockUploadFile(filename)
    file_info = get_file_info(mock_file)
    
    return FileInfoResponse(**file_info)


# ============================================================
# INTERVIEW CRUD ENDPOINTS
# ============================================================

@router.post("", response_model=InterviewDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    jd_text: Optional[str] = Form(None, description="Job description text"),
    jd_file: Optional[UploadFile] = File(None, description="Optional job description file (PDF, DOCX, or TXT)"),
    cv_file: UploadFile = File(..., description="CV file (PDF, DOCX, or TXT)"),
    target_company: Optional[str] = Form(None, description="Optional company name override"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new interview by uploading CV and providing job description.
    
    The system will:
    1. Extract text from the CV file
    2. Analyze both CV and JD using AI
    3. Generate interview strategy and configuration
    4. Return the created interview with analysis data
    """
    try:
        # Extract text from CV file
        cv_text, cv_metadata = await extract_text_from_file(cv_file)

        # Resolve JD text from direct text or uploaded file
        resolved_jd_text = jd_text.strip() if jd_text else None
        if jd_file is not None:
            resolved_jd_text, _ = await extract_text_from_file(jd_file)

        if not resolved_jd_text:
            raise ValidationError("Provide either jd_text or jd_file")
        
        # Create interview with AI processing
        interview = await interview_service.create_interview(
            db=db,
            user=current_user,
            cv_text=cv_text,
            jd_text=resolved_jd_text,
            cv_metadata=cv_metadata,
            target_company=target_company
        )
        
        return create_interview_detail_response(interview, include_analysis=True)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview creation failed: {str(e)}"
        )


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's interviews with optional filtering and pagination.
    
    Returns a paginated list of interviews with summary information.
    """
    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = InterviewStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get interviews
        interviews, total_count = await interview_service.list_user_interviews(
            db=db,
            user=current_user,
            status=status_enum,
            limit=page_size,
            offset=offset
        )
        
        # Convert to response format
        interview_responses = [
            create_interview_summary_response(interview)
            for interview in interviews
        ]
        
        return InterviewListResponse(
            interviews=interview_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total_count,
            has_previous=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list interviews: {str(e)}"
        )


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
async def get_interview(
    interview_id: uuid.UUID,
    include_analysis: bool = Query(False, description="Include CV/JD analysis data"),
    include_turns: bool = Query(False, description="Include interview turns"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific interview.
    
    Optionally include analysis data and turns for complete interview context.
    """
    try:
        interview = await interview_service.get_interview_by_id(
            db=db,
            interview_id=interview_id,
            user=current_user,
            include_turns=include_turns
        )
        
        return create_interview_detail_response(interview, include_analysis=include_analysis)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview: {str(e)}"
        )


@router.put("/{interview_id}", response_model=InterviewDetailResponse)
async def update_interview(
    interview_id: uuid.UUID,
    update_data: UpdateInterviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update interview metadata (company name, etc.).
    
    Note: Cannot update CV/JD analysis data - create a new interview for that.
    """
    try:
        interview = await interview_service.get_interview_by_id(
            db=db,
            interview_id=interview_id,
            user=current_user
        )
        
        # Update allowed fields
        if update_data.target_company is not None:
            interview.target_company = update_data.target_company
        
        await db.commit()
        await db.refresh(interview)
        
        return create_interview_detail_response(interview)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interview: {str(e)}"
        )


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an interview and all related data.
    
    Cannot delete interviews that are currently in progress.
    """
    try:
        await interview_service.delete_interview(
            db=db,
            interview_id=interview_id,
            user=current_user
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except InterviewStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete interview: {str(e)}"
        )


# ============================================================
# INTERVIEW ACTION ENDPOINTS
# ============================================================

@router.post("/{interview_id}/start", response_model=InterviewDetailResponse)
async def start_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start an interview session.
    
    Transitions the interview from READY to IN_PROGRESS status.
    Initializes session state for WebSocket connection.
    """
    try:
        interview = await interview_service.start_interview(
            db=db,
            interview_id=interview_id,
            user=current_user
        )
        
        return create_interview_detail_response(interview)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except InterviewStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/{interview_id}/complete", response_model=InterviewDetailResponse)
async def complete_interview(
    interview_id: uuid.UUID,
    total_duration_seconds: Optional[float] = Query(None, description="Total interview duration"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete an interview session.
    
    Transitions the interview from IN_PROGRESS to COMPLETED status.
    Records completion time and duration.
    """
    try:
        interview = await interview_service.complete_interview(
            db=db,
            interview_id=interview_id,
            user=current_user,
            total_duration_seconds=total_duration_seconds
        )
        
        return create_interview_detail_response(interview)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except InterviewStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete interview: {str(e)}"
        )


# ============================================================
# INTERVIEW TURNS ENDPOINTS
# ============================================================

@router.get("/{interview_id}/turns", response_model=List[TurnResponse])
async def get_interview_turns(
    interview_id: uuid.UUID,
    include_evaluation: bool = Query(True, description="Include evaluation data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all turns for an interview.
    
    Returns the complete question-answer history with optional evaluation data.
    """
    try:
        interview = await interview_service.get_interview_by_id(
            db=db,
            interview_id=interview_id,
            user=current_user,
            include_turns=True
        )
        
        if not interview.turns:
            return []
        
        return [
            TurnResponse(
                id=str(turn.id),
                interview_id=str(turn.interview_id),
                turn_number=turn.turn_number,
                phase=turn.phase.value,
                ai_question=turn.ai_question,
                user_answer=turn.user_answer,
                duration_seconds=turn.duration_seconds,
                difficulty_level=turn.difficulty_level,
                created_at=turn.created_at,
                has_answer=turn.has_answer,
                has_evaluation=turn.has_evaluation,
                evaluation=turn.evaluation if include_evaluation else None,
                overall_score=turn.get_overall_score() if include_evaluation else None
            )
            for turn in interview.turns
        ]
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview turns: {str(e)}"
        )


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================

@router.get("/stats/summary", response_model=InterviewStatsResponse)
async def get_interview_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive interview statistics for the current user.
    
    Includes completion rates, average scores, time spent, and skill trends.
    """
    try:
        stats = await interview_service.get_user_interview_stats(
            db=db,
            user=current_user
        )
        
        return InterviewStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview stats: {str(e)}"
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
async def interview_service_health():
    """
    Health check endpoint for the interview service.
    
    Verifies that the interview service is operational.
    """
    return {
        "status": "healthy",
        "service": "interviews",
        "features": [
            "cv_upload",
            "ai_analysis", 
            "interview_management",
            "statistics"
        ]
    }