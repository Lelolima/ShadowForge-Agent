import pytest
from observability.metrics import (
    OODA_DURATION_SECONDS,
    OODA_ITERATIONS_TOTAL,
    EVENTS_PUBLISHED_TOTAL,
    EVENTS_PROCESSED_TOTAL,
    EVENT_PROCESSING_LATENCY_SECONDS,
    ERRORS_TOTAL,
    ACTIVE_OODA_CYCLES,
    QUEUED_EVENTS,
    SUBSYSTEM_HEALTH,
    record_ooda_phase,
    increment_ooda_iterations,
    record_event_published,
    record_event_processed,
    record_error,
    set_active_ooda_cycles,
    set_queued_events,
    set_subsystem_health
)

def test_metrics_import():
    """Test that the metrics module imports successfully."""
    assert OODA_DURATION_SECONDS is not None
    assert OODA_ITERATIONS_TOTAL is not None
    assert EVENTS_PUBLISHED_TOTAL is not None
    assert EVENTS_PROCESSED_TOTAL is not None
    assert EVENT_PROCESSING_LATENCY_SECONDS is not None
    assert ERRORS_TOTAL is not None
    assert ACTIVE_OODA_CYCLES is not None
    assert QUEUED_EVENTS is not None
    assert SUBSYSTEM_HEALTH is not None

def test_record_ooda_phase():
    """Test recording OODA phase duration."""
    # This should not raise an exception
    record_ooda_phase("observe", 0.1)
    record_ooda_phase("orient", 0.2)
    record_ooda_phase("decide", 0.15)
    record_ooda_phase("act", 0.05)

def test_increment_ooda_iterations():
    """Test incrementing OODA iterations."""
    # This should not raise an exception
    increment_ooda_iterations()
    increment_ooda_iterations()

def test_record_event_published():
    """Test recording event published."""
    # This should not raise an exception
    record_event_published("test_event", "high")

def test_record_event_processed():
    """Test recording event processed."""
    # This should not raise an exception
    record_event_processed("test_event", "success", 0.5)
    record_event_processed("test_event", "failure", 0.3)

def test_record_error():
    """Test recording error."""
    # This should not raise an exception
    record_error("test_component", "test_error")

def test_set_active_ooda_cycles():
    """Test setting active OODA cycles."""
    # This should not raise an exception
    set_active_ooda_cycles(1)
    set_active_ooda_cycles(0)

def test_set_queued_events():
    """Test setting queued events."""
    # This should not raise an exception
    set_queued_events(10)
    set_queued_events(0)

def test_set_subsystem_health():
    """Test setting subsystem health."""
    # This should not raise an exception
    set_subsystem_health("event_bus", True)
    set_subsystem_health("nim_client", False)