"""
Streaming Response Test Suite
Tests the real-time streaming of AI-generated interview questions
"""

import asyncio
import json
import websockets
import time
from datetime import datetime
from typing import List, Dict, Any

# Test configuration
BACKEND_URL = "ws://localhost:8000"
TEST_TOKEN = None  # Will be fetched from /dev/test-auth
TEST_INTERVIEW_ID = None  # Will be created during test
TEST_USER_ID = None

class StreamingTestResults:
    def __init__(self):
        self.chunks_received: List[str] = []
        self.chunk_timestamps: List[float] = []
        self.completion_received = False
        self.total_time = 0
        self.time_to_first_chunk = 0
        self.errors: List[str] = []
        
    def add_chunk(self, chunk: str, timestamp: float):
        self.chunks_received.append(chunk)
        self.chunk_timestamps.append(timestamp)
        
        if len(self.chunks_received) == 1:
            self.time_to_first_chunk = timestamp
    
    def mark_complete(self, timestamp: float):
        self.completion_received = True
        self.total_time = timestamp
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def get_summary(self) -> Dict[str, Any]:
        full_message = "".join(self.chunks_received)
        avg_chunk_size = len(full_message) / len(self.chunks_received) if self.chunks_received else 0
        
        chunk_intervals = []
        for i in range(1, len(self.chunk_timestamps)):
            interval = self.chunk_timestamps[i] - self.chunk_timestamps[i-1]
            chunk_intervals.append(interval)
        
        avg_interval = sum(chunk_intervals) / len(chunk_intervals) if chunk_intervals else 0
        
        return {
            "total_chunks": len(self.chunks_received),
            "full_message": full_message,
            "message_length": len(full_message),
            "avg_chunk_size": round(avg_chunk_size, 2),
            "time_to_first_chunk_ms": round(self.time_to_first_chunk * 1000, 2),
            "total_time_ms": round(self.total_time * 1000, 2),
            "avg_chunk_interval_ms": round(avg_interval * 1000, 2),
            "completion_received": self.completion_received,
            "errors": self.errors,
            "status": "PASS" if self.completion_received and not self.errors else "FAIL"
        }


