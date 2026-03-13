"""
Direct CV Processor Test
"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.ai.cv_processor import analyze_cv_with_ai

async def test_cv_processor_directly():
    print("DIRECT CV PROCESSOR TEST")
    print("=" * 50)
    
    sample_cv = """
    John Smith
    Software Developer with 3 years of experience
    
    Technical Skills: Python, FastAPI, React, PostgreSQL, Docker
    
    Professional Experience:
    - Software Developer at Tech Corp (2021-2024)
    - Built scalable APIs using FastAPI
    - Developed React frontend applications
    - Managed PostgreSQL databases
    
    Education:
    - BS Computer Science, University (2021)
    """
    
    try:
        print("Testing CV analysis...")
        result = await analyze_cv_with_ai(sample_cv)
        print("SUCCESS!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e)}")
        
        # Let's trace through the CV processor manually
        print("\\nTracing through CV processor...")
        
        from groq import AsyncGroq
        from app.config import settings
        
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        
        prompt = f"""You are an expert HR professional and career coach analyzing a candidate's CV. Your task is to extract structured information that will be used to conduct a tailored technical interview.

IMPORTANT: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Analyze the following CV text and extract information in this exact JSON structure:

{{
  "candidate_name": "Full name of the candidate",
  "years_of_experience": 0,
  "current_role": "Most recent job title",
  "seniority_level": "junior|mid|senior|lead|principal",
  "skills": {{
    "technical": ["List of technical skills, programming languages, frameworks, tools"],
    "soft": ["Communication", "Leadership", "Problem-solving", etc.]
  }},
  "experience": [
    {{
      "role": "Job title",
      "company": "Company name",
      "duration": "Time period (e.g., '2 years', '6 months')",
      "key_achievements": ["Notable accomplishments", "Quantified results"],
      "technologies_used": ["Tech stack used in this role"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "School/University name",
      "year": "Graduation year or 'ongoing'",
      "relevant_coursework": ["Relevant courses if mentioned"]
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech stack used"],
      "achievements": ["Key outcomes or metrics"]
    }}
  ],
  "certifications": ["List of professional certifications"],
  "notable_points": ["Unique achievements", "Publications", "Awards", "Open source contributions"],
  "potential_gaps": ["Areas where experience might be lacking", "Skills not mentioned but typically expected"],
  "interview_focus_areas": ["Areas to probe deeper", "Strengths to validate", "Gaps to explore"]
}}

CV TEXT TO ANALYZE:
{sample_cv}"""
        
        try:
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9,
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"AI Response: {ai_response[:200]}...")
            
            # Try parsing
            try:
                cv_analysis = json.loads(ai_response)
                print("Direct JSON parse: SUCCESS")
            except json.JSONDecodeError as e:
                print(f"Direct JSON parse failed: {e}")
                
                # Try markdown extraction
                if "```" in ai_response:
                    if "```json" in ai_response:
                        json_start = ai_response.find("```json") + 7
                    else:
                        json_start = ai_response.find("```") + 3
                    
                    json_end = ai_response.find("```", json_start)
                    if json_end > json_start:
                        extracted = ai_response[json_start:json_end].strip()
                        print(f"Extracted JSON: {extracted[:200]}...")
                        
                        try:
                            cv_analysis = json.loads(extracted)
                            print("Markdown extraction: SUCCESS")
                            print(f"Parsed keys: {list(cv_analysis.keys())}")
                            
                            # Check required fields
                            required_fields = ["candidate_name", "years_of_experience", "skills", "experience"]
                            for field in required_fields:
                                if field not in cv_analysis:
                                    print(f"Missing field: {field}")
                                else:
                                    print(f"Field {field}: {cv_analysis[field]}")
                            
                        except json.JSONDecodeError as e2:
                            print(f"Markdown extraction failed: {e2}")
                            print(f"Extracted content: {repr(extracted)}")
                
        except Exception as e2:
            print(f"Manual trace error: {e2}")

if __name__ == "__main__":
    asyncio.run(test_cv_processor_directly())