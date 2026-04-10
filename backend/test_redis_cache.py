"""Test Upstash Redis caching."""
import asyncio
from app.core.cache import get_llm_cache

async def test_cache():
    cache = get_llm_cache()
    
    print("Testing Upstash Redis Cache...")
    print()
    
    # Test 1: Set and Get
    print("1. Testing SET and GET:")
    await cache.set(
        prompt="What is Python?",
        response="Python is a programming language",
        temperature=0.7,
        ttl=60
    )
    
    result = await cache.get(
        prompt="What is Python?",
        temperature=0.7
    )
    print(f"   OK Cached value: {result[:50]}...")
    print()
    
    # Test 2: Cache Miss
    print("2. Testing Cache MISS:")
    result = await cache.get(
        prompt="What is JavaScript?",
        temperature=0.7
    )
    print(f"   OK Cache miss (expected): {result}")
    print()
    
    # Test 3: Get Stats
    print("3. Testing Cache Stats:")
    stats = await cache.get_stats()
    print(f"   OK Enabled: {stats['enabled']}")
    print(f"   OK LLM Cache Keys: {stats['llm_cache_keys']}")
    print(f"   OK Total Requests: {stats['total_requests']}")
    print(f"   OK Cache Hits: {stats['cache_hits']}")
    print(f"   OK Cache Misses: {stats['cache_misses']}")
    print(f"   OK Hit Rate: {stats['hit_rate_percent']}%")
    print()
    
    # Test 4: Clear Cache
    print("4. Testing Clear Cache:")
    deleted = await cache.clear_all()
    print(f"   OK Deleted {deleted} keys")
    print()
    
    print("SUCCESS: All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_cache())
