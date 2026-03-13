"""
AI Debug Script - Check Groq API Responses
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.ai.cv_processor import analyze_cv_with_ai
from app.modules.ai.jd_processor import analyze_jd_with_ai

async def debug_ai_responses():
    print("AI DEBUG - Checking Groq API Responses")
    print("=" * 50)
    
    sample_cv = """
    John Smith
    Software Developer
    3 years experience
    
    Skills: Python, FastAPI, React, PostgreSQL
    
    Experience:
    - Software Developer at Tech Corp (2021-2024)
    - Built APIs using FastAPI
    """
    
    try:
        print("Testing CV Analysis...")
        result = await analyze_cv_with_ai(sample_cv)
        print("SUCCESS - CV Analysis Result:")
        print(result)
        
    except Exception as e:
        print(f"ERROR in CV Analysis: {e}")
        print(f"Error type: {type(e)}")
        
        # Let's try to see the raw response
        try:
            from groq import AsyncGroq
            from app.config import settings
            
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            
            prompt = f"""You are an expert HR professional analyzing a CV. Extract information in JSON format.

CV TEXT:
{sample_cv}

Return ONLY valid JSON with this structure:
{{
  "candidate_name": "Full name",
  "years_of_experience": 3,
  "skills": {{"technical": ["Python", "FastAPI"]}}
}}"""
            
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            raw_response = response.choices[0].message.content
            print(f"RAW GROQ RESPONSE:")
            print(repr(raw_response))
            print(f"RESPONSE CONTENT:")
            print(raw_response)
            
        except Exception as e2:
            print(f"Error getting raw response: {e2}")

if __name__ == "__main__":
    asyncio.run(debug_ai_responses())