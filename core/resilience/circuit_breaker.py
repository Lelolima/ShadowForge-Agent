"""
Circuit Breaker pattern implementation for ShadowForge Agent.
Provides fault tolerance for external service calls by preventing cascading failures.
"""

import asyncio
import time
import functools
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, TypeVar, Generic, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """States of the circuit breaker."""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Circuit is open, requests blocked
    HALF_OPEN = "half_open" # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker."""
    failure_threshold: int = 5              # Number of failures before opening
    recovery_timeout: float = 60.0          # Seconds before trying half-open
    expected_exception: type = Exception    # Exception type that counts as failure
    success_threshold: int = 3              # Successes needed to close from half-open
    timeout: Optional[float] = None         # Request timeout in seconds
    name: str = "circuit_breaker"           # Name for logging/monitoring


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation for async and sync functions.

    Prevents cascading failures by temporarily stopping requests to a failing service.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()  # For thread-safe state transitions

    @property
    def state(self) -> CircuitBreakerState:
        """Current state of the circuit breaker."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Current failure count."""
        return self._failure_count

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute (sync or async)
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Returns:
            result
        Raises:
            CircuitBreaker
        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by the function
        """
        if self._state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.config.name}' is OPEN. "
                    f"Too many failures. Try again in {self._time_until_retry():.1f}s."
                )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await self._call_async(func, *args, **kwargs)
            else:
                result = self._call_sync(func, *args, **kwargs)

            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            # Non-expected exceptions don't count as failures
            logger.debug(f"Non-expected exception in circuit breaker: {e}")
            raise e

    async def _call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Call async function with optional timeout."""
        if self.config.timeout:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
        else:
            return await func(*args, **kwargs)

    def _call_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Call sync function with optional timeout."""
        if self.config.timeout:
            # For sync functions, we can't easily enforce timeout without threading
            # In practice, you might want to use concurrent.futures or similar
            return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self._last_failure_time is not None and
            time.time() - self._last_failure_time >= self.config.recovery_timeout
        )

    def _time_until_retry(self) -> float:
        """Calculate time until retry is allowed."""
        if self._last_failure_time is None:
            return 0

        elapsed = time.time() - self._last_failure_time
        return max(0, self.config.recovery_timeout - elapsed)

    def _set_half_open(self) -> None:
        """Set circuit breaker to half-open state."""
        self._state = CircuitBreakerState.HALF_OPEN
        self._success_count = 0
        logger.info(f"Circuit breaker '{self.config.name}' moved to HALF_OPEN")

    def _set_open(self) -> None:
        """Set circuit breaker to open state."""
        self._state = CircuitBreakerState.OPEN
        self._last_failure_time = time.time()
        logger.warning(f"Circuit breaker '{self.config.name}' opened after {self._failure_count} failures")

    def _set_closed(self) -> None:
        """Set circuit breaker to closed state."""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        logger.info(f"Circuit breaker '{self.config.name}' closed")

    def _on_success(self) -> None:
        """Handle successful execution."""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._set_closed()
        elif self._state == CircuitBreakerState.CLOSED:
            # Reset failure count on success in closed state
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed execution."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open -> go back to open
            self._set_open()
        elif self._state == CircuitBreakerState.CLOSED:
            # Check if we should open the circuit
            if self._failure_count >= self.config.failure_threshold:
                self._set_open()


def circuit_breaker(config: Optional[CircuitBreakerConfig] = None) -> Callable:
    """
    Decorator for applying circuit breaker pattern to functions.

    Args:
        config: Circuit breaker configuration. If None, uses default config.

    Returns:
        Decorated function with circuit breaker protection
    """
    if config is None:
        config = CircuitBreakerConfig()

    breaker = CircuitBreaker(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return breaker.call(func, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await breaker.call(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator