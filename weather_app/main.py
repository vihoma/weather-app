#!/usr/bin/env python3
"""Main entry point for the Weather Application."""

from rich.traceback import install
from services.ui_service import UIService

def main():
    """Initialize and run the weather application."""
    install(show_locals=True)  # Rich traceback handler
    
    try:
        ui = UIService()
        ui.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        Console().print(
            f"\n[red bold]⚠️ Critical Error:[/red bold] {e}\n"
            "Please check:\n"
            "1. Internet connection 🌐\n"
            "2. API key validity 🔑\n"
            "3. Location format (City,CC) 🏙️"
        )

if __name__ == "__main__":
    main()
