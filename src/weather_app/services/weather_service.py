"""Core weather data operations using PyOWM."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
            location,
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
        try:
            cache_path = Path(cache_file_path).expanduser()
            if not cache_path.exists():
                logger.debug("Cache file does not exist: %s", cache_path)
                return

            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            now = datetime.now(timezone.utc)
            ttl_delta = timedelta(seconds=self.config.cache_ttl)
            loaded = 0
            skipped_expired = 0
            skipped_legacy = 0

            for cache_key, entry in cache_data.items():
                # Detect legacy format (bare dict, no "data" wrapper)
                if not isinstance(entry, dict) or "data" not in entry:
                    skipped_legacy += 1
                    continue

                # Check fetched_at expiry
                fetched_at: datetime | None = None
                fetched_at_str = entry.get("fetched_at")
                if fetched_at_str:
                    try:
                        fetched_at = datetime.fromisoformat(fetched_at_str)
                        if fetched_at.tzinfo is None:
                            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                        if now - fetched_at > ttl_delta:
                            skipped_expired += 1
                            continue
                    except (ValueError, TypeError):
                        skipped_legacy += 1
                        continue

                try:
                    weather_data = WeatherData.model_validate(entry["data"])
                    self.cache[cache_key] = weather_data
                    self._cache_metadata[cache_key] = fetched_at or now
                    loaded += 1
                except Exception as e:
                    logger.warning("Skipping corrupt cache entry %s: %s", cache_key, e)

            logger.info(
                "Loaded %d cache items from %s (skipped: %d expired, %d legacy)",
                loaded,
                cache_path,
                skipped_expired,
                skipped_legacy,
            )
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            logger.warning("Failed to load cache from %s: %s", cache_file_path, e)

    def _save_cache_to_disk(self, cache_file_path: str) -> None:
        """Save cache to JSON file with fetched_at timestamps.

        Only saves non-expired entries. Uses the ``_cache_metadata`` dict
        for accurate fetch timestamps.
        """
        try:
            cache_path = Path(cache_file_path).expanduser()
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            now = datetime.now(timezone.utc)
            ttl = self.config.cache_ttl

            cache_data: dict[str, dict[str, Any]] = {}
            for cache_key, weather_data in self.cache.items():
                fetched_at = self._cache_metadata.get(cache_key)
                # Skip entries that are already expired
                if fetched_at is not None and (now - fetched_at).total_seconds() >= ttl:
                    continue
                cache_data[cache_key] = {
                    "data": weather_data.model_dump(),
                    "fetched_at": (fetched_at or now).isoformat(),
                }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug("Saved %d cache items to %s", len(cache_data), cache_path)
        except (IOError, PermissionError) as e:
            logger.warning("Failed to save cache to %s: %s", cache_file_path, e)

    def save_cache(self) -> None:
        """Explicitly save cache to disk."""
        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)
