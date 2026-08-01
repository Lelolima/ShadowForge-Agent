"""
Fallback mechanism implementation for ShadowForge Agent.
Provides fallback strategies when primary operations fail.
"""

import asyncio
import functools
import logging
from typing import Callable, Any, Optional, TypeVar, Union, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F')


class FallbackTrigger(Enum):
    """Conditions that trigger fallback execution."""
    ALWAYS = "always"                    # Always execute fallback
    ON_EXCEPTION = "on_exception"        # Execute fallback on exception
    ON_TIMEOUT = "on_timeout"            # Execute fallback on timeout
    ON_RESULT = "on_result"              # Execute fallback based on result


@dataclass
class FallbackConfig:
    """Configuration for fallback mechanism."""
    trigger: FallbackTrigger = FallbackTrigger.ON_EXCEPTION
    fallback_func: Optional[Callable[..., T]] = None
    fallback_args: tuple = field(default_factory=tuple)
    fallback_kwargs: dict = field(default_factory=dict)
    exception_types: tuple = (Exception,)  # Exception types that trigger fallback
    result_condition: Optional[Callable[[Any], bool]] = None  # Condition for ON_RESULT
    timeout: Optional[float] = None        # Timeout for primary operation
    name: str = "fallback"                 # Name for logging/monitoring


