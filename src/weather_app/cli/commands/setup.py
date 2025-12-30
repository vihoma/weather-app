"""Setup subcommand for API key management."""

import click
from rich.console import Console
from rich.prompt import Prompt

from weather_app.security import SecureConfig


@click.group(
    name="setup",
    help="Manage application setup and configuration.\n\nExamples:\n  weather setup api-key set --interactive\n  weather setup api-key view\n  weather setup api-key remove --force"
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
def api_key_set(interactive: bool, key: str | None) -> None:
    """Set or update the OpenWeatherMap API key.

    If interactive flag is set, prompts for API key securely.
    If key is provided via --key, stores it directly.
    If neither, defaults to interactive mode.
    """
    console = Console()
    secure_config = SecureConfig()
    
    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nPlease use one of these alternatives:",
            "  • Set OWM_API_KEY environment variable",
            "  • Create .weather.env file with your API key",
            sep="\n",
        )
        raise click.Abort()
    
    api_key = key
    if interactive or not api_key:
        console.print("\n[bold blue]🔑 OpenWeatherMap API Key Setup[/bold blue]")
        console.print("\nThis will securely store your API key in your system's keyring.")
        api_key = Prompt.ask("\nEnter your OpenWeatherMap API key", password=True)
    
    if not api_key:
        console.print("\n[yellow]❌ No API key provided. Setup cancelled.[/yellow]")
        raise click.Abort()
    
    try:
        secure_config.store_api_key(api_key, service_name="openweathermap")
        console.print("\n[green]✅ API key stored securely in keyring![/green]")
        console.print(
            "\nYou can now run the weather app without setting environment variables."
        )
    except Exception as e:
        console.print(f"\n[red]❌ Failed to store API key: {e}[/red]")
        raise click.ClickException(f"Failed to store API key: {e}")


@api_key_group.command(name="view", help="View the stored API key (masked for security).")
def api_key_view() -> None:
    """View the stored API key (masked for security)."""
    console = Console()
    secure_config = SecureConfig()
    
    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nCannot view stored API key.",
        )
        raise click.Abort()
    
    try:
        api_key = secure_config.get_api_key(service_name="openweathermap")
        if api_key:
            # Mask the API key for security (show first 4 and last 4 chars)
            masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            console.print(f"\n[green]✅ API key stored: {masked}[/green]")
        else:
            console.print("\n[yellow]⚠️  No API key found in secure storage.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to retrieve API key: {e}[/red]")
        raise click.ClickException(f"Failed to retrieve API key: {e}")


@api_key_group.command(name="remove", help="Remove the stored API key.")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force removal without confirmation.",
)
def api_key_remove(force: bool) -> None:
    """Remove the stored API key from secure storage."""
    console = Console()
    secure_config = SecureConfig()
    
    if not secure_config.is_keyring_available():
        console.print(
            "[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nCannot remove stored API key.",
        )
        raise click.Abort()
    
    try:
        api_key = secure_config.get_api_key(service_name="openweathermap")
        if not api_key:
            console.print("\n[yellow]⚠️  No API key found in secure storage.[/yellow]")
            return
        
        if not force:
            console.print("\n[bold yellow]⚠️  Warning: This will remove your stored API key.[/bold yellow]")
            confirm = Prompt.ask(
                "Are you sure you want to remove the API key?", choices=["y", "n"], default="n"
            )
            if confirm.lower() != "y":
                console.print("\n[green]Operation cancelled.[/green]")
                return
        
        secure_config.delete_api_key(service_name="openweathermap")
        console.print("\n[green]✅ API key removed from secure storage.[/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to remove API key: {e}[/red]")
        raise click.ClickException(f"Failed to remove API key: {e}")