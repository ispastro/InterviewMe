

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.integrations.upstash import get_qstash, JobStatus
from app.core.job_tracker import get_job_tracker
from app.modules.interviews import service as interview_service
from app.modules.ai.cv_processor import analyze_cv_with_ai
from app.modules.ai.jd_processor import analyze_jd_with_ai
from app.models import Interview
from app.core.exceptions import AIServiceError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_qstash_signature(request: Request) -> bool:
    
    qstash = get_qstash()
    
    if not qstash.enabled:
        logger.warning("⚠️  QStash not enabled - skipping signature verification")
        return True
    
    # Get signature from headers
    signature = request.headers.get("Upstash-Signature")
    if not signature:
        logger.error("❌ Missing Upstash-Signature header")
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Get request body
    body = await request.body()
    
    # Get URL
    url = str(request.url)
    
    # Verify signature
    is_valid = qstash.verify_signature(
        signature=signature,
        body=body,
        url=url
    )
    
    if not is_valid:
        logger.error(f"❌ Invalid signature for webhook: {url}")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    return True


@router.post("/process-interview")
async def process_interview_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    verified: bool = Depends(verify_qstash_signature)
):
    
    tracker = get_job_tracker()
    
    try:
        # Parse payload
        data = await request.json()
        interview_id = data.get("interview_id")
        job_id = data.get("job_id")
        cv_text = data.get("cv_text")
        jd_text = data.get("jd_text")
        
        if not all([interview_id, cv_text, jd_text]):
            raise ValueError("Missing required fields")
        
        logger.info(f"🔄 Processing interview: {interview_id}")
        
        # Update job status
        if job_id:
            await tracker.update_status(job_id, JobStatus.PROCESSING)
        
        # Get interview
        from sqlalchemy import select
        result = await db.execute(select(Interview).where(Interview.id == interview_id))
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise NotFoundError(f"Interview {interview_id} not found")
        
        # Process CV
        logger.info(f"📄 Analyzing CV for interview {interview_id}")
        cv_analysis = await analyze_cv_with_ai(cv_text)
        
        # Process JD
        logger.info(f"📋 Analyzing JD for interview {interview_id}")
        jd_analysis = await analyze_jd_with_ai(jd_text)
        
        # Update interview
        interview.cv_analysis = cv_analysis
        interview.jd_analysis = jd_analysis
        interview.status = "ready"
        await db.commit()
        
        logger.info(f"✅ Interview processed: {interview_id}")
        
        # Complete job
        if job_id:
            await tracker.complete_job(job_id, {
                "interview_id": interview_id,
                "cv_skills_count": len(cv_analysis.get("skills", [])),
                "jd_requirements_count": len(jd_analysis.get("requirements", []))
            })
        
        return {
            "status": "success",
            "interview_id": interview_id,
            "message": "Interview processed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error (process-interview): {str(e)}")
        
        # Fail job
        if 'job_id' in locals() and job_id:
            await tracker.fail_job(job_id, str(e))
        
        # Return 200 to prevent QStash retries for permanent errors
        if isinstance(e, (NotFoundError, ValueError)):
            return {
                "status": "error",
                "error": str(e),
                "retry": False
            }
        
        # Return 500 to trigger QStash retry for transient errors
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-question")
async def generate_question_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    verified: bool = Depends(verify_qstash_signature)
):
    
    tracker = get_job_tracker()
    
    try:
        data = await request.json()
        interview_id = data.get("interview_id")
        job_id = data.get("job_id")
        turn_number = data.get("turn_number")
        phase = data.get("phase")
        
        logger.info(f"🔄 Generating question for interview {interview_id}, turn {turn_number}")
        
        if job_id:
            await tracker.update_status(job_id, JobStatus.PROCESSING)
        
        # TODO: Implement question generation logic
        # This would use the interview conductor to generate questions
        
        question = f"Sample question for turn {turn_number}"
        
        if job_id:
            await tracker.complete_job(job_id, {
                "question": question,
                "turn_number": turn_number
            })
        
        return {
            "status": "success",
            "question": question
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error (generate-question): {str(e)}")
        
        if 'job_id' in locals() and job_id:
            await tracker.fail_job(job_id, str(e))
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-answer")
async def evaluate_answer_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    verified: bool = Depends(verify_qstash_signature)
):
    
    tracker = get_job_tracker()
    
    try:
        data = await request.json()
        turn_id = data.get("turn_id")
        job_id = data.get("job_id")
        question = data.get("question")
        answer = data.get("answer")
        
        logger.info(f"🔄 Evaluating answer for turn {turn_id}")
        
        if job_id:
            await tracker.update_status(job_id, JobStatus.PROCESSING)
        
        # TODO: Implement evaluation logic
        # This would use the interview conductor to evaluate answers
        
        evaluation = {
            "score": 8.5,
            "feedback": "Good answer with relevant details"
        }
        
        if job_id:
            await tracker.complete_job(job_id, evaluation)
        
        return {
            "status": "success",
            "evaluation": evaluation
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error (evaluate-answer): {str(e)}")
        
        if 'job_id' in locals() and job_id:
            await tracker.fail_job(job_id, str(e))
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-notification")
async def send_notification_webhook(
    request: Request,
    verified: bool = Depends(verify_qstash_signature)
):
    
    try:
        data = await request.json()
        user_id = data.get("user_id")
        notification_type = data.get("type")
        notification_data = data.get("data", {})
        
        logger.info(f"📧 Sending notification to user {user_id}: {notification_type}")
        
        # TODO: Implement notification logic
        # - Email via SendGrid/AWS SES
        # - Push notification
        # - WebSocket notification
        # - SMS via Twilio
        
        return {
            "status": "success",
            "message": "Notification sent"
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error (send-notification): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-cleanup")
async def daily_cleanup_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    verified: bool = Depends(verify_qstash_signature)
):
    
    try:
        logger.info("🧹 Running daily cleanup")
        
        # TODO: Implement cleanup tasks
        # - Delete old job tracking data (> 7 days)
        # - Archive old interviews (> 30 days)
        # - Generate daily stats
        # - Clear expired cache
        
        return {
            "status": "success",
            "message": "Daily cleanup completed"
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error (daily-cleanup): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    
    qstash = get_qstash()
    tracker = get_job_tracker()
    
    return {
        "status": "healthy",
        "qstash_enabled": qstash.enabled,
        "job_tracking_enabled": tracker.redis.enabled
    }
