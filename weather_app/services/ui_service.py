"""Rich-based user interface components."""

from rich.prompt import Prompt, Confirm
from rich.console import Console
from rich.table import Table
from rich.text import Text
from models.weather_data import WeatherData
from config import Config

class UIService:
    """Handles all user interaction and display."""
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.config.validate()
        self.weather_service = WeatherService(self.config)
        self.current_units = self.config.units

    def run(self):
        """Main application loop."""
        self.console.print("[bold green]🌦️ Welcome to Weather App![/bold green]")
        
        while True:
            location = self._prompt_location()
            weather_data = self.weather_service.get_weather(location, self.current_units)
            self._display_weather(weather_data)
            
            if not self._prompt_continue():
                break

    def _prompt_location(self) -> str:
        """Get validated location input."""
        while True:
            location = Prompt.ask("📌 Enter city name (e.g. [bold]London,GB[/bold])")
            if location.strip():
                return location.strip()
            self.console.print("[red]⚠️ City name cannot be empty![/red]")

    def _display_weather(self, data: WeatherData):
        """Display weather data in a rich table."""
        table = Table(title=f"🌤️ Weather in {data.city}", show_header=False)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")
        
        self._add_table_row(table, "Condition", f"{data.get_emoji()} {data.detailed_status}")
        self._add_table_row(table, "Temperature", f"{data.temperature} {self._temp_unit()}")
        self._add_table_row(table, "Feels Like", f"{data.feels_like} {self._temp_unit()}")
        self._add_table_row(table, "Humidity", f"{data.humidity}% 💧")
        
        if data.precipitation_probability:
            self._add_table_row(table, "Precipitation", f"{data.precipitation_probability}% ☔")
            
        self.console.print(table)

    def _add_table_row(self, table: Table, metric: str, value: str):
        """Helper to add styled rows to table."""
        table.add_row(
            Text(metric, style="bold cyan"),
            Text(value)
        )

    def _temp_unit(self) -> str:
        """Get temperature unit symbol."""
        return {
            "metric": "°C",
            "imperial": "°F",
            "default": "K"
        }.get(self.current_units, "K")

    def _prompt_continue(self) -> bool:
        """Ask user if they want to continue."""
        return Confirm.ask("\n🔍 Check another location?", default=True)

    def _prompt_units(self):
        """Handle unit system selection."""
        # Implementation omitted for brevity
