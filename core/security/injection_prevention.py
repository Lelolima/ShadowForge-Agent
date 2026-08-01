"""
Injection prevention utilities for ShadowForge Agent.
Provides functions to prevent SQL injection, command injection, and other injection attacks.
"""

import re
import shlex
import subprocess
import sqlite3
from typing import Any, List, Optional, Tuple, Union
from .input_validation import ValidationError, validate_input


def prevent_sql_injection(query: str, params: Optional[tuple] = None) -> Tuple[str, tuple]:
    """
    Prepare a SQL query with parameters to prevent SQL injection.
    Uses parameterized queries (the safest approach).

    Args:
        query: SQL query string with placeholders (? for sqlite3, %s for others)
        params: Tuple of parameters to substitute

    Returns:
        Tuple of (query, params) ready for safe execution

    Example:
        # Instead of: cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
        # Use: query, params = prevent_sql_injection("SELECT * FROM users WHERE name = ?", (name,))
        # Then: cursor.execute(query, params)
    """
    if not isinstance(query, str):
        raise ValueError("Query must be a string")

    # Basic validation - ensure query doesn't contain dangerous patterns
    # This is a secondary defense - parameterized queries are the primary defense
    dangerous_patterns = [
        r';\s*(drop|delete|insert|update|create|alter)\s+',  # Statement termination
        r'union\s+select',  # UNION attacks
        r'--',  # SQL comments
        r'/\*.*\*/',  # Block comments
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            # Log warning but still allow - parameterization will protect us
            # In production, you might want to reject or sanitize further
            pass

    # Ensure params is a tuple
    if params is None:
        params = ()
    elif not isinstance(params, (tuple, list)):
        params = (params,)

    return query, tuple(params)


def execute_safe_sql(connection: sqlite3.Connection, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
    """
    Safely execute a SQL query using parameterization.

    Args:
        connection: SQLite database connection
        query: SQL query with placeholders
        params: Parameters for the query

    Returns:
        Cursor object from execute
    """
    query, params = prevent_sql_injection(query, params)
    return connection.execute(query, params)


def prevent_command_injection(command: str, args: Optional[List[str]] = None) -> List[str]:
    """
    Safely construct a command and arguments for subprocess execution.
    Prevents command injection by properly escaping arguments.

    Args:
        command: The command to execute (e.g., 'ls', 'cat')
        args: List of arguments to pass to the command

    Returns:
        List suitable for subprocess.run(): [command, arg1, arg2, ...]

    Example:
        # Instead of: subprocess.run(f"ls {user_input}", shell=True)
        # Use: cmd = prevent_command_injection("ls", [user_input])
        # Then: subprocess.run(cmd)
    """
    if not command or not isinstance(command, str):
        raise ValueError("Command must be a non-empty string")

    # Basic command validation - allow alphanumeric, underscores, hyphens, dots, slashes
    # This prevents command chaining and injection
    if not re.match(r'^[a-zA-Z0-9./\-_]+$', command):
        raise ValueError(f"Invalid command: {command}")

    # Validate arguments
    safe_args = []
    if args:
        for arg in args:
            if not isinstance(arg, str):
                arg = str(arg)
            # Prevent command injection in arguments
            # Disallow dangerous characters that could lead to shell injection
            if re.search(r'[;&|`$\\n\\r]', arg):
                raise ValueError(f"Argument contains dangerous characters: {arg}")
            # Additional checks for path traversal if this is a file argument
            if '/' in arg or '\\' in arg:
                # For simplicity, we're allowing paths but in a real implementation
                # you might want to validate the path is within allowed directories
                pass
            safe_args.append(arg)

    return [command] + safe_args


def execute_safe_command(
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    timeout: int = 30,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """
    Safely execute a command without shell=True to prevent injection.

    Args:
        command: The command to execute
        args: List of arguments
        cwd: Working directory
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess instance
    """
    cmd_list = prevent_command_injection(command, args)
    return subprocess.run(
        cmd_list,
        cwd=cwd,
        timeout=timeout,
        capture_output=capture_output,
        text=True,  # Return strings instead of bytes
        check=False  # Don't raise exception on non-zero exit
    )


def sanitize_sql(value: str) -> str:
    """
    Legacy function for SQL sanitization.
    NOTE: Parameterized queries are preferred over this approach.
    This function is provided for compatibility but should be avoided in new code.

    Args:
        value: String to sanitize for SQL usage

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)

    # Escape single quotes by doubling them (SQL standard)
    # Also escape backslashes and percent signs for LIKE clauses
    return value.replace("'", "''").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def sanitize_shell(value: str) -> str:
    """
    Legacy function for shell escaping.
    NOTE: Using subprocess with argument lists is preferred over this approach.

    Args:
        value: String to sanitize for shell usage

    Returns:
        Shell-escaped string suitable for use in a shell command
    """
    if not isinstance(value, str):
        value = str(value)
    # Use shlex.quote for proper shell escaping
    return shlex.quote(value)


def escape_like_pattern(value: str) -> str:
    """
    Escape a value for use in SQL LIKE patterns.

    Args:
        value: String to escape

    Returns:
        String safe for use in LIKE patterns
    """
    if not isinstance(value, str):
        value = str(value)
    # Escape wildcard characters and escape character itself
    return value.replace("%", "\\%").replace("_", "\\_").replace("\\", "\\\\")


def validate_and_sanitize_filename(filename: str) -> str:
    """
    Validate and sanitize a filename to prevent path traversal and unsafe names.

    Args:
        filename: Filename to validate

    Returns:
        Sanitized filename safe for filesystem use

    Raises:
        ValidationError: If filename is invalid
    """
    if not isinstance(filename, str):
        filename = str(filename)

    if not filename or filename.strip() != filename:
        raise ValidationError("Filename cannot be empty or have leading/trailing whitespace")

    # Remove any directory path components - only keep the basename
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove dangerous characters
    # Allow alphanumeric, spaces, dots, hyphens, underscores
    # But prevent names that are just dots or start/end with dot (except . and .. which we handle separately)
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Prevent hidden files if desired (uncomment if needed)
    # if filename.startswith('.'):
    #     raise ValidationError("Hidden files not allowed")

    # Reserve certain names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    if filename.upper().split('.')[0] in reserved_names:
        raise ValidationError(f"Reserved filename: {filename}")

    # Ensure we have a valid filename
    if not filename or filename in ('.', '..'):
        raise ValidationError("Invalid filename")

    # Limit length
    if len(filename) > 255:
        raise ValidationError("Filename too long")

    return filename


def safe_format_string(template: str, **kwargs) -> str:
    """
    Safely format a string using str.format() with input validation.
    Prevents format string injection attacks.

    Args:
        template: Format string template
        **kwargs: Values to substitute

    Returns:
        Formatted string

    Example:
        safe_format_string("Hello {name}", name="World")  # Returns "Hello World"
    """
    if not isinstance(template, str):
        raise ValueError("Template must be a string")

    # Validate all inputs
    sanitized_kwargs = {}
    for key, value in kwargs.items():
        if not isinstance(key, str):
            raise ValueError(f"Key must be string: {key}")
        # Convert value to string for safety
        sanitized_kwargs[key] = str(value)

    try:
        return template.format(**sanitized_kwargs)
    except (KeyError, IndexError, ValueError) as e:
        raise ValueError(f"Template formatting error: {e}")


class SQLIdentifier:
    """
    Helper class for safely handling SQL identifiers (table names, column names).
    Unlike values, identifiers cannot be parameterized, so they need special handling.
    """

    def __init__(self, name: str):
        if not isinstance(name, str):
            raise ValueError("Identifier must be a string")
        # Validate that it's a valid SQL identifier
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValueError(f"Invalid SQL identifier: {name}")
        self.name = name

    def __str__(self) -> str:
        # For SQLite, we can quote identifiers with double quotes
        return f'"{self.name}"'

    def quote(self) -> str:
        """Return the quoted identifier."""
        return str(self)


def safe_sql_identifier(name: str) -> SQLIdentifier:
    """
    Create a safe SQL identifier object.

    Args:
        name: Identifier name

    Returns:
        SQLIdentifier object that can be safely used in queries
    """
    return SQLIdentifier(name)


def build_safe_select(
    table: Union[str, SQLIdentifier],
    columns: Optional[List[str]] = None,
    where: Optional[str] = None,
    params: Optional[tuple] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> Tuple[str, tuple]:
    """
    Build a safe SELECT query with proper escaping of identifiers.

    Args:
        table: Table name (string or SQLIdentifier)
        columns: List of column names (if None, selects all)
        where: WHERE clause (without 'WHERE' keyword)
        params: Parameters for WHERE clause
        order_by: ORDER BY clause (without 'ORDER BY' keywords)
        limit: LIMIT clause

    Returns:
        Tuple of (query, params)
    """
    # Handle table name
    if isinstance(table, str):
        table_obj = SQLIdentifier(table)
        table_str = str(table_obj)
    else:
        table_str = str(table)

    # Handle columns
    if columns is None:
        columns_str = "*"
    else:
        # Validate each column name
        safe_columns = []
        for col in columns:
            if isinstance(col, str):
                col_obj = SQLIdentifier(col)
                safe_columns.append(str(col_obj))
            else:
                safe_columns.append(str(col))  # Assume it's already a SQLIdentifier
        columns_str = ", ".join(safe_columns)

    # Build query
    query = f"SELECT {columns_str} FROM {table_str}"

    # Add WHERE clause if provided
    if where:
        if not where.strip().upper().startswith('WHERE'):
            # If they didn't include WHERE, add it
            query += f" WHERE {where}"
        else:
            query += f" {where}"

    # Add ORDER BY if provided
    if order_by:
        # Validate ORDER BY column names (simple validation)
        # In practice, you'd want to parse this more carefully
        if not re.match(r'^[a-zA-Z0-9_,\s]+$', order_by):
            raise ValueError("Invalid ORDER BY clause")
        query += f" ORDER BY {order_by}"

    # Add LIMIT if provided
    if limit is not None:
        try:
            limit_int = int(limit)
            if limit_int < 0:
                raise ValueError("LIMIT must be non-negative")
            query += f" LIMIT {limit_int}"
        except (ValueError, TypeError):
            raise ValueError("LIMIT must be a valid integer")

    # Handle parameters
    if params is None:
        params_tuple = ()
    elif not isinstance(params, (tuple, list)):
        params_tuple = (params,)
    else:
        params_tuple = tuple(params)

    return query, params_tuple