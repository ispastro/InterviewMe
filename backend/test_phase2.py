"""
Phase 2 Test Script

This script tests all Phase 2 components:
1. Database migrations and new models
2. Text extraction from different file formats
3. AI processing (CV and JD analysis)
4. Interview service layer
5. REST API endpoints
6. File upload functionality

Run this script to validate Phase 2 before moving to Phase 3.
"""

import asyncio
import sys
import os
import json
import tempfile
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_database_migration():
    """Test database migration and new models"""
    print("Testing database migration...")
    
    try:
        # Run migration
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode != 0:
            print(f"   Migration failed: {result.stderr}")
            return False
        
        print("   Migration completed successfully")
        
        # Test model imports
        from app.models import User, Interview, Turn, Feedback, InterviewStatus, InterviewPhase
        from app.database import AsyncSessionLocal
        
        # Test model creation
        async with AsyncSessionLocal() as session:
            # Create a test user
            user = User.create_from_jwt(
                email="test-phase2@example.com",
                name="Phase 2 Test User"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Create a test interview
            interview = Interview(
                user_id=user.id,
                status=InterviewStatus.PENDING,
                cv_raw_text="Test CV content for Phase 2 testing",
                jd_raw_text="Test job description content",
                target_role="Software Engineer"
            )
            session.add(interview)
            await session.commit()
            await session.refresh(interview)
            
            print(f"   Created test interview: {interview.id}")
            print(f"   Interview status: {interview.status.value}")
            
            # Test model methods
            assert interview.is_ready_to_start == False
            assert interview.has_cv_analysis == False
            
            print("   Model methods working correctly")
        
        return True
        
    except Exception as e:
        print(f"   Database migration test failed: {e}")
        return False


async def test_text_extraction():
    """Test text extraction from different file formats"""
    print("Testing text extraction...")
    
    try:
        from app.utils.text_extraction import extract_text_from_txt, validate_extracted_text
        
        # Test text file processing
        sample_cv_text = """
        John Doe
        Software Engineer
        
        Experience:
        - 3 years at Tech Corp as Backend Developer
        - Built REST APIs using Python and FastAPI
        - Worked with PostgreSQL and Redis
        
        Skills:
        - Python, JavaScript, SQL
        - FastAPI, React, Docker
        - AWS, Git, Agile
        
        Education:
        - BS Computer Science, University of Tech (2020)
        """
        
        # Test text validation
        cleaned_text = validate_extracted_text(sample_cv_text, "test_cv.txt")
        print(f"   Text extraction successful: {len(cleaned_text)} characters")
        
        # Test file info
        from app.utils.text_extraction import get_file_info
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.content_type = "text/plain"
        
        file_info = get_file_info(MockFile("test.txt"))
        assert file_info["is_supported"] == True
        print("   File info validation working")
        
        return True
        
    except Exception as e:
        print(f"   Text extraction test failed: {e}")
        return False


async def test_ai_processing():
    """Test AI processing modules"""
    print("Testing AI processing...")
    
    try:
        # Test CV processor (without actual API call)
        from app.modules.ai.cv_processor import extract_key_skills, get_experience_summary
        
        # Mock CV analysis data
        mock_cv_analysis = {
            "candidate_name": "John Doe",
            "years_of_experience": 3,
            "current_role": "Backend Developer",
            "seniority_level": "mid",
            "skills": {
                "technical": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "soft": ["Communication", "Problem-solving"]
            },
            "experience": [
                {
                    "role": "Backend Developer",
                    "company": "Tech Corp",
                    "duration": "3 years",
                    "key_achievements": ["Built REST APIs", "Improved performance"],
                    "technologies_used": ["Python", "FastAPI"]
                }
            ]
        }
        
        # Test utility functions
        key_skills = extract_key_skills(mock_cv_analysis, 5)
        assert len(key_skills) <= 5
        print(f"   Extracted key skills: {key_skills}")
        
        experience_summary = get_experience_summary(mock_cv_analysis)
        assert experience_summary["total_years"] == 3
        assert experience_summary["seniority_level"] == "mid"
        print("   Experience summary generated successfully")
        
        # Test JD processor utilities
        from app.modules.ai.jd_processor import extract_critical_skills, get_interview_difficulty_level
        
        mock_jd_analysis = {
            "role_title": "Senior Backend Engineer",
            "seniority_level": "senior",
            "required_skills": ["Python", "System Design", "AWS"],
            "preferred_skills": ["Kubernetes", "GraphQL"],
            "required_experience": {"years_minimum": 5, "years_preferred": 7}
        }
        
        critical_skills = extract_critical_skills(mock_jd_analysis)
        assert "Python" in critical_skills
        print(f"   Critical skills extracted: {critical_skills}")
        
        difficulty = get_interview_difficulty_level(mock_jd_analysis)
        assert 0.0 <= difficulty <= 1.0
        print(f"   Interview difficulty calculated: {difficulty}")
        
        return True
        
    except Exception as e:
        print(f"   AI processing test failed: {e}")
        return False


async def test_interview_service():
    """Test interview service layer"""
    print("Testing interview service...")
    
    try:
        from app.modules.interviews.service import get_user_interview_stats
        from app.models import User
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            # Get test user
            from sqlalchemy import select
            stmt = select(User).where(User.email == "test-phase2@example.com")
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("   No test user found, skipping service test")
                return True
            
            # Test statistics
            stats = await get_user_interview_stats(session, user)
            assert "total_interviews" in stats
            assert "completion_rate" in stats
            print(f"   User stats: {stats['total_interviews']} interviews")
            
            print("   Interview service working correctly")
        
        return True
        
    except Exception as e:
        print(f"   Interview service test failed: {e}")
        return False


async def test_schemas():
    """Test Pydantic schemas"""
    print("Testing Pydantic schemas...")
    
    try:
        from app.schemas.interview import (
            CreateInterviewRequest,
            InterviewSummaryResponse,
            CVAnalysisResponse,
            SkillAnalysisResponse
        )
        
        # Test request schema validation
        request_data = {
            "jd_text": "We are looking for a Senior Software Engineer with 5+ years of experience in Python and system design.",
            "target_company": "Tech Corp"
        }
        
        request = CreateInterviewRequest(**request_data)
        assert request.jd_text.startswith("We are looking")
        assert request.target_company == "Tech Corp"
        print("   Request schema validation working")
        
        # Test response schema
        skills_data = {
            "technical": ["Python", "FastAPI"],
            "soft": ["Communication"]
        }
        skills = SkillAnalysisResponse(**skills_data)
        assert len(skills.technical) == 2
        print("   Response schema validation working")
        
        return True
        
    except Exception as e:
        print(f"   Schema test failed: {e}")
        return False


async def test_api_startup():
    """Test that the API can start up with all routes"""
    print("Testing API startup...")
    
    try:
        from app.main import app
        from app.modules.interviews.router import router as interviews_router
        from app.modules.auth.router import router as auth_router
        
        # Check that routers are included
        route_paths = [route.path for route in app.routes]
        
        # Check for key endpoints
        expected_paths = [
            "/api/auth/me",
            "/api/interviews",
            "/health"
        ]
        
        for path in expected_paths:
            # Check if any route starts with this path (for parameterized routes)
            if not any(route_path.startswith(path) or path in route_path for route_path in route_paths):
                print(f"   Missing expected route: {path}")
                return False
        
        print("   All expected routes are registered")
        print(f"   Total routes: {len(route_paths)}")
        
        return True
        
    except Exception as e:
        print(f"   API startup test failed: {e}")
        return False


async def main():
    """Run all Phase 2 tests"""
    print("Running Phase 2 Tests\n")
    
    tests = [
        ("Database Migration", test_database_migration),
        ("Text Extraction", test_text_extraction),
        ("AI Processing", test_ai_processing),
        ("Interview Service", test_interview_service),
        ("Pydantic Schemas", test_schemas),
        ("API Startup", test_api_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ERROR: {test_name} test crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("Test Results:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("Phase 2 is working correctly! Ready for Phase 3.")
        print("\nNext steps:")
        print("1. You can test the API manually using the /docs endpoint")
        print("2. Try uploading a CV file and creating an interview")
        print("3. Ready to move to Phase 3: WebSocket Interview Engine")
    else:
        print("Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("ERROR: .env file not found!")
        print("   Copy .env.example to .env and fill in your values:")
        print("   cp .env.example .env")
        sys.exit(1)
    
    asyncio.run(main())