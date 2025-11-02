"""Security utilities for the Weather Application.

This module provides secure storage for API keys using the system's keyring
and sensitive data masking for logging.
"""

import logging
import re
from typing import Dict, Optional

import keyring
from keyring.errors import KeyringError


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class KeyringUnavailableError(SecurityError):
    """Raised when the system keyring is not available."""

    pass


class SensitiveDataFilter(logging.Filter):
    """Logging filter that masks sensitive information.

    Masks API keys, passwords, and other sensitive data in log messages.
    """

    def __init__(self, name: str = ""):
        """Initialize the sensitive data filter.

        Args:
            name: Filter name

        """
        super().__init__(name)
        # Patterns to match sensitive data
        self.sensitive_patterns = [
            r"(?i)(api[_-]?key)[\s\"\']*[=:][\s\"\']*([^\s\"\']+)",
            r"(?i)(password)[\s\"\']*[=:][\s\"\']*([^\s\"\']+)",
            r"(?i)(token)[\s\"\']*[=:][\s\"\']*([^\s\"\']+)",
            r"(?i)(secret)[\s\"\']*[=:][\s\"\']*([^\s\"\']+)",
            r"[a-fA-F0-9]{32}",  # MD5-like hashes
            r"[a-fA-F0-9]{40}",  # SHA-1-like hashes
            r"[a-fA-F0-9]{64}",  # SHA-256-like hashes
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to mask sensitive data."""
        if hasattr(record, "msg") and record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))

        if hasattr(record, "args") and record.args:
            # Convert args to string and mask sensitive data
            masked_args: list[object] = []
            for arg in record.args:
                if isinstance(arg, str):
                    masked_args.append(self._mask_sensitive_data(arg))
                else:
                    masked_args.append(arg)
            record.args = tuple(masked_args)

        return True

    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in text."""
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, self._mask_replacer, text)
        return text

    def _mask_replacer(self, match: re.Match) -> str:
        """Replace matched sensitive data with masked version."""
        full_match = match.group(0)

        # If it's a key-value pair, mask just the value
        if "=" in full_match or ":" in full_match:
            parts = re.split(r"[=:]", full_match, 1)
            if len(parts) == 2:
                key_part = parts[0].strip()
                value_part = parts[1].strip()
                # Keep first 4 and last 4 characters of the value
                if len(value_part) > 8:
                    masked_value = f"{value_part[:4]}...{value_part[-4:]}"
                else:
                    masked_value = "***"
                return f"{key_part}={masked_value}"

        # For other patterns, mask the entire match
        if len(full_match) > 8:
            return f"{full_match[:4]}...{full_match[-4:]}"
        else:
            return "***"


class SecureConfig:
    """Secure configuration manager that uses keyring for sensitive data."""

    SERVICE_NAME = "weather-app"

    def __init__(self):
        """Initialize the secure configuration manager."""
        self._keyring_available = self._check_keyring_availability()

    def _check_keyring_availability(self) -> bool:
        """Check if keyring is available on this system."""
        try:
            # Try to set and get a test value
            test_key = "test_availability"
            test_value = "test_value"
            keyring.set_password(self.SERVICE_NAME, test_key, test_value)
            retrieved = keyring.get_password(self.SERVICE_NAME, test_key)
            keyring.delete_password(self.SERVICE_NAME, test_key)
            return retrieved == test_value
        except (KeyringError, PermissionError, OSError, ImportError):
            return False

    def is_keyring_available(self) -> bool:
        """Return whether keyring is available on this system."""
        return self._keyring_available

    def store_api_key(self, api_key: str, service_name: str = "openweathermap") -> None:
        """Store an API key securely using keyring.

        Args:
            api_key: The API key to store
            service_name: Name of the service (used as keyring key)

        Raises:
            KeyringUnavailableError: If keyring is not available
            ValueError: If API key is empty or invalid

        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        if not self._keyring_available:
            raise KeyringUnavailableError(
                "System keyring is not available. Please use environment variables or config files."
            )

        try:
            keyring.set_password(self.SERVICE_NAME, service_name, api_key)
        except Exception as e:
            raise SecurityError(f"Failed to store API key: {e}") from e

    def get_api_key(self, service_name: str = "openweathermap") -> Optional[str]:
        """Retrieve an API key from secure storage.

        Args:
            service_name: Name of the service to retrieve key for

        Returns:
            The API key if found, None otherwise

        Raises:
            KeyringUnavailableError: If keyring is not available

        """
        if not self._keyring_available:
            raise KeyringUnavailableError("System keyring is not available")

        try:
            return keyring.get_password(self.SERVICE_NAME, service_name)
        except (KeyringError, PermissionError, OSError) as e:
            raise SecurityError(f"Failed to retrieve API key: {e}") from e

    def delete_api_key(self, service_name: str = "openweathermap") -> None:
        """Delete an API key from secure storage.

        Args:
            service_name: Name of the service to delete key for

        Raises:
            KeyringUnavailableError: If keyring is not available

        """
        if not self._keyring_available:
            raise KeyringUnavailableError("System keyring is not available")

        try:
            keyring.delete_password(self.SERVICE_NAME, service_name)
        except (KeyringError, PermissionError, OSError) as e:
            raise SecurityError(f"Failed to delete API key: {e}") from e

    def list_stored_keys(self) -> Dict[str, str]:
        """List all stored API keys (returns masked versions for security).

        Returns:
            Dictionary of service names to masked API keys

        Raises:
            KeyringUnavailableError: If keyring is not available

        """
        if not self._keyring_available:
            raise KeyringUnavailableError("System keyring is not available")

        # Note: keyring doesn't have a built-in way to list all keys for a service
        # This is a limitation of the keyring API
        return {}


def setup_secure_logging() -> None:
    """Set up secure logging with sensitive data filtering.

    This should be called early in the application startup.
    """
    # Add sensitive data filter to all existing loggers
    sensitive_filter = SensitiveDataFilter()

    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        # Don't add duplicate filters
        if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
            logger.addFilter(sensitive_filter)

    # Also add to root logger
    root_logger = logging.getLogger()
    if not any(isinstance(f, SensitiveDataFilter) for f in root_logger.filters):
        root_logger.addFilter(sensitive_filter)


def mask_sensitive_string(text: str) -> str:
    """Mask sensitive information in a string for safe display.

    Args:
        text: The text containing potentially sensitive information

    Returns:
        Text with sensitive information masked

    """
    filter = SensitiveDataFilter()
    return filter._mask_sensitive_data(text)
