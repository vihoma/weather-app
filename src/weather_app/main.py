#!/usr/bin/env python3
"""Main entry point for the Weather Application.

This module initializes the application and handles top-level exceptions.
Uses Rich for enhanced terminal output and structured logging.
"""

import asyncio
import logging
import sys

from rich.console import Console
from rich.prompt import Prompt
from rich.traceback import install

from weather_app.config import Config
from weather_app.exceptions import (APIRequestError, ConfigurationError,
                                    LocationNotFoundError, WeatherAppError)
from weather_app.logging_config import (LoggingConfig, log_with_context,
                                        setup_default_logging)
from weather_app.services.ui_service import UIService

# Global logger instance
logger = None


def setup_api_key() -> bool:
    """Interactive setup for storing API key in secure keyring.

    Returns:
        bool: True if setup was successful, False otherwise
    """
    console = Console()
    config = Config()

    if not config.is_keyring_available():
        console.print(
            "\n[yellow]⚠️  Secure keyring storage is not available on this system[/yellow]",
            "\nPlease use one of these alternatives:",
            "  • Set OWM_API_KEY environment variable",
            "  • Create .weather.env file with your API key",
            sep="\n",
        )
        return False

    console.print("\n[bold blue]🔑 OpenWeatherMap API Key Setup[/bold blue]")
    console.print("\nThis will securely store your API key in your system's keyring.")

    try:
        api_key = Prompt.ask("\nEnter your OpenWeatherMap API key", password=True)

        if not api_key:
            console.print("\n[yellow]❌ No API key provided. Setup cancelled.[/yellow]")
            return False

        config.store_api_key(api_key)
        console.print("\n[green]✅ API key stored securely in keyring![/green]")
        console.print(
            "\nYou can now run the weather app without setting environment variables."
        )
        return True

    except Exception as e:
        console.print(f"\n[red]❌ Failed to store API key: {e}[/red]")
        return False


async def main_async() -> None:
    """Initialize and run the weather application in async mode."""
    install(show_locals=True)  # Rich traceback handler

    # Set up configuration and logging
    config = Config()

    # First-run setup: prompt for API key storage if none found and keyring available
    if not config.api_key and config.is_keyring_available():
        console = Console()
        console.print("\n[bold yellow]🔑 No API key found[/bold yellow]")
        console.print(
            "\nWould you like to set up your OpenWeatherMap API key securely?"
        )

        try:
            setup_now = Prompt.ask(
                "Store API key in secure keyring?", choices=["y", "n"], default="y"
            )

            if setup_now.lower() == "y":
                if setup_api_key():
                    # Reload config to get the stored key
                    config = Config()
                else:
                    console.print(
                        "\n[yellow]Continuing without API key setup...[/yellow]"
                    )
        except KeyboardInterrupt:
            console.print("\n[yellow]Setup cancelled by user.[/yellow]")

    config.validate()
    setup_default_logging(config)
    global logger
    logger = LoggingConfig.get_logger(__name__)

    ui = None
    try:
        if config.use_async:
            log_with_context(
                logger, logging.INFO, "Starting Weather Application", mode="async"
            )
            ui = UIService(use_async=True)
            await ui.run_async()
        else:
            log_with_context(
                logger, logging.INFO, "Starting Weather Application", mode="sync"
            )
            ui = UIService(use_async=False)
            ui.run()
        log_with_context(
            logger, logging.INFO, "Weather Application completed successfully"
        )
    except KeyboardInterrupt:
        log_with_context(
            logger,
            logging.INFO,
            "Application cancelled by user",
            reason="keyboard_interrupt",
        )
        print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
    except ConfigurationError as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Configuration error",
            error_type="configuration",
            error_message=str(e),
        )
        Console().print(
            "\n[red bold]⚙️  Configuration Error ⚙️[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Solution:[/bold]",
            "1. [blue]Set OWM_API_KEY environment variable[/blue] 🔑",
            "2. [blue]Or create .weather.env file with your API key[/blue] 📁",
            sep="\n",
        )
    except LocationNotFoundError as e:
        log_with_context(
            logger,
            logging.WARNING,
            "Location not found",
            error_type="location_not_found",
            location=str(e),
        )
        Console().print(
            "\n[yellow bold]📍 Location Not Found 📍[/yellow bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Suggestions:[/bold]",
            "1. [blue]Check spelling and formatting (City,CC)[/blue] ✏️",
            "2. [blue]Try a different location name[/blue] 🌍",
            sep="\n",
        )
    except APIRequestError as e:
        log_with_context(
            logger,
            logging.ERROR,
            "API request failed",
            error_type="api_request",
            error_message=str(e),
            exc_info=True,
        )
        Console().print(
            "\n[red bold]🌐 API Error 🌐[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Possible solutions:[/bold]",
            "1. [blue]Check your internet connection[/blue] 🌐",
            "2. [blue]Verify your API key is valid[/blue] 🔑",
            "3. [blue]Wait a moment and try again[/blue] ⏰",
            sep="\n",
        )
    except WeatherAppError as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Application error",
            error_type="application",
            error_message=str(e),
            exc_info=True,
        )
        Console().print(
            "\n[red bold]⚠️  Application Error ⚠️[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            sep="\n",
        )
    except (OSError, MemoryError, ImportError, SystemError) as e:
        log_with_context(
            logger,
            logging.CRITICAL,
            "System-level error",
            error_type="system",
            error_message=str(e),
            exc_info=True,
        )
        Console().print(
            "\n[red bold]💥 System Error 💥[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]This is a system-level issue:[/bold]",
            "[blue]Please check system resources and dependencies[/blue] ⚙️",
            sep="\n",
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Unexpected error",
            error_type="unexpected",
            error_message=str(e),
            exc_info=True,
        )
        Console().print(
            "\n[red bold]❌ Unexpected Error ❌[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Please report this issue:[/bold]",
            "[blue]https://github.com/vihoma/weather-app/issues[/blue] 🐛",
            sep="\n",
        )
    finally:
        # Ensure cache is saved on application exit
        if ui and hasattr(ui, "weather_service") and ui.weather_service:
            try:
                ui.weather_service.save_cache()
                log_with_context(logger, logging.DEBUG, "Cache saved successfully")
            except Exception as e:
                log_with_context(
                    logger, logging.WARNING, "Failed to save cache", error=str(e)
                )


def main() -> None:
    """Initialize and run the weather application (sync wrapper)."""
    # Check for setup command
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-api-key":
        success = setup_api_key()
        sys.exit(0 if success else 1)

    # Check for help command
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        console = Console()
        console.print("\n[bold blue]🌦️ Weather App[/bold blue]")
        console.print("\nUsage:")
        console.print("  weather                    - Run the weather application")
        console.print("  weather --setup-api-key   - Set up API key securely")
        console.print("  weather --help            - Show this help")
        console.print("\nConfiguration:")
        console.print("  • Set OWM_API_KEY environment variable")
        console.print("  • Or use --setup-api-key to store securely in keyring")
        sys.exit(0)

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
