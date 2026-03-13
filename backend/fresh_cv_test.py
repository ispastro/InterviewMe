"""
Fresh CV Processor Test - After Fix
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_fresh_cv_processor():
    print("FRESH CV PROCESSOR TEST")
    print("=" * 50)
    
    # Import after adding to path
    from app.modules.ai.cv_processor import analyze_cv_with_ai
    
    sample_cv = """
    John Smith
    Senior Software Developer with 5 years of experience
    
    Technical Skills: Python, FastAPI, React, PostgreSQL, Docker, AWS
    
    Professional Experience:
    - Senior Software Developer at Tech Corp (2021-2024)
    - Built scalable APIs using FastAPI serving 10,000+ users
    - Developed React frontend applications
    - Managed PostgreSQL databases and optimized queries
    - Deployed applications using Docker and AWS
    
    Education:
    - BS Computer Science, University (2019)
    
    Projects:
    - E-commerce API: Built REST API with FastAPI and PostgreSQL
    - Real-time Chat: WebSocket-based messaging system
    """
    
    try:
        print("Testing CV analysis with comprehensive CV...")
        result = await analyze_cv_with_ai(sample_cv)
        print("SUCCESS!")
        print(f"Candidate: {result.get('candidate_name')}")
        print(f"Experience: {result.get('years_of_experience')} years")
        print(f"Skills: {result.get('skills', {}).get('technical', [])}")
        print(f"Seniority: {result.get('seniority_level')}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fresh_cv_processor())