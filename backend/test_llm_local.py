"""
🧪 LLM Infrastructure Local Validation Script

Tests:
- Redis connection
- Layer 1: LLM Client
- Layer 2: LLM Cache
- Layer 3: LLM Gateway
- Cache performance metrics

Run: python test_llm_local.py
"""

import asyncio
import time
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.llm.client import llm_client
from app.modules.llm.cache import initialize_cache, get_cache
from app.modules.llm.gateway import llm_gateway
from app.config import settings

# Initialize Redis
import redis.asyncio as redis


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")


async def test_redis_connection() -> bool:
    """Test 1: Redis Connection"""
    print_header("TEST 1: Redis Connection")
    
    try:
        # Initialize Redis client
        print_info(f"Connecting to Redis at {settings.REDIS_URL}...")
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        print_success("Redis PING successful!")
        
        # Initialize cache with Redis client
        initialize_cache(redis_client=redis_client, default_ttl=settings.CACHE_TTL_SECONDS)
        llm_cache = get_cache()
        
        # Test basic operations
        await llm_cache.set("test_key", "test_value", ttl=10)
        value = await llm_cache.get("test_key")
        
        if value == "test_value":
            print_success("Redis read/write successful!")
            print_info(f"Redis URL: {settings.REDIS_URL}")
            print_info(f"Cache TTL: {settings.CACHE_TTL_SECONDS}s")
            
            # Cleanup
            await llm_cache.delete("test_key")
            return True
        else:
            print_error("Redis returned unexpected value")
            return False
            
    except Exception as e:
        print_error(f"Redis connection failed: {str(e)}")
        print_info("Make sure Redis is running: docker ps")
        print_info("Or start it: docker start redis")
        return False


async def test_llm_client() -> bool:
    """Test 2: LLM Client"""
    print_header("TEST 2: LLM Client (Layer 1)")
    
    try:
        print_info("Sending test request to Groq API...")
        
        start = time.time()
        response = await llm_client.chat_completion(
            prompt="Say 'Hello from InterviewMe!' in exactly 5 words.",
            max_tokens=50
        )
        duration = time.time() - start
        
        if response and len(response) > 0:
            print_success("LLM Client working!")
            print_info(f"Response: {response[:100]}...")
            print_info(f"Duration: {duration:.2f}s")
            return True
        else:
            print_error("Empty response from LLM")
            return False
            
    except Exception as e:
        print_error(f"LLM Client failed: {str(e)}")
        print_info("Check your GROQ_API_KEY in .env")
        return False


async def test_llm_cache() -> bool:
    """Test 3: LLM Cache"""
    print_header("TEST 3: LLM Cache (Layer 2)")
    
    try:
        llm_cache = get_cache()
        
        # Clear any existing cache
        await llm_cache.clear_all()
        print_info("Cache cleared")
        
        # Test cache miss (first call)
        print_info("Testing cache MISS (first call)...")
        prompt = "What is 2+2? Answer in one word."
        
        start = time.time()
        response1 = await llm_client.chat_completion(prompt=prompt, max_tokens=20)
        duration_miss = time.time() - start
        
        # Manually cache the response
        await llm_cache.set(
            prompt=prompt,
            response=response1,
            model=llm_client.model,
            temperature=llm_client.default_temperature,
            max_tokens=20
        )
        
        print_success(f"Cache MISS: {duration_miss:.2f}s")
        
        # Test cache hit (second call)
        print_info("Testing cache HIT (second call)...")
        
        start = time.time()
        response2 = await llm_cache.get(
            prompt=prompt,
            model=llm_client.model,
            temperature=llm_client.default_temperature,
            max_tokens=20
        )
        duration_hit = time.time() - start
        
        if response2 == response1:
            speedup = duration_miss / duration_hit if duration_hit > 0 else 0
            print_success(f"Cache HIT: {duration_hit:.4f}s")
            print_success(f"Speedup: {speedup:.0f}x faster! 🚀")
            return True
        else:
            print_error("Cache returned different value")
            return False
            
    except Exception as e:
        print_error(f"Cache test failed: {str(e)}")
        return False


async def test_llm_gateway() -> bool:
    """Test 4: LLM Gateway"""
    print_header("TEST 4: LLM Gateway (Layer 3)")
    
    try:
        llm_cache = get_cache()
        # Clear cache for clean test
        await llm_cache.clear_all()
        
        prompt = "Name one color. Just one word."
        
        # First call (cache miss)
        print_info("First call (should hit API)...")
        start = time.time()
        response1 = await llm_gateway.completion(prompt=prompt, max_tokens=20)
        duration1 = time.time() - start
        
        metrics1 = llm_gateway.get_metrics()
        
        print_success(f"Response: {response1[:50]}...")
        print_info(f"Cache hits: {metrics1['cache_hits']}")
        print_info(f"API calls: {metrics1['api_calls']}")
        print_info(f"Duration: {duration1:.2f}s")
        
        # Second call (cache hit)
        print_info("\nSecond call (should hit cache)...")
        start = time.time()
        response2 = await llm_gateway.completion(prompt=prompt, max_tokens=20)
        duration2 = time.time() - start
        
        metrics2 = llm_gateway.get_metrics()
        
        print_success(f"Response: {response2[:50]}...")
        print_info(f"Cache hits: {metrics2['cache_hits']}")
        print_info(f"API calls: {metrics2['api_calls']}")
        print_info(f"Duration: {duration2:.4f}s")
        
        if metrics2['cache_hits'] > 0 and response1 == response2:
            speedup = duration1 / duration2 if duration2 > 0 else 0
            print_success(f"\n🎉 Gateway working perfectly!")
            print_success(f"Cache speedup: {speedup:.0f}x")
            print_success(f"Cache hit rate: {metrics2['cache_hit_rate']}%")
            return True
        else:
            print_error("Gateway not using cache properly")
            return False
            
    except Exception as e:
        print_error(f"Gateway test failed: {str(e)}")
        return False


async def test_gateway_health() -> bool:
    """Test 5: Gateway Health Check"""
    print_header("TEST 5: Gateway Health Check")
    
    try:
        health = await llm_gateway.get_health()
        
        print_info(f"Status: {health['status']}")
        print_info(f"Cache enabled: {health['cache']['enabled']}")
        print_info(f"Model: {health['client']['model']}")
        
        if health['status'] == 'healthy':
            print_success("Gateway health check passed!")
            return True
        else:
            print_error("Gateway health check failed")
            return False
            
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all validation tests"""
    print(f"\n{Colors.BOLD}🚀 InterviewMe LLM Infrastructure Validation{Colors.END}")
    print(f"{Colors.BOLD}Testing Layers 1-3 (Client, Cache, Gateway){Colors.END}")
    
    results = {}
    
    # Run tests
    results['redis'] = await test_redis_connection()
    
    if results['redis']:
        results['client'] = await test_llm_client()
        results['cache'] = await test_llm_cache()
        results['gateway'] = await test_llm_gateway()
        results['health'] = await test_gateway_health()
    else:
        print_error("\nSkipping other tests - Redis not available")
        results['client'] = False
        results['cache'] = False
        results['gateway'] = False
        results['health'] = False
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        color = Colors.GREEN if passed_test else Colors.RED
        print(f"{color}{status}{Colors.END} - {test_name.upper()}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Your LLM architecture is ready!{Colors.END}")
        print(f"\n{Colors.YELLOW}Next steps:{Colors.END}")
        print("1. Update your .env with REDIS_ENABLED=True")
        print("2. Integrate LLMGateway into your AI service")
        print("3. Enjoy 100-400x speedup from caching! 🚀")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Check errors above.{Colors.END}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)
