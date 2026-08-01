"""
Output encoding utilities for ShadowForge Agent.
Provides functions to encode output for different contexts to prevent XSS and injection attacks.
"""

import html
import urllib.parse
import re
import json
from typing import Union


def encode_html(text: str) -> str:
    """
    HTML encode text to prevent XSS attacks.

    Args:
        text: Text to encode

    Returns:
        HTML-encoded string
    """
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text)


def encode_html_attribute(text: str) -> str:
    """
    HTML encode text for use in HTML attributes.

    Args:
        text: Text to encode

    Returns:
        HTML-encoded string safe for attributes
    """
    if not isinstance(text, str):
        text = str(text)
    # Escape quotes and other characters that can break out of attributes
    encoded = html.escape(text, quote=True)
    # Additional encoding for attribute contexts
    return encoded.replace('"', '"').replace("'", "'")


def encode_url(text: str) -> str:
    """
    URL encode text to prevent injection in URLs.

    Args:
        text: Text to encode

    Returns:
        URL-encoded string
    """
    if not isinstance(text, str):
        text = str(text)
    return urllib.parse.quote(str(text), safe='')


def encode_url_path(path: str) -> str:
    """
    URL encode a path component.

    Args:
        path: Path to encode

    Returns:
        URL-encoded path
    """
    if not isinstance(path, str):
        path = str(path)
    # Don't encode slashes as they are path separators
    return urllib.parse.quote(str(path), safe='/')


def encode_url_query_value(value: str) -> str:
    """
    URL encode a query parameter value.

    Args:
        value: Value to encode

    Returns:
        URL-encoded value
    """
    if not isinstance(value, str):
        value = str(value)
    return urllib.parse.quote_plus(str(value))


def encode_javascript(text: str) -> str:
    """
    JavaScript encode text to prevent injection in JS contexts.

    Args:
        text: Text to encode

    Returns:
        JavaScript-encoded string
    """
    if not isinstance(text, str):
        text = str(text)

    # Escape characters that have special meaning in JavaScript strings
    # This includes quotes, backslashes, newlines, etc.
    escapes = {
        '\\': '\\\\',
        '"': '\\"',
        "'": "\\'",
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f',
        '\v': '\\v',
        '\0': '\\0',
        ' ': '\\u2028',  # Line separator
        ' ': '\\u2029',  # Paragraph separator
    }

    result = []
    for char in text:
        if char in escapes:
            result.append(escapes[char])
        elif ord(char) < 32 or ord(char) > 126:
            # Non-printable ASCII and Unicode characters
            if ord(char) < 256:
                # Hex escape for Latin-1
                result.append(f'\\x{ord(char):02x}')
            else:
                # Unicode escape
                result.append(f'\\u{ord(char):04x}')
        else:
            result.append(char)

    return ''.join(result)


def encode_json(data: any) -> str:
    """
    JSON encode data to prevent injection in JSON contexts.

    Args:
        data: Data to encode

    Returns:
        JSON-encoded string
    """
    return json.dumps(data, ensure_ascii=False)


def encode_css(value: str) -> str:
    """
    CSS encode a value to prevent injection in CSS contexts.

    Args:
        value: Value to encode

    Returns:
        CSS-encoded string
    """
    if not isinstance(value, str):
        value = str(value)

    # Escape CSS special characters
    # Based on CSS escaping rules
    escaped = []
    for char in value:
        code_point = ord(char)
        # Characters that are safe in CSS identifiers (unchanged)
        if (code_point >= 0x30 and code_point <= 0x39) or \
           (code_point >= 0x41 and code_point <= 0x5A) or \
           (code_point >= 0x61 and code_point <= 0x7A) or \
           code_point == 0x5F:  # underscore
            escaped.append(char)
        elif code_point == 0x2D:  # hyphen
            # Hyphen is safe except at the start
            if len(escaped) == 0:
                escaped.append('\\2d ')  # Escape leading hyphen
            else:
                escaped.append(char)
        else:
            # Escape as Unicode
            escaped.append(f'\\{code_point:0x} ')

    return ''.join(escaped)


def normalize_path(path: str) -> str:
    """
    Normalize a file path to prevent directory traversal attacks.

    Args:
        path: Path to normalize

    Returns:
        Normalized path safe from traversal (relative to current directory)
    """
    if not isinstance(path, str):
        path = str(path)

    # Remove any null bytes
    path = path.replace('\x00', '')

    # Split by path separators
    parts = []
    for part in path.replace('\\', '/').split('/'):
        if part == '' or part == '.':
            # Skip empty or current directory
            continue
        elif part == '..':
            # Parent directory - remove last component if possible
            if parts and parts[-1] != '..':
                parts.pop()
            # If we're at root and see .., we keep it (but this could still be dangerous)
            # For security, we'll not allow going above root
        else:
            parts.append(part)

    # Join back together
    if not parts:
        return '.'

    return '/'.join(parts)


def safe_string_truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Safely truncate a string to prevent DoS via overly long strings.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append when truncating

    Returns:
        Truncated string
    """
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    return text[:max_length - len(suffix)] + suffix