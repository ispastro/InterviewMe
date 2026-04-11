"""
Quick check if streaming is enabled in the backend code
"""

import os

routes_file = "app/modules/websocket/routes.py"

print("Checking if streaming is enabled in backend code...")
print("=" * 60)

with open(routes_file, 'r') as f:
    content = f.read()
    
    if "use_streaming=True" in content:
        print("✓ PASS: use_streaming=True found in routes.py")
        print("\nStreaming IS enabled in the code.")
        print("\n⚠️  If test failed, you need to RESTART the backend:")
        print("   1. Stop the backend (Ctrl+C)")
        print("   2. Start it again: uvicorn app.main:app --reload")
        print("   3. Run the test again: python test_streaming.py")
    else:
        print("✗ FAIL: use_streaming=True NOT found in routes.py")
        print("\nStreaming is NOT enabled in the code.")
        print("This shouldn't happen - the code should have been updated.")
    
print("=" * 60)
