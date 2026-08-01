"""
Alerting for ShadowForge Agent.

Evaluates alert rules based on metrics and sends notifications via webhook.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Any, Optional, Callable
from urllib import request, error

logger = logging.getLogger("shadowforge.observability.alerting")

# Alert rule configuration
ALERT_RULES = [
    {
        "name": "high_error_rate",
        "description": "Error rate exceeds threshold",
        "metric": "shadowforge_errors_total",
        "threshold": 10,  # errors per minute
        "evaluation_interval": 60,  # seconds
        "webhook_key": "ERROR_RATE_WEBHOOK_URL",
    },
    {
        "name": "high_ooda_latency",
        "description": "OODA loop duration too high",
        "metric": "shadowforge_ooda_duration_seconds",
        "threshold": 5.0,  # seconds
        "evaluation_interval": 30,
        "quantile": 0.95,  # 95th percentile
        "webhook_key": "OODA_LATENCY_WEBHOOK_URL",
    },
    {
        "name": "subsystem_unhealthy",
        "description": "A subsystem is unhealthy",
        "metric": "shadowforge_subsystem_health",
        "threshold": 0.5,  # less than 50% healthy (since it's 0 or 1)
        "evaluation_interval": 15,
        "webhook_key": "SUBSYSTEM_HEALTH_WEBHOOK_URL",
    },
]

# State for tracking alerts to avoid spamming
_alert_state: dict[str, bool] = {rule["name"]: False for rule in ALERT_RULES}
_last_alert_time: dict[str, float] = {rule["name"]: 0 for rule in ALERT_RULES}
_ALERT_COOLDOWN = 300  # 5 minutes between same alert notifications


def _send_webhook(url: str, payload: dict) -> bool:
    """Send a JSON payload to a webhook URL."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                logger.info(f"Alert webhook sent successfully to {url}")
                return True
            else:
                logger.warning(f"Webhook returned status {resp.status}")
                return False
    except error.URLError as e:
        logger.error(f"Failed to send webhook to {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending webhook: {e}")
        return False


def _get_metric_value(rule_name: str, value: float) -> str:
    """Return a human-readable message for an alert."""
    messages = {
        "high_error_rate": f"Error rate is {value:.2f} per minute, exceeding threshold of {ALERT_RULES[0]['threshold']}",
        "high_ooda_latency": f"OODA loop 95th percentile latency is {value:.2f}s, exceeding threshold of {ALERT_RULES[1]['threshold']}s",
        "subsystem_unhealthy": f"Subsystem health score is {value:.2f}, below threshold of {ALERT_RULES[2]['threshold']}",
    }
    return messages.get(rule_name, f"Metric {rule_name} has value {value}")


def evaluate_alert_rules(get_metric_fn: Optional[callable] = None) -> None:
    """
    Evaluate all alert rules and send notifications if thresholds are exceeded.

    Args:
        get_metric_fn: A function that takes a metric name and returns its current value.
                      If not provided, we will skip evaluation (metrics may not be available).
    """
    if not get_metric_fn:
        # We cannot evaluate without a way to get metrics
        return

    current_time = time.time()
    for rule in ALERT_RULES:
        rule_name = rule["name"]
        # Check if we are in cooldown period for this alert
        if current_time - _last_alert_time.get(rule_name, 0) < _ALERT_COOLDOWN:
            continue

        try:
            # Get the metric value (this is a placeholder; in reality, we'd query Prometheus)
            # For simplicity, we'll assume get_metric_fn can give us the current value.
            # In a real implementation, we might query the Prometheus endpoint.
            value = get_metric_fn(rule["metric"])
            if value is None:
                continue

            # Check threshold
            exceeds_threshold = False
            if rule.get("quantile"):
                # For histogram metrics, we might need to query a specific quantile.
                # This is a simplification; we assume get_metric_fn returns the quantile if specified.
                pass
            else:
                # For counters and gauges, we compare the value directly
                if rule["name"] == "subsystem_unhealthy":
                    # We want to alert if health is below threshold (i.e., unhealthy)
                    exceeds_threshold = value < rule["threshold"]
                else:
                    exceeds_threshold = value > rule["threshold"]

            if exceeds_threshold:
                if not _alert_state.get(rule_name, False):
                    # First time triggering this alert
                    message = _(rule_name, value)
                    payload = {
                        "alert": rule_name,
                        "message": message,
                        "value": value,
                        "threshold": rule.get("threshold"),
                        "timestamp": current_time,
                    }
                    webhook_url = os.environ.get(rule["webhook_key"])
                    if webhook_url:
                        if _send_webhook(webhook_url, payload):
                            _alert_state[rule_name] = True
                            _last_alert_time[rule_name] = current_time
                    else:
                        logger.warning(f"No webhook URL configured for {rule['webhook_key']}")
            else:
                # Reset alert state if metric is back to normal
                if _alert_state.get(rule_name, False):
                    _alert_state[rule_name] = False
                    logger.info(f"Alert {rule_name} resolved")

        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule_name}: {e}")


def setup_periodic_evaluation(interval: int = 30) -> None:
    """
    Set up periodic evaluation of alert rules.
    This function should be called from the agent's main loop or a background task.
    """
    # We'll implement a simple loop that can be run as a task
    async def _evaluate_loop():
        while True:
            try:
                # We need a way to get metric values; this would require integrating with Prometheus
                # For now, we'll just log that we're evaluating.
                logger.debug("Evaluating alert rules (stub)")
                # In a real implementation, we would get the metric values from Prometheus
                # and call evaluate_alert_rules(get_metric_fn=get_prometheus_metric)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(interval)

    # We return the coroutine so the caller can schedule it
    return _evaluate_loop()