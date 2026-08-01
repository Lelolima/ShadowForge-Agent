"""
OpenTelemetry tracing for ShadowForge Agent.

Provides optional tracing of OODA cycles, external API calls, and internal functions.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger("shadowforge.observability.tracing")

# Try to import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    HAS_OPENTELEMETRY = True
except ImportError:
    HAS_OPENTELEMETRY = False
    logger.warning("OpenTelemetry not installed, tracing will be disabled")

if HAS_OPENTELEMETRY:
    # Configure the tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Optional: Add an OTLP exporter if endpoint is configured
    try:
        otlp_exporter = OTLPSpanExporter()
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        logger.info("OpenTelemetry OTLP exporter configured")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP exporter: {e}")
        # Continue without exporter (will use NoOp exporter if none configured)
else:
    # No-op tracer and decorator
    class _DummyTracer:
        def start_as_current_span(self, name, *args, **kwargs):
            return _DummySpan()

    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def set_attribute(self, key, value):
            pass

        def record_exception(self, exception):
            pass

        def set_status(self, status):
            pass

    tracer = _DummyTracer()  # type: ignore


def trace_async(func: Callable) -> Callable:
    """Decorator to trace an async function."""
    if not HAS_OPENTELEMETRY:
        return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f"{func.__module__}.{func.__qualname__}") as span:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    return wrapper


def trace_sync(func: Callable) -> Callable:
    """Decorator to trace a synchronous function."""
    if not HAS_OPENTELEMETRY:
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f"{func.__module__}.{func.__qualname__}"):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # In a sync context, we can still record exception on the current span
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    return wrapper


def trace_ooda_phase(phase: str):
    """Decorator to trace an OODA phase and record its duration in metrics."""
    def decorator(func: Callable) -> Callable:
        if not HAS_OPENTELEMETRY:
            return func

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                with tracer.start_as_current_span(f"ooda.{phase}") as span:
                    span.set_attribute("ooda.phase", phase)
                    result = await func(*args, **kwargs)
                    return result
            except Exception as e:
                span.record_exception(e)
                raise
            finally:
                duration = time.time() - start_time
                # Record duration in metrics (if available)
                try:
                    from .metrics import record_ooda_phase
                    record_ooda_phase(phase, duration)
                except ImportError:
                    pass

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                with tracer.start_as_current_span(f"ooda.{phase}") as span:
                    span.set_attribute("ooda.phase", phase)
                    result = func(*args, **kwargs)
                    return result
            except Exception as e:
                span.record_exception(e)
                raise
            finally:
                duration = time.time() - start_time
                try:
                    from .metrics import record_ooda_phase
                    record_ooda_phase(phase, duration)
                except ImportError:
                    pass

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper

    return decorator