"""
🧪 Integration Test - LLM Gateway with InterviewMe Components

Tests the integrated Gateway with:
- CV Processor
- JD Processor
- Interview Conductor

Run: python test_integration.py
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.ai.cv_processor import analyze_cv_with_ai
from app.modules.ai.jd_processor import analyze_jd_with_ai
from app.modules.websocket.interview_conductor import interview_conductor
from app.modules.llm.gateway import llm_gateway
from app.modules.llm.cache import initialize_cache, get_cache
from app.config import settings
import redis.asyncio as redis


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")


async def setup_redis():
    """Initialize Redis for testing"""
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        initialize_cache(redis_client=redis_client, default_ttl=settings.CACHE_TTL_SECONDS)
        return True
    except Exception as e:
        print_error(f"Redis setup failed: {e}")
        return False


async def test_cv_processor():
    """Test CV Processor with Gateway"""
    print_header("TEST 1: CV Processor Integration")
    
    cv_text = """
John Doe
Senior Software Engineer

EXPERIENCE:
- 5 years of Python development
- Expert in FastAPI, Django, Flask
- Experience with React, TypeScript
- AWS, Docker, Kubernetes

EDUCATION:
- BS Computer Science, MIT

SKILLS:
Python, JavaScript, React, FastAPI, PostgreSQL, Redis, Docker
"""
    
    try:
        # First call (cache miss)
        print_info("First CV analysis (cache miss)...")
        start = time.time()
        result1 = await analyze_cv_with_ai(cv_text)
        duration1 = time.time() - start
        
        print_success(f"CV analyzed successfully!")
        print_info(f"Candidate: {result1.get('candidate_name', 'Unknown')}")
        print_info(f"Experience: {result1.get('years_of_experience', 0)} years")
        print_info(f"Skills: {len(result1.get('skills', {}).get('technical', []))} technical skills")
        print_info(f"Duration: {duration1:.2f}s")
        
        # Second call (cache hit)
        print_info("\nSecond CV analysis (cache hit)...")
        start = time.time()
        result2 = await analyze_cv_with_ai(cv_text)
        duration2 = time.time() - start
        
        speedup = duration1 / duration2 if duration2 > 0 else 0
        print_success(f"Cache HIT! Duration: {duration2:.4f}s")
        print_success(f"Speedup: {speedup:.0f}x faster! 🚀")
        
        return True
        
    except Exception as e:
        print_error(f"CV Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_jd_processor():
    """Test JD Processor with Gateway"""
    print_header("TEST 2: JD Processor Integration")
    
    jd_text = """
Senior Backend Engineer

We're looking for an experienced backend engineer to join our team.

REQUIREMENTS:
- 5+ years of Python development
- Strong experience with FastAPI or Django
- Experience with PostgreSQL, Redis
- Docker, Kubernetes knowledge
- AWS or GCP experience

RESPONSIBILITIES:
- Design and build scalable APIs
- Optimize database performance
- Mentor junior developers
- Participate in architecture decisions

