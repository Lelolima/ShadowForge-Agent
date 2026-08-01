"""
Rate limiting utilities for ShadowForge Agent.
Provides rate limiting functionality to prevent abuse and brute force attacks.
"""

import time
import threading
from typing import Optional, Dict, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests: int = 100  # Number of requests allowed
    window: int = 60     # Time window in seconds
    burst: int = 20      # Burst allowance (for token bucket)
    algorithm: str = "fixed_window"  # "fixed_window", "sliding_window", or "token_bucket"


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: float = 0.0
    limited: bool = False  # True if rate limit was exceeded


class TokenBucket:
    """Token bucket algorithm implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are added (tokens per second)
        """
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_updated = time.time()
        self._lock = threading.RLock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self._lock:
            now = time.time()
            # Add tokens based on time passed
            elapsed = now - self.last_updated
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_updated = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def tokens_available(self) -> float:
        """Get the current number of available tokens."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_updated
            return min(self.capacity, self.tokens + elapsed * self.refill_rate)


class RateLimiter:
    """Rate limiter supporting multiple algorithms."""

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.

        Args:
            config: RateLimitConfig object
        """
        self.config = config
        self._storage: Dict[str, dict] = {}
        self._lock = threading.RLock()

        # Initialize algorithm-specific components
        if config.algorithm == "token_bucket":
            # For token bucket, we create buckets per key
            self._buckets: Dict[str, TokenBucket] = {}
        else:
            self._buckets = {}

    def _get_client_key(self, identifier: str) -> str:
        """
        Generate a storage key for the client identifier.

        Args:
            identifier: Client identifier (IP, user ID, etc.)

        Returns:
            Hashed key for storage
        """
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def is_allowed(self, identifier: str, cost: int = 1) -> RateLimitResult:
        """
        Check if a request is allowed under the rate limit.

        Args:
            identifier: Unique identifier for the client (IP, user ID, API key, etc.)
            cost: Cost of this request (default 1)

        Returns:
            RateLimitResult indicating if request is allowed and related metrics
        """
        key = self._get_client_key(identifier)
        now = time.time()

        with self._lock:
            if self.config.algorithm == "fixed_window":
                return self._fixed_window(key, now, cost)
            elif self.config.algorithm == "sliding_window":
                return self._sliding_window(key, now, cost)
            elif self.config.algorithm == "token_bucket":
                return self._token_bucket(key, now, cost)
            else:
                # Default to fixed window
                return self._fixed_window(key, now, cost)

    def _fixed_window(self, key: str, now: float, cost: int) -> RateLimitResult:
        """Fixed window algorithm."""
        window_start = now - (now % self.config.window)
        window_key = f"{key}:{window_start}"

        # Clean up old entries
        self._cleanup_old_entries(now)

        # Get current count
        current_data = self._storage.get(window_key, {"count": 0, "reset_time": window_start + self.config.window})
        current_count = current_data["count"]

        # Check if allowed
        if current_count + cost <= self.config.requests:
            # Allow request
            new_count = current_count + cost
            self._storage[window_key] = {
                "count": new_count,
                "reset_time": current_data["reset_time"]
            }

            remaining = self.config.requests - new_count
            reset_time = current_data["reset_time"]
            retry_after = max(0, reset_time - now)

            return RateLimitResult(
                allowed=True,
                remaining=max(0, remaining),
                reset_time=reset_time,
                retry_after=retry_after
            )
        else:
            # Deny request
            reset_time = current_data["reset_time"]
            retry_after = max(0, reset_time - now)

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after,
                limited=True
            )

    def _sliding_window(self, key: str, now: float, cost: int) -> RateLimitResult:
        """Sliding window algorithm using sorted set approach (simplified)."""
        window_start = now - self.config.window

        # Clean up old entries
        self._cleanup_old_entries(now)

        # Get request timestamps for this key
        if key not in self._storage:
            self._storage[key] = {"timestamps": []}

        timestamps = self._storage[key]["timestamps"]

        # Remove timestamps outside the window
        timestamps[:] = [ts for ts in timestamps if ts > window_start]

        # Check if adding this request would exceed limit
        if len(timestamps) + cost <= self.config.requests:
            # Allow request
            timestamps.extend([now] * cost)

            # Calculate remaining requests in window
            remaining = self.config.requests - len(timestamps)

            # Estimate reset time (when oldest request will expire)
            if timestamps:
                oldest = min(timestamps)
                reset_time = oldest + self.config.window
            else:
                reset_time = now + self.config.window

            retry_after = max(0, reset_time - now)

            return RateLimitResult(
                allowed=True,
                remaining=max(0, remaining),
                reset_time=reset_time,
                retry_after=retry_after
            )
        else:
            # Deny request
            if timestamps:
                oldest = min(timestamps)
                reset_time = oldest + self.config.window
            else:
                reset_time = now + self.config.window

            retry_after = max(0, reset_time - now)

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after,
                limited=True
            )

    def _token_bucket(self, key: str, now: float, cost: int) -> RateLimitResult:
        """Token bucket algorithm."""
        # Get or create bucket for this key
        if key not in self._buckets:
            # refill_rate = requests per second
            refill_rate = self.config.requests / self.config.window
            self._buckets[key] = TokenBucket(
                capacity=self.config.requests + self.config.burst,
                refill_rate=refill_rate
            )

        bucket = self._buckets[key]

        # Try to consume tokens
        if bucket.consume(cost):
            # Request allowed
            tokens_available = bucket.tokens_available()
            # Estimate reset time (when bucket will be full again)
            if tokens_available < self._buckets[key].capacity:
                # Time to fill remaining capacity
                needed = self._buckets[key].capacity - tokens_available
                reset_time = now + (needed / self._buckets[key].refill_rate)
            else:
                reset_time = now  # Bucket is full

            retry_after = 0.0 if tokens_available >= cost else (cost - tokens_available) / self._buckets[key].refill_rate

            return RateLimitResult(
                allowed=True,
                remaining=int(tokens_available),
                reset_time=reset_time,
                retry_after=max(0, retry_after)
            )
        else:
            # Request denied
            tokens_available = bucket.tokens_available()
            # Estimate when enough tokens will be available
            needed = cost - tokens_available
            reset_time = now + (needed / self._buckets[key].refill_rate) if self._buckets[key].refill_rate > 0 else float('inf')
            retry_after = max(0, needed / self._buckets[key].refill_rate) if self._buckets[key].refill_rate > 0 else 0.0

            return RateLimitResult(
                allowed=False,
                remaining=int(tokens_available),
                reset_time=reset_time,
                retry_after=retry_after,
                limited=True
            )

    def _cleanup_old_entries(self, now: float):
        """Clean up old entries to prevent memory leak."""
        # For fixed and sliding window, clean entries older than 2 windows
        cutoff_time = now - (2 * self.config.window)

        keys_to_delete = []
        for key, value in self._storage.items():
            if isinstance(value, dict):
                # Check if it's a timestamp-based entry (sliding window) or window-based (fixed)
                if "timestamps" in value:
                    # Sliding window - remove old timestamps
                    timestamps = value["timestamps"]
                    # This is simplified - in practice we'd use a sorted structure
                    # For now, we'll clean if all timestamps are old
                    if timestamps and max(timestamps) < cutoff_time:
                        keys_to_delete.append(key)
                elif "reset_time" in value:
                    # Fixed window - check if window is old
                    if value["reset_time"] < cutoff_time:
                        keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._storage[key]

    def get_stats(self, identifier: str) -> dict:
        """
        Get current statistics for an identifier.

        Args:
            identifier: Client identifier

        Returns:
            Dictionary with current rate limit stats
        """
        key = self._get_client_key(identifier)
        now = time.time()

        with self._lock:
            if self.config.algorithm == "token_bucket" and key in self._buckets:
                bucket = self._buckets[key]
                tokens_available = bucket.tokens_available()
                return {
                    "tokens_available": tokens_available,
                    "capacity": bucket.capacity,
                    "refill_rate": bucket.refill_rate
                }
            else:
                # For window-based algorithms, return info about current window
                window_start = now - (now % self.config.window)
                window_key = f"{key}:{window_start}"
                current_data = self._storage.get(window_key, {"count": 0})
                return {
                    "current_count": current_data["count"],
                    "limit": self.config.requests,
                    "window_start": window_start,
                    "window_end": window_start + self.config.window
                }


