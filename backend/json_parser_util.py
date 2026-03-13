"""
Robust JSON Parser for AI Responses
Handles various formats that AI models might return
"""
import json
import re
from typing import Dict, Any, Optional

def parse_ai_json_response(content: str) -> Dict[str, Any]:
    """
    Robustly parse JSON from AI response, handling various formats.
    
    Args:
        content: Raw AI response content
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    # Clean the content
    content = content.strip()
    
    # Try direct JSON parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    if "```" in content:
        # Handle ```json format
        if "```json" in content:
            json_start = content.find("```json") + 7
        else:
            # Handle ``` format
            json_start = content.find("```") + 3
        
        json_end = content.find("```", json_start)
        if json_end > json_start:
            json_content = content[json_start:json_end].strip()
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                pass
    
    # Try to find JSON-like content using regex
    json_pattern = r'\{.*\}'
    matches = re.findall(json_pattern, content, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Try to fix common JSON issues
    # Remove trailing commas
    fixed_content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    # Try parsing the fixed content
    try:
        return json.loads(fixed_content)
    except json.JSONDecodeError:
        pass
    
    # If all else fails, raise the original error
    raise json.JSONDecodeError(f"Could not parse JSON from AI response: {content[:200]}...", content, 0)

def test_json_parser():
    """Test the JSON parser with various formats"""
    test_cases = [
        # Direct JSON
        '{"name": "test", "value": 123}',
        
        # Markdown with ```json
        '```json\n{"name": "test", "value": 123}\n```',
        
        # Markdown with ```
        '```\n{"name": "test", "value": 123}\n```',
        
        # With extra text
        'Here is the JSON:\n```\n{"name": "test", "value": 123}\n```\nThat\'s it!',
        
        # Incomplete JSON (should fail)
        '{"name": "test", "value":',
    ]
    
    for i, test_case in enumerate(test_cases):
        try:
            result = parse_ai_json_response(test_case)
            print(f"Test {i+1}: SUCCESS - {result}")
        except json.JSONDecodeError as e:
            print(f"Test {i+1}: FAILED - {e}")

if __name__ == "__main__":
    test_json_parser()