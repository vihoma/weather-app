"""Configuration subcommand for viewing current settings and sources."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.table import Table

from weather_app.config import Config


@click.group(name="config", help="View and manage application configuration.")
def config_group() -> None:
    """Group for configuration commands."""
    pass


def _get_yaml_config_path() -> Optional[Path]:
    """Find which YAML config file is being used, if any.

    Returns:
        Path to the YAML file, or None if no YAML file is found.
    """
    locations = [
        Path(".weather.yaml").expanduser(),
        Path(os.getenv("HOME", "")).expanduser() / ".weather.yaml",
    ]
    for path in locations:
        if path.is_file():
            return path
    return None


def _get_env_var_status(config_field: str) -> Tuple[bool, Optional[str]]:
    """Check if an environment variable is set for a config field.

    Args:
        config_field: The Config field name (uppercase, e.g., "OWM_API_KEY").

    Returns:
        Tuple of (is_set, value). Value is masked for sensitive fields.
    """
    env_var = config_field
    value = os.getenv(env_var)
    if value is None:
        return False, None

    # Mask sensitive values
    if "API_KEY" in config_field or "KEY" in config_field:
        if len(value) > 8:
            masked = f"{value[:4]}...{value[-4:]}"
        else:
            masked = "***"
    else:
        masked = value
    return True, masked


def _get_keyring_status(config: Config) -> Tuple[bool, Optional[str]]:
    """Check if API key is stored in keyring.

    Args:
        config: Config instance.

    Returns:
        Tuple of (has_keyring_key, masked_key). masked_key is None if no key.
    """
    try:
        if not config.is_keyring_available():
            return False, None
        key = config._secure.get_api_key()
        if key:
            if len(key) > 8:
                masked = f"{key[:4]}...{key[-4:]}"
            else:
                masked = "***"
            return True, masked
    except Exception:
        pass
    return False, None


def _get_source_hint(config_field: str, config: Config) -> List[str]:
    """Generate source hints for a configuration field.

    Args:
        config_field: The Config field name (uppercase).
        config: Config instance.

    Returns:
        List of source hints (strings).
    """
    hints = []

    # Check YAML
    yaml_path = _get_yaml_config_path()
    if yaml_path:
        # Read YAML to see if this field is present
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
            yaml_key = config_field.lower()
            if yaml_key in yaml_data:
                hints.append(f"yaml:{yaml_path.name}")
        except Exception:
            pass

    # Check environment variable
    env_set, env_value = _get_env_var_status(config_field)
    if env_set:
        hints.append("env")

    # Check keyring (only for API key)
    if "API_KEY" in config_field:
        has_keyring, _ = _get_keyring_status(config)
        if has_keyring:
            hints.append("keyring")

    # Default if no hints
    if not hints:
        hints.append("default")

    return hints


@config_group.command(
    name="show", help="Show current configuration with source indications."
)
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration with source indications."""
    console = Console()

    # Get config with CLI overrides applied
    from weather_app.cli.group import get_config_from_context

    config = get_config_from_context(ctx)

    # Find YAML file
    yaml_path = _get_yaml_config_path()

    # Table for configuration values
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    # Fields to display (mapping from property name to display name)
    fields = [
        ("OWM_API_KEY", "API Key"),
        ("OWM_UNITS", "Units"),
        ("CACHE_TTL", "Cache TTL (seconds)"),
        ("REQUEST_TIMEOUT", "Request Timeout (seconds)"),
        ("USE_ASYNC", "Use Async"),
        ("LOG_LEVEL", "Log Level"),
        ("LOG_FORMAT", "Log Format"),
        ("CACHE_PERSIST", "Cache Persist"),
        ("CACHE_DIR", "Cache Directory"),
        ("CACHE_FILE", "Cache File"),
        ("LOG_FILE", "Log File"),
    ]

    for field_name, display_name in fields:
        # Get value from config
        value = getattr(config, field_name, None)

        # Mask sensitive values
        if "API_KEY" in field_name and value:
            if len(value) > 8:
                value_str = f"{value[:4]}...{value[-4:]}"
            else:
                value_str = "***"
        else:
            value_str = str(value) if value is not None else "None"

        # Get source hints
        hints = _get_source_hint(field_name, config)
        source_str = ", ".join(hints)

        table.add_row(display_name, value_str, source_str)

    console.print(table)

    # Additional information
    console.print("\n[bold]Configuration Sources:[/bold]")

    if yaml_path:
        console.print(f"  • YAML file: {yaml_path}")
    else:
        console.print("  • YAML file: [dim]Not found[/dim]")

    # Show which environment variables are set
    env_vars = []
    for field_name, _ in fields:
        env_set, _ = _get_env_var_status(field_name)
        if env_set:
            env_vars.append(field_name)

    if env_vars:
        console.print(f"  • Environment variables set: {', '.join(env_vars)}")
    else:
        console.print("  • Environment variables: [dim]None set[/dim]")

    # Keyring status
    has_keyring, masked_key = _get_keyring_status(config)
    if has_keyring:
        console.print(f"  • Keyring storage: [green]Available[/green] (API key stored)")
    else:
        if config.is_keyring_available():
            console.print(
                "  • Keyring storage: [yellow]Available but no key stored[/yellow]"
            )
        else:
            console.print("  • Keyring storage: [dim]Not available[/dim]")

    # CLI overrides
    if ctx.obj:
        overrides = []
        for key in ["units", "use_async", "no_cache"]:
            if key in ctx.obj and ctx.obj[key] is not None:
                overrides.append(f"--{key.replace('_', '-')}")
        if overrides:
            console.print(f"  • CLI overrides applied: {', '.join(overrides)}")

    console.print("\n[dim]Note: Source hints indicate where a value *could* be from.")
    console.print("[dim]Actual precedence: CLI > env > YAML > keyring > default</dim>")


