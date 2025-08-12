#!/usr/bin/env python3
"""
Main entry point for the Weather Application.

This module initializes the application and handles top-level exceptions.
Uses Rich for enhanced terminal output and error handling.
"""

from rich.traceback import install
from rich.console import Console
from services.ui_service import UIService

def main() -> None:
    """Initialize and run the weather application."""
    install(show_locals=True)  # Rich traceback handler
    
    try:
        ui = UIService()
        ui.run()
    except KeyboardInterrupt:
        print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
    except Exception as e:
        Console().print(
            "\n[red bold]⚠️  Application Error ⚠️[/red bold]",
            f"\n[bold]Error details:[/bold] {e}",
            "\n[bold]Possible solutions:[/bold]",
            "1. [blue]Check your internet connection[/blue] 🌐",
            "2. [blue]Verify your API key is valid[/blue] 🔑",
            "3. [blue]Ensure location format is correct (City,CC)[/blue] 🏙️",
            sep="\n"
        )

if __name__ == "__main__":
    main()
