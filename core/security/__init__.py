"""
Security module for ShadowForge Agent.
Provides security utilities, input validation, output encoding, and protection mechanisms.
"""

from .injection_prevention import (
    prevent_command_injection,
    prevent_sql_injection,
    sanitize_shell,
    sanitize_sql,
)
from .input_validation import ValidationError, sanitize_input, validate_input
from .output_encoding import encode_html, encode_javascript, encode_url
from .rate_limiting import (
    RateLimitConfig,
    RateLimiter,
    RateLimitResult,
    TokenBucket,
    create_api_key_rate_limiter,
    create_burst_tolerant_limiter,
    create_ip_rate_limiter,
    create_rate_limiter,
    rate_limit,
)
from .security_headers import (
    CSP_POLICIES,
    SecurityHeaders,
    apply_security_headers,
    get_csp_policy,
    get_security_headers,
)

__all__ = [
    # Input validation
    "validate_input",
    "sanitize_input",
    "ValidationError",
    # Output encoding
    "encode_html",
    "encode_url",
    "encode_javascript",
    # Injection prevention
    "prevent_sql_injection",
    "prevent_command_injection",
    "sanitize_sql",
    "sanitize_shell",
    # Security headers
    "SecurityHeaders",
    "get_security_headers",
    "apply_security_headers",
    "get_csp_policy",
    "CSP_POLICIES",
    # Rate limiting
    "RateLimitConfig",
    "RateLimitResult",
    "TokenBucket",
    "RateLimiter",
    "rate_limit",
    "create_rate_limiter",
    "create_ip_rate_limiter",
    "create_api_key_rate_limiter",
    "create_burst_tolerant_limiter",
]
