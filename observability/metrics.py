"""
Prometheus metrics for ShadowForge Agent.

Exposes metrics via HTTP endpoint if prometheus_client is available.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("shadowforge.observability.metrics")

# Try to import prometheus_client
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    logger.warning("prometheus_client not installed, metrics will be disabled")

if HAS_PROMETHEUS:
    # OODA Loop Metrics
    OODA_DURATION_SECONDS = Histogram(
        "shadowforge_ooda_duration_seconds",
        "Duration of OODA cycle phases",
        ["phase"],  # phase: observe, orient, decide, act
    )

    OODA_ITERATIONS_TOTAL = Counter(
        "shadowforge_ooda_iterations_total",
        "Total number of OODA iterations completed",
    )

    # Event Bus Metrics
    EVENTS_PUBLISHED_TOTAL = Counter(
        "shadowforge_events_published_total",
        "Total number of events published",
        ["event_type", "priority"],
    )

    EVENTS_PROCESSED_TOTAL = Counter(
        "shadowforge_events_processed_total",
        "Total number of events processed by handlers",
        ["event_type", "outcome"],  # outcome: success, failure, retry_exhausted
    )

    EVENT_PROCESSING_LATENCY_SECONDS = Histogram(
        "shadowforge_event_processing_latency_seconds",
        "Latency of event processing",
        ["event_type"],
    )

    # Error Metrics
    ERRORS_TOTAL = Counter(
        "shadowforge_errors_total",
        "Total number of errors",
        ["component", "error_type"],
    )

    # Gauges for current state
    ACTIVE_OODA_CYCLES = Gauge(
        "shadowforge_active_ooda_cycles",
        "Number of active OODA cycles (usually 0 or 1)",
    )

    QUEUED_EVENTS = Gauge(
        "shadowforge_queued_events",
        "Number of events waiting in the event bus queue",
    )

    # Subsystem Health Gauges (1 = healthy, 0 = unhealthy)
    SUBSYSTEM_HEALTH = Gauge(
        "shadowforge_subsystem_health",
        "Health status of subsystems (1=healthy, 0=unhealthy)",
        ["subsystem"],
    )
else:
    # No-op implementations if prometheus_client is not available
    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, amount=1):
            pass

        def dec(self, amount=1):
            pass

        def set(self, value):
            pass

        def observe(self, value):
            pass

    OODA_DURATION_SECONDS = _DummyMetric()  # type: ignore
    OODA_ITERATIONS_TOTAL = _DummyMetric()  # type: ignore
    EVENTS_PUBLISHED_TOTAL = _DummyMetric()  # type: ignore
    EVENTS_PROCESSED_TOTAL = _DummyMetric()  # type: ignore
    EVENT_PROCESSING_LATENCY_SECONDS = _DummyMetric()  # type: ignore
    ERRORS_TOTAL = _DummyMetric()  # type: ignore
    ACTIVE_OODA_CYCLES = _DummyMetric()  # type: ignore
    QUEUED_EVENTS = _DummyMetric()  # type: ignore
    SUBSYSTEM_HEALTH = _DummyMetric()  # type: ignore

    def generate_latest():
        return b"# prometheus_client not available\n"

    CONTENT_TYPE_LATEST = "text/plain"


def record_ooda_phase(phase: str, duration_seconds: float) -> None:
    """Record the duration of an OODA phase."""
    OODA_DURATION_SECONDS.labels(phase=phase).observe(duration_seconds)


def increment_ooda_iterations() -> None:
    """Increment the OODA iteration counter."""
    OODA_ITERATIONS_TOTAL.inc()


def record_event_published(event_type: str, priority: str) -> None:
    """Record that an event was published."""
    EVENTS_PUBLISHED_TOTAL.labels(event_type=event_type, priority=priority).inc()


def record_event_processed(event_type: str, outcome: str, latency_seconds: float) -> None:
    """Record that an event was processed by a handler."""
    EVENTS_PROCESSED_TOTAL.labels(event_type=event_type, outcome=outcome).inc()
    EVENT_PROCESSING_LATENCY_SECONDS.labels(event_type=event_type).observe(latency_seconds)


def record_error(component: str, error_type: str) -> None:
    """Record an error occurrence."""
    ERRORS_TOTAL.labels(component=component, error_type=error_type).inc()


def set_active_ooda_cycles(count: int) -> None:
    """Set the gauge for active OODA cycles."""
    ACTIVE_OODA_CYCLES.set(count)


def set_queued_events(count: int) -> None:
    """Set the gauge for queued events."""
    QUEUED_EVENTS.set(count)


def set_subsystem_health(subsystem: str, healthy: bool) -> None:
    """Set the health gauge for a subsystem."""
    SUBSYSTEM_HEALTH.labels(subsystem=subsystem).set(1 if healthy else 0)


def get_metrics() -> bytes:
    """Get the latest Prometheus metrics."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST