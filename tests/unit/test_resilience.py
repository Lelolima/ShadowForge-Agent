"""
Unit tests for resilience patterns in ShadowForge Agent.
Tests circuit breaker, retry, fallback, and chaos engineering implementations.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerError
)
from core.resilience.retry import (
    RetryManager,
    RetryConfig,
    BackoffStrategy,
    RetryError,
    retry,
    retry_on_failure,
    retry_exponential
)
from core.resilience.fallback import (
    Fallback,
    FallbackConfig,
    FallbackTrigger,
    FallbackError
)
from core.resilience.chaos import (
    ChaosExperiment,
    ChaosExperimentConfig,
    ChaosType,
    ChaosState,
    ChaosError,
    chaos_experiment,
    latency_chaos,
    exception_chaos
)


class TestCircuitBreaker:
    """Test circuit breaker implementation."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        config = CircuitBreakerConfig()
        breaker = CircuitBreaker(config)

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        # Simulate failures
        for i in range(3):
            try:
                def failing_func():
                    raise ValueError("test")
                await breaker.call(failing_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(config)

        # Open the circuit breaker
        for i in range(2):
            try:
                def failing_func():
                    raise ValueError("test")
                await breaker.call(failing_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Should raise CircuitBreakerError when trying to call
        with pytest.raises(CircuitBreakerError):
            def success_func():
                return "success"
            await breaker.call(success_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker moves to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1  # 100ms for fast test
        )
        breaker = CircuitBreaker(config)

        # Open the circuit breaker
        for i in range(2):
            try:
                def failing_func():
                    raise ValueError("test")
                await breaker.call(failing_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should move to HALF_OPEN and allow the call
        def success_func():
            return "success"
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_success_threshold(self):
        """Test circuit breaker closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2
        )
        breaker = CircuitBreaker(config)

        # Open the circuit breaker
        for i in range(2):
            try:
                def failing_func():
                    raise ValueError("test")
                await breaker.call(failing_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Successful calls should eventually close the circuit
        def success_func():
            return "success"
        result1 = await breaker.call(success_func)
        assert result1 == "success"
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        result2 = await breaker.call(success_func)
        assert result2 == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Test circuit breaker with async functions."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(config)

        # Simulate async failures
        for i in range(2):
            try:
                async def failing_async_func():
                    await asyncio.sleep(0.01)
                    raise ValueError("test")
                await breaker.call(failing_async_func)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Should raise CircuitBreakerError for async call
        async def success_async_func():
            await asyncio.sleep(0.01)
            return "success"

        with pytest.raises(CircuitBreakerError):
            await breaker.call(success_async_func)


class TestRetryMechanism:
    """Test retry mechanism implementation."""

    def test_retry_success_on_first_attempt(self):
        """Test retry succeeds on first attempt."""
        config = RetryConfig(max_attempts=3)
        retry_manager = RetryManager(config)

        mock_func = Mock(return_value="success")
        result = retry_manager.execute_sync(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_failures(self):
        """Test retry succeeds after initial failures."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        retry_manager = RetryManager(config)

        mock_func = Mock()
        mock_func.side_effect = [
            ValueError("fail 1"),
            ValueError("fail 2"),
            "success"
        ]

        result = retry_manager.execute_sync(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_fails_after_max_attempts(self):
        """Test retry fails after max attempts exceeded."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        retry_manager = RetryManager(config)

        mock_func = Mock()
        mock_func.side_effect = ValueError("always fails")

        with pytest.raises(RetryError) as exc_info:
            retry_manager.execute_sync(mock_func)

        assert "All 2 attempts failed" in str(exc_info.value)
        assert mock_func.call_count == 2
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_retry_does_not_retry_on_non_matching_exception(self):
        """Test retry doesn't retry on non-matching exception types."""
        config = RetryConfig(
            max_attempts=3,
            retry_exceptions=(ValueError,),
            base_delay=0.01
        )
        retry_manager = RetryManager(config)

        mock_func = Mock()
        mock_func.side_effect = TypeError("wrong exception type")

        with pytest.raises(TypeError):
            retry_manager.execute_sync(mock_func)

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test retry with async functions."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        retry_manager = RetryManager(config)

        async def mock_async_func():
            if not hasattr(mock_async_func, 'call_count'):
                mock_async_func.call_count = 0
            mock_async_func.call_count += 1

            if mock_async_func.call_count == 1:
                raise ValueError("fail 1")
            elif mock_async_func.call_count == 2:
                raise ValueError("fail 2")
            else:
                return "success"

        result = await retry_manager.execute_async(mock_async_func)

        assert result == "success"
        assert mock_async_func.call_count == 3

    def test_retry_decorator(self):
        """Test retry decorator."""
        @retry_on_failure(max_attempts=2, base_delay=0.01)
        def flaky_function():
            if not hasattr(flaky_function, 'call_count'):
                flaky_function.call_count = 0
            flaky_function.call_count += 1
            if flaky_function.call_count < 2:
                raise ValueError("temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert flaky_function.call_count == 2

    def test_retry_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            base_delay=0.1,
            backoff_strategy=BackoffStrategy.EXPONENTIAL
        )
        retry_manager = RetryManager(config)

        # Test delay calculation
        delay_0 = retry_manager._calculate_delay(0)  # First retry
        delay_1 = retry_manager._calculate_delay(1)  # Second retry
        delay_2 = retry_manager._calculate_delay(2)  # Third retry

        assert delay_0 == 0.1 * (2 ** 0)  # 0.1
        assert delay_1 == 0.1 * (2 ** 1)  # 0.2
        assert delay_2 == 0.1 * (2 ** 2)  # 0.4


class TestFallbackMechanism:
    """Test fallback mechanism implementation."""

    def test_fallback_not_triggered_on_success(self):
        """Test fallback not triggered when primary succeeds."""
        def primary_func():
            return "primary success"

        def fallback_func():
            return "fallback success"

        config = FallbackConfig(
            trigger=FallbackTrigger.ON_EXCEPTION,
            fallback_func=fallback_func
        )
        fallback = Fallback(config)

        result = fallback.execute_sync(primary_func)
        assert result == "primary success"

    def test_fallback_triggered_on_exception(self):
        """Test fallback triggered when primary raises exception."""
        def primary_func():
            raise ValueError("primary failed")

        def fallback_func():
            return "fallback success"

        config = FallbackConfig(
            trigger=FallbackTrigger.ON_EXCEPTION,
            fallback_func=fallback_func,
            exception_types=(ValueError,)
        )
        fallback = Fallback(config)

        result = fallback.execute_sync(primary_func)
        assert result == "fallback success"

    def test_fallback_error_when_both_fail(self):
        """Test FallbackError when both primary and fallback fail."""
        def primary_func():
            raise ValueError("primary failed")

        def fallback_func():
            raise RuntimeError("fallback failed")

        config = FallbackConfig(
            trigger=FallbackTrigger.ON_EXCEPTION,
            fallback_func=fallback_func,
            exception_types=(ValueError,)
        )
        fallback = Fallback(config)

        with pytest.raises(FallbackError) as exc_info:
            fallback.execute_sync(primary_func)

        assert "Both primary and fallback functions failed" in str(exc_info.value)
        assert isinstance(exc_info.value.primary_exception, ValueError)
        assert isinstance(exc_info.value.fallback_exception, RuntimeError)

    def test_fallback_always_trigger(self):
        """Test fallback with ALWAYS trigger."""
        def primary_func():
            return "primary success"

        def fallback_func():
            return "fallback success"

        config = FallbackConfig(
            trigger=FallbackTrigger.ALWAYS,
            fallback_func=fallback_func
        )
        fallback = Fallback(config)

        result = fallback.execute_sync(primary_func)
        assert result == "fallback success"

    @pytest.mark.asyncio
    async def test_async_fallback(self):
        """Test fallback with async functions."""
        async def async_primary_func():
            return "async primary success"

        async def async_fallback_func():
            return "async fallback success"

        config = FallbackConfig(
            trigger=FallbackTrigger.ON_EXCEPTION,
            fallback_func=async_fallback_func
        )
        fallback = Fallback(config)

        result = await fallback.execute_async(async_primary_func)
        assert result == "async primary success"

    def test_fallback_on_result_condition(self):
        """Test fallback triggered based on result condition."""
        def primary_func():
            return {"status": "error"}

        def fallback_func():
            return {"status": "fallback"}

        def is_error_result(result):
            return result.get("status") == "error"

        config = FallbackConfig(
            trigger=FallbackTrigger.ON_RESULT,
            fallback_func=fallback_func,
            result_condition=is_error_result
        )
        fallback = Fallback(config)

        result = fallback.execute_sync(primary_func)
        assert result == {"status": "fallback"}


class TestChaosEngineering:
    """Test chaos engineering implementation."""

    def test_chaos_experiment_initial_state(self):
        """Test chaos experiment starts in STOPPED state."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=0.1
        )
        experiment = ChaosExperiment(config)

        assert experiment.state == ChaosState.STOPPED
        assert experiment.is_active == False

    def test_chaos_experiment_start_stop(self):
        """Test starting and stopping chaos experiment."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=0.1
        )
        experiment = ChaosExperiment(config)

        assert experiment.state == ChaosState.STOPPED

        experiment.start()
        assert experiment.state == ChaosState.RUNNING
        assert experiment.is_active == True

        experiment.stop()
        assert experiment.state == ChaosState.STOPPED
        assert experiment.is_active == False

    def test_chaos_experiment_pause_resume(self):
        """Test pausing and resuming chaos experiment."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=0.1
        )
        experiment = ChaosExperiment(config)

        experiment.start()
        assert experiment.state == ChaosState.RUNNING

        experiment.pause()
        assert experiment.state == ChaosState.PAUSED
        assert experiment.is_active == False

        experiment.resume()
        assert experiment.state == ChaosState.RUNNING
        assert experiment.is_active == True

    def test_chaos_experiment_should_inject(self):
        """Test chaos injection decision logic."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=0.5,  # 50% chance
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        # Test with probability - should inject roughly half the time
        injections = 0
        total_tests = 100

        for i in range(total_tests):
            if experiment.should_inject("test_function"):
                injections += 1

        # Should be roughly 50% (allowing for randomness)
        assert 30 <= injections <= 70

    def test_chaos_experiment_target_functions(self):
        """Test chaos experiment target function filtering."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=1.0,  # Always inject if not filtered
            target_functions=["allowed_func"],
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        # Should inject for allowed function
        assert experiment.should_inject("allowed_func") == True

        # Should not inject for non-target function
        assert experiment.should_inject("blocked_func") == False

    def test_chaos_experiment_exclude_functions(self):
        """Test chaos experiment exclude function filtering."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=1.0,  # Always inject if not filtered
            exclude_functions=["blocked_func"],
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        # Should not inject for blocked function
        assert experiment.should_inject("blocked_func") == False

        # Should inject for non-blocked function
        assert experiment.should_inject("allowed_func") == True

    @pytest.mark.asyncio
    async def test_latency_chaos_async(self):
        """Test latency chaos with async function."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=1.0,  # Always inject
            parameters={'base_delay': 0.01, 'max_delay': 0.02},
            intensity=1.0,  # Maximum intensity
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        async def async_func():
            return "success"

        start_time = time.time()
        result = await experiment.apply_async(async_func)
        end_time = time.time()

        assert result == "success"
        # Should have taken at least the base delay time
        assert (end_time - start_time) >= 0.01

    def test_latency_chaos_sync(self):
        """Test latency chaos with sync function."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=1.0,  # Always inject
            parameters={'base_delay': 0.01, 'max_delay': 0.02},
            intensity=1.0,  # Maximum intensity
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        def sync_func():
            return "success"

        start_time = time.time()
        result = experiment.apply_sync(sync_func)
        end_time = time.time()

        assert result == "success"
        # Should have taken at least the base delay time
        assert (end_time - start_time) >= 0.01

    @pytest.mark.asyncio
    async def test_exception_chaos_async(self):
        """Test exception chaos with async function."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.EXCEPTION,
            probability=1.0,  # Always inject
            parameters={'exception_type': RuntimeError, 'message': 'chaos test'},
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        async def async_func():
            return "success"

        with pytest.raises(RuntimeError, match="chaos test"):
            await experiment.apply_async(async_func)

    def test_exception_chaos_sync(self):
        """Test exception chaos with sync function."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.EXCEPTION,
            probability=1.0,  # Always inject
            parameters={'exception_type': RuntimeError, 'message': 'chaos test'},
            enabled=True
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        def sync_func():
            return "success"

        with pytest.raises(RuntimeError, match="chaos test"):
            experiment.apply_sync(sync_func)

    def test_chaos_experiment_decorator(self):
        """Test chaos experiment decorator."""
        call_count = 0

        @latency_chaos(probability=1.0, base_delay=0.01, max_delay=0.02)
        async def async_func():
            nonlocal call_count
            call_count += 1
            return "success"

        # Should inject latency
        start_time = time.time()
        result = asyncio.run(async_func())
        end_time = time.time()

        assert result == "success"
        assert call_count == 1
        # Should have taken at least the base delay time
        assert (end_time - start_time) >= 0.01

    def test_chaos_experiment_stats(self):
        """Test chaos experiment statistics."""
        config = ChaosExperimentConfig(
            chaos_type=ChaosType.LATENCY,
            probability=0.5,
            enabled=True,
            name="test_chaos"
        )
        experiment = ChaosExperiment(config)
        experiment.start()

        # Simulate some calls
        for i in range(20):
            experiment.should_inject("test_func")

        stats = experiment.get_stats()

        assert stats['name'] == "test_chaos"
        assert stats['state'] == "running"
        assert stats['enabled'] == True
        assert stats['total_calls'] == 20
        assert 0 <= stats['injection_rate'] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])