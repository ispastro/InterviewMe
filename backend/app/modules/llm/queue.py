import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from celery import Celery, Task
from celery.result import AsyncResult
from kombu import Queue, Exchange

from .gateway import llm_gateway
from app.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    STARTED = "started"
    RETRY = "retry"
    SUCCESS = "success"
    FAILURE = "failure"
    REVOKED = "revoked"


@dataclass
class TaskInfo:
    """Information about a queued task."""
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: int = 0
    retries: int = 0
    max_retries: int = 3
    
    @property
    def is_complete(self) -> bool:
        """Check if task is complete (success or failure)."""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "is_complete": self.is_complete,
            "duration_seconds": self.duration_seconds
        }


# Celery app configuration
def create_celery_app() -> Celery:
    """
    Create and configure Celery application.
    
    Returns:
        Configured Celery app
    """
    # Use Redis as broker and backend
    broker_url = settings.REDIS_URL
    backend_url = settings.REDIS_URL
    
    app = Celery(
        "llm_tasks",
        broker=broker_url,
        backend=backend_url
    )
    
    # Configure Celery
    app.conf.update(
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Result backend settings
        result_expires=3600,  # Results expire after 1 hour
        result_backend_transport_options={
            "master_name": "mymaster",
            "visibility_timeout": 3600,
        },
        
        # Task execution settings
        task_acks_late=True,  # Acknowledge after task completes
        task_reject_on_worker_lost=True,
        task_track_started=True,
        
        # Retry settings
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,
        
        # Rate limiting
        task_default_rate_limit="10/m",  # 10 tasks per minute default
        
        # Priority queues
        task_routes={
            "llm_tasks.completion": {"queue": "llm_normal"},
            "llm_tasks.completion_json": {"queue": "llm_normal"},
            "llm_tasks.batch_completion": {"queue": "llm_batch"},
        },
        
        # Define queues with priorities
        task_queues=(
            Queue("llm_critical", Exchange("llm"), routing_key="llm.critical", priority=10),
            Queue("llm_high", Exchange("llm"), routing_key="llm.high", priority=7),
            Queue("llm_normal", Exchange("llm"), routing_key="llm.normal", priority=5),
            Queue("llm_low", Exchange("llm"), routing_key="llm.low", priority=3),
            Queue("llm_batch", Exchange("llm"), routing_key="llm.batch", priority=1),
        ),
        
        # Worker settings
        worker_prefetch_multiplier=1,  # One task at a time
        worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    )
    
    return app


# Create Celery app instance
celery_app = create_celery_app()


