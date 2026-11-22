"""
Resilience patterns for ShadowForge Agent.
Provides circuit breaker, retry, fallback, and chaos engineering patterns.
"""

from .chaos import (
    ChaosError,
    ChaosExperiment,
    ChaosExperimentConfig,
    ChaosState,
    ChaosType,
    chaos_experiment,
    exception_chaos,
    latency_chaos,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerState,
)
from .fallback import Fallback, FallbackConfig, FallbackError, FallbackTrigger
from .retry import (
    BackoffStrategy,
    RetryConfig,
    RetryError,
    RetryManager,
    retry,
    retry_exponential,
    retry_on_failure,
)

# For backward compatibility and ease of import
__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreakerError",

    # Retry
    "RetryManager",
    "RetryConfig",
    "BackoffStrategy",
    "RetryError",
    "retry",
    "retry_on_failure",
    "retry_exponential",

    # Fallback
    "Fallback",
    "FallbackConfig",
    "FallbackTrigger",
    "FallbackError",

    # Chaos Engineering
    "ChaosExperiment",
    "ChaosExperimentConfig",
    "ChaosType",
    "ChaosState",
    "ChaosError",
    "chaos_experiment",
    "latency_chaos",
    "exception_chaos",
]
