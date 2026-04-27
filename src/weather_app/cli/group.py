"""Click command group for weather application.

This module defines the main CLI group with global options that apply to all
subcommands.
"""

import logging

import click

from weather_app.cli.commands.cache import cache_group
from weather_app.cli.commands.config import config_group
from weather_app.cli.commands.setup import setup_group
from weather_app.cli.commands.version import version_command

# Import subcommands
from weather_app.cli.commands.weather import weather_command
from weather_app.cli.help_formatter import apply_preserve_epilog_formatting
from weather_app.cli.config_override import apply_cli_overrides
from weather_app.config import Config
from weather_app.logging_config import (
    LoggingConfig,
    log_with_context,
    setup_default_logging,
)

logger = logging.getLogger(__name__)

CONFIG_KEY = "config"
LOGGER_KEY = "logger"
LOGGING_INITIALIZED_KEY = "logging_initialized"
HELP_REQUESTED_KEY = "help_requested"


class WeatherCLIGroup(click.Group):
    """Click group that marks help-only invocations before callbacks run."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        help_option_names = set(ctx.help_option_names or ["--help"])
        ctx.meta[HELP_REQUESTED_KEY] = any(arg in help_option_names for arg in args)
        return super().parse_args(ctx, args)


def _create_effective_config(ctx: click.Context) -> Config:
    """Build and cache the effective configuration for the current CLI run."""
    root_ctx = ctx.find_root()
    root_ctx.ensure_object(dict)

    cached_config = root_ctx.obj.get(CONFIG_KEY)
    if isinstance(cached_config, Config):
        return cached_config

    config = Config()
    if root_ctx.obj:
        apply_cli_overrides(config, **root_ctx.obj)

    root_ctx.obj[CONFIG_KEY] = config
    return config


def _should_bootstrap_logging(ctx: click.Context) -> bool:
    """Return True when the current invocation should initialize subcommand logging."""
    return bool(
        ctx.invoked_subcommand is not None
        and not ctx.meta.get(HELP_REQUESTED_KEY, False)
    )


def _bootstrap_subcommand_logging(ctx: click.Context) -> None:
    """Initialize logging for Click-based subcommand execution."""
    root_ctx = ctx.find_root()
    root_ctx.ensure_object(dict)

    if root_ctx.obj.get(LOGGING_INITIALIZED_KEY) or not _should_bootstrap_logging(
        root_ctx
    ):
        return

    config = _create_effective_config(root_ctx)
    setup_default_logging(config, enable_console=False)

    command_logger = LoggingConfig.get_logger(__name__)
    root_ctx.obj[LOGGER_KEY] = command_logger
    root_ctx.obj[LOGGING_INITIALIZED_KEY] = True

    log_with_context(
        command_logger,
        logging.DEBUG,
        "CLI logging configured",
        subcommand=root_ctx.invoked_subcommand,
        log_level=config.log_level,
        log_format=config.log_format,
        log_file=config.log_file,
    )


@apply_preserve_epilog_formatting
@click.group(
    cls=WeatherCLIGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="""
Examples:
  # Interactive mode (traditional TUI)
  weather
  
  # One-shot weather queries
  weather weather --city "London,GB" --output json
  weather weather --coordinates "51.5074,-0.1278" --output markdown
  
  # API key management
  weather setup api-key set --interactive
  weather setup api-key view
  
  # Cache management
  weather cache clear --force
  weather cache status
  
  # Configuration inspection
  weather config show
  weather config sources
  
  # Version information
  weather version
  
  # Global options can be used with any command
  weather --verbose weather --city "Paris,FR"
  weather --no-cache --units imperial weather --city "New York"
""",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output (debug logging).",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to custom configuration file (YAML).",
)
@click.option(
    "--units",
    type=click.Choice(["metric", "imperial", "standard"]),
    help="Temperature units: metric (°C), imperial (°F), standard (K).",
)
@click.option(
    "--async",
    "use_async",
    is_flag=True,
    help="Force asynchronous mode (default: from config).",
)
@click.option(
    "--no-async",
    "no_async",
    is_flag=True,
    help="Force synchronous mode (default: from config).",
)
@click.option(
    "--cache",
    "use_cache",
    is_flag=True,
    help="Enable caching for this request (default: from config).",
)
@click.option(
    "--no-cache",
    "no_cache",
    is_flag=True,
    help="Disable caching for this request.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool,
    config_file: str | None,
    units: str | None,
    use_async: bool,
    no_async: bool,
    use_cache: bool,
    no_cache: bool,
) -> None:
    """Weather App CLI - Get weather forecasts from OpenWeatherMap.

    Provides both interactive TUI and one-shot command-line modes.
    """
    # Store configuration overrides in context object
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_file"] = config_file
    ctx.obj["units"] = units
    # Resolve --async / --no-async: explicit flag wins, else leave as None
    if use_async:
        ctx.obj["use_async"] = True
    elif no_async:
        ctx.obj["use_async"] = False
    else:
        ctx.obj["use_async"] = None
    # Resolve --cache / --no-cache: explicit flag wins, else leave as None
    if use_cache:
        ctx.obj["cache_persist"] = True
    elif no_cache:
        ctx.obj["cache_persist"] = False
    else:
        ctx.obj["cache_persist"] = None

    # Apply overrides to config instance (will be created lazily when needed)
    # Actual override logic will be applied in config_override module
    _bootstrap_subcommand_logging(ctx)


def get_config_from_context(ctx: click.Context) -> Config:
    """Create a Config instance with CLI overrides applied.

    Args:
        ctx: Click context containing override values.

    Returns:
        Config instance with CLI overrides applied.
    """
    return _create_effective_config(ctx)


# Register subcommands
cli.add_command(weather_command)
cli.add_command(setup_group)
cli.add_command(cache_group)
cli.add_command(config_group)
cli.add_command(version_command)
