"""Configuration handling for the Weather Application.

This module now uses **Pydantic** ``BaseSettings`` to load configuration from a YAML file
(`.weather.yaml` in the project root or ``$HOME/.weather.yaml``) and from environment
variables. The public API (attributes, ``store_api_key`` and ``validate``) remains
compatible with the original implementation, so existing code and tests continue
to work.

Key points:
- ``Config`` inherits from ``pydantic.BaseSettings``.
- ``customise_sources`` loads the first existing YAML file, then environment
  variables, then any explicit arguments.
- ``CACHE_FILE`` and ``LOG_FILE`` are derived automatically if not supplied.
- ``_secure`` (Keyring helper) and the legacy ``_api_key`` private attribute are
  kept for backward compatibility.
- ``_load_environment_variables`` is retained as a no‑op to keep the test
  patches functional.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import APIKeyError
from .security import KeyringUnavailableError, SecureConfig

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    """Application configuration loaded via Pydantic.

    Environment variables take precedence over values defined in a YAML file.
    Supported locations for the YAML file (the first existing file is used)::

        .weather.yaml                # project root
        $HOME/.weather.yaml          # user home directory
    """

    # ---------------------------------------------------------------------
    # Raw configuration values – names match the historic environment vars
    # ---------------------------------------------------------------------
    OWM_API_KEY: Optional[str] = Field(default=None, env="OWM_API_KEY")
    OWM_UNITS: str = Field(default="metric", env="OWM_UNITS")
    CACHE_TTL: int = Field(default=600, env="CACHE_TTL")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    USE_ASYNC: bool = Field(default=True, env="USE_ASYNC")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="text", env="LOG_FORMAT")
    CACHE_DIR: str = Field(
        default_factory=lambda: (
            os.getenv("CACHE_DIR")
            or os.path.join(os.getenv("HOME", ""), ".cache", "weather_app")
        ),
        env="CACHE_DIR" or os.getenv("TEMP"),
    )
    CACHE_FILE: Optional[str] = Field(default=None, env="CACHE_FILE")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    CACHE_PERSIST: bool = Field(default=False, env="CACHE_PERSIST")

    # ---------------------------------------------------------------------
    # Compatibility helpers (private attributes used by the legacy API)
    # ---------------------------------------------------------------------
    _secure: SecureConfig | None = None
    _api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=None, extra="allow")

    # ---------------------------------------------------------------------
    # Custom source order – YAML first, then environment variables, then explicit init data
    # ---------------------------------------------------------------------
    @classmethod
    def customise_sources(cls, init_settings, env_settings, file_secret_settings):
        import sys

        print(f"[DEBUG] customise_sources called for {cls.__name__}", file=sys.stderr)
        return (
            cls._yaml_settings_source,
            cls._env_file_settings_source,
            env_settings,
            init_settings,
        )

    @classmethod
    def _yaml_settings_source(cls, settings: BaseSettings) -> Dict[str, Any]:
        """Load configuration from the first existing ``.weather.yaml`` file.

        The function returns a dictionary that Pydantic will treat as if the values
        were passed directly to the model constructor.
        """
        locations = [
            Path(".weather.yaml").expanduser(),
            Path(os.getenv("HOME", "")).expanduser() / ".weather.yaml",
        ]
        for path in locations:
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                # Normalise keys to the upper‑case style used by the model
                return {k.upper(): v for k, v in data.items()}
        return {}

    @classmethod
    def _env_file_settings_source(cls, settings: BaseSettings) -> Dict[str, Any]:
        """Load configuration from the first existing ``.weather.env`` file using python-dotenv."""
        import sys

        print("[DEBUG] _env_file_settings_source called, locations:", file=sys.stderr)
        locations = [
            Path(".weather.env").expanduser(),
            Path(os.getenv("HOME", "")).expanduser() / ".weather.env",
        ]
        for i, path in enumerate(locations):
            print(f"[DEBUG]   Checking location {i}: {path}", file=sys.stderr)
            if path.is_file():
                print(f"[DEBUG]   File exists, loading dotenv: {path}", file=sys.stderr)
                # Load env vars from the file
                load_dotenv(dotenv_path=path, override=False)
                # Once loaded, break – env_settings will pick them up
                break
        return {}

    # ---------------------------------------------------------------------
    # Validators for derived defaults (CACHE_FILE and LOG_FILE)
    # ---------------------------------------------------------------------
    @field_validator("USE_ASYNC", "CACHE_PERSIST", mode="before")
    def _parse_bool(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)

    @field_validator("CACHE_FILE", mode="before")
    def _default_cache_file(cls, v: Optional[str], info: Any) -> str:
        if v:
            return v
        cache_dir = info.data.get("CACHE_DIR")
        return os.path.join(cache_dir, "weather_app_cache.json")

    @field_validator("LOG_FILE", mode="before")
    def _default_log_file(cls, v: Optional[str], info: Any) -> str:
        if v:
            return v
        cache_dir = info.data.get("CACHE_DIR")
        fmt = info.data.get("LOG_FORMAT", "text").lower()
        filename = "weather_app.log.json" if fmt == "json" else "weather_app.log"
        return os.path.join(cache_dir, filename)

    # ---------------------------------------------------------------------
    # Post‑initialisation – set up SecureConfig and resolve the API key
    # ---------------------------------------------------------------------
    def __init__(self, **data: Any):
        super().__init__(**data)
        # Keep legacy private attributes in sync with the Pydantic fields
        self._secure = SecureConfig()
        self._api_key = self.OWM_API_KEY
        # Prefer keyring if it contains a value; otherwise keep whatever we got
        try:
            keyring_key = self._secure.get_api_key()
            if keyring_key:
                self._api_key = keyring_key
                self.OWM_API_KEY = keyring_key
                logger.debug("🔑 API key loaded from secure keyring storage")
        except KeyringUnavailableError:
            # Keyring not available – fall back to YAML / env value
            pass

    # ---------------------------------------------------------------------
    # Public property façade – identical to the original implementation
    # ---------------------------------------------------------------------
    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("API key must be a non‑empty string")
        self._api_key = value
        self.OWM_API_KEY = value

    # Convenience lower‑case accessors expected by logging_config
    @property
    def log_level(self) -> str:
        """Return the logging level (fallback to INFO if unset)."""
        return self.LOG_LEVEL

    @property
    def log_file(self) -> Optional[str]:
        """Return the configured log file path (may be None)."""
        return self.LOG_FILE

    @property
    def log_format(self) -> str:
        """Return the logging format string (e.g., "text" or "json")."""
        return self.LOG_FORMAT

    @property
    def use_async(self) -> bool:
        """Compatibility alias for the ``USE_ASYNC`` setting.

        Returns the flag that determines whether the application runs in async mode.
        """
        return self.USE_ASYNC

    # ---------------------------------------------------------------------
    # Lower‑case read‑only accessors for all configuration fields
    # ---------------------------------------------------------------------
    @property
    def owm_api_key(self) -> Optional[str]:
        """Return the OpenWeatherMap API key (may be None)."""
        return self.OWM_API_KEY

    @property
    def owm_units(self) -> str:
        """Return the unit system used for the API (e.g., "metric" or "imperial")."""
        return self.OWM_UNITS

    @property
    def units(self) -> str:
        """Backward-compatibility alias for owm_units."""
        return self.OWM_UNITS

    @units.setter
    def units(self, value: str) -> None:
        """Allow mutation of the units through the legacy attribute."""
        self.OWM_UNITS = value

    @property
    def cache_ttl(self) -> int:
        """Return the cache time‑to‑live value (seconds)."""
        return self.CACHE_TTL

    @property
    def request_timeout(self) -> int:
        """Return the HTTP request timeout (seconds)."""
        return self.REQUEST_TIMEOUT

    @property
    def cache_dir(self) -> str:
        """Return the base directory used for cache files."""
        return self.CACHE_DIR

    @property
    def cache_file(self) -> str:
        """Return the path to the cache file."""
        # CACHE_FILE is guaranteed to be non-None after validation
        return self.CACHE_FILE if self.CACHE_FILE is not None else ""

    @property
    def cache_persist(self) -> bool:
        """Return whether the cache should be persisted across runs."""
        return self.CACHE_PERSIST

    # ---------------------------------------------------------------------
    # Compatibility helpers (store_api_key, is_keyring_available, validate)
    # ---------------------------------------------------------------------
    def store_api_key(self, api_key: str) -> None:
        """Store the API key securely via ``SecureConfig``.

        The method mirrors the original behaviour – it validates the value,
        stores it in the keyring, updates the internal ``_api_key`` attribute and
        prints a short confirmation message.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non‑empty string")
        self._secure.store_api_key(api_key)
        self.api_key = api_key
        print("🔑 API key stored securely in keyring")

    def is_keyring_available(self) -> bool:
        """Return ``True`` if the underlying keyring backend is functional."""
        return self._secure.is_keyring_available()

    def validate(self) -> None:
        """Validate that a usable API key is present.

        If the key is missing, the error message mentions the preferred
        environment variable and, when possible, suggests the key‑ring fallback.
        """
        if not self.api_key:
            keyring_available = self.is_keyring_available()
            msg = "API key not found. Please set OWM_API_KEY environment variable."
            if keyring_available:
                msg += (
                    "\nAlternatively, you can store your API key securely in keyring "
                    "using: weather --setup-api-key"
                )
            else:
                msg += "\nNote: Secure keyring storage is not available on this system."
            raise APIKeyError(msg)

    # ---------------------------------------------------------------------
    # Legacy method retained for test patches – does nothing now
    # ---------------------------------------------------------------------
    def _load_environment_variables(self) -> None:  # pragma: no cover
        """Placeholder kept for backward compatibility.

        The original implementation loaded ``.weather.env`` files.  That logic has
        been superseded by the YAML loader, but some tests still patch this
        method.  Keeping it as a no‑op ensures those patches continue to work
        without altering behaviour.
        """
        return
