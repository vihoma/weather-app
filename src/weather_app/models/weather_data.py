"""Data models for weather information."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherData:
    """Structured weather data container."""

    city: str
    units: str
    status: str
    detailed_status: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction_deg: Optional[float]
    precipitation_probability: Optional[int]
    clouds: Optional[int]
    visibility_distance: Optional[float]
    pressure_hpa: float
    icon_code: Optional[int] = None

    WEATHER_EMOJI_MAP = {
        "clear": "☀️",
        "scattered clouds": "🌤️",
        "broken clouds": "🌥️",
        "few clouds": "🌥️",
        "overcast clouds": "☁️",
        "light rain": "🌦️",
        "rain": "🌧️",
        "drizzle": "💧",
        "snow": "❄️",
        "sleet": "🌨️",
        "mist": "🌫️",
        "haze": "🌫️",
        "fog": "🌫️",
        "thunderstorm": "⛈️",
        "windy": "💨",
        "sunny": "☀️",
        "clouds": "☁️",
    }

    def get_emoji(self) -> str:
        """Get emoji for weather status."""
        status_lower = self.detailed_status.lower()
        for key, emoji in self.WEATHER_EMOJI_MAP.items():
            if key in status_lower:
                return emoji
        return "🌈"
