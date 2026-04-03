"""CLI configuration override mechanism.

This module applies command-line argument overrides to the configuration,
ensuring the precedence: CLI > environment > YAML > keyring.
"""

import logging
from typing import Any

from weather_app.config import Config

logger = logging.getLogger(__name__)


def apply_cli_overrides(config: Config, **kwargs: Any) -> None:
    """Apply CLI argument overrides to a Config instance.

    Overrides are collected first, then applied via ``model_validate`` so that
    Pydantic validators (type coercion, boolean parsing, etc.) are invoked.

    Args:
        config: The Config instance to modify.
        **kwargs: CLI arguments mapping from argument names to values.
            Supported keys: verbose, config_file, units, use_async, no_cache.
    """
    # Load custom config file first (lowest CLI priority – explicit flags win)
    config_file = kwargs.get("config_file")
    if config_file:
        _load_custom_config_file(config, config_file)

    # Map CLI argument names to Config field names
    field_map = {
        "units": "OWM_UNITS",
        "use_async": "USE_ASYNC",
        "cache_ttl": "CACHE_TTL",
        "request_timeout": "REQUEST_TIMEOUT",
        "log_level": "LOG_LEVEL",
        "log_format": "LOG_FORMAT",
        "cache_persist": "CACHE_PERSIST",
    }

    # Collect overrides that the user actually supplied
    overrides: dict[str, Any] = {}
    for cli_key, field_name in field_map.items():
        if cli_key in kwargs and kwargs[cli_key] is not None:
            overrides[field_name] = kwargs[cli_key]

    # Special handling for verbose flag (sets log level to DEBUG)
    if kwargs.get("verbose"):
        overrides["LOG_LEVEL"] = "DEBUG"

    # Special handling for no_cache flag (disables caching)
    if kwargs.get("no_cache"):
        overrides["CACHE_TTL"] = 0

    # Apply overrides with validation via model_validate
    if overrides:
        current = config.model_dump()
        current.update(overrides)
        validated = Config.model_validate(current)
        for field_name in overrides:
            setattr(config, field_name, getattr(validated, field_name))


def _load_custom_config_file(config: Config, config_file: str) -> None:
    """Load configuration from a custom YAML file and apply to config.

    This overrides any existing YAML settings but maintains precedence:
    CLI overrides still take priority (they are applied after this).

    Args:
        config: Config instance to modify.
        config_file: Path to YAML configuration file.
    """
    from pathlib import Path

    import yaml

    path = Path(config_file).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    known_fields = set(Config.model_fields.keys())
    overrides: dict[str, Any] = {}
    for key, value in data.items():
        upper_key = key.upper()
        if upper_key in known_fields:
            overrides[upper_key] = value
        else:
            logger.warning(
                "Unknown configuration key in custom YAML '%s': '%s' (ignored)",
                config_file,
                key,
            )

    if overrides:
        current = config.model_dump()
        current.update(overrides)
        validated = Config.model_validate(current)
        for field_name in overrides:
            setattr(config, field_name, getattr(validated, field_name))
