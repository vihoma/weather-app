"""Configuration handling for the Weather Application."""

import os
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from .security import SecureConfig, KeyringUnavailableError
from .exceptions import APIKeyError, ConfigurationError


class Config:
    """Handles application configuration and environment variables."""

    def __init__(self):
        """Initialize configuration with multiple config file support."""
        self._load_environment_variables()
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

    def _load_environment_variables(self) -> None:
        """Load environment variables from multiple potential config files."""
        config_locations = [
            ".weather.env",  # Project directory
            "~/.weather.env",  # User home directory
            "/etc/weather_app/.env",  # System-wide configuration
        ]

        loaded = False
        for location in config_locations:
            try:
                config_path = Path(location).expanduser()
                if config_path.exists():
                    load_dotenv(dotenv_path=config_path, override=False)
                    loaded = True
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

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.api_key:
            raise APIKeyError(
                "API key (OWM_API_KEY) not found in environment variables "
                "or .weather.env file. Please set OWM_API_KEY environment variable."
            )