class FallbackError(Exception):
    """Exception raised when both primary and fallback operations fail."""

    def __init__(
        self,
        message: str,
        primary_exception: Optional[Exception] = None,
        fallback_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.primary_exception = primary_exception
        self.fallback_exception = fallback_exception


class Fallback:
    """
    Fallback mechanism implementation.

    Provides graceful degradation when primary operations fail by executing
    a fallback function.
    """

    def __init__(self, config: FallbackConfig):
        if config.fallback_func is None:
            raise ValueError("fallback_func must be provided in FallbackConfig")
        self.config = config

    async def execute_async(
        self,
        primary_func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute primary function with fallback to secondary function.

        Args:
            primary_func: Primary async function to execute
            *args: Positional arguments for the primary function
            **kwargs: Keyword arguments for the primary function

        Returns:
            Result from either primary or fallback function

        Raises:
            FallbackError: If both primary and fallback functions fail
        """
        primary_exception = None
        fallback_exception = None

        # Handle ALWAYS trigger first - bypass primary execution entirely
        if self.config.trigger == FallbackTrigger.ALWAYS:
            return await self._execute_fallback()

        try:
            # Execute primary function
            if self.config.timeout:
                result = await asyncio.wait_for(
                    primary_func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                result = await primary_func(*args, **kwargs)

            # Check if we should use fallback based on result
            if self._should_fallback_on_result(result):
                logger.info(
                    f"Fallback triggered for '{self.config.name}' based on result"
                )
                return await self._execute_fallback()

            # Success - return result
            return result

        except asyncio.TimeoutError as e:
            primary_exception = e
            if self.config.trigger in [
                FallbackTrigger.ON_TIMEOUT,
                FallbackTrigger.ALWAYS
            ] or (self.config.trigger == FallbackTrigger.ON_EXCEPTION and
                  isinstance(e, self.config.exception_types)):
                return await self._execute_fallback_with_tracking(
                    primary_exception, fallback_exception
                )
            else:
                raise

        except self.config.exception_types as e:
            primary_exception = e
            if self.config.trigger in [
                FallbackTrigger.ON_EXCEPTION,
                FallbackTrigger.ALWAYS
            ]:
                return await self._execute_fallback_with_tracking(
                    primary_exception, fallback_exception
                )
            else:
                raise

        except Exception as e:
            # Non-matching exception
            logger.debug(
                f"Non-matching exception in fallback '{self.config.name}': {e}"
            )
            raise

    def execute_sync(
        self,
        primary_func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute primary function with fallback to secondary function.

        Args:
            primary_func: Primary function to execute
            *args: Positional arguments for the primary function
            **kwargs: Keyword arguments for the primary function

        Returns:
            Result from either primary or fallback function

        Raises:
            FallbackError: If both primary and fallback functions fail
        """
        primary_exception = None
        fallback_exception = None

        # Handle ALWAYS trigger first - bypass primary execution entirely
        if self.config.trigger == FallbackTrigger.ALWAYS:
            return self._execute_fallback_sync()

        try:
            # Execute primary function
            # Note: Timeout enforcement for sync functions is limited
            result = primary_func(*args, **kwargs)

            # Check if we should use fallback based on result
            if self._should_fallback_on_result(result):
                logger.info(
                    f"Fallback triggered for '{self.config.name}' based on result"
                )
                return self._execute_fallback_sync()

            # Success - return result
            return result

        except self.config.exception_types as e:
            primary_exception = e
            if self.config.trigger in [
                FallbackTrigger.ON_EXCEPTION,
                FallbackTrigger.ALWAYS
            ]:
                return self._execute_fallback_sync_with_tracking(
                    primary_exception, fallback_exception
                )
            else:
                raise

        except Exception as e:
            # Non-matching exception
            logger.debug(
                f"Non-matching exception in fallback '{self.config.name}': {e}"
            )
            raise

    async def _execute_fallback(self) -> any:
        """Execute fallback function asynchronously."""
        try:
            if asyncio.iscoroutinefunction(self.config.fallback_func):
                if self.config.timeout:
                    return await asyncio.wait_for(
                        self.config.fallback_func(
                            *self.config.fallback_args,
                            **self.config.fallback_kwargs
                        ),
                        timeout=self.config.timeout
                    )
                else:
                    return await self.config.fallback_func(
                        *self.config.fallback_args,
                        **self.config.fallback_kwargs
                    )
            else:
                # Fallback is sync function
                if self.config.timeout:
                    # For sync functions with timeout, we run in thread pool
                    loop = asyncio.get_event_loop()
                    return await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self.config.fallback_func(
                                *self.config.fallback_args,
                                **self.config.fallback_kwargs
                            )
                        ),
                        timeout=self.config.timeout
                    )
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None,
                        lambda: self.config.fallback_func(
                            *self.config.fallback_args,
                            **self.config.fallback_kwargs
                        )
                    )
        except Exception as e:
            fallback_exception = e
            raise e

    def _execute_fallback_sync(self) -> any:
        """Execute fallback function synchronously."""
        try:
            return self.config.fallback_func(
                *self.config.fallback_args,
                **self.config.fallback_kwargs
            )
        except Exception as e:
            fallback_exception = e
            raise e

    async def _execute_fallback_with_tracking(
        self,
        primary_exception: Exception,
        fallback_exception: Optional[Exception]
    ) -> any:
        """Execute fallback and track exceptions."""
        try:
            result = await self._execute_fallback()
            return result
        except Exception as e:
            fallback_exception = e
            raise FallbackError(
                f"Both primary and fallback functions failed for '{self.config.name}'",
                primary_exception,
                fallback_exception
            )

    def _execute_fallback_sync_with_tracking(
        self,
        primary_exception: Exception,
        fallback_exception: Optional[Exception]
    ) -> any:
        """Execute fallback synchronously and track exceptions."""
        try:
            result = self._execute_fallback_sync()
            return result
        except Exception as e:
            fallback_exception = e
            raise FallbackError(
                f"Both primary and fallback functions failed for '{self.config.name}'",
                primary_exception,
                fallback_exception
            )

    def _should_fallback_on_result(self, result: any) -> bool:
        """Check if fallback should be triggered based on result."""
        if (
            self.config.trigger == FallbackTrigger.ON_RESULT and
            self.config.result_condition is not None
        ):
            return self.config.result_condition(result)
        return False


def fallback(
    fallback_func: Callable[..., T],
    *fallback_args,
    **fallback_kwargs
) -> Callable:
    """
    Decorator for applying fallback logic to functions.

    Args:
        fallback_func: Function to call when primary function fails
        *fallback_args: Arguments to pass to fallback function
        **fallback_kwargs: Keyword arguments to pass to fallback function

    Returns:
        Decorator function
    """
    def decorator(
        trigger: FallbackTrigger = FallbackTrigger.ON_EXCEPTION,
        exception_types: tuple = (Exception,),
        result_condition: Optional[Callable[[Any], bool]] = None,
        timeout: Optional[float] = None,
        name: str = "fallback"
    ) -> Callable:
        config = FallbackConfig(
            trigger=trigger,
            fallback_func=fallback_func,
            fallback_args=fallback_args,
            fallback_kwargs=fallback_kwargs,
            exception_types=exception_types,
            result_condition=result_condition,
            timeout=timeout,
            name=name
        )
        fallback_handler = Fallback(config)

        def decorator_wrapper(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                return fallback_handler.execute_sync(func, *args, **kwargs)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                return await fallback_handler.execute_async(func, *args, **kwargs)

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator_wrapper

    return decorator