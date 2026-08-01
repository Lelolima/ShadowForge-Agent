"""
Security headers utilities for ShadowForge Agent.
Provides functions to generate and apply security HTTP headers.
"""

from typing import Dict, Optional, List, Union
from dataclasses import dataclass, field


@dataclass
class SecurityHeaders:
    """
    Container for security HTTP headers.
    """
    # Content Security Policy
    content_security_policy: Optional[str] = None

    # HTTP Strict Transport Security (HSTS)
    strict_transport_security: Optional[str] = None

    # X-Frame-Options (clickjacking protection)
    x_frame_options: Optional[str] = None

    # X-Content-Type-Options (MIME sniffing protection)
    x_content_type_options: Optional[str] = None

    # X-XSS-Protection (XSS protection)
    x_xss_protection: Optional[str] = None

    # Referrer-Policy (referrer information)
    referrer_policy: Optional[str] = None

    # Permissions-Policy (formerly Feature-Policy)
    permissions_policy: Optional[str] = None

    # Custom headers
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """
        Convert to dictionary format suitable for HTTP headers.

        Returns:
            Dictionary of header names and values
        """
        headers = {}

        if self.content_security_policy:
            headers["Content-Security-Policy"] = self.content_security_policy

        if self.strict_transport_security:
            headers["Strict-Transport-Security"] = self.strict_transport_security

        if self.x_frame_options:
            headers["X-Frame-Options"] = self.x_frame_options

        if self.x_content_type_options:
            headers["X-Content-Type-Options"] = self.x_content_type_options

        if self.x_xss_protection:
            headers["X-XSS-Protection"] = self.x_xss_protection

        if self.referrer_policy:
            headers["Referrer-Policy"] = self.referrer_policy

        if self.permissions_policy:
            headers["Permissions-Policy"] = self.permissions_policy

        # Add custom headers
        headers.update(self.custom_headers)

        return headers


def get_security_headers(
    *,
    # CSP settings
    csp_default_src: Optional[Union[str, List[str]]] = None,
    csp_script_src: Optional[Union[str, List[str]]] = None,
    csp_style_src: Optional[Union[str, List[str]]] = None,
    csp_img_src: Optional[Union[str, List[str]]] = None,
    csp_font_src: Optional[Union[str, List[str]]] = None,
    csp_connect_src: Optional[Union[str, List[str]]] = None,
    csp_object_src: Optional[Union[str, List[str]]] = None,
    csp_base_uri: Optional[Union[str, List[str]]] = None,
    csp_frame_ancestors: Optional[Union[str, List[str]]] = None,
    csp_form_action: Optional[Union[str, List[str]]] = None,

    # HSTS settings
    hsts_max_age: int = 31536000,  # 1 year
    hsts_include_subdomains: bool = True,
    hsts_preload: bool = False,

    # Other security headers
    frame_options: str = "DENY",  # DENY, SAMEORIGIN, or ALLOW-FROM uri
    content_type_nosniff: bool = True,
    xss_protection: str = "1; mode=block",  # 1; mode=block
    referrer_policy: str = "strict-origin-when-cross-origin",
    permissions_policy: Optional[str] = None,

    # Custom headers
    custom_headers: Optional[Dict[str, str]] = None,
) -> SecurityHeaders:
    """
    Generate security headers based on provided configuration.

    Args:
        csp_*: Content Security Policy directives
        hsts_*: HTTP Strict Transport Security settings
        frame_options: X-Frame-Options value
        content_type_nosniff: Whether to set X-Content-Type-Options
        xss_protection: X-XSS-Protection value
        referrer_policy: Referrer-Policy value
        permissions_policy: Permissions-Policy value
        custom_headers: Additional custom headers

    Returns:
        SecurityHeaders object containing the configured headers
    """
    # Build CSP directive
    csp_directives = []

    if csp_default_src is not None:
        sources = csp_default_src if isinstance(csp_default_src, list) else [csp_default_src]
        csp_directives.append(f"default-src {' '.join(sources)}")

    if csp_script_src is not None:
        sources = csp_script_src if isinstance(csp_script_src, list) else [csp_script_src]
        csp_directives.append(f"script-src {' '.join(sources)}")

    if csp_style_src is not None:
        sources = csp_style_src if isinstance(csp_style_src, list) else [csp_style_src]
        csp_directives.append(f"style-src {' '.join(sources)}")

    if csp_img_src is not None:
        sources = csp_img_src if isinstance(csp_img_src, list) else [csp_img_src]
        csp_directives.append(f"img-src {' '.join(sources)}")

    if csp_font_src is not None:
        sources = csp_font_src if isinstance(csp_font_src, list) else [csp_font_src]
        csp_directives.append(f"font-src {' '.join(sources)}")

    if csp_connect_src is not None:
        sources = csp_connect_src if isinstance(csp_connect_src, list) else [csp_connect_src]
        csp_directives.append(f"connect-src {' '.join(sources)}")

    if csp_object_src is not None:
        sources = csp_object_src if isinstance(csp_object_src, list) else [csp_object_src]
        csp_directives.append(f"object-src {' '.join(sources)}")

    if csp_base_uri is not None:
        sources = csp_base_uri if isinstance(csp_base_uri, list) else [csp_base_uri]
        csp_directives.append(f"base-uri {' '.join(sources)}")

    if csp_frame_ancestors is not None:
        sources = csp_frame_ancestors if isinstance(csp_frame_ancestors, list) else [csp_frame_ancestors]
        csp_directives.append(f"frame-ancestors {' '.join(sources)}")

    if csp_form_action is not None:
        sources = csp_form_action if isinstance(csp_form_action, list) else [csp_form_action]
        csp_directives.append(f"form-action {' '.join(sources)}")

    csp_policy = "; ".join(csp_directives) if csp_directives else None

    # Build HSTS header
    hsts_value = f"max-age={hsts_max_age}"
    if hsts_include_subdomains:
        hsts_value += "; includeSubDomains"
    if hsts_preload:
        hsts_value += "; preload"
    hsts_header = hsts_value if hsts_max_age > 0 else None

    # Validate frame options
    valid_frame_options = ["DENY", "SAMEORIGIN"]
    if frame_options not in valid_frame_options and not frame_options.startswith("ALLOW-FROM"):
        frame_options = "DENY"  # fallback to secure default

    # Build security headers object
    return SecurityHeaders(
        content_security_policy=csp_policy,
        strict_transport_security=hsts_header,
        x_frame_options=frame_options,
        x_content_type_options="nosniff" if content_type_nosniff else None,
        x_xss_protection=xss_protection,
        referrer_policy=referrer_policy,
        permissions_policy=permissions_policy,
        custom_headers=custom_headers or {}
    )


def apply_security_headers(headers: dict, security_headers: SecurityHeaders) -> dict:
    """
    Apply security headers to a dictionary of headers.

    Args:
        headers: Existing headers dictionary to update
        security_headers: SecurityHeaders object containing headers to apply

    Returns:
        Updated headers dictionary
    """
    headers.update(security_headers.to_dict())
    return headers


# Predefined CSP policies for common use cases
CSP_POLICIES = {
    "strict": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
    "moderate": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
    "relaxed": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
}


def get_csp_policy(policy_name: str) -> Optional[str]:
    """
    Get a predefined CSP policy by name.

    Args:
        policy_name: Name of the policy ("strict", "moderate", "relaxed")

    Returns:
        CSP policy string or None if not found
    """
    return CSP_POLICIES.get(policy_name)


__all__ = [
    "SecurityHeaders",
    "get_security_headers",
    "apply_security_headers",
    "get_csp_policy",
    "CSP_POLICIES",
]