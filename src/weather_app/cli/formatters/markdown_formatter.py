"""Markdown formatter for weather data."""

from weather_app.cli.output_formatters import BaseFormatter
from weather_app.models.weather_data import WeatherData


class MarkdownFormatter(BaseFormatter):
    """Formatter that outputs weather data as Markdown."""

    def __init__(self, **kwargs) -> None:
        """Initialize Markdown formatter (ignores extra arguments)."""
        super().__init__()
        # Accept but ignore any kwargs for compatibility

    def format(self, weather_data: WeatherData) -> str:
        """Convert WeatherData to Markdown.

        Args:
            weather_data: The weather data to format.

        Returns:
            Markdown string with headings, tables, and emojis.
        """
        # Handle None values
        precip_prob = weather_data.precipitation_probability
        precip_str = f"{precip_prob}%" if precip_prob is not None else "N/A"
        visibility = weather_data.visibility_distance
        visibility_str = f"{visibility} meters" if visibility is not None else "N/A"
        wind_dir = weather_data.wind_direction_deg
        wind_dir_str = f"{wind_dir}°" if wind_dir is not None else "N/A"

        # Build a simple Markdown representation
        lines = [
            f"# Weather Report for {weather_data.city}",
            "",
            f"**Status**: {weather_data.detailed_status} {weather_data.get_emoji()}",
            f"**Temperature**: {weather_data.temperature}°{weather_data.units.upper()}",
            f"**Feels like**: {weather_data.feels_like}°{weather_data.units.upper()}",
            f"**Humidity**: {weather_data.humidity}%",
            f"**Wind**: {weather_data.wind_speed} m/s, direction {wind_dir_str}",
            f"**Pressure**: {weather_data.pressure_hpa} hPa",
            f"**Visibility**: {visibility_str}",
            f"**Cloud cover**: {weather_data.clouds}%",
            f"**Precipitation probability**: {precip_str}",
            "",
            f"*Units: {weather_data.units}*",
        ]
        return "\n".join(lines)
