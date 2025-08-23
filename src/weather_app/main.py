#!/usr/bin/env python3
"""
Main entry point for the Weather Application.

This module initializes the application and handles top-level exceptions.
Uses Rich for enhanced terminal output and structured logging.
"""

import logging
from rich.traceback import install
from rich.console import Console
from .services.ui_service import UIService
from .logging_config import setup_default_logging, LoggingConfig
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


def main() -> None:
    """Initialize and run the weather application."""
    install(show_locals=True)  # Rich traceback handler

    logger.info("Starting Weather Application")

    try:
        ui = UIService()
        ui.run()
        logger.info("Weather Application completed successfully")
    except KeyboardInterrupt:
        logger.info("Application cancelled by user")
        print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
    except ConfigurationError as e:
        logger.error("Configuration error: %s", e)
        Console().print(
            "\n[red bold]⚙️  Configuration Error ⚙️[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Solution:[/bold]",
            "1. [blue]Set OWM_API_KEY environment variable[/blue] 🔑",
            "2. [blue]Or create .weather.env file with your API key[/blue] 📁",
            sep="\n",
        )
    except LocationNotFoundError as e:
        logger.warning("Location not found: %s", e)
        Console().print(
            "\n[yellow bold]📍 Location Not Found 📍[/yellow bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Suggestions:[/bold]",
            "1. [blue]Check spelling and formatting (City,CC)[/blue] ✏️",
            "2. [blue]Try a different location name[/blue] 🌍",
            sep="\n",
        )
    except APIRequestError as e:
        logger.error("API request failed: %s", e, exc_info=True)
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
        logger.error("Application error: %s", e, exc_info=True)
        Console().print(
            "\n[red bold]⚠️  Application Error ⚠️[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            sep="\n",
        )
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        Console().print(
            "\n[red bold]❌ Unexpected Error ❌[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Please report this issue:[/bold]",
            "[blue]https://github.com/vihoma/weather-app/issues[/blue] 🐛",
            sep="\n",
        )


if __name__ == "__main__":
    main()
