"""Core weather data operations using PyOWM."""

import json
import logging
from pathlib import Path
from typing import Any
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import PyOWMError, NotFoundError
from cachetools import TTLCache
from weather_app.models.weather_data import WeatherData
from weather_app.config import Config
from weather_app.exceptions import (
    LocationNotFoundError,
    APIRequestError,
)

logger = logging.getLogger(__name__)


class WeatherService:
    """Handles all interactions with OpenWeatherMap API."""

    def __init__(self, config: Config):
        self.config_dict = get_default_config()
        self.config_dict["use_ssl"] = True

        if not config.api_key:
            logger.error("API key is required but not provided")
            raise ValueError("API key is required")

        logger.info("Initializing WeatherService with API key")
        self.owm = OWM(config.api_key, self.config_dict)
        self.weather_manager = self.owm.weather_manager()

        # Store config reference for cache persistence
        self.config = config

        # Initialize cache with configurable TTL and max 100 items
        self.cache = TTLCache(maxsize=100, ttl=config.cache_ttl)
        logger.debug("WeatherService initialized successfully with caching")

        # Load cache from disk if persistence is enabled
        if config.cache_persist:
            self._load_cache_from_disk(config.cache_file)

    def get_weather(self, location: str, units: str) -> WeatherData:
        """
        Get current weather data for a location with caching.

        Args:
            location: City name and country code (e.g., "London,GB")
            units: Measurement system (metric/imperial/default)

        Returns:
            WeatherData: Parsed weather data
        """
        # Create cache key
        cache_key = f"{location}:{units}"

        # Check cache first
        if cache_key in self.cache:
            logger.info("Returning cached weather data for: %s", location)
            return self.cache[cache_key]

        logger.info(
            "Fetching fresh weather data for location: %s with units: %s",
            location,
            units,
        )

        try:
            logger.debug("Calling weather_at_place for location: %s", location)
            observation = self.weather_manager.weather_at_place(location)
            weather = observation.weather
            logger.debug("Successfully retrieved weather data for %s", location)

            parsed_data = self._parse_weather_data(location, weather, units)

            # Cache the result
            self.cache[cache_key] = parsed_data
            logger.info("Weather data cached successfully for %s", location)

            return parsed_data

        except NotFoundError as e:
            logger.warning("Location not found: %s", location)
            raise LocationNotFoundError(
                f"Location '{location}' not found. Please check the spelling and format (City,CC)."
            ) from e
        except PyOWMError as e:
            logger.error("API request failed for %s: %s", location, e, exc_info=True)
            raise APIRequestError(f"Failed to fetch weather data: {e}") from e

    def _parse_weather_data(
        self, location: str, weather: Any, units: str
    ) -> WeatherData:
        """Convert PyOWM weather object to our data model."""
        # Map our unit names to PyOWM's expected values
        temp_unit = {
            "metric": "celsius",
            "imperial": "fahrenheit",
            "default": "kelvin",
        }.get(units, "kelvin")

        dist_unit = {
            "metric": "kilometers",
            "imperial": "miles",
            "default": "meters",
        }.get(units, "meters")

        speed_unit = {
            "metric": "meters_sec",
            "imperial": "miles_hour",
            "default": "meters_sec",
        }.get(units, "meters_sec")

        return WeatherData(
            city=location,
            units=units,
            status=weather.status,
            detailed_status=weather.detailed_status.capitalize(),
            temperature=weather.temperature(temp_unit).get("temp", "N/A"),
            feels_like=weather.temperature(temp_unit).get("feels_like", "N/A"),
            humidity=weather.humidity,
            wind_speed=round(weather.wind(speed_unit).get("speed", 0), 2),
            wind_direction_deg=weather.wind().get("deg"),
            precipitation_probability=getattr(
                weather, "precipitation_probability", None
            ),
            clouds=weather.clouds,
            visibility_distance=weather.visibility(unit=dist_unit),
            pressure_hpa=weather.pressure.get("press"),
            icon_code=weather.weather_code,
        )

    def _load_cache_from_disk(self, cache_file_path: str) -> None:
        """Load cache from JSON file."""
        try:
            cache_path = Path(cache_file_path).expanduser()
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Convert loaded data back to WeatherData objects
                for cache_key, weather_dict in cache_data.items():
                    weather_data = WeatherData(**weather_dict)
                    self.cache[cache_key] = weather_data

                logger.info(
                    "Loaded %d cache items from %s", len(cache_data), cache_path
                )
            else:
                logger.debug("Cache file does not exist: %s", cache_path)
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            logger.warning("Failed to load cache from %s: %s", cache_file_path, e)

    def _save_cache_to_disk(self, cache_file_path: str) -> None:
        """Save cache to JSON file."""
        try:
            cache_path = Path(cache_file_path).expanduser()
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert cache to serializable format
            cache_data = {}
            for cache_key, weather_data in self.cache.items():
                cache_data[cache_key] = weather_data.__dict__

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug("Saved %d cache items to %s", len(cache_data), cache_path)
        except (IOError, PermissionError) as e:
            logger.warning("Failed to save cache to %s: %s", cache_file_path, e)

    def __del__(self):
        """Save cache to disk when service is destroyed."""
        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)
