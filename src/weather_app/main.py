#!/usr/bin/env python3
"""
Main entry point for the Weather Application.

This module initializes the application and handles top-level exceptions.
Uses Rich for enhanced terminal output and structured logging.
"""

import asyncio
import logging
from rich.traceback import install
from rich.console import Console
from .services.ui_service import UIService
from .logging_config import setup_default_logging, LoggingConfig, log_with_context
from .config import Config
from .exceptions import (
    WeatherAppError,
    ConfigurationError,
    LocationNotFoundError,
    APIRequestError,
)

# Set up configuration and logging
config = Config()
config.validate()
setup_default_logging(config)
logger = LoggingConfig.get_logger(__name__)


async def main_async() -> None:
    """Initialize and run the weather application in async mode."""
    install(show_locals=True)  # Rich traceback handler

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


def main() -> None:
    """Initialize and run the weather application (sync wrapper)."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
