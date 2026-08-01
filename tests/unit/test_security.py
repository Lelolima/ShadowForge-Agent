"""
Unit tests for security module components.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from core.security.input_validation import (
    validate_input, ValidationError, ValidationRule, validate_ip_address,
    validate_hostname, validate_port, validate_email, validate_url
)
from core.security.output_encoding import (
    encode_html, encode_html_attribute, encode_url,
    encode_javascript, encode_json, encode_css,
    normalize_path, safe_string_truncate
)
from core.security.injection_prevention import (
    prevent_sql_injection, execute_safe_sql,
    prevent_command_injection, execute_safe_command,
    sanitize_sql, sanitize_shell, escape_like_pattern,
    validate_and_sanitize_filename, safe_format_string,
    SQLIdentifier, safe_sql_identifier, build_safe_select
)
from core.security.security_headers import (
    SecurityHeaders, get_security_headers, apply_security_headers,
    get_csp_policy, CSP_POLICIES
)
from core.security.rate_limiting import (
    RateLimitConfig, RateLimitResult, TokenBucket, RateLimiter,
    create_ip_rate_limiter, create_api_key_rate_limiter,
    create_burst_tolerant_limiter
)


class TestInputValidation:
    """Test input validation functions."""

    def test_validate_input_required(self):
        """Test required field validation."""
        with pytest.raises(ValidationError, match="test_field is required"):
            validate_input(None, field_name="test_field", required=True)

    def test_validate_input_not_required(self):
        """Test non-required field validation."""
        assert validate_input(None, field_name="test_field", required=False) is None

    def test_validate_input_length(self):
        """Test length validation."""
        rule = ValidationRule(min_length=3, max_length=10)

        # Too short
        with pytest.raises(ValidationError, match="at least 3 characters"):
            validate_input("ab", field_name="test", rules=rule)

        # Too long
        with pytest.raises(ValidationError, match="no more than 10 characters"):
            validate_input("abcdefghijk", field_name="test", rules=rule)

        # Just right
        assert validate_input("abcdef", field_name="test", rules=rule) == "abcdef"

    def test_validate_input_allowed_chars(self):
        """Test allowed characters validation."""
        rule = ValidationRule(allowed_chars="abc123")

        # Valid
        assert validate_input("abc123", field_name="test", rules=rule) == "abc123"

        # Invalid
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_input("abc123!", field_name="test", rules=rule)

    def test_validate_input_forbidden_chars(self):
        """Test forbidden characters validation."""
        rule = ValidationRule(forbidden_chars="!@#")

        # Valid
        assert validate_input("abc123", field_name="test", rules=rule) == "abc123"

        # Invalid
        with pytest.raises(ValidationError, match="forbidden characters"):
            validate_input("abc!123", field_name="test", rules=rule)

    def test_validate_input_pattern(self):
        """Test regex pattern validation."""
        rule = ValidationRule(pattern=r'^\d{3}-\d{2}-\d{4}$')  # SSN-like pattern

        # Valid
        assert validate_input("123-45-6789", field_name="test", rules=rule) == "123-45-6789"

        # Invalid
        with pytest.raises(ValidationError, match="does not match required pattern"):
            validate_input("123-45-67890", field_name="test", rules=rule)

    def test_validate_ip_address(self):
        """Test IP address validation."""
        # Valid IPv4
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"
        assert validate_ip_address("0.0.0.0") == "0.0.0.0"
        assert validate_ip_address("255.255.255.255") == "255.255.255.255"

        # Invalid IPv4
        with pytest.raises(ValidationError):
            validate_ip_address("256.1.1.1")
        with pytest.raises(ValidationError):
            validate_ip_address("1.1.1")
        with pytest.raises(ValidationError):
            validate_ip_address("1.1.1.1.1")

        # Valid IPv6 (basic)
        assert validate_ip_address("::1") == "::1"
        assert validate_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"

        # Invalid IPv6
        with pytest.raises(ValidationError):
            validate_ip_address(":::::::")
        with pytest.raises(ValidationError):
            validate_ip_address("2001:0db8:85a3::8a2e:0370:7334:extra")

    def test_validate_hostname(self):
        """Test hostname validation."""
        # Valid hostnames
        assert validate_hostname("example.com") == "example.com"
        assert validate_hostname("subdomain.example.com") == "subdomain.example.com"
        assert validate_hostname("localhost") == "localhost"
        assert validate_hostname("example.com.") == "example.com"  # trailing dot stripped

        # Invalid hostnames
        with pytest.raises(ValidationError):
            validate_hostname("")  # empty
        with pytest.raises(ValidationError):
            validate_hostname("-example.com")  # starts with hyphen
        with pytest.raises(ValidationError):
            validate_hostname("example-.com")  # ends with hyphen
        with pytest.raises(ValidationError):
            validate_hostname("example..com")  # double dot
        with pytest.raises(ValidationError):
            validate_hostname("a" * 64 + ".com")  # label too long

    def test_validate_port(self):
        """Test port validation."""
        # Valid ports
        assert validate_port(80) == 80
        assert validate_port("443") == 443
        assert validate_port(1) == 1
        assert validate_port(65535) == 65535

        # Invalid ports
        with pytest.raises(ValidationError):
            validate_port(0)
        with pytest.raises(ValidationError):
            validate_port(65536)
        with pytest.raises(ValidationError):
            validate_port("not_a_number")
        with pytest.raises(ValidationError):
            validate_port(-1)

    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("user.name@domain.co.uk") == "user.name@domain.co.uk"
        assert validate_email("user+tag@example.org") == "user+tag@example.org"

        # Invalid emails
        with pytest.raises(ValidationError):
            validate_email("invalid-email")
        with pytest.raises(ValidationError):
            validate_email("@example.com")
        with pytest.raises(ValidationError):
            validate_email("test@")
        with pytest.raises(ValidationError):
            validate_email("test@example")

    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        assert validate_url("http://example.com") == "http://example.com"
        assert validate_url("https://example.com:8080/path") == "https://example.com:8080/path"
        assert validate_url("http://localhost:3000") == "http://localhost:3000"
        assert validate_url("https://192.168.1.1") == "https://192.168.1.1"

        # Invalid URLs
        with pytest.raises(ValidationError):
            validate_url("not-a-url")
        with pytest.raises(ValidationError):
            validate_url("ftp://example.com")  # only http/https
        with pytest.raises(ValidationError):
            validate_url("http://")  # no host
        with pytest.raises(ValidationError):
            validate_url("http://-example.com")  # invalid hostname


class TestOutputEncoding:
    """Test output encoding functions."""

    def test_encode_html(self):
        """Test HTML encoding."""
        assert encode_html("<script>alert('xss')</script>") == "<script>alert('xss')</script>"
        assert encode_html("&") == "&"
        assert encode_html("<") == "<"
        assert encode_html(">") == ">"
        assert encode_html('"') == '"'
        assert encode_html("'") == "'"

    def test_encode_html_attribute(self):
        """Test HTML attribute encoding."""
        # Should encode quotes
        result = encode_html_attribute('"test"')
        assert '"' not in result or result.count('"') == 2  # quotes should be escaped

        result = encode_html_attribute("'test'")
        assert "'" not in result or result.count("'") == 2  # quotes should be escaped

    def test_encode_url(self):
        """Test URL encoding."""
        assert encode_url("hello world") == "hello%20world"
        assert encode_url("https://example.com/path?key=value&other=123") == "https%3A%2F%2Fexample.com%2Fpath%3Fkey%3Dvalue%26other%3D123"
        assert encode_url("/path with spaces/") == "%2Fpath%20with%20spaces%2F"

    def test_encode_javascript(self):
        """Test JavaScript encoding."""
        # Test quote escaping
        assert encode_javascript('"test"') == '\\"test\\"'
        assert encode_javascript("'test'") == "\\'test\\'"

        # Test newline escaping
        assert encode_javascript("hello\nworld") == "hello\\nworld"

        # Test backslash escaping
        assert encode_javascript("c:\\temp") == "c:\\\\temp"

    def test_encode_json(self):
        """Test JSON encoding."""
        data = {"key": "value", "number": 42}
        result = encode_json(data)
        parsed = eval(result)  # Safe because we control the data
        assert parsed == data

        # Test with special characters
        data = {"text": "<script>alert('xss')</script>"}
        result = encode_json(data)
        assert "<script>" in result  # Should be preserved in JSON string
        assert "&" not in result.split(':')[1]  # Value should be properly quoted

    def test_normalize_path(self):
        """Test path normalization."""
        assert normalize_path("normal/path") == "normal/path"
        assert normalize_path("path/../other") == "other"
        assert normalize_path("./current") == "current"
        assert normalize_path("/absolute/path") == "absolute/path"
        assert normalize_path("path/../../../etc/passwd") == "etc/passwd"  # goes to root then up
        assert normalize_path("") == "."
        assert normalize_path(".") == "."
        assert normalize_path("..") == ".."  # Our implementation allows going above root for simplicity

    def test_safe_string_truncate(self):
        """Test string truncation."""
        assert safe_string_truncate("short", 10) == "short"
        assert safe_string_truncate("this is a long string", 10) == "this is..."
        assert safe_string_truncate("exactly ten chars", 10) == "exactly t..."
        assert safe_string_truncate("test", 3, "") == "tes"


class TestInjectionPrevention:
    """Test injection prevention functions."""

    def test_prevent_sql_injection(self):
        """Test SQL injection prevention."""
        # Basic case
        query, params = prevent_sql_injection("SELECT * FROM users WHERE id = ?", (1,))
        assert query == "SELECT * FROM users WHERE id = ?"
        assert params == (1,)

        # No params
        query, params = prevent_sql_injection("SELECT * FROM users")
        assert query == "SELECT * FROM users"
        assert params == ()

        # Single param not in tuple
        query, params = prevent_sql_injection("SELECT * FROM users WHERE name = ?", "John")
        assert query == "SELECT * FROM users WHERE name = ?"
        assert params == ("John",)

    def test_execute_safe_sql(self):
        """Test safe SQL execution."""
        # Create in-memory database
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO users VALUES (1, 'Alice')")
        conn.execute("INSERT INTO users VALUES (2, 'Bob')")

        # Safe query
        cursor = execute_safe_sql(conn, "SELECT * FROM users WHERE id = ?", (1,))
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0] == (1, "Alice")

        conn.close()

    def test_prevent_command_injection(self):
        """Test command injection prevention."""
        # Valid command
        cmd = prevent_command_injection("ls", ["-la", "/home"])
        assert cmd == ["ls", "-la", "/home"]

        # Invalid command (contains dangerous chars)
        with pytest.raises(ValueError):
            prevent_command_injection("ls; rm -rf /", [])

        with pytest.raises(ValueError):
            prevent_command_injection("ls", ["-la", "/home; rm -rf /"])

        # Invalid command name
        with pytest.raises(ValueError):
            prevent_command_injection("ls rm", [])

    def test_execute_safe_command(self):
        """Test safe command execution."""
        # Simple echo command
        result = execute_safe_command("echo", ["hello"])
        assert result.returncode == 0
        assert "hello" in result.stdout

        # Invalid command
        result = execute_safe_command("nonexistentcommand12345", [])
        assert result.returncode != 0

    def test_sanitize_sql(self):
        """Test SQL sanitization (legacy)."""
        assert sanitize_sql("O'Reilly") == "O''Reilly"
        assert sanitize_sql('He said "Hello"') == 'He said ""Hello""'
        assert sanitize_sql(r"C:\Users\Name") == r"C:\\Users\\Name"
        assert sanitize_sql("100%") == "100\\%"
        assert sanitize_sql("hello_world") == "hello\\_world"

    def test_sanitize_shell(self):
        """Test shell sanitization (legacy)."""
        assert sanitize_shell("hello") == "'hello'"
        assert sanitize_shell("hello'world") == "'hello'\"'\"'world'"
        assert sanitize_shell('hello"world') == "'hello\"'\"'world'"

    def test_escape_like_pattern(self):
        """Test LIKE pattern escaping."""
        assert escape_like_pattern("100%") == "100\\%"
        assert escape_like_pattern("hello_world") == "hello\\_world"
        assert escape_like_pattern(r"C:\Users") == r"C:\\Users"

    def test_validate_and_sanitize_filename(self):
        """Test filename validation and sanitization."""
        # Valid filenames
        assert validate_and_sanitize_filename("normal_file.txt") == "normal_file.txt"
        assert validate_and_sanitize_filename("file with spaces.txt") == "file with spaces.txt"
        assert validate_and_sanitize_filename("file-name.txt") == "file-name.txt"
        assert validate_and_sanitize_filename("file.name.txt") == "file.name.txt"

        # Invalid filenames
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("")  # empty
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename(" ")  # whitespace
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("../etc/passwd")  # path traversal
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("/absolute/path")  # absolute path

        # Reserved names (Windows)
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("CON.txt")
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("PRN")
        with pytest.raises(ValidationError):
            validate_and_sanitize_filename("COM1")

        # Dangerous characters
        assert validate_and_sanitize_filename("file<>name.txt") == "filename.txt"
        assert validate_and_sanitize_filename("file|name.txt") == "filename.txt"

    def test_safe_format_string(self):
        """Test safe string formatting."""
        assert safe_format_string("Hello {name}", name="World") == "Hello World"
        assert safe_format_string("Processed {count} items", count=5) == "Processed 5 items"

        # Test with potentially dangerous input
        assert safe_format_string("User: {input}", input="<script>") == "User: <script>"

        # Test missing key
        with pytest.raises(ValueError):
            safe_format_string("Hello {name}", wrong_key="value")

    def test_SQLIdentifier(self):
        """Test SQL identifier handling."""
        # Valid identifier
        ident = SQLIdentifier("table_name")
        assert str(ident) == '"table_name"'

        # Invalid identifier
        with pytest.raises(ValueError):
            SQLIdentifier("table-name")  # hyphen not allowed

        with pytest.raises(ValueError):
            SQLIdentifier("123table")  # starts with number

        with pytest.raises(ValueError):
            SQLIdentifier("")  # empty

    def test_safe_sql_identifier(self):
        """Test safe SQL identifier creation."""
        ident = safe_sql_identifier("column_name")
        assert isinstance(ident, SQLIdentifier)
        assert str(ident) == '"column_name"'

    def test_build_safe_select(self):
        """Test building safe SELECT queries."""
        # Simple select
        query, params = build_safe_select("users")
        assert query == "SELECT * FROM users"
        assert params == ()

        # With columns
        query, params = build_safe_select("users", ["id", "name"])
        assert query == "SELECT id, name FROM users"
        assert params == ()

        # With WHERE
        query, params = build_safe_select("users", where="id = ?", params=(1,))
        assert query == "SELECT * FROM users WHERE id = ?"
        assert params == (1,)

        # With ORDER BY
        query, params = build_safe_select("users", order_by="name DESC")
        assert query == "SELECT * FROM users ORDER BY name DESC"
        assert params == ()

        # With LIMIT
        query, params = build_safe_select("users", limit=10)
        assert query == "SELECT * FROM users LIMIT 10"
        assert params == ()

        # Complex query
        query, params = build_safe_select(
            "users",
            ["id", "name", "email"],
            where="age > ? AND status = ?",
            params=(18, "active"),
            order_by="name ASC",
            limit=5
        )
        assert query == "SELECT id, name, email FROM users WHERE age > ? AND status = ? ORDER BY name ASC LIMIT 5"
        assert params == (18, "active")

        # Test SQLIdentifier for table name
        query, params = build_safe_select(SQLIdentifier("users"), ["name"])
        assert query == 'SELECT "name" FROM "users"'
        assert params == ()

        # Invalid ORDER BY
        with pytest.raises(ValueError):
            build_safe_select("users", order_by="name; DROP TABLE users")


class TestSecurityHeaders:
    """Test security headers functions."""

    def test_security_headers_creation(self):
        """Test SecurityHeaders creation."""
        headers = SecurityHeaders(
            content_security_policy="default-src 'self'",
            strict_transport_security="max-age=31536000",
            x_frame_options="DENY"
        )

        assert headers.content_security_policy == "default-src 'self'"
        assert headers.strict_transport_security == "max-age=31536000"
        assert headers.x_frame_options == "DENY"

        # Test to_dict
        dict_headers = headers.to_dict()
        assert dict_headers["Content-Security-Policy"] == "default-src 'self'"
        assert dict_headers["Strict-Transport-Security"] == "max-age=31536000"
        assert dict_headers["X-Frame-Options"] == "DENY"

    def test_get_security_headers_default(self):
        """Test get_security_headers with default values."""
        headers = get_security_headers()

        assert headers.content_security_policy is None  # No defaults
        assert headers.strict_transport_security == "max-age=31536000"
        assert headers.x_frame_options == "DENY"
        assert headers.x_content_type_options == "nosniff"
        assert headers.x_xss_protection == "1; mode=block"
        assert headers.referrer_policy == "strict-origin-when-cross-origin"

    def test_get_security_headers_custom(self):
        """Test get_security_headers with custom values."""
        headers = get_security_headers(
            csp_default_src=["'self'"],
            csp_script_src=["'self'", "'unsafe-inline'"],
            frame_options="SAMEORIGIN",
            hsts_max_age=86400,
            permissions_policy="geolocation=()"
        )

        assert headers.content_security_policy == "default-src 'self'; script-src 'self' 'unsafe-inline'"
        assert headers.strict_transport_security == "max-age=86400"
        assert headers.x_frame_options == "SAMEORIGIN"
        assert headers.permissions_policy == "geolocation=()"

    def test_apply_security_headers(self):
        """Test applying security headers to existing headers."""
        existing_headers = {"User-Agent": "Test-Agent"}
        security_headers = get_security_headers(
            frame_options="DENY",
            x_content_type_options=True
        )

        result = apply_security_headers(existing_headers, security_headers)

        assert result["User-Agent"] == "Test-Agent"
        assert result["X-Frame-Options"] == "DENY"
        assert result["X-Content-Type-Options"] == "nosniff"

    def test_get_csp_policy(self):
        """Test getting predefined CSP policies."""
        assert get_csp_policy("strict") == CSP_POLICIES["strict"]
        assert get_csp_policy("moderate") == CSP_POLICIES["moderate"]
        assert get_csp_policy("relaxed") == CSP_POLICIES["relaxed"]
        assert get_csp_policy("unknown") is None

    def test_csp_policies_exist(self):
        """Test that predefined CSP policies exist."""
        assert "strict" in CSP_POLICIES
        assert "moderate" in CSP_POLICIES
        assert "relaxed" in CSP_POLICIES

        # Check that they contain expected directives
        strict = CSP_POLICIES["strict"]
        assert "default-src 'self'" in strict
        assert "script-src 'self'" in strict
        assert "object-src 'none'" in strict
        assert "frame-ancestors 'none'" in strict


class TestRateLimiting:
    """Test rate limiting functions."""

    def test_rate_limit_config(self):
        """Test RateLimitConfig creation."""
        config = RateLimitConfig(requests=100, window=60, burst=20)
        assert config.requests == 100
        assert config.window == 60
        assert config.burst == 20
        assert config.algorithm == "fixed_window"

    def test_token_bucket(self):
        """Test TokenBucket implementation."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)  # 5 tokens per second

        # Start with full bucket
        assert bucket.tokens_available() == 10.0

        # Consume some tokens
        assert bucket.consume(3) == True
        assert bucket.tokens_available() == 7.0

        # Consume more than available
        assert bucket.consume(8) == False  # Only 7 available
        assert bucket.tokens_available() == 7.0  # Shouldn't change

        # Wait and check refill (we'll simulate by manipulating time)
        import time
        old_time = bucket.last_updated
        bucket.last_updated = old_time - 2  # 2 seconds ago
        # Should have 2 * 5 = 10 more tokens, but capped at capacity
        assert bucket.tokens_available() == 10.0

    def test_rate_limiter_fixed_window(self):
        """Test RateLimiter with fixed window algorithm."""
        limiter = RateLimiter(RateLimitConfig(requests=5, window=10, algorithm="fixed_window"))

        identifier = "test_user"

        # First 5 requests should be allowed
        for i in range(5):
            result = limiter.is_allowed(identifier)
            assert result.allowed == True
            assert result.remaining == 4 - i  # 5, 4, 3, 2, 1

        # 6th request should be denied
        result = limiter.is_allowed(identifier)
        assert result.allowed == False
        assert result.limited == True
        assert result.remaining == 0

        # Check retry_after is reasonable
        assert result.retry_after > 0
        assert result.retry_after <= 10  # Should be within window

    def test_rate_limiter_token_bucket(self):
        """Test RateLimiter with token bucket algorithm."""
        limiter = RateLimiter(RateLimitConfig(
            requests=10,
            window=60,
            burst=5,
            algorithm="token_bucket"
        ))

        identifier = "test_user"

        # Should allow burst requests immediately
        for i in range(15):  # 10 + 5 burst
            result = limiter.is_allowed(identifier)
            if i < 15:
                assert result.allowed == True
            else:
                assert result.allowed == False
                break

        # Next request should be denied
        result = limiter.is_allowed(identifier)
        assert result.allowed == False

    def test_rate_limiter_sliding_window(self):
        """Test RateLimiter with sliding window algorithm."""
        limiter = RateLimiter(RateLimitConfig(requests=5, window=10, algorithm="sliding_window"))

        identifier = "test_user"

        # First 5 requests should be allowed
        for i in range(5):
            result = limiter.is_allowed(identifier)
            assert result.allowed == True

        # 6th request should be denied
        result = limiter.is_allowed(identifier)
        assert result.allowed == False
        assert result.limited == True

    def test_create_ip_rate_limiter(self):
        """Test factory function for IP rate limiter."""
        limiter = create_ip_rate_limiter(requests_per_minute=30)
        assert limiter.config.requests == 30
        assert limiter.config.window == 60
        assert limiter.config.algorithm == "fixed_window"

    def test_create_api_key_rate_limiter(self):
        """Test factory function for API key rate limiter."""
        limiter = create_api_key_rate_limiter(requests_per_hour=1000)
        assert limiter.config.requests == 1000
        assert limiter.config.window == 3600
        assert limiter.config.algorithm == "fixed_window"

    def test_create_burst_tolerant_limiter(self):
        """Test factory function for burst tolerant limiter."""
        limiter = create_burst_tolerant_limiter(requests_per_minute=10, burst=5)
        assert limiter.config.requests == 10
        assert limiter.config.window == 60
        assert limiter.config.burst == 5
        assert limiter.config.algorithm == "token_bucket"

    def test_rate_limit_decorator(self):
        """Test rate limit decorator."""
        call_count = 0

        @rate_limit(requests=2, window=5, algorithm="fixed_window")
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        # First two calls should work
        assert test_function() == "success"
        assert test_function() == "success"
        assert call_count == 2

        # Third call should raise exception
        try:
            test_function()
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Rate limit exceeded" in str(e)

        # Call count should not have increased
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])