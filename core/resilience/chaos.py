"""
Chaos engineering implementation for ShadowForge Agent.
Provides controlled failure injection for testing system resilience.
"""

import asyncio
import random
import time
import functools
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, TypeVar, Union, List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ChaosType(Enum):
    """Types of chaos experiments."""
    LATENCY = "latency"           # Inject latency
    EXCEPTION = "exception"       # Throw exceptions
    TERMINATE = "terminate"       # Simulate process termination
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Consume resources
    NETWORK_PARTITION = "network_partition"      # Simulate network issues


class ChaosState(Enum):
    """State of chaos experiment."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class ChaosExperimentConfig:
    """Configuration for chaos experiment."""
    chaos_type: ChaosType
    enabled: bool = True
    probability: float = 0.1              # Probability of injecting chaos (0.0 to 1.0)
    duration: Optional[float] = None      # Duration of chaos in seconds
    intensity: float = 0.5                # Intensity of chaos (0.0 to 1.0)
    target_functions: List[str] = field(default_factory=list)  # Function names to target
    exclude_functions: List[str] = field(default_factory=list) # Function names to exclude
    start_time: Optional[datetime] = None # When to start chaos
    end_time: Optional[datetime] = None   # When to stop chaos
    parameters: Dict[str, Any] = field(default_factory=dict)  # Type-specific parameters
    name: str = "chaos_experiment"        # Name for logging/monitoring


class ChaosError(Exception):
    """Exception raised by chaos experiments."""
    pass


class ChaosExperiment:
    """
    Chaos engineering experiment implementation.

    Injects controlled failures into the system to test resilience and
    verify that fallback mechanisms work correctly.
    """

    def __init__(self, config: ChaosExperimentConfig):
        self.config = config
        self._state = ChaosState.STOPPED
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._injection_count = 0
        self._total_calls = 0

    @property
    def state(self) -> ChaosState:
        """Current state of the chaos experiment."""
        return self._state

    @property
    def is_active(self) -> bool:
        """Check if chaos experiment is currently active."""
        if not self.config.enabled:
            return False

        if self._state != ChaosState.RUNNING:
            return False

        now = time.time()
        if self._start_time is not None and now < self._start_time:
            return False

        if self._end_time is not None and now > self._end_time:
            return False

        return True

    def start(self) -> None:
        """Start the chaos experiment."""
        self._state = ChaosState.RUNNING
        self._start_time = time.time()
        if self.config.duration:
            self._end_time = self._start_time + self.config.duration
        logger.info(f"Chaos experiment '{self.config.name}' started")

    def stop(self) -> None:
        """Stop the chaos experiment."""
        self._state = ChaosState.STOPPED
        self._start_time = None
        self._end_time = None
        logger.info(f"Chaos experiment '{self.config.name}' stopped")

    def pause(self) -> None:
        """Pause the chaos experiment."""
        self._state = ChaosState.PAUSED
        logger.info(f"Chaos experiment '{self.config.name}' paused")

    def resume(self) -> None:
        """Resume the chaos experiment."""
        self._state = ChaosState.RUNNING
        logger.info(f"Chaos experiment '{self.config.name}' resumed")

    def should_inject(self, func_name: str) -> bool:
        """
        Determine if chaos should be injected for this function call.

        Args:
            func_name: Name of the function being called

        Returns:
            True if chaos should be injected
        """
        if not self.is_active:
            return False

        self._total_calls += 1

        # Check target functions filter
        if self.config.target_functions:
            if func_name not in self.config.target_functions:
                return False

        # Check exclude functions filter
        if self.config.exclude_functions:
            if func_name in self.config.exclude_functions:
                return False

        # Check probability
        if random.random() > self.config.probability:
            return False

        self._injection_count += 1
        return True

    async def apply_async(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Apply chaos to an async function call.

        Args:
            func: Function to potentially apply chaos to
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call (potentially modified by chaos)

        Raises:
            ChaosError: If chaos experiment fails internally
            Exception: Any exception from the original function or injected chaos
        """
        func_name = getattr(func, '__name__', str(func))

        if not self.should_inject(func_name):
            # No chaos injection - call function normally
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        # Apply chaos based on type
        if self.config.chaos_type == ChaosType.LATENCY:
            return await self._apply_latency_chaos(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.EXCEPTION:
            return await self._apply_exception_chaos(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.TERMINATE:
            return await self._apply_terminate_chaos(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.RESOURCE_EXHAUSTION:
            return await self._apply_resource_exhaustion_chaos(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.NETWORK_PARTITION:
            return await self._apply_network_partition_chaos(func, *args, **kwargs)
        else:
            # Unknown chaos type - fall through to normal execution
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

    def apply_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Apply chaos to a synchronous function call.

        Args:
            func: Function to potentially apply chaos to
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call (potentially modified by chaos)

        Raises:
            ChaosError: If chaos experiment fails internally
            Exception: Any exception from the original function or injected chaos
        """
        func_name = getattr(func, '__name__', str(func))

        if not self.should_inject(func_name):
            # No chaos injection - call function normally
            return func(*args, **kwargs)

        # Apply chaos based on type
        if self.config.chaos_type == ChaosType.LATENCY:
            return self._apply_latency_chaos_sync(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.EXCEPTION:
            return self._apply_exception_chaos_sync(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.TERMINATE:
            return self._apply_terminate_chaos_sync(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.RESOURCE_EXHAUSTION:
            return self._apply_resource_exhaustion_chaos_sync(func, *args, **kwargs)
        elif self.config.chaos_type == ChaosType.NETWORK_PARTITION:
            return self._apply_network_partition_chaos_sync(func, *args, **kwargs)
        else:
            # Unknown chaos type - fall through to normal execution
            return func(*args, **kwargs)

    async def _apply_latency_chaos(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply latency chaos to async function."""
        delay = self._calculate_latency_delay()
        logger.debug(f"Injecting {delay:.3f}s latency chaos")
        await asyncio.sleep(delay)

        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _apply_latency_chaos_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply latency chaos to sync function."""
        delay = self._calculate_latency_delay()
        logger.debug(f"Injecting {delay:.3f}s latency chaos")
        time.sleep(delay)
        return func(*args, **kwargs)

    async def _apply_exception_chaos(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply exception chaos to async function."""
        exception_type = self.config.parameters.get('exception_type', RuntimeError)
        message = self.config.parameters.get('message', 'Chaos engineering: injected exception')

        logger.debug(f"Injecting {exception_type.__name__} chaos: {message}")
        raise exception_type(message)

    def _apply_exception_chaos_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply exception chaos to sync function."""
        exception_type = self.config.parameters.get('exception_type', RuntimeError)
        message = self.config.parameters.get('message', 'Chaos engineering: injected exception')

        logger.debug(f"Injecting {exception_type.__name__} chaos: {message}")
        raise exception_type(message)

    async def _apply_terminate_chaos(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply termination chaos to async function."""
        logger.warning("Injecting termination chaos - simulating process exit")
        # In reality, we don't actually terminate the process
        # Instead we simulate by raising a special exception or delaying significantly
        raise ChaosError("Simulated process termination")

    def _apply_terminate_chaos_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply termination chaos to sync function."""
        logger.warning("Injecting termination chaos - simulating process exit")
        raise ChaosError("Simulated process termination")

    async def _apply_resource_exhaustion_chaos(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply resource exhaustion chaos to async function."""
        # Simulate memory or CPU pressure
        intensity = self.config.intensity
        size = int(1024 * 1024 * 10 * intensity)  # 10MB * intensity

        logger.debug(f"Injecting resource exhaustion chaos: {size} bytes allocation")
        # Allocate memory to simulate pressure
        data = bytearray(size)
        # Touch some memory to ensure allocation
        for i in range(0, len(data), 4096):
            data[i] = 0

        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        finally:
            # Clean up
            del data

    def _apply_resource_exhaustion_chaos_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply resource exhaustion chaos to sync function."""
        # Simulate memory or CPU pressure
        intensity = self.config.intensity
        size = int(1024 * 1024 * 10 * intensity)  # 10MB * intensity

        logger.debug(f"Injecting resource exhaustion chaos: {size} bytes allocation")
        # Allocate memory to simulate pressure
        data = bytearray(size)
        # Touch some memory to ensure allocation
        for i in range(0, len(data), 4096):
            data[i] = 0

        try:
            return func(*args, **kwargs)
        finally:
            # Clean up
            del data

    async def _apply_network_partition_chaos(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply network partition chaos to async function."""
        # Simulate network issues by dropping connections or adding latency
        drop_probability = self.config.parameters.get('drop_probability', 0.3)
        latency_increase = self.config.parameters.get('latency_increase', 2.0)

        if random.random() < drop_probability:
            logger.debug("Injecting network partition chaos: connection drop")
            raise ConnectionError("Simulated network partition: connection dropped")
        else:
            delay = min(latency_increase, 5.0)  # Cap at 5 seconds
            logger.debug(f"Injecting network partition chaos: {delay}s latency")
            await asyncio.sleep(delay)

            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

    def _apply_network_partition_chaos_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Apply network partition chaos to sync function."""
        # Simulate network issues by dropping connections or adding latency
        drop_probability = self.config.parameters.get('drop_probability', 0.3)
        latency_increase = self.config.parameters.get('latency_increase', 2.0)

        if random.random() < drop_probability:
            logger.debug("Injecting network partition chaos: connection drop")
            raise ConnectionError("Simulated network partition: connection dropped")
        else:
            delay = min(latency_increase, 5.0)  # Cap at 5 seconds
            logger.debug(f"Injecting network partition chaos: {delay}s latency")
            time.sleep(delay)
            return func(*args, **kwargs)

    def _calculate_latency_delay(self) -> float:
        """Calculate latency delay based on intensity."""
        base_delay = self.config.parameters.get('base_delay', 0.1)
        max_delay = self.config.parameters.get('max_delay', 5.0)

        # Scale delay by intensity (0.0 to 1.0)
        delay = base_delay + (max_delay - base_delay) * self.config.intensity
        return min(delay, max_delay)

    def get_stats(self) -> dict:
        """Get statistics about the chaos experiment."""
        return {
            'name': self.config.name,
            'state': self.state.value,
            'enabled': self.config.enabled,
            'injection_count': self._injection_count,
            'total_calls': self._total_calls,
            'injection_rate': (
                self._injection_count / max(self._total_calls, 1)
                if self._total_calls > 0 else 0
            ),
            'chaos_type': self.config.chaos_type.value,
            'probability': self.config.probability,
            'intensity': self.config.intensity
        }


def chaos_experiment(config: ChaosExperimentConfig) -> Callable:
    """
    Decorator for applying chaos engineering to functions.

    Args:
        config: Chaos experiment configuration

    Returns:
        Decorator function
    """
    experiment = ChaosExperiment(config)
    # Automatically start the experiment when used as a decorator
    if config.enabled:
        experiment.start()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return experiment.apply_sync(func, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await experiment.apply_async(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience functions for common chaos experiments
def latency_chaos(
    probability: float = 0.1,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    intensity: float = 0.5,
    duration: Optional[float] = None,
    name: str = "latency_chaos"
) -> Callable:
    """
    Convenience decorator for latency chaos experiments.

    Args:
        probability: Probability of injecting latency (0.0 to 1.0)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        intensity: Intensity of chaos (0.0 to 1.0)
        duration: Duration of experiment in seconds
        name: Name for the experiment

    Returns:
        Decorator function
    """
    config = ChaosExperimentConfig(
        chaos_type=ChaosType.LATENCY,
        probability=probability,
        parameters={
            'base_delay': base_delay,
            'max_delay': max_delay
        },
        intensity=intensity,
        duration=duration,
        name=name
    )
    return chaos_experiment(config)


def exception_chaos(
    probability: float = 0.05,
    exception_type: type = RuntimeError,
    message: str = "Chaos engineering: injected exception",
    duration: Optional[float] = None,
    name: str = "exception_chaos"
) -> Callable:
    """
    Convenience decorator for exception chaos experiments.

    Args:
        probability: Probability of injecting exception (0.0 to 1.0)
        exception_type: Type of exception to throw
        message: Exception message
        duration: Duration of experiment in seconds
        name: Name for the experiment

    Returns:
        Decorator function
    """
    config = ChaosExperimentConfig(
        chaos_type=ChaosType.EXCEPTION,
        probability=probability,
        parameters={
            'exception_type': exception_type,
            'message': message
        },
        duration=duration,
        name=name
    )
    return chaos_experiment(config)