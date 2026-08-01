"""
Resilience patterns for ShadowForge Agent.
Provides circuit breaker, retry, fallback, and chaos engineering patterns.
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerError
)

from .retry import (
    RetryManager,
    RetryConfig,
    BackoffStrategy,
    RetryError,
    retry,
    retry_on_failure,
    retry_exponential
)

from .fallback import (
    Fallback,
    FallbackConfig,
    FallbackTrigger,
    FallbackError
)

from .chaos import (
    ChaosExperiment,
    ChaosExperimentConfig,
    ChaosType,
    ChaosState,
    ChaosError,
    chaos_experiment,
    latency_chaos,
    exception_chaos
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