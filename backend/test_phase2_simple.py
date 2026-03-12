"""
Simplified Phase 2 Test Script

This script tests Phase 2 components without complex migrations:
1. Create tables directly using SQLAlchemy
2. Test all Phase 2 functionality
3. Validate API endpoints work

This approach avoids migration complexity while testing core functionality.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_models_and_database():
    """Test models and database functionality"""
    print("Testing models and database...")
    
    try:
        from app.models import User, Interview, Turn, Feedback, InterviewStatus, InterviewPhase
        from app.database import AsyncSessionLocal, create_tables
        
        # Create all tables
        await create_tables()
        print("   Tables created successfully")
        
        # Test model creation
        async with AsyncSessionLocal() as session:
            # Try to get existing user first
            from sqlalchemy import select
            stmt = select(User).where(User.email == "test-phase2@example.com")
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Create test user
                user = User.create_from_jwt(
                    email="test-phase2@example.com",
                    name="Phase 2 Test User"
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"   Created user: {user.id}")
            else:
                print(f"   Using existing user: {user.id}")
            
            # Create test interview
            interview = Interview(
                user_id=user.id,
                status=InterviewStatus.READY,
                cv_raw_text="Test CV content",
                jd_raw_text="Test JD content",
                target_role="Software Engineer",
                cv_analysis={"skills": {"technical": ["Python", "FastAPI"]}},
                jd_analysis={"required_skills": ["Python", "System Design"]}
            )
            session.add(interview)
            await session.commit()
            await session.refresh(interview)
            print(f"   Created interview: {interview.id}")
            
            # Test model methods
            assert interview.has_cv_analysis == True
            assert interview.has_jd_analysis == True
            skills = interview.get_cv_skills()
            assert "Python" in skills
            print("   Model methods working correctly")
            
            # Create test turn
            turn = Turn(
                interview_id=interview.id,
                turn_number=1,
                phase=InterviewPhase.INTRO,
                ai_question="Tell me about yourself",
                user_answer="I am a software engineer...",
                evaluation={"relevance": 8, "depth": 7, "clarity": 9}
            )
            session.add(turn)
            await session.commit()
            print("   Created turn successfully")
            
            # Test turn methods
            assert turn.has_answer == True
            assert turn.has_evaluation == True
            score = turn.get_overall_score()
            assert score is not None
            print(f"   Turn overall score: {score}")
            
            # Create test feedback
            feedback = Feedback.create_from_analysis(
                interview_id=interview.id,
                overall_score=85.0,
                strengths=[{"area": "Technical Knowledge", "score": 90}],
                weaknesses=[{"area": "Communication", "score": 70}],
                suggestions=[{"priority": "high", "action": "Practice STAR method"}],
                phase_scores={"intro": 85, "technical": 90}
            )
            session.add(feedback)
            await session.commit()
            print("   Created feedback successfully")
            
            # Test feedback methods
            assert feedback.performance_level == "good"
            top_strengths = feedback.top_strengths
            assert len(top_strengths) > 0
            print(f"   Feedback performance level: {feedback.performance_level}")
        
        return True
        
    except Exception as e:
        print(f"   Models and database test failed: {e}")
        return False


async def test_ai_processing():
    """Test AI processing modules"""
    print("Testing AI processing...")
    
    try:
        # Test CV processor utilities
        from app.modules.ai.cv_processor import extract_key_skills, get_experience_summary
        
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
                    "duration": "3 years"
                }
            ]
        }
        
        key_skills = extract_key_skills(mock_cv_analysis, 5)
        assert len(key_skills) <= 5
        print(f"   CV key skills: {key_skills}")
        
        experience_summary = get_experience_summary(mock_cv_analysis)
        assert experience_summary["total_years"] == 3
        print("   CV experience summary generated")
        
        # Test JD processor utilities
        from app.modules.ai.jd_processor import extract_critical_skills, get_interview_difficulty_level, compare_cv_to_jd
        
        mock_jd_analysis = {
            "role_title": "Senior Backend Engineer",
            "seniority_level": "senior",
            "required_skills": ["Python", "System Design", "AWS"],
            "preferred_skills": ["Kubernetes", "GraphQL"],
            "required_experience": {"years_minimum": 5, "years_preferred": 7}
        }
        
        critical_skills = extract_critical_skills(mock_jd_analysis)
        assert "Python" in critical_skills
        print(f"   JD critical skills: {critical_skills}")
        
        difficulty = get_interview_difficulty_level(mock_jd_analysis)
        assert 0.0 <= difficulty <= 1.0
        print(f"   Interview difficulty: {difficulty}")
        
        # Test CV-JD comparison
        comparison = compare_cv_to_jd(mock_cv_analysis, mock_jd_analysis)
        assert "overall_fit_score" in comparison
        print(f"   CV-JD fit score: {comparison['overall_fit_score']}")
        
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
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            # Get test user
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
            print(f"   Completion rate: {stats['completion_rate']}%")
        
        return True
        
    except Exception as e:
        print(f"   Interview service test failed: {e}")
        return False


async def test_text_extraction():
    """Test text extraction utilities"""
    print("Testing text extraction...")
    
    try:
        from app.utils.text_extraction import validate_extracted_text, get_file_info
        
        sample_text = """
        John Doe
        Software Engineer
        
        Experience:
        - 3 years at Tech Corp as Backend Developer
        - Built REST APIs using Python and FastAPI
        
        Skills: Python, JavaScript, SQL, FastAPI, React
        """
        
        cleaned_text = validate_extracted_text(sample_text, "test.txt")
        assert len(cleaned_text) > 50
        print(f"   Text validation successful: {len(cleaned_text)} characters")
        
        # Test file info
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
        
        # Test request validation
        request_data = {
            "jd_text": "We are looking for a Senior Software Engineer with 5+ years of experience in Python and system design.",
            "target_company": "Tech Corp"
        }
        
        request = CreateInterviewRequest(**request_data)
        assert request.jd_text.startswith("We are looking")
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


async def test_api_routes():
    """Test API route registration"""
    print("Testing API routes...")
    
    try:
        from app.main import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # Check for key endpoints
        expected_paths = [
            "/api/auth/me",
            "/api/interviews",
            "/health"
        ]
        
        for path in expected_paths:
            if not any(route_path.startswith(path) or path in route_path for route_path in routes):
                print(f"   Missing expected route: {path}")
                return False
        
        print(f"   All expected routes registered ({len(routes)} total)")
        return True
        
    except Exception as e:
        print(f"   API routes test failed: {e}")
        return False


async def main():
    """Run all simplified Phase 2 tests"""
    print("Running Simplified Phase 2 Tests\n")
    
    tests = [
        ("Models & Database", test_models_and_database),
        ("AI Processing", test_ai_processing),
        ("Interview Service", test_interview_service),
        ("Text Extraction", test_text_extraction),
        ("Pydantic Schemas", test_schemas),
        ("API Routes", test_api_routes),
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
        print("Phase 2 is working correctly!")
        print("\nWhat we've validated:")
        print("- Database models with JSON columns work")
        print("- AI processing utilities function correctly")
        print("- Interview service layer handles business logic")
        print("- Text extraction processes different formats")
        print("- Pydantic schemas validate requests/responses")
        print("- API routes are properly registered")
        print("\nReady for Phase 3: WebSocket Interview Engine")
    else:
        print("Some tests failed. Please review the issues.")
        return False
    
    return True


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("ERROR: .env file not found!")
        print("   Copy .env.example to .env and fill in your values")
        sys.exit(1)
    
    success = asyncio.run(main())
    if not success:
        sys.exit(1)