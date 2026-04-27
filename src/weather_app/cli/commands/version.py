"""Version command for weather application CLI."""

import sys
from importlib import metadata

import click
from rich.console import Console
from rich.table import Table

from weather_app.cli.command_logging import (
    get_command_logger,
    log_command_start,
    log_command_success,
)

logger = get_command_logger(__name__)


@click.command(
    name="version",
    help="Show application version information.",
)
@click.pass_context
def version_command(ctx: click.Context) -> None:
    """Display weather application version information."""
    console = Console()
    log_command_start(logger, ctx)

    try:
        # Get package version from installed metadata
        version = metadata.version("weather-app")
    except metadata.PackageNotFoundError:
        version = "unknown (package not installed)"

    # Create version information table
    table = Table(title="Weather Application")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Application", "weather-app")
    table.add_row("Version", version)
    table.add_row("Python", sys.version.split()[0])  # Just version number

    console.print(table)
    log_command_success(logger, ctx, version=version)
