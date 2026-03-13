"""
Quick Interview Workflow Debug
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.user import User
from app.modules.interviews import service as interview_service

async def debug_interview_workflow():
    print("DEBUGGING INTERVIEW WORKFLOW")
    print("=" * 50)
    
    sample_cv = """
    John Smith
    Senior Software Developer with 5 years of experience
    
    Technical Skills: Python, FastAPI, React, PostgreSQL, Docker, AWS
    
    Professional Experience:
    - Senior Software Developer at Tech Corp (2021-2024)
    - Built scalable APIs using FastAPI serving 10,000+ users
    """
    
    sample_jd = """
    SENIOR BACKEND DEVELOPER
    InnovateTech Solutions
    
    We are seeking a talented Senior Backend Developer to join our team.
    
    REQUIRED QUALIFICATIONS
    • 4+ years of professional software development experience
    • Strong expertise in Python and modern web frameworks (FastAPI, Django)
    • Experience with relational databases (PostgreSQL, MySQL)
    """
    
    try:
        async with AsyncSessionLocal() as db:
            # Create test user
            user = User.create_from_jwt(
                email=f"debug-test-{int(time.time())}@example.com",
                name="Debug Test User"
            )
            db.add(user)
            await db.flush()
            
            print("Creating interview...")
            interview = await interview_service.create_interview(
                db, user, sample_cv, sample_jd, target_company="InnovateTech"
            )
            
            print(f"SUCCESS: Interview created with ID {interview.id}")
            print(f"Status: {interview.status}")
            print(f"CV Analysis: {bool(interview.cv_analysis)}")
            print(f"JD Analysis: {bool(interview.jd_analysis)}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    asyncio.run(debug_interview_workflow())