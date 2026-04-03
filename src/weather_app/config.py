"""Configuration handling for the Weather Application.

This module uses **Pydantic** ``BaseSettings`` (pydantic-settings v2) to load
configuration from a YAML file (`.weather.yaml` in the project root or
``$HOME/.weather.yaml``), ``.weather.env`` files, and environment variables.
The public API (attributes, ``store_api_key`` and ``validate``) remains
compatible with the original implementation, so existing code and tests
continue to work.

Key points:
- ``Config`` inherits from ``pydantic_settings.BaseSettings``.
- ``settings_customise_sources`` (v2 API) defines the source priority:
  init args (CLI) > environment variables > ``.weather.env`` > YAML file.
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
from dotenv import dotenv_values
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import APIKeyError
from .security import KeyringUnavailableError, SecureConfig

logger = logging.getLogger(__name__)

_BOOL_TRUTHY = frozenset({"true", "yes", "1", "on"})


def _default_cache_dir() -> str:
    """Return a cross-platform default cache directory."""
    return os.path.join(os.path.expanduser("~"), ".cache", "weather_app")


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
    OWM_API_KEY: Optional[str] = Field(default=None)
    OWM_UNITS: str = Field(default="metric")
    CACHE_TTL: int = Field(default=600)
    REQUEST_TIMEOUT: int = Field(default=30)
    USE_ASYNC: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="text")
    CACHE_DIR: str = Field(default_factory=_default_cache_dir)
    CACHE_FILE: Optional[str] = Field(default=None)
    LOG_FILE: Optional[str] = Field(default=None)
    CACHE_PERSIST: bool = Field(default=False)

    # ---------------------------------------------------------------------
    # Compatibility helpers (private attributes used by the legacy API)
    # ---------------------------------------------------------------------
    _secure: SecureConfig | None = None
    _api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=None, extra="allow")

    # ---------------------------------------------------------------------
    # Custom source order (pydantic-settings v2 API)
    # Priority: init_settings (highest) > env > env_file > yaml (lowest)
    # ---------------------------------------------------------------------
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple:
        """Define configuration source priority (pydantic-settings v2).

        Returns sources ordered from highest to lowest priority:
        1. Explicit init arguments (used indirectly by CLI overrides)
        2. Environment variables
        3. .weather.env file
        4. YAML configuration file
        """
        logger.debug("settings_customise_sources called for %s", cls.__name__)
        return (
            init_settings,
            env_settings,
            cls._env_file_settings_source,
            cls._yaml_settings_source,
        )

    @classmethod
    def _yaml_settings_source(
        cls, settings: BaseSettings | None = None
    ) -> Dict[str, Any]:
        """Load configuration from the first existing ``.weather.yaml`` file.

        The function returns a dictionary that Pydantic will treat as if the values
        were passed directly to the model constructor.
        """
        locations = [Path(".weather.yaml")]
        try:
            locations.append(Path.home() / ".weather.yaml")
        except RuntimeError:
            pass
        for path in locations:
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                result: Dict[str, Any] = {}
                known_fields = set(cls.model_fields.keys())
                for k, v in data.items():
                    upper_key = k.upper()
                    if upper_key not in known_fields:
                        logger.warning(
                            "Unknown configuration key in YAML: '%s' (will be ignored)",
                            k,
                        )
                    else:
                        result[upper_key] = v
                return result
        return {}

    @classmethod
    def _env_file_settings_source(
        cls, settings: BaseSettings | None = None
    ) -> Dict[str, Any]:
        """Load configuration from the first existing ``.weather.env`` file.

        Uses ``dotenv_values`` to parse the file without mutating ``os.environ``,
        then returns the parsed values as a dictionary for Pydantic to merge.
        """
        locations = [Path(".weather.env")]
        try:
            locations.append(Path.home() / ".weather.env")
        except RuntimeError:
            pass
        for path in locations:
            logger.debug("Checking env file location: %s", path)
            try:
                if path.is_file():
                    logger.debug("Loading env file: %s", path)
                    data = dotenv_values(dotenv_path=path)
                    return {k.upper(): v for k, v in data.items() if v is not None}
            except (OSError, PermissionError) as exc:
                logger.warning("Could not read env file '%s': %s", path, exc)
        return {}

    # ---------------------------------------------------------------------
    # Validators for derived defaults (CACHE_FILE and LOG_FILE)
    # ---------------------------------------------------------------------
    @field_validator("USE_ASYNC", "CACHE_PERSIST", mode="before")
    def _parse_bool(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in _BOOL_TRUTHY
        return bool(v)

    @field_validator("CACHE_FILE", mode="before")
    def _default_cache_file(cls, v: Optional[str], info: Any) -> str:
        if v:
            return v
        cache_dir = info.data.get("CACHE_DIR") or _default_cache_dir()
        return os.path.join(cache_dir, "weather_app_cache.json")

    @field_validator("LOG_FILE", mode="before")
    def _default_log_file(cls, v: Optional[str], info: Any) -> str:
        if v:
            return v
        cache_dir = info.data.get("CACHE_DIR") or _default_cache_dir()
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
