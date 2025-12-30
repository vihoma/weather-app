"""Cache subcommand for managing weather data cache."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from weather_app.cli.help_formatter import apply_preserve_epilog_formatting
from weather_app.config import Config


@apply_preserve_epilog_formatting
@click.group(
    name="cache",
    help="Manage weather data cache.",
    epilog="""
Examples:
  weather cache clear --force
  weather cache status
  weather cache ttl
""",
)
def cache_group() -> None:
    """Group for cache management commands."""
    pass


@cache_group.command(name="clear", help="Clear the cache file.")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation.",
)
@click.pass_context
def cache_clear(ctx: click.Context, force: bool) -> None:
    """Clear the cache file."""
    console = Console()
    config = Config()
    cache_file = Path(config.cache_file).expanduser()

    if not cache_file.exists():
        console.print("[yellow]⚠️  Cache file does not exist.[/yellow]")
        return

    if not force:
        console.print(
            "[bold yellow]⚠️  Warning: This will delete cache file:[/bold yellow]"
        )
        console.print(f"    {cache_file}")
        confirm = click.confirm("Are you sure you want to delete the cache file?")
        if not confirm:
            console.print("[green]Operation cancelled.[/green]")
            return

    try:
        cache_file.unlink()
        console.print("[green]✅ Cache file deleted successfully.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to delete cache file: {e}[/red]")
        raise click.ClickException(f"Failed to delete cache file: {e}")


@cache_group.command(name="status", help="Show cache status and statistics.")
@click.pass_context
def cache_status(ctx: click.Context) -> None:
    """Show cache status and statistics."""
    console = Console()
    config = Config()
    cache_file = Path(config.cache_file).expanduser()

    table = Table(title="Cache Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row(
        "Cache persistence", "Enabled" if config.cache_persist else "Disabled"
    )
    table.add_row("Cache TTL (seconds)", str(config.cache_ttl))
    table.add_row("Cache file", str(cache_file))
    table.add_row("File exists", "Yes" if cache_file.exists() else "No")

    if cache_file.exists():
        try:
            file_size = cache_file.stat().st_size
            table.add_row("File size (bytes)", str(file_size))
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            num_entries = len(cache_data)
            table.add_row("Number of cache entries", str(num_entries))
            # Show sample keys (first 3)
            sample_keys = list(cache_data.keys())[:3]
            sample_str = ", ".join(sample_keys)
            if num_entries > 3:
                sample_str += f" ... (+{num_entries - 3} more)"
            table.add_row("Sample keys", sample_str)
        except (json.JSONDecodeError, OSError) as e:
            table.add_row("File readable", f"No ({e})")
    else:
        table.add_row("File size", "N/A")
        table.add_row("Number of cache entries", "N/A")

    console.print(table)


@cache_group.command(name="ttl", help="Show or set cache TTL (Time To Live).")
@click.option(
    "--set",
    "ttl_value",
    type=int,
    help="Set cache TTL in seconds (applies to new cache entries).",
)
@click.pass_context
def cache_ttl(ctx: click.Context, ttl_value: int | None) -> None:
    """Show or set cache TTL (Time To Live)."""
    console = Console()
    config = Config()

    if ttl_value is not None:
        if ttl_value <= 0:
            raise click.BadParameter("TTL must be positive integer.")
        console.print(
            "[yellow]⚠️  Setting TTL via this command is not supported.[/yellow]"
        )
        console.print(
            "[yellow]   To change cache TTL, use one of these methods:[/yellow]"
        )
        console.print("  • Set CACHE_TTL environment variable")
        console.print("  • Add CACHE_TTL to .weather.yaml config file")
        console.print(
            "  • Use --cache-ttl option with weather commands (future feature)"
        )
        console.print(f"\nRequested TTL: {ttl_value} seconds")
    else:
        console.print(f"Current cache TTL: {config.cache_ttl} seconds")
        console.print("\nTo change TTL permanently, use one of these methods:")
        console.print("  • Set CACHE_TTL environment variable")
        console.print("  • Add CACHE_TTL to .weather.yaml config file")
        console.print(
            "  • Use --cache-ttl option with weather commands (future feature)"
        )
