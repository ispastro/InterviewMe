"""
Detailed AI Response Debug Script
"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from groq import AsyncGroq
from app.config import settings

async def debug_detailed_response():
    print("DETAILED AI RESPONSE DEBUG")
    print("=" * 50)
    
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    sample_cv = """
    John Smith
    Software Developer
    3 years experience
    
    Skills: Python, FastAPI, React, PostgreSQL
    
    Experience:
    - Software Developer at Tech Corp (2021-2024)
    - Built APIs using FastAPI
    """
    
    prompt = f"""You are an expert HR professional analyzing a CV. Extract information in JSON format.

CV TEXT:
{sample_cv}

Return ONLY valid JSON with this structure:
{{
  "candidate_name": "Full name",
  "years_of_experience": 3,
  "skills": {{"technical": ["Python", "FastAPI"]}}
}}"""
    
    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        raw_response = response.choices[0].message.content
        print(f"RAW RESPONSE (repr): {repr(raw_response)}")
        print(f"RAW RESPONSE (str):")
        print(raw_response)
        print(f"LENGTH: {len(raw_response)}")
        
        # Try to extract JSON manually
        if "```" in raw_response:
            json_start = raw_response.find("```") + 3
            json_end = raw_response.find("```", json_start)
            if json_end > json_start:
                json_content = raw_response[json_start:json_end].strip()
                print(f"\\nEXTRACTED JSON (repr): {repr(json_content)}")
                print(f"EXTRACTED JSON (str):")
                print(json_content)
                
                try:
                    parsed = json.loads(json_content)
                    print(f"\\nPARSED SUCCESSFULLY: {parsed}")
                except json.JSONDecodeError as e:
                    print(f"\\nJSON PARSE ERROR: {e}")
                    print(f"ERROR POSITION: {e.pos}")
                    if e.pos < len(json_content):
                        print(f"CHARACTER AT ERROR: {repr(json_content[e.pos])}")
                        print(f"CONTEXT: {repr(json_content[max(0, e.pos-10):e.pos+10])}")
        
    except Exception as e:
        print(f"API ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_detailed_response())