import json
import logging
import time
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from .client import llm_client
from app.core.cache import get_llm_cache
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


@dataclass
class GatewayMetrics:
    """Metrics for monitoring gateway performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    total_latency_ms: float = 0.0
    cache_latency_ms: float = 0.0
    api_latency_ms: float = 0.0
    errors: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests
    
    @property
    def avg_cache_latency_ms(self) -> float:
        """Calculate average cache latency."""
        if self.cache_hits == 0:
            return 0.0
        return self.cache_latency_ms / self.cache_hits
    
    @property
    def avg_api_latency_ms(self) -> float:
        """Calculate average API latency."""
        if self.api_calls == 0:
            return 0.0
        return self.api_latency_ms / self.api_calls
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hit_rate, 2),
            "api_calls": self.api_calls,
            "errors": self.errors,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "avg_cache_latency_ms": round(self.avg_cache_latency_ms, 2),
            "avg_api_latency_ms": round(self.avg_api_latency_ms, 2)
        }


class LLMGateway:
    """
    Gateway layer that orchestrates LLM Client and Cache.
    
    Features:
    - Automatic cache checking (transparent to caller)
    - Metrics tracking (hits, misses, latency)
    - Batch processing support
    - Cache warming capabilities
    - Unified error handling
    """
    
    def __init__(self):
        """Initialize the gateway."""
        self.metrics = GatewayMetrics()
        logger.info("LLM Gateway initialized")
    
    async def completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> str:
        """
        Get text completion with automatic caching.
        
        This is the main method - it handles cache checking and API calls automatically.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens setting
            use_cache: Whether to use cache (default: True)
            cache_ttl: Custom TTL for this request (optional)
            
        Returns:
            Completion text
            
        Raises:
            AIServiceError: If both cache and API fail
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            cache = get_llm_cache()
            
            # Step 1: Try cache first (if enabled)
            if use_cache and cache.redis.enabled:
                cache_start = time.time()
                cached = await cache.get(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=llm_client.model
                )
                cache_elapsed = (time.time() - cache_start) * 1000
                
                if cached:
                    # Cache HIT
                    self.metrics.cache_hits += 1
                    self.metrics.cache_latency_ms += cache_elapsed
                    total_elapsed = (time.time() - start_time) * 1000
                    self.metrics.total_latency_ms += total_elapsed
                    
                    logger.info(f"Gateway: Cache HIT ({cache_elapsed:.1f}ms)")
                    return cached
                
                # Cache MISS
                self.metrics.cache_misses += 1
                logger.debug(f"Gateway: Cache MISS ({cache_elapsed:.1f}ms)")
            
            # Step 2: Call API
            api_start = time.time()
            response = await llm_client.chat_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            api_elapsed = (time.time() - api_start) * 1000
            
            self.metrics.api_calls += 1
            self.metrics.api_latency_ms += api_elapsed
            
            logger.info(f"Gateway: API call completed ({api_elapsed:.1f}ms)")
            
            # Step 3: Cache the response (if enabled)
            if use_cache and cache.redis.enabled:
                await cache.set(
                    prompt=prompt,
                    response=response,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=llm_client.model,
                    ttl=cache_ttl
                )
            
            # Update metrics
            total_elapsed = (time.time() - start_time) * 1000
            self.metrics.total_latency_ms += total_elapsed
            
            return response
            
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Gateway completion error: {str(e)}")
            raise AIServiceError(f"Gateway completion failed: {str(e)}")
    
    async def completion_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get JSON completion with automatic caching.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens setting
            use_cache: Whether to use cache (default: True)
            cache_ttl: Custom TTL for this request (optional)
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            AIServiceError: If both cache and API fail, or JSON parsing fails
        """
        # Get text response (with caching)
        content = await self.completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            use_cache=use_cache,
            cache_ttl=cache_ttl
        )
        
        # Parse JSON
        try:
            return llm_client._parse_json_response(content)
        except json.JSONDecodeError as e:
            logger.error(f"Gateway JSON parse error: {content[:200]}")
            raise AIServiceError(f"Invalid JSON response: {str(e)}")
    
    async def batch_completion(
        self,
        requests: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> List[str]:
        """
        Process multiple completion requests efficiently.
        
        Args:
            requests: List of request dicts with keys: prompt, system_prompt, temperature, max_tokens
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of completion texts in same order as requests
            
        Example:
            requests = [
                {"prompt": "What is Python?"},
                {"prompt": "What is JavaScript?", "temperature": 0.5},
                {"prompt": "What is Rust?"}
            ]
            responses = await gateway.batch_completion(requests)
        """
        import asyncio
        
        tasks = []
        for req in requests:
            task = self.completion(
                prompt=req.get("prompt"),
                system_prompt=req.get("system_prompt"),
                temperature=req.get("temperature"),
                max_tokens=req.get("max_tokens"),
                use_cache=use_cache,
                cache_ttl=req.get("cache_ttl")
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error strings
        responses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch request failed: {str(result)}")
                responses.append(f"ERROR: {str(result)}")
            else:
                responses.append(result)
        
        return responses
    
    async def warm_cache(
        self,
        prompts: List[Dict[str, Any]],
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pre-populate cache with common queries.
        
        Useful for:
        - Warming cache after deployment
        - Pre-caching common job descriptions
        - Preparing for high-traffic periods
        
        Args:
            prompts: List of prompt dicts to cache
            cache_ttl: Custom TTL for cached items
            
        Returns:
            Dictionary with warming results
            
        Example:
            prompts = [
                {"prompt": "Analyze CV for Python Developer role"},
                {"prompt": "Analyze CV for Frontend Developer role"}
            ]
            result = await gateway.warm_cache(prompts)
        """
        logger.info(f"Cache warming started: {len(prompts)} prompts")
        start_time = time.time()
        
        # Process all prompts
        responses = await self.batch_completion(prompts, use_cache=True)
        
        # Count successes and failures
        successes = sum(1 for r in responses if not r.startswith("ERROR:"))
        failures = len(responses) - successes
        
        elapsed = time.time() - start_time
        
        result = {
            "total": len(prompts),
            "successes": successes,
            "failures": failures,
            "elapsed_seconds": round(elapsed, 2)
        }
        
        logger.info(f"Cache warming completed: {result}")
        return result
    
    async def invalidate_cache(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens setting
            
        Returns:
            True if invalidated successfully
        """
        cache = get_llm_cache()
        return await cache.delete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=llm_client.model
        )
    
    async def clear_all_cache(self) -> int:
        """
        Clear all cached responses.
        
        Returns:
            Number of keys deleted
        """
        cache = get_llm_cache()
        return await cache.clear_all()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get gateway performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        return self.metrics.to_dict()
    
    def reset_metrics(self):
        """Reset all metrics to zero."""
        self.metrics = GatewayMetrics()
        logger.info("Gateway metrics reset")
    
    async def get_health(self) -> Dict[str, Any]:
        """
        Get health status of gateway and dependencies.
        
        Returns:
            Dictionary with health information
        """
        cache = get_llm_cache()
        cache_stats = await cache.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "cache": cache_stats,
            "client": {
                "model": llm_client.model,
                "max_tokens": llm_client.default_max_tokens,
                "temperature": llm_client.default_temperature
            },
            "metrics": self.get_metrics()
        }
    
    async def completion_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Stream completion with automatic caching.
        
        Note: Streaming responses are NOT cached during generation,
        but the final complete response IS cached for future requests.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens
            use_cache: Check cache before streaming
            cache_ttl: Custom TTL for caching final response
            
        Yields:
            Text chunks as they arrive
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            cache = get_llm_cache()
            
            # Step 1: Check cache first
            if use_cache and cache.redis.enabled:
                cache_start = time.time()
                cached = await cache.get(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=llm_client.model
                )
                cache_elapsed = (time.time() - cache_start) * 1000
                
                if cached:
                    # Cache HIT - yield entire cached response at once
                    self.metrics.cache_hits += 1
                    self.metrics.cache_latency_ms += cache_elapsed
                    total_elapsed = (time.time() - start_time) * 1000
                    self.metrics.total_latency_ms += total_elapsed
                    
                    logger.info(f"Gateway Stream: Cache HIT ({cache_elapsed:.1f}ms)")
                    yield cached
                    return
                
                # Cache MISS
                self.metrics.cache_misses += 1
                logger.debug(f"Gateway Stream: Cache MISS ({cache_elapsed:.1f}ms)")
            
            # Step 2: Stream from API
            api_start = time.time()
            accumulated_response = ""
            
            async for chunk in llm_client.chat_completion_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                accumulated_response += chunk
                yield chunk
            
            api_elapsed = (time.time() - api_start) * 1000
            self.metrics.api_calls += 1
            self.metrics.api_latency_ms += api_elapsed
            
            logger.info(f"Gateway Stream: API completed ({api_elapsed:.1f}ms)")
            
            # Step 3: Cache the complete response
            if use_cache and cache.redis.enabled and accumulated_response:
                await cache.set(
                    prompt=prompt,
                    response=accumulated_response,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=llm_client.model,
                    ttl=cache_ttl
                )
            
            # Update metrics
            total_elapsed = (time.time() - start_time) * 1000
            self.metrics.total_latency_ms += total_elapsed
            
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Gateway stream error: {str(e)}")
            raise AIServiceError(f"Gateway stream failed: {str(e)}")


# Singleton instance
llm_gateway = LLMGateway()