@config_group.command(
    name="sources", help="Show detailed configuration source information."
)
def config_sources() -> None:
    """Show detailed configuration source information."""
    console = Console()
    config = Config()

    console.print("[bold]Configuration Source Analysis[/bold]\n")

    # YAML file
    yaml_path = _get_yaml_config_path()
    if yaml_path:
        console.print(f"[green]✓[/green] YAML configuration file found: {yaml_path}")
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
            yaml_fields = [k for k in yaml_data.keys()]
            console.print(f"   Contains fields: {', '.join(yaml_fields)}")
        except Exception as e:
            console.print(f"   [red]Error reading YAML: {e}[/red]")
    else:
        console.print("[dim]✗[/dim] No YAML configuration file found")
        console.print("   Checked locations: .weather.yaml, ~/.weather.yaml")

    # Environment variables
    console.print("\n[bold]Environment Variables:[/bold]")
    env_fields = [
        "OWM_API_KEY",
        "OWM_UNITS",
        "CACHE_TTL",
        "REQUEST_TIMEOUT",
        "USE_ASYNC",
        "LOG_LEVEL",
        "LOG_FORMAT",
        "CACHE_PERSIST",
        "CACHE_DIR",
        "CACHE_FILE",
        "LOG_FILE",
    ]
    for field in env_fields:
        env_set, value = _get_env_var_status(field)
        if env_set:
            console.print(f"  [green]✓[/green] {field}={value}")
        else:
            console.print(f"  [dim]✗[/dim] {field} [dim](not set)[/dim]")

    # Keyring
    console.print("\n[bold]Keyring Storage:[/bold]")
    if config.is_keyring_available():
        console.print("  [green]✓[/green] Keyring backend is available")
        has_keyring, masked_key = _get_keyring_status(config)
        if has_keyring:
            console.print(f"  [green]✓[/green] API key stored in keyring: {masked_key}")
        else:
            console.print("  [dim]✗[/dim] No API key stored in keyring")
    else:
        console.print("  [dim]✗[/dim] Keyring backend not available")

    # Current effective values
    console.print("\n[bold]Effective Configuration (after applying precedence):[/bold]")
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    effective_fields = [
        ("API Key", config.api_key),
        ("Units", config.units),
        ("Cache TTL", config.cache_ttl),
        ("Request Timeout", config.request_timeout),
        ("Use Async", config.use_async),
        ("Log Level", config.log_level),
        ("Log Format", config.log_format),
        ("Cache Persist", config.cache_persist),
        ("Cache Dir", config.cache_dir),
        ("Cache File", config.cache_file),
        ("Log File", config.log_file),
    ]

    for name, value in effective_fields:
        if "API" in name and value:
            if len(value) > 8:
                value_str = f"{value[:4]}...{value[-4:]}"
            else:
                value_str = "***"
        else:
            value_str = str(value) if value is not None else "None"
        table.add_row(name, value_str)

    console.print(table)

    console.print(
        "\n[dim]Precedence order: CLI arguments > environment variables > YAML file > keyring > defaults</dim>"
    )