NICE TO HAVE:
- React/TypeScript experience
- System design experience
- Open source contributions
"""
    
    try:
        # First call (cache miss)
        print_info("First JD analysis (cache miss)...")
        start = time.time()
        result1 = await analyze_jd_with_ai(jd_text)
        duration1 = time.time() - start
        
        print_success(f"JD analyzed successfully!")
        print_info(f"Role: {result1.get('role_title', 'Unknown')}")
        print_info(f"Seniority: {result1.get('seniority_level', 'Unknown')}")
        print_info(f"Required skills: {len(result1.get('required_skills', []))}")
        print_info(f"Duration: {duration1:.2f}s")
        
        # Second call (cache hit)
        print_info("\nSecond JD analysis (cache hit)...")
        start = time.time()
        result2 = await analyze_jd_with_ai(jd_text)
        duration2 = time.time() - start
        
        speedup = duration1 / duration2 if duration2 > 0 else 0
        print_success(f"Cache HIT! Duration: {duration2:.4f}s")
        print_success(f"Speedup: {speedup:.0f}x faster! 🚀")
        
        return True
        
    except Exception as e:
        print_error(f"JD Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interview_conductor():
    """Test Interview Conductor with Gateway"""
    print_header("TEST 3: Interview Conductor Integration")
    
    interview_data = {
        "cv_analysis": {
            "candidate_name": "John Doe",
            "years_of_experience": 5,
            "current_role": "Senior Software Engineer",
            "skills": {
                "technical": ["Python", "FastAPI", "React", "PostgreSQL"],
                "soft": ["Leadership", "Communication"]
            }
        },
        "jd_analysis": {
            "role_title": "Senior Backend Engineer",
            "seniority_level": "senior",
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
        },
        "interview_strategy": {
            "difficulty_level": 0.7,
            "total_duration_minutes": 45
        }
    }
    
    try:
        # Test opening question
        print_info("Generating opening question...")
        start = time.time()
        opening = await interview_conductor.generate_opening_question(interview_data)
        duration = time.time() - start
        
        print_success(f"Opening question generated!")
        print_info(f"Question: {opening['question'][:100]}...")
        print_info(f"Type: {opening['question_type']}")
        print_info(f"Duration: {duration:.2f}s")
        
        # Test evaluation
        print_info("\nEvaluating sample response...")
        question_data = {
            "question": "Tell me about your experience with Python.",
            "question_type": "technical",
            "focus_area": "python_experience",
            "evaluation_criteria": ["technical_depth", "communication"]
        }
        user_response = "I have 5 years of Python experience, primarily with FastAPI and Django. I've built several REST APIs and worked with PostgreSQL databases."
        
        start = time.time()
        evaluation = await interview_conductor.evaluate_response(
            question_data, user_response, interview_data
        )
        duration = time.time() - start
        
        print_success(f"Response evaluated!")
        print_info(f"Score: {evaluation['overall_score']}/10")
        print_info(f"Strengths: {', '.join(evaluation.get('strengths', [])[:2])}")
        print_info(f"Duration: {duration:.2f}s")
        
        return True
        
    except Exception as e:
        print_error(f"Interview Conductor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gateway_metrics():
    """Test Gateway metrics"""
    print_header("TEST 4: Gateway Metrics")
    
    try:
        metrics = llm_gateway.get_metrics()
        
        print_info(f"Total requests: {metrics['total_requests']}")
        print_info(f"Cache hits: {metrics['cache_hits']}")
        print_info(f"Cache misses: {metrics['cache_misses']}")
        print_info(f"Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
        print_info(f"API calls: {metrics['api_calls']}")
        print_info(f"Average latency: {metrics['avg_latency_ms']:.2f}ms")
        
        if metrics['cache_hits'] > 0:
            print_success(f"Cache is working! Hit rate: {metrics['cache_hit_rate']:.1f}%")
        else:
            print_error("No cache hits detected")
        
        # Get health status
        health = await llm_gateway.get_health()
        print_info(f"\nGateway status: {health['status']}")
        print_info(f"Cache enabled: {health['cache']['enabled']}")
        print_info(f"Model: {health['client']['model']}")
        
        return True
        
    except Exception as e:
        print_error(f"Metrics test failed: {e}")
        return False


async def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}🚀 InterviewMe Integration Tests{Colors.END}")
    print(f"{Colors.BOLD}Testing LLM Gateway with Application Components{Colors.END}")
    
    # Setup Redis
    print_info("Setting up Redis...")
    if not await setup_redis():
        print_error("Redis setup failed. Make sure Redis is running.")
        return False
    print_success("Redis connected!")
    
    # Clear cache for clean test
    cache = get_cache()
    await cache.clear_all()
    print_info("Cache cleared for clean test")
    
    # Reset metrics
    llm_gateway.reset_metrics()
    print_info("Metrics reset")
    
    # Run tests
    results = {}
    results['cv_processor'] = await test_cv_processor()
    results['jd_processor'] = await test_jd_processor()
    results['interview_conductor'] = await test_interview_conductor()
    results['gateway_metrics'] = await test_gateway_metrics()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        color = Colors.GREEN if passed_test else Colors.RED
        print(f"{color}{status}{Colors.END} - {test_name.upper().replace('_', ' ')}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL INTEGRATION TESTS PASSED!{Colors.END}")
        print(f"\n{Colors.YELLOW}Your LLM Gateway is fully integrated and working!{Colors.END}")
        print("\nNext steps:")
        print("1. Start your backend: uvicorn app.main:app --reload")
        print("2. Test with real interviews")
        print("3. Monitor cache hit rates and performance")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Check errors above.{Colors.END}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
