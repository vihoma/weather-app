"""Version command for weather application CLI."""

import sys
from importlib import metadata

import click
from rich.console import Console
from rich.table import Table


@click.command(
    name="version",
    help="Show application version information.",
)
def version_command() -> None:
    """Display weather application version information."""
    console = Console()
    
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