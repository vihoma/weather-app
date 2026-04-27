"""Setup subcommand for API key management."""

import logging

import click
from rich.console import Console
from rich.prompt import Prompt

from weather_app.cli.command_logging import (
    get_command_logger,
    log_command_failure,
    log_command_start,
    log_command_success,
)
from weather_app.cli.help_formatter import apply_preserve_epilog_formatting
from weather_app.security import SecureConfig

logger = get_command_logger(__name__)


@apply_preserve_epilog_formatting
@click.group(
    name="setup",
    help="Manage application setup and configuration.",
    epilog="""
Examples:
  weather setup api-key set --interactive
  weather setup api-key view
  weather setup api-key remove --force
""",
)
def setup_group() -> None:
    """Group for setup-related commands."""
    pass


@setup_group.group(name="api-key", help="Manage OpenWeatherMap API key storage.")
def api_key_group() -> None:
    """Group for API key management commands."""
    pass


@api_key_group.command(name="set", help="Set or update the OpenWeatherMap API key.")
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode (prompt for API key).",
)
@click.option(
    "--key",
    "-k",
    type=str,
    help="API key value (use with caution as it may be visible in shell history).",
)
@click.pass_context
def api_key_set(ctx: click.Context, interactive: bool, key: str | None) -> None:
    """Set or update the OpenWeatherMap API key.

    If interactive flag is set, prompts for API key securely.
    If key is provided via --key, stores it directly.
    If neither, defaults to interactive mode.
    """
    console = Console()
    secure_config = SecureConfig()
    log_command_start(
        logger,
        ctx,
        interactive=interactive or not key,
        key_provided=key is not None,
    )

    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nPlease use one of these alternatives:",
            "  • Set OWM_API_KEY environment variable",
            "  • Create .weather.env file with your API key",
            sep="\n",
        )
        error = click.Abort()
        log_command_failure(logger, ctx, error, level=logging.WARNING)
        raise error

    api_key = key
    if interactive or not api_key:
        console.print("\n[bold blue]🔑 OpenWeatherMap API Key Setup[/bold blue]")
        console.print(
            "\nThis will securely store your API key in your system's keyring."
        )
        api_key = Prompt.ask("\nEnter your OpenWeatherMap API key", password=True)

    if not api_key:
        console.print("\n[yellow]❌ No API key provided. Setup cancelled.[/yellow]")
        error = click.Abort()
        log_command_failure(logger, ctx, error, level=logging.WARNING)
        raise error

    try:
        secure_config.store_api_key(api_key, service_name="openweathermap")
        console.print("\n[green]✅ API key stored securely in keyring![/green]")
        console.print(
            "\nYou can now run the weather app without setting environment variables."
        )
        log_command_success(logger, ctx, interactive=interactive or not key)
    except Exception as e:
        log_command_failure(logger, ctx, e, exc_info=True)
        console.print(f"\n[red]❌ Failed to store API key: {e}[/red]")
        raise click.ClickException(f"Failed to store API key: {e}")


@api_key_group.command(
    name="view", help="View the stored API key (masked for security)."
)
@click.pass_context
def api_key_view(ctx: click.Context) -> None:
    """View the stored API key (masked for security)."""
    console = Console()
    secure_config = SecureConfig()
    log_command_start(logger, ctx)

    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nCannot view stored API key.",
        )
        error = click.Abort()
        log_command_failure(logger, ctx, error, level=logging.WARNING)
        raise error

    try:
        api_key = secure_config.get_api_key(service_name="openweathermap")
        if api_key:
            # Mask the API key for security (show first 4 and last 4 chars)
            masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            console.print(f"\n[green]✅ API key stored: {masked}[/green]")
        else:
            console.print("\n[yellow]⚠️  No API key found in secure storage.[/yellow]")
        log_command_success(logger, ctx, key_present=bool(api_key))
    except Exception as e:
        log_command_failure(logger, ctx, e, exc_info=True)
        console.print(f"\n[red]❌ Failed to retrieve API key: {e}[/red]")
        raise click.ClickException(f"Failed to retrieve API key: {e}")


@api_key_group.command(name="remove", help="Remove the stored API key.")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force removal without confirmation.",
)
@click.pass_context
def api_key_remove(ctx: click.Context, force: bool) -> None:
    """Remove the stored API key from secure storage."""
    console = Console()
    secure_config = SecureConfig()
    log_command_start(logger, ctx, force=force)

    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nCannot remove stored API key.",
        )
        error = click.Abort()
        log_command_failure(logger, ctx, error, level=logging.WARNING)
        raise error

    try:
        api_key = secure_config.get_api_key(service_name="openweathermap")
        if not api_key:
            console.print("\n[yellow]⚠️  No API key found in secure storage.[/yellow]")
            log_command_success(logger, ctx, removed=False, key_present=False)
            return

        if not force:
            console.print(
                "\n[bold yellow]⚠️  Warning: This will remove your stored API key.[/bold yellow]"
            )
            confirm = Prompt.ask(
                "Are you sure you want to remove the API key?",
                choices=["y", "n"],
                default="n",
            )
            if confirm.lower() != "y":
                console.print("\n[green]Operation cancelled.[/green]")
                log_command_success(logger, ctx, removed=False, cancelled=True)
                return

        secure_config.delete_api_key(service_name="openweathermap")
        console.print("\n[green]✅ API key removed from secure storage.[/green]")
        log_command_success(logger, ctx, removed=True)
    except Exception as e:
        log_command_failure(logger, ctx, e, exc_info=True)
        console.print(f"\n[red]❌ Failed to remove API key: {e}[/red]")
        raise click.ClickException(f"Failed to remove API key: {e}")
