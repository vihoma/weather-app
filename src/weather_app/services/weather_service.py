"""Core weather data operations using PyOWM."""

import logging
from typing import Any
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import PyOWMError, NotFoundError
from cachetools import TTLCache
from ..models.weather_data import WeatherData
from ..config import Config
from ..exceptions import (
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

        # Initialize cache with configurable TTL and max 100 items
        self.cache = TTLCache(maxsize=100, ttl=config.cache_ttl)
        logger.debug("WeatherService initialized successfully with caching")

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
