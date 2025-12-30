"""Click command group for weather application.

This module defines the main CLI group with global options that apply to all subcommands.
"""

import click

from weather_app.cli.help_formatter import apply_preserve_epilog_formatting
from weather_app.config import Config


@apply_preserve_epilog_formatting
@click.group(
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
    "--use-async",
    is_flag=True,
    help="Force asynchronous mode (default: from config).",
)
@click.option(
    "--no-cache",
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
    ctx.obj["use_async"] = use_async
    ctx.obj["no_cache"] = no_cache

    # Apply overrides to config instance (will be created lazily when needed)
    # Actual override logic will be applied in config_override module
    pass


def get_config_from_context(ctx: click.Context) -> Config:
    """Create a Config instance with CLI overrides applied.

    Args:
        ctx: Click context containing override values.

    Returns:
        Config instance with CLI overrides applied.
    """
    from weather_app.cli.config_override import apply_cli_overrides

    config = Config()
    if ctx.obj:
        apply_cli_overrides(config, **ctx.obj)
    return config


# Import and register subcommands
from weather_app.cli.commands.weather import weather_command
from weather_app.cli.commands.setup import setup_group
from weather_app.cli.commands.cache import cache_group
from weather_app.cli.commands.config import config_group
from weather_app.cli.commands.version import version_command

cli.add_command(weather_command)
cli.add_command(setup_group)
cli.add_command(cache_group)
cli.add_command(config_group)
cli.add_command(version_command)
