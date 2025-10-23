"""Configuration handling for the Weather Application."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from .exceptions import APIKeyError
from .security import SecureConfig, KeyringUnavailableError


class Config:
    """Handles application configuration and environment variables."""

    def __init__(self):
        """Initialize configuration with multiple config file support."""
        self._load_environment_variables()

        # Initialize secure config for API key storage
        self._secure = SecureConfig()

        # Try keyring first, fall back to environment variable
        try:
            self._api_key = self._secure.get_api_key()
            if self._api_key:
                print("🔑 API key loaded from secure keyring storage")
            else:
                self._api_key = os.getenv("OWM_API_KEY")
        except KeyringUnavailableError:
            self._api_key = os.getenv("OWM_API_KEY")

        self._units = os.getenv("OWM_UNITS", "metric")
        self._cache_ttl = int(os.getenv("CACHE_TTL", "600"))  # Default 10 minutes
        self._request_timeout = int(
            os.getenv("REQUEST_TIMEOUT", "30")
        )  # Default 30 seconds
        self._use_async = os.getenv("USE_ASYNC", "true").lower() == "true"
        self._log_level = os.getenv("LOG_LEVEL", "INFO")
        self._log_file = os.getenv("LOG_FILE")
        self._log_format = os.getenv("LOG_FORMAT", "text").lower()
        self._cache_persist = os.getenv("CACHE_PERSIST", "false").lower() == "true"
        self._cache_file = os.getenv("CACHE_FILE", "~/.weather_app_cache.json")

    def _load_environment_variables(self) -> None:
        """Load environment variables from multiple potential config files."""
        config_locations = [
            ".weather.env",  # Project directory
            "~/.weather.env",  # User home directory
            "/etc/weather_app/.env",  # System-wide configuration
        ]

        for location in config_locations:
            try:
                config_path = Path(location).expanduser()
                if config_path.exists():
                    load_dotenv(dotenv_path=config_path, override=False)

                    break
            except (IOError, PermissionError):
                continue

        # Also load from environment variables (they take precedence)
        load_dotenv(override=True)

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set the API key with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("API key must be a non-empty string")
        self._api_key = value

    @property
    def units(self) -> str:
        """Get the measurement units."""
        return self._units

    @property
    def cache_ttl(self) -> int:
        """Get the cache TTL in seconds."""
        return self._cache_ttl

    @property
    def request_timeout(self) -> int:
        """Get the request timeout in seconds."""
        return self._request_timeout

    @property
    def use_async(self) -> bool:
        """Get whether to use async mode."""
        return self._use_async

    @property
    def log_level(self) -> str:
        """Get the log level."""
        return self._log_level

    @property
    def log_file(self) -> Optional[str]:
        """Get the log file path."""
        return self._log_file

    @property
    def log_format(self) -> str:
        """Get the log format (text or json)."""
        return self._log_format

    @property
    def cache_persist(self) -> bool:
        """Get whether to persist cache to disk."""
        return self._cache_persist

    @property
    def cache_file(self) -> str:
        """Get the cache file path."""
        return self._cache_file

    def store_api_key(self, api_key: str) -> None:
        """Store API key securely in keyring.

        Args:
            api_key: The API key to store

        Raises:
            KeyringUnavailableError: If keyring is not available
            ValueError: If API key is empty or invalid

        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        self._secure.store_api_key(api_key)
        self._api_key = api_key
        print("🔑 API key stored securely in keyring")

    def is_keyring_available(self) -> bool:
        """Check if keyring storage is available on this system."""
        return self._secure.is_keyring_available()

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.api_key:
            keyring_available = self.is_keyring_available()
            error_message = (
                "API key not found. Please set OWM_API_KEY environment variable."
            )
            if keyring_available:
                error_message += (
                    "\nAlternatively, you can store your API key securely in keyring "
                    "using the store_api_key() method."
                )
            else:
                error_message += (
                    "\nNote: Secure keyring storage is not available on this system."
                )
            raise APIKeyError(error_message)