def rate_limit(
    requests: int = 100,
    window: int = 60,
    burst: int = 20,
    algorithm: str = "fixed_window",
    key_func: Optional[Callable[[], str]] = None
):
    """
    Decorator for rate limiting functions.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        burst: Burst allowance (for token bucket)
        algorithm: Algorithm to use
        key_func: Function to extract identifier from arguments (defaults to IP)

    Returns:
        Decorator function
    """
    limiter = RateLimiter(RateLimitConfig(
        requests=requests,
        window=window,
        burst=burst,
        algorithm=algorithm
    ))

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract identifier
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                # Default: try to get from first arg if it's a request-like object
                identifier = "default"
                if args:
                    # Try common patterns for web frameworks
                    arg = args[0]
                    if hasattr(arg, 'client') and hasattr(arg.client, 'host'):
                        identifier = arg.client.host
                    elif hasattr(arg, 'remote_addr'):
                        identifier = arg.remote_addr
                    elif hasattr(arg, 'request') and hasattr(arg.request, 'remote_addr'):
                        identifier = arg.request.remote_addr

            # Check rate limit
            result = limiter.is_allowed(identifier)

            if not result.allowed:
                # In a real web framework, we'd raise an HTTP exception here
                # For now, we'll raise a generic exception
                raise Exception(f"Rate limit exceeded. Retry after {result.retry_after:.0f} seconds")

            # Call the original function
            return func(*args, **kwargs)

        return wrapper
    return decorator


