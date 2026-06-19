"""Core weather data operations using PyOWM."""

import logging
from datetime import datetime, timezone
from typing import Any, cast

from cachetools import TTLCache
from pyowm.commons.exceptions import NotFoundError, PyOWMError
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config

from ..config import Config
from ..exceptions import APIRequestError, LocationNotFoundError
from ..models.weather_data import WeatherData
from ..utils import sanitize_string_for_logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Handles all interactions with OpenWeatherMap API."""

    def __init__(self, config: Config):
        """Initialize the weather service.

        Args:
            config: Configuration object containing API settings

        Raises:
            ValueError: If API key is not provided

        """
        self.config_dict: dict[str, Any] = cast(dict[str, Any], get_default_config())
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
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=config.cache_ttl)
        # Track when each cache entry was originally fetched (for persistence)
        self._cache_metadata: dict[str, datetime] = {}
        logger.debug("WeatherService initialized successfully with caching")

        # Load cache from disk if persistence is enabled
        if config.cache_persist:
            self._load_cache_from_disk(config.cache_file)

    def get_weather(self, location: str, units: str) -> WeatherData:
        """Get current weather data for a location with caching.

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
            logger.info(
                "Returning cached weather data for: %s",
                sanitize_string_for_logging(location),
            )
            return self.cache[cache_key]

        logger.info(
            "Fetching fresh weather data for location: %s with units: %s",
            sanitize_string_for_logging(location),
            units,
        )

        try:
            logger.debug(
                "Calling weather_at_place for location: %s",
                sanitize_string_for_logging(location),
            )
            observation = self.weather_manager.weather_at_place(location)
            if observation is None:
                raise LocationNotFoundError(
                    f"Location '{location}' not found. Please check the spelling and format (City,CC)."
                )
            weather = observation.weather
            logger.debug(
                "Successfully retrieved weather data for %s",
                sanitize_string_for_logging(location),
            )

            parsed_data = self._parse_weather_data(location, weather, units)

            # Cache the result
            self.cache[cache_key] = parsed_data
            self._cache_metadata[cache_key] = datetime.now(timezone.utc)
            logger.info(
                "Weather data cached successfully for %s",
                sanitize_string_for_logging(location),
            )

            return parsed_data

        except NotFoundError as e:
            logger.warning(
                "Location not found: %s", sanitize_string_for_logging(location)
            )
            raise LocationNotFoundError(
                f"Location '{location}' not found. Please check the spelling and format (City,CC)."
            ) from e
        except PyOWMError as e:
            logger.error(
                "API request failed for %s: %s",
                sanitize_string_for_logging(location),
                e,
                exc_info=True,
            )
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
        """Load cache from JSON file, skipping expired entries.

        Supports two formats:
        - New (timestamped): ``{"data": {...}, "fetched_at": "ISO..."}``
        - Old (legacy): bare weather dict — treated as expired, discarded.
        """
        from .cache_persistence import load_cache_from_disk as _load

        _load(
            cache_file_path=cache_file_path,
            cache_dir=self.config.cache_dir,
            cache_ttl=self.config.cache_ttl,
            in_memory_cache=self.cache,
            cache_metadata=self._cache_metadata,
            model_validate=WeatherData.model_validate,
        )

    def _save_cache_to_disk(self, cache_file_path: str) -> None:
        """Save cache to JSON file with fetched_at timestamps.

        Only saves non-expired entries. Uses the ``_cache_metadata`` dict
        for accurate fetch timestamps.
        """
        from .cache_persistence import save_cache_to_disk as _save

        _save(
            cache_file_path=cache_file_path,
            cache_dir=self.config.cache_dir,
            cache_ttl=self.config.cache_ttl,
            in_memory_cache=self.cache,
            cache_metadata=self._cache_metadata,
        )

    def save_cache(self) -> None:
        """Explicitly save cache to disk."""
        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)
