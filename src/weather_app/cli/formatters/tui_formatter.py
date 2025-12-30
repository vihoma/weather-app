"""TUI formatter for weather data using Rich terminal UI.

Reuses the existing UIService rendering logic.
"""

import io
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

from weather_app.cli.output_formatters import BaseFormatter
from weather_app.models.weather_data import WeatherData


class TUIFormatter(BaseFormatter):
    """Formatter that uses Rich terminal UI for interactive display.

    Reuses the existing UIService rendering logic.
    """

    def __init__(self, units: str = "metric"):
        """Initialize TUI formatter.

        Args:
            units: Temperature units (metric, imperial, default).
        """
        self.units = units

    def format(self, weather_data: WeatherData) -> str:
        """Format weather data for Rich terminal display.

        This method delegates to UIService display methods.

        Args:
            weather_data: The weather data to format.

        Returns:
            A string with ANSI escape codes for Rich terminal output.
        """
        # Create a console that captures output
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, color_system="auto")

        # Create and display table similar to UIService._display_weather
        table = Table(title=f"🌤️ Weather in {weather_data.city}", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")

        # Helper to add rows
        def add_row(metric: str, value: str) -> None:
            table.add_row(Text(metric, style="bold cyan"), Text(value))

        # Temperature unit symbol
        unit_symbol = {"metric": "°C", "imperial": "°F", "default": "K"}.get(
            self.units, "K"
        )
        speed_unit = {"metric": "m/s", "imperial": "mph", "default": "m/s"}[self.units]

        # Add rows matching UIService._display_weather
        add_row(
            "Condition", f"{weather_data.get_emoji()} {weather_data.detailed_status}"
        )
        add_row("Temperature", f"{weather_data.temperature} {unit_symbol}")
        add_row("Feels Like", f"{weather_data.feels_like} {unit_symbol}")
        add_row("Humidity", f"{weather_data.humidity}% 💧")

        if weather_data.precipitation_probability:
            add_row("Precipitation", f"{weather_data.precipitation_probability}% ☔")

        if weather_data.wind_direction_deg:
            # 16-point compass directions (0°-360° in 22.5° increments)
            wind_arrows = [
                "↓",  # N    (0°)
                "↙",  # NNE  (22.5°)
                "←",  # NE   (45°)
                "↙",  # ENE  (67.5°)
                "←",  # E    (90°)
                "↖",  # ESE  (112.5°)
                "↑",  # SE   (135°)
                "↖",  # SSE  (157.5°)
                "↑",  # S    (180°)
                "↗",  # SSW  (202.5°)
                "→",  # SW   (225°)
                "↗",  # WSW  (247.5°)
                "→",  # W    (270°)
                "↘",  # WNW  (292.5°)
                "↓",  # NW   (315°)
                "↘",  # NNW  (337.5°)
            ]
            wind_directions = [
                "N",
                "NNE",
                "NE",
                "ENE",
                "E",
                "ESE",
                "SE",
                "SSE",
                "S",
                "SSW",
                "SW",
                "WSW",
                "W",
                "WNW",
                "NW",
                "NNW",
            ]
            dir_index = int((weather_data.wind_direction_deg + 11.25) / 22.5) % 16
            wind_info = (
                f"{weather_data.wind_speed} {speed_unit} "
                f"{wind_arrows[dir_index]} ({wind_directions[dir_index]})"
            )
        else:
            wind_info = f"{weather_data.wind_speed} {speed_unit}"
        add_row("Wind", wind_info)

        pressure_bar = "█" * int(
            weather_data.pressure_hpa / 100
        )  # Simple bar visualization
        add_row("Pressure", f"{weather_data.pressure_hpa} hPa {pressure_bar}")

        # Render table to console
        console.print(table)

        # Return captured output (includes ANSI escape codes)
        return output.getvalue()