# Task definitions
@celery_app.task(
    bind=True,
    name="llm_tasks.completion",
    max_retries=3,
    default_retry_delay=60
)
def completion_task(
    self: Task,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_cache: bool = True,
    cache_ttl: Optional[int] = None
) -> str:
    """
    Async task for text completion.
    
    Args:
        self: Celery task instance
        prompt: The user prompt
        system_prompt: Optional system prompt
        temperature: Temperature setting
        max_tokens: Max tokens setting
        use_cache: Whether to use cache
        cache_ttl: Custom cache TTL
        
    Returns:
        Completion text
    """
    try:
        # Update task state to STARTED
        self.update_state(state="STARTED", meta={"progress": 0})
        
        # Import here to avoid circular imports
        import asyncio
        
        # Run async gateway method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            llm_gateway.completion(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_cache=use_cache,
                cache_ttl=cache_ttl
            )
        )
        
        # Update progress
        self.update_state(state="SUCCESS", meta={"progress": 100})
        
        return result
        
    except Exception as e:
        logger.error(f"Completion task failed: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    bind=True,
    name="llm_tasks.completion_json",
    max_retries=3,
    default_retry_delay=60
)
def completion_json_task(
    self: Task,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_cache: bool = True,
    cache_ttl: Optional[int] = None
) -> Dict[str, Any]:
    """
    Async task for JSON completion.
    
    Args:
        self: Celery task instance
        prompt: The user prompt
        system_prompt: Optional system prompt
        temperature: Temperature setting
        max_tokens: Max tokens setting
        use_cache: Whether to use cache
        cache_ttl: Custom cache TTL
        
    Returns:
        Parsed JSON dictionary
    """
    try:
        self.update_state(state="STARTED", meta={"progress": 0})
        
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            llm_gateway.completion_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_cache=use_cache,
                cache_ttl=cache_ttl
            )
        )
        
        self.update_state(state="SUCCESS", meta={"progress": 100})
        
        return result
        
    except Exception as e:
        logger.error(f"JSON completion task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    bind=True,
    name="llm_tasks.batch_completion",
    max_retries=2,
    default_retry_delay=120
)
def batch_completion_task(
    self: Task,
    requests: List[Dict[str, Any]],
    use_cache: bool = True
) -> List[str]:
    """
    Async task for batch completion.
    
    Args:
        self: Celery task instance
        requests: List of request dictionaries
        use_cache: Whether to use cache
        
    Returns:
        List of completion texts
    """
    try:
        self.update_state(state="STARTED", meta={"progress": 0, "total": len(requests)})
        
        import asyncio
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            llm_gateway.batch_completion(requests, use_cache=use_cache)
        )
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "total": len(requests)})
        
        return results
        
    except Exception as e:
        logger.error(f"Batch completion task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


class LLMQueue:
    """
    Queue layer for async LLM task processing.
    
    Features:
    - Async task submission with Celery
    - Priority queues (critical, high, normal, low, batch)
    - Task status tracking
    - Automatic retries
    - Rate limit management
    """
    
    def __init__(self):
        """Initialize the queue."""
        self.celery_app = celery_app
        logger.info("LLM Queue initialized")
    
    def _get_queue_name(self, priority: TaskPriority) -> str:
        """Get queue name from priority."""
        queue_map = {
            TaskPriority.CRITICAL: "llm_critical",
            TaskPriority.HIGH: "llm_high",
            TaskPriority.NORMAL: "llm_normal",
            TaskPriority.LOW: "llm_low"
        }
        return queue_map.get(priority, "llm_normal")
    
    async def submit_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        countdown: int = 0
    ) -> str:
        """
        Submit text completion task to queue.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens setting
            use_cache: Whether to use cache
            cache_ttl: Custom cache TTL
            priority: Task priority
            countdown: Delay before execution (seconds)
            
        Returns:
            Task ID for tracking
        """
        queue_name = self._get_queue_name(priority)
        
        task = completion_task.apply_async(
            kwargs={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "use_cache": use_cache,
                "cache_ttl": cache_ttl
            },
            queue=queue_name,
            countdown=countdown
        )
        
        logger.info(f"Submitted completion task: {task.id} (queue={queue_name}, priority={priority.value})")
        return task.id
    
    async def submit_completion_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        countdown: int = 0
    ) -> str:
        """
        Submit JSON completion task to queue.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max tokens setting
            use_cache: Whether to use cache
            cache_ttl: Custom cache TTL
            priority: Task priority
            countdown: Delay before execution (seconds)
            
        Returns:
            Task ID for tracking
        """
        queue_name = self._get_queue_name(priority)
        
        task = completion_json_task.apply_async(
            kwargs={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "use_cache": use_cache,
                "cache_ttl": cache_ttl
            },
            queue=queue_name,
            countdown=countdown
        )
        
        logger.info(f"Submitted JSON completion task: {task.id} (queue={queue_name}, priority={priority.value})")
        return task.id
    
    async def submit_batch_completion(
        self,
        requests: List[Dict[str, Any]],
        use_cache: bool = True,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Submit batch completion task to queue.
        
        Args:
            requests: List of request dictionaries
            use_cache: Whether to use cache
            priority: Task priority
            
        Returns:
            Task ID for tracking
        """
        # Batch tasks always go to batch queue
        task = batch_completion_task.apply_async(
            kwargs={
                "requests": requests,
                "use_cache": use_cache
            },
            queue="llm_batch"
        )
        
        logger.info(f"Submitted batch completion task: {task.id} (items={len(requests)})")
        return task.id
    
    async def get_task_status(self, task_id: str) -> TaskInfo:
        """
        Get status of a queued task.
        
        Args:
            task_id: Task ID
            
        Returns:
            TaskInfo with current status
        """
        result = AsyncResult(task_id, app=self.celery_app)
        
        # Map Celery states to our TaskStatus
        status_map = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.STARTED,
            "RETRY": TaskStatus.RETRY,
            "SUCCESS": TaskStatus.SUCCESS,
            "FAILURE": TaskStatus.FAILURE,
            "REVOKED": TaskStatus.REVOKED
        }
        
        status = status_map.get(result.state, TaskStatus.PENDING)
        
        # Extract metadata
        meta = result.info if isinstance(result.info, dict) else {}
        
        task_info = TaskInfo(
            task_id=task_id,
            status=status,
            created_at=datetime.utcnow(),  # Celery doesn't track creation time
            progress=meta.get("progress", 0),
            retries=meta.get("retries", 0)
        )
        
        if status == TaskStatus.SUCCESS:
            task_info.result = result.result
            task_info.completed_at = datetime.utcnow()
            task_info.progress = 100
        elif status == TaskStatus.FAILURE:
            task_info.error = str(result.info)
            task_info.completed_at = datetime.utcnow()
        
        return task_info
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get result of a completed task (blocks until ready).
        
        Args:
            task_id: Task ID
            timeout: Max seconds to wait (None = wait forever)
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        result = AsyncResult(task_id, app=self.celery_app)
        return result.get(timeout=timeout)
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cancelled successfully
        """
        result = AsyncResult(task_id, app=self.celery_app)
        result.revoke(terminate=True)
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        inspect = self.celery_app.control.inspect()
        
        # Get active tasks
        active = inspect.active() or {}
        active_count = sum(len(tasks) for tasks in active.values())
        
        # Get scheduled tasks
        scheduled = inspect.scheduled() or {}
        scheduled_count = sum(len(tasks) for tasks in scheduled.values())
        
        # Get reserved tasks
        reserved = inspect.reserved() or {}
        reserved_count = sum(len(tasks) for tasks in reserved.values())
        
        # Get registered tasks
        registered = inspect.registered() or {}
        
        # Get worker stats
        stats = inspect.stats() or {}
        worker_count = len(stats)
        
        return {
            "workers": worker_count,
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
            "total_pending": active_count + scheduled_count + reserved_count,
            "registered_tasks": list(registered.values())[0] if registered else []
        }


# Singleton instance
llm_queue = LLMQueue()
