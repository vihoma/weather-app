"""JSON formatter for weather data."""

import dataclasses
import json

from weather_app.cli.output_formatters import BaseFormatter
from weather_app.models.weather_data import WeatherData


class JSONFormatter(BaseFormatter):
    """Formatter that outputs weather data as JSON."""

    def __init__(self, **kwargs) -> None:
        """Initialize JSON formatter (ignores extra arguments)."""
        super().__init__()
        # Accept but ignore any kwargs for compatibility

    def format(self, weather_data: WeatherData) -> str:
        """Convert WeatherData to JSON string.

        Args:
            weather_data: The weather data to format.

        Returns:
            JSON string with indentation.
        """
        # Convert WeatherData dataclass to dict
        data = dataclasses.asdict(weather_data)
        return json.dumps(data, indent=2, default=str)
