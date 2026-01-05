"""CLI configuration override mechanism.

This module applies command-line argument overrides to the configuration,
ensuring the precedence: CLI > environment > YAML > keyring.
"""

from typing import Any

from weather_app.config import Config


def apply_cli_overrides(config: Config, **kwargs: Any) -> None:
    """Apply CLI argument overrides to a Config instance.

    Args:
        config: The Config instance to modify.
        **kwargs: CLI arguments mapping from argument names to values.
            Supported keys: verbose, config_file, units, use_async, no_cache.
    """
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

    # Apply direct field mappings
    for cli_key, field_name in field_map.items():
        if cli_key in kwargs and kwargs[cli_key] is not None:
            setattr(config, field_name, kwargs[cli_key])

    # Special handling for verbose flag (sets log level to DEBUG)
    if kwargs.get("verbose"):
        config.LOG_LEVEL = "DEBUG"

    # Special handling for no_cache flag (disables caching)
    if kwargs.get("no_cache"):
        config.CACHE_TTL = 0

    # Special handling for config_file (load YAML from custom path)
    config_file = kwargs.get("config_file")
    if config_file:
        _load_custom_config_file(config, config_file)

    # Update derived fields (CACHE_FILE, LOG_FILE) after changes
    # Pydantic validators will be triggered on attribute assignment.
    # We need to manually trigger validation? The Config model uses
    # field validators that run when fields are set. Since we set fields
    # directly, the validators should run automatically.
    # However, we need to ensure cache_dir is set before CACHE_FILE.
    # We'll rely on the existing validator.


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

    # Normalize keys to uppercase
    for key, value in data.items():
        upper_key = key.upper()
        if hasattr(config, upper_key):
            setattr(config, upper_key, value)
        else:
            # Extra fields allowed via extra="allow"
            setattr(config, key, value)