async def get_test_token() -> str:
    """Get test authentication token"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/dev/test-auth") as response:
            if response.status != 200:
                raise Exception(f"Failed to get test token: {response.status}")
            
            data = await response.json()
            token = data["token"]
            
            # Decode token to get user_id
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get("sub", "test@example.com")
            
            return token, user_id


async def create_test_interview(token: str, user_id: str) -> str:
    """Create a test interview"""
    import aiohttp
    from io import BytesIO
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create CV file
    cv_content = b"""Software Engineer with 5 years of Python experience. 
    Worked extensively on FastAPI, Django, and Flask projects.
    Strong background in async programming, WebSocket, and real-time systems.
    Experience with PostgreSQL, Redis, and microservices architecture.
    Led team of 3 developers on multiple successful projects."""
    cv_file = BytesIO(cv_content)
    
    # Create JD file
    jd_content = b"""Senior Python Developer Position
    
    We are looking for an experienced Senior Python Developer with strong FastAPI experience.
    Must have deep knowledge of WebSocket and real-time systems.
    Experience with async programming, PostgreSQL, and Redis is required.
    Should be able to lead technical discussions and mentor junior developers.
    Minimum 5 years of Python development experience required.
    Strong problem-solving skills and ability to work in agile environment."""
    jd_file = BytesIO(jd_content)
    
    # Create multipart form data
    data = aiohttp.FormData()
    data.add_field('cv_file', cv_file, filename='cv.txt', content_type='text/plain')
    data.add_field('jd_file', jd_file, filename='jd.txt', content_type='text/plain')
    data.add_field('target_company', 'Test Company')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/interviews",
            headers=headers,
            data=data
        ) as response:
            if response.status != 201:
                text = await response.text()
                raise Exception(f"Failed to create interview: {response.status} - {text}")
            
            data = await response.json()
            return data["id"]


async def test_streaming_websocket(token: str, interview_id: str, user_id: str) -> StreamingTestResults:
    """Test streaming via WebSocket"""
    results = StreamingTestResults()
    start_time = time.time()
    
    ws_url = f"{BACKEND_URL}/ws/interview/{interview_id}?token={token}"
    
    print(f"\nConnecting to WebSocket: {ws_url[:50]}...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("WebSocket connected")
            
            # Wait for connection message
            connect_msg = await websocket.recv()
            connect_data = json.loads(connect_msg)
            print(f"Received: {connect_data['type']}")
            
            if connect_data["type"] != "connect":
                results.add_error(f"Expected 'connect' message, got '{connect_data['type']}'")
                return results
            
            # Start interview
            print("\nStarting interview...")
            await websocket.send(json.dumps({
                "type": "start_interview",
                "data": {}
            }))
            
            # Wait for opening question (non-streaming)
            opening_msg = await websocket.recv()
            opening_data = json.loads(opening_msg)
            print(f"Received: {opening_data['type']}")
            
            if opening_data["type"] == "ai_question":
                print(f"Opening question: {opening_data['data']['question'][:50]}...")
            
            # Wait for session status
            status_msg = await websocket.recv()
            status_data = json.loads(status_msg)
            print(f"Received: {status_data['type']}")
            
            # Send user response to trigger streaming
            print("\nSending user response...")
            await websocket.send(json.dumps({
                "type": "user_response",
                "data": {
                    "response": "I have 5 years of experience with Python, specializing in FastAPI and async programming."
                }
            }))
            
            # Collect streaming chunks
            print("\nWaiting for streaming chunks...")
            chunk_start_time = time.time()
            streaming_started = False
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    msg_data = json.loads(message)
                    msg_type = msg_data["type"]
                    
                    current_time = time.time() - start_time
                    
                    if msg_type == "ai_feedback":
                        print(f"Received feedback (score: {msg_data['data'].get('overall_score', 'N/A')})")
                    
                    elif msg_type == "ai_question_chunk":
                        if not streaming_started:
                            streaming_started = True
                            print(f"First chunk received at {round((time.time() - chunk_start_time) * 1000, 2)}ms")
                        
                        chunk = msg_data["data"]["chunk"]
                        results.add_chunk(chunk, current_time)
                        print(f"Chunk {len(results.chunks_received)}: '{chunk}'")
                    
                    elif msg_type == "ai_question_complete":
                        results.mark_complete(current_time)
                        question = msg_data["data"].get("question", "")
                        print(f"\nStreaming complete!")
                        print(f"Full question: {question[:100]}...")
                        break
                    
                    elif msg_type == "ai_question":
                        # Non-streaming fallback
                        print(f"Received non-streaming question (streaming may be disabled)")
                        results.add_error("Received non-streaming question instead of chunks")
                        break
                    
                except asyncio.TimeoutError:
                    results.add_error("Timeout waiting for streaming response")
                    print("Timeout waiting for response")
                    break
                except Exception as e:
                    results.add_error(f"Error receiving message: {str(e)}")
                    print(f"Error: {e}")
                    break
            
            # Close connection
            await websocket.close()
            print("\nWebSocket closed")
    
    except Exception as e:
        results.add_error(f"WebSocket connection error: {str(e)}")
        print(f"Connection error: {e}")
    
    return results


async def run_streaming_tests():
    """Run all streaming tests"""
    print("=" * 60)
    print("STREAMING RESPONSE TEST SUITE")
    print("=" * 60)
    
    try:
        # Step 1: Get test token
        print("\n1. Getting test authentication token...")
        token, user_id = await get_test_token()
        print(f"Token obtained for user: {user_id}")
        
        # Step 2: Create test interview
        print("\n2. Creating test interview...")
        interview_id = await create_test_interview(token, user_id)
        print(f"Interview created: {interview_id}")
        
        # Step 3: Test streaming
        print("\n3. Testing streaming WebSocket...")
        results = await test_streaming_websocket(token, interview_id, user_id)
        
        # Step 4: Display results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        summary = results.get_summary()
        
        print(f"\nStatus: {summary['status']}")
        print(f"\nStreaming Metrics:")
        print(f"   - Total chunks: {summary['total_chunks']}")
        print(f"   - Message length: {summary['message_length']} characters")
        print(f"   - Avg chunk size: {summary['avg_chunk_size']} characters")
        print(f"   - Time to first chunk: {summary['time_to_first_chunk_ms']}ms")
        print(f"   - Total streaming time: {summary['total_time_ms']}ms")
        print(f"   - Avg chunk interval: {summary['avg_chunk_interval_ms']}ms")
        print(f"   - Completion received: {summary['completion_received']}")
        
        if summary['full_message']:
            print(f"\nFull Message:")
            print(f"   {summary['full_message'][:200]}...")
        
        if summary['errors']:
            print(f"\nErrors:")
            for error in summary['errors']:
                print(f"   - {error}")
        
        # Validation checks
        print(f"\nValidation Checks:")
        checks = {
            "Chunks received": summary['total_chunks'] > 0,
            "Time to first chunk < 1s": summary['time_to_first_chunk_ms'] < 1000,
            "Completion signal received": summary['completion_received'],
            "No errors": len(summary['errors']) == 0,
            "Message not empty": len(summary['full_message']) > 0
        }
        
        for check, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"   [{status}] {check}")
        
        all_passed = all(checks.values())
        
        print("\n" + "=" * 60)
        if all_passed:
            print("ALL TESTS PASSED!")
        else:
            print("SOME TESTS FAILED")
        print("=" * 60)
        
        return all_passed
        
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPREREQUISITES:")
    print("   1. Backend must be running: uvicorn app.main:app --reload")
    print("   2. Database must be initialized")
    print("   3. GROQ_API_KEY must be set in .env")
    print("\nStarting tests in 3 seconds...\n")
    
    time.sleep(3)
    
    success = asyncio.run(run_streaming_tests())
    
    exit(0 if success else 1)
