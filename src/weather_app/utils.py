"""Utility functions for the weather application."""

import re


def sanitize_string_for_logging(text: str, max_length: int = 100) -> str:
    """
    Sanitize string for safe logging.

    Removes or escapes potentially dangerous characters that could be used
    in log injection attacks or cause log parsing issues.

    Args:
        text: Raw string to sanitize
        max_length: Maximum length before truncation (default: 100)

    Returns:
        str: Sanitized string safe for logging
    """
    if not text:
        return "[empty]"

    # Remove or escape problematic characters
    sanitized = text.strip()

    # Replace newlines and carriage returns to prevent log injection
    sanitized = sanitized.replace("\n", "\\n").replace("\r", "\\r")

    # Replace tabs
    sanitized = sanitized.replace("\t", "\\t")

    # Truncate very long strings to prevent log flooding
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate the basic format of an OpenWeatherMap API key.

    Args:
        api_key: API key string to validate

    Returns:
        bool: True if format appears valid
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # OpenWeatherMap API keys are typically 32-character hex strings
    # but this can vary, so we'll do basic length and character checks
    if len(api_key) < 16 or len(api_key) > 64:
        return False

    # Check for common invalid patterns
    if re.search(r"[\s\n\r\t]", api_key):
        return False

    return True
