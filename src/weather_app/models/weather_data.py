"""Data models for weather information."""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class WeatherData(BaseModel):
    """Structured weather data container.

    Uses Pydantic BaseModel for built-in validation, type coercion,
    and serialization via model_dump() / model_validate().
    """

    model_config = ConfigDict(extra="ignore")

    city: str
    units: str
    status: str
    detailed_status: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction_deg: float | None
    precipitation_probability: int | None
    clouds: int | None
    visibility_distance: float | None
    pressure_hpa: float
    icon_code: int | None = None

    WEATHER_EMOJI_MAP: ClassVar[dict[str, str]] = {
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
