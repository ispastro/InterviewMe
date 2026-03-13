"""
WebSocket Client Demo for InterviewMe Platform
Demonstrates real-time interview functionality
"""
import asyncio
import json
import websockets
import sys
import os

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.auth.dependencies import create_test_token

class InterviewWebSocketClient:
    """Demo WebSocket client for testing interview sessions"""
    
    def __init__(self, base_url="ws://localhost:8000"):
        self.base_url = base_url
        self.websocket = None
        self.token = None
        
    async def create_auth_token(self):
        """Create test authentication token"""
        self.token = create_test_token(
            email="demo@example.com",
            name="Demo User"
        )
        print(f"Created auth token: {self.token[:50]}...")
        
    async def connect(self, interview_id="demo-interview-123"):
        """Connect to WebSocket interview endpoint"""
        if not self.token:
            await self.create_auth_token()
            
        uri = f"{self.base_url}/ws/interview/{interview_id}?token={self.token}"
        
        try:
            self.websocket = await websockets.connect(uri)
            print(f"Connected to interview {interview_id}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def send_message(self, message_type, data=None):
        """Send message to WebSocket"""
        if not self.websocket:
            print("Not connected to WebSocket")
            return
            
        message = {
            "type": message_type,
            "data": data or {}
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"Sent: {message_type}")
    
    async def receive_message(self):
        """Receive message from WebSocket"""
        if not self.websocket:
            return None
            
        try:
            raw_message = await self.websocket.recv()
            message = json.loads(raw_message)
            return message
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
    
    async def start_interview_demo(self):
        """Demonstrate a complete interview session"""
        print("\n" + "="*50)
        print("WEBSOCKET INTERVIEW DEMO")
        print("="*50)
        
        # Connect
        if not await self.connect():
            return
        
        # Listen for connection confirmation
        print("\nWaiting for connection confirmation...")
        connect_msg = await self.receive_message()
        if connect_msg and connect_msg.get("type") == "connect":
            print(f"✓ Connected: {connect_msg['data']['message']}")
        
        # Start interview
        print("\nStarting interview...")
        await self.send_message("start_interview")
        
        # Wait for opening question
        question_msg = await self.receive_message()
        if question_msg and question_msg.get("type") == "ai_question":
            question_data = question_msg["data"]
            print(f"\n🤖 AI: {question_data['question']}")
            print(f"   Type: {question_data['question_type']}")
            print(f"   Turn: {question_data['turn_number']}")
        
        # Simulate user responses
        responses = [
            "Hi! I'm a software developer with 3 years of experience in Python and web development. I'm passionate about building scalable applications and I'm excited about this opportunity because it aligns with my skills in backend development.",
            
            "I recently worked on a challenging project where I had to optimize a slow API that was taking 5+ seconds to respond. I analyzed the database queries, implemented proper indexing, added caching with Redis, and refactored the code to use async operations. This reduced response time to under 500ms.",
            
            "I prefer to break down complex problems into smaller, manageable pieces. I start by understanding the requirements clearly, then I research existing solutions, design a plan, implement incrementally with testing, and iterate based on feedback. I also believe in documenting the process for future reference."
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n👤 You: {response}")
            
            # Send response
            await self.send_message("user_response", {"response": response})
            
            # Wait for feedback
            feedback_msg = await self.receive_message()
            if feedback_msg and feedback_msg.get("type") == "ai_feedback":
                evaluation = feedback_msg["data"]["evaluation"]
                print(f"\n📊 Evaluation (Score: {evaluation['overall_score']}/10):")
                print(f"   Strengths: {', '.join(evaluation['strengths'])}")
                print(f"   Feedback: {evaluation['feedback']}")
            
            # Wait for next question (if not the last response)
            if i < len(responses):
                question_msg = await self.receive_message()
                if question_msg and question_msg.get("type") == "ai_question":
                    question_data = question_msg["data"]
                    print(f"\n🤖 AI: {question_data['question']}")
                    print(f"   Type: {question_data['question_type']}")
                    print(f"   Turn: {question_data['turn_number']}")
            
            # Small delay between responses
            await asyncio.sleep(1)
        
        # Wait for interview completion or manually end it
        print("\nEnding interview...")
        await self.send_message("end_interview")
        
        # Wait for final summary
        summary_msg = await self.receive_message()
        if summary_msg and summary_msg.get("type") == "session_status":
            if summary_msg["data"]["status"] == "completed":
                summary = summary_msg["data"]["summary"]
                print(f"\n📋 INTERVIEW SUMMARY:")
                print(f"   Overall Rating: {summary['overall_rating']}")
                print(f"   Overall Score: {summary['overall_score']}/10")
                print(f"   Recommendation: {summary['recommendation']}")
                print(f"   Key Strengths: {', '.join(summary['key_strengths'])}")
                print(f"   Total Turns: {summary['total_turns']}")
        
        # Close connection
        await self.websocket.close()
        print("\n✓ Interview demo completed!")
    
    async def ping_test(self):
        """Test WebSocket connection health"""
        print("\nTesting WebSocket ping...")
        
        if not await self.connect():
            return
        
        # Send ping
        await self.send_message("ping")
        
        # Wait for pong
        pong_msg = await self.receive_message()
        if pong_msg and pong_msg.get("type") == "pong":
            print(f"✓ Received pong: {pong_msg['data']['timestamp']}")
        
        await self.websocket.close()

async def main():
    """Run WebSocket demo"""
    client = InterviewWebSocketClient()
    
    print("InterviewMe WebSocket Client Demo")
    print("Make sure the FastAPI server is running on localhost:8000")
    
    try:
        # Run ping test first
        await client.ping_test()
        
        # Run full interview demo
        await client.start_interview_demo()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())