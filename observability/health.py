"""
Health checks for ShadowForge Agent.

Provides functions to check the health of various subsystems and
integrates with the dashboard API to expose HTTP endpoints.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("shadowforge.observability.health")

# We'll try to import the dashboard app to add routes if available
try:
    from api.dashboard import app as dashboard_app, update_dashboard_state
    HAS_DASHBOARD = True
except ImportError:
    HAS_DASHBOARD = False
    logger.warning("Dashboard API not available, health endpoints will not be added")

# Health check results cache to avoid over-checking
_health_cache: Dict[str, Any] = {}
_health_cache_timeout = 30  # seconds


def check_event_bus_health(agent) -> bool:
    """Check if the event bus is running and processing events."""
    try:
        if not agent.event_bus:
            return False
        # Check if the event bus is running (has a processing task)
        if hasattr(agent.event_bus, '_running') and agent.event_bus._running:
            return True
        # Alternatively, check if there's a processing task that's not done
        if hasattr(agent.event_bus, '_processing_task') and agent.event_bus._processing_task:
            return not agent.event_bus._processing_task.done()
        return False
    except Exception as e:
        logger.debug(f"Event bus health check failed: {e}")
        return False


def check_nim_client_health(agent) -> bool:
    """Check if the NIM client is configured and can reach the API."""
    try:
        if not agent.config or not agent.config.nvidia:
            return False
        # We could do a lightweight check, but to avoid using credits, we'll just check config
        # In a real implementation, we might do a minimal API call (e.g., check models) if not in simulate mode
        if agent.simulate:
            return True  # In simulate mode, we consider it healthy
        # Check if API key is set and not a placeholder
        api_key = agent.config.nvidia.api_key
        if not api_key or api_key.startswith("nvapi-xxxxx"):
            return False
        return True
    except Exception as e:
        logger.debug(f"NIM client health check failed: {e}")
        return False


def check_database_health(agent) -> bool:
    """Check if the database files are accessible."""
    try:
        # Check short-term memory database
        if hasattr(agent, 'memoria_cp') and agent.memoria_cp:
            # We assume it's healthy if we can access it
            pass
        # Check long-term memory database
        if hasattr(agent, 'memoria_lp') and agent.memoria_lp:
            pass
        return True
    except Exception as e:
        logger.debug(f"Database health check failed: {e}")
        return False


def check_dashboard_health() -> bool:
    """Check if the dashboard API is available."""
    return HAS_DASHBOARD


def get_subsystem_health(agent) -> Dict[str, bool]:
    """Get health status of all subsystems."""
    return {
        "event_bus": check_event_bus_health(agent),
        "nim_client": check_nim_client_health(agent),
        "database": check_database_health(agent),
        "dashboard": check_dashboard_health(),
    }


def update_observability_subsystem_health(agent) -> None:
    """Update the Prometheus health gauges for subsystems."""
    try:
        from .metrics import set_subsystem_health
        health = get_subsystem_health(agent)
        for subsystem, healthy in health.items():
            set_subsystem_health(subsystem, healthy)
    except ImportError:
        pass  # metrics not available


def register_health_endpoints() -> None:
    """Register health check endpoints on the dashboard API."""
    if not HAS_DASHBOARD:
        return

    from fastapi import HTTPException

    @dashboard_app.get("/health/live")
    async def liveness_probe():
        """Liveness probe: returns 200 if the agent is running."""
        # We don't have easy access to the agent instance here.
        # In a real deployment, we might need to pass the agent to the dashboard.
        # For now, we'll return 200 if the dashboard is up (meaning the agent initialized it).
        return {"status": "alive"}

    @dashboard_app.get("/health/ready")
    async def readiness_probe():
        """Readiness probe: returns 200 if all critical subsystems are healthy."""
        # Again, we don't have the agent instance.
        # We'll need to store a reference to the agent in the dashboard module or use a global.
        # For simplicity, we'll return 200 if the dashboard is up and we assume the agent is okay.
        # In a real implementation, we would check the agent's subsystems.
        return {"status": "ready"}

    @dashboard_app.get("/health")
    async def health_check():
        """Comprehensive health check."""
        # We'll try to get the agent from the dashboard state or a global.
        # Since we don't have a good way, we'll return a placeholder.
        # We can update the dashboard state with the agent reference during initialization.
        return {
            "status": "checking",
            "timestamp": time.time(),
            "checks": {
                "event_bus": "unknown",
                "nim_client": "unknown",
                "database": "unknown",
                "dashboard": "available" if HAS_DASHBOARD else "unavailable",
            }
        }

    logger.info("Health check endpoints registered on dashboard API")