def create_rate_limiter(
    requests: int = 100,
    window: int = 60,
    burst: int = 20,
    algorithm: str = "fixed_window"
) -> RateLimiter:
    """
    Factory function to create a rate limiter.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        burst: Burst allowance (for token bucket)
        algorithm: Algorithm to use ("fixed_window", "sliding_window", "token_bucket")

    Returns:
        Configured RateLimiter instance
    """
    return RateLimiter(RateLimitConfig(
        requests=requests,
        window=window,
        burst=burst,
        algorithm=algorithm
    ))


# Convenience functions for common rate limiting scenarios
def create_ip_rate_limiter(requests_per_minute: int = 60) -> RateLimiter:
    """Create a rate limiter for IP-based limiting."""
    return create_rate_limiter(
        requests=requests_per_minute,
        window=60,
        algorithm="fixed_window"
    )

def create_api_key_rate_limiter(requests_per_hour: int = 1000) -> RateLimiter:
    """Create a rate limiter for API key-based limiting."""
    return create_rate_limiter(
        requests=requests_per_hour,
        window=3600,
        algorithm="fixed_window"
    )

def create_burst_tolerant_limiter(requests_per_minute: int = 30, burst: int = 10) -> RateLimiter:
    """Create a rate limiter that allows bursts."""
    return create_rate_limiter(
        requests=requests_per_minute,
        window=60,
        burst=burst,
        algorithm="token_bucket"
    )


__all__ = [
    "RateLimitConfig",
    "RateLimitResult",
    "TokenBucket",
    "RateLimiter",
    "rate_limit",
    "create_rate_limiter",
    "create_ip_rate_limiter",
    "create_api_key_rate_limiter",
    "create_burst_tolerant_limiter"
]