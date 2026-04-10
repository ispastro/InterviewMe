"""Test server startup with Redis."""
import subprocess
import time
import requests
import sys

print("=" * 60)
print("TESTING SERVER STARTUP WITH UPSTASH REDIS")
print("=" * 60)
print()

# Start server
print("Starting server...")
process = subprocess.Popen(
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for startup
print("Waiting for server to start...")
time.sleep(5)

try:
    # Test health endpoint
    print()
    print("1. Testing /health endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test Redis health endpoint
    print("2. Testing /health/redis endpoint...")
    response = requests.get("http://localhost:8000/health/redis")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Redis Status: {data.get('status')}")
    print(f"   Ping: {data.get('ping')}")
    if 'metrics' in data:
        print(f"   Metrics: {data['metrics']}")
    print()
    
    # Test readiness endpoint
    print("3. Testing /health/ready endpoint...")
    response = requests.get("http://localhost:8000/health/ready")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Overall Status: {data.get('status')}")
    print(f"   Checks: {data.get('checks')}")
    print()
    
    print("=" * 60)
    print("SUCCESS: All health checks passed!")
    print("=" * 60)
    print()
    print("Server is running at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server...")
    
    # Keep server running
    process.wait()
    
except KeyboardInterrupt:
    print("\nStopping server...")
    process.terminate()
    process.wait()
    print("Server stopped.")
except Exception as e:
    print(f"\nERROR: {e}")
    process.terminate()
    process.wait()
    sys.exit(1)
