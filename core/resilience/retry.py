"""
Retry mechanism implementation for ShadowForge Agent.
Provides retry mechanisms with exponential backoff, jitter, and various backoff strategies.
"""

import asyncio
import random
import time
import functools
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, TypeVar, Generic, Union, Tuple, List, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BackoffStrategy(Enum):
    """Backoff strategies for retry mechanisms."""
    FIXED = "fixed"           # Fixed delay between retries
    LINEAR = "linear"         # Linear increase in delay
    EXPONENTIAL = "exponential" # Exponential increase in delay
    EXPONENTIAL_JITTER = "exponential_jitter" # Exponential with jitter


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3                 # Maximum number of attempts
    base_delay: float = 1.0               # Base delay in seconds
    max_delay: float = 60.0               # Maximum delay in seconds
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    retry_exceptions: tuple = (Exception,)  # Exception types to retry on
    jitter_range: float = 0.1             # Jitter range (0.0 to 1.0)
    timeout: Optional[float] = None         # Timeout per attempt in seconds
    name: str = "retry"                     # Name for logging/monitoring


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


class RetryManager:
    """
    Retry mechanism implementation with various backoff strategies.

    Supports both synchronous and asynchronous functions with configurable
    retry policies, backoff strategies, and jitter.
    """

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute an async function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            RetryError: If all attempts are exhausted
            Exception: Last exception if not in retry_exceptions
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await func(*args, **kwargs)

                # Success - return result
                if attempt > 0:
                    logger.info(
                        f"Retry successful for '{self.config.name}' "
                        f"after {attempt + 1} attempts"
                    )
                return result

            except self.config.retry_exceptions as e:
                last_exception = e

                # If this was the last attempt, don't retry
                if attempt == self.config.max_attempts - 1:
                    break

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"Attempt {attempt + 1} failed for '{self.config.name}': {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )

                await asyncio.sleep(delay)

            except Exception as e:
                # Non-retryable exception - don't retry
                logger.error(
                    f"Non-retryable exception in '{self.config.name}': {str(e)}"
                )
                raise e

        # All attempts exhausted
        error_msg = (
            f"All {self.config.max_attempts} attempts failed for '{self.config.name}'"
        )
        raise RetryError(error_msg, last_exception)

    def execute_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a synchronous function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            RetryError: If all attempts are exhausted
            Exception: Last exception if not in retry_exceptions
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if self.config.timeout:
                    # Note: For sync functions, timeout enforcement is limited
                    # In a production environment, you might use threading or signals
                    result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - return result
                if attempt > 0:
                    logger.info(
                        f"Retry successful for '{self.config.name}' "
                        f"after {attempt + 1} attempts"
                    )
                return result

            except self.config.retry_exceptions as e:
                last_exception = e

                # If this was the last attempt, don't retry
                if attempt == self.config.max_attempts - 1:
                    break

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"Attempt {attempt + 1} failed for '{self.config.name}': {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )

                time.sleep(delay)

            except Exception as e:
                # Non-retryable exception - don't retry
                logger.error(
                    f"Non-retryable exception in '{self.config.name}': {str(e)}"
                )
                raise e

        # All attempts exhausted
        error_msg = (
            f"All {self.config.max_attempts} attempts failed for '{self.config.name}'"
        )
        raise RetryError(error_msg, last_exception)

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt number.

        Args:
            attempt: Zero-based attempt number

        Returns:
            Delay in seconds
        """
        if attempt < 0:
            return 0

        # Calculate base delay based on strategy
        if self.config.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (2 ** attempt)
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL_JITTER:
            delay = self.config.base_delay * (2 ** attempt)
        else:
            delay = self.config.base_delay

        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)

        # Add jitter if configured
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL_JITTER and self.config.jitter_range > 0:
            jitter = delay * self.config.jitter_range * (2 * random.random() - 1)
            delay += jitter
            # Ensure delay doesn't go negative
            delay = max(0, delay)

        return delay


def retry(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for applying retry logic to functions.

    Args:
        config: Retry configuration. If None, uses default config.

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    retry_manager = RetryManager(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return retry_manager.execute_sync(func, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await retry_manager.execute_async(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience decorators with common configurations
def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER,
    retry_exceptions: tuple = (Exception,),
    timeout: Optional[float] = None
) -> Callable:
    """
    Convenience decorator for retry with common parameters.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_strategy: Backoff strategy to use
        retry_exceptions: Exception types to retry on
        timeout: Timeout per attempt in seconds

    Returns:
        Decorator function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_strategy=backoff_strategy,
        retry_exceptions=retry_exceptions,
        timeout=timeout
    )
    return retry(config)


def retry_exponential(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_exceptions: tuple = (Exception,),
    timeout: Optional[float] = None
) -> Callable:
    """
    Convenience decorator for exponential backoff retry.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        retry_exceptions: Exception types to retry on
        timeout: Timeout per attempt in seconds

    Returns:
        Decorator function
    """
    return retry_on_failure(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
        retry_exceptions=retry_exceptions,
        timeout=timeout
    )