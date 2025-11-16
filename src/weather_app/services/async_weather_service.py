"""Async weather data operations using aiohttp and OpenWeatherMap API."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from async_timeout import timeout
from cachetools import TTLCache

from ..config import Config
from ..exceptions import (APIRequestError, DataParsingError,
                          LocationNotFoundError, NetworkError, RateLimitError)
from ..models.weather_data import WeatherData
from ..utils import sanitize_string_for_logging

logger = logging.getLogger(__name__)


class AsyncWeatherService:
    """Handles all async interactions with OpenWeatherMap API."""

    def __init__(self, config: Config):
        """Initialize the async weather service.

        Args:
            config: Configuration object containing API settings

        Raises:
            ValueError: If API key is not provided

        """
        self.api_key = config.api_key
        if not self.api_key:
            logger.error("API key is required but not provided")
            raise ValueError("API key is required")

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = config.request_timeout

        # Store config reference for cache persistence
        self.config = config

        # Initialize cache with configurable TTL and max 100 items
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=config.cache_ttl)

        # Shared aiohttp session for connection reuse
        self._session: Optional[aiohttp.ClientSession] = None

        logger.debug("AsyncWeatherService initialized successfully with caching")

        # Load cache from disk if persistence is enabled
        if config.cache_persist:
            self._load_cache_from_disk(config.cache_file)

    async def get_weather(self, location: str, units: str) -> WeatherData:
        """Get current weather data for a location with caching.

        Args:
            location: City name and country code (e.g., "London,GB") or coordinates
            units: Measurement system (metric/imperial/standard)

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
            weather_data = await self._fetch_weather_data(location, units)

            # Cache the result
            self.cache[cache_key] = weather_data
            logger.info(
                "Weather data cached successfully for %s",
                sanitize_string_for_logging(location),
            )

            return weather_data

        except (
            LocationNotFoundError,
            APIRequestError,
            NetworkError,
            RateLimitError,
            DataParsingError,
        ):
            # Re-raise specific exceptions that we already handle
            raise
        except Exception as e:
            logger.error(
                "Unexpected error fetching weather data for %s: %s",
                sanitize_string_for_logging(location),
                e,
                exc_info=True,
            )
            raise APIRequestError(f"Unexpected error fetching weather data: {e}") from e

    async def _fetch_weather_data(self, location: str, units: str) -> WeatherData:
        """Fetch weather data from OpenWeatherMap API."""
        # Determine if location is coordinates or city name
        if self._is_coordinates(location):
            lat, lon = location.split(",")
            url = f"{self.base_url}/weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
        else:
            url = f"{self.base_url}/weather?q={location}&appid={self.api_key}&units={units}"

        try:
            session = await self._ensure_session()
            async with timeout(self.timeout):
                async with session.get(url) as response:
                    if response.status == 404:
                        logger.warning(
                            "Location not found: %s",
                            sanitize_string_for_logging(location),
                        )
                        raise LocationNotFoundError(
                            f"Location '{location}' not found. Please check the spelling and format (City,CC)."
                        )

                    if response.status == 401:
                        logger.error("Invalid API key")
                        raise APIRequestError(
                            "Invalid API key. Please check your OpenWeatherMap API key."
                        )

                    if response.status == 429:
                        logger.warning("Rate limit exceeded")
                        raise RateLimitError(
                            "Rate limit exceeded. Please wait before making more requests."
                        )

                    if response.status != 200:
                        logger.error(
                            "API request failed with status %d", response.status
                        )
                        raise APIRequestError(
                            f"API request failed with status {response.status}"
                        )

                    data = await response.json()
                    return self._parse_weather_data(location, data, units)

        except asyncio.TimeoutError:
            logger.error(
                "Request timeout for location: %s",
                sanitize_string_for_logging(location),
            )
            raise NetworkError(
                "Request timeout. Please check your internet connection."
            )
        except (aiohttp.ClientError, ConnectionError) as e:
            logger.error(
                "Network error for location %s: %s",
                sanitize_string_for_logging(location),
                e,
            )
            raise NetworkError(f"Network error: {e}")

    def _is_coordinates(self, location: str) -> bool:
        """Check if location string represents coordinates."""
        try:
            parts = location.split(",")
            if len(parts) != 2:
                return False
            lat, lon = map(float, parts)
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except ValueError:
            return False

    def _parse_weather_data(
        self, location: str, data: Dict[str, Any], units: str
    ) -> WeatherData:
        """Convert OpenWeatherMap API response to WeatherData model."""
        try:
            weather = data["weather"][0]
            main = data["main"]
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})

            # Get temperature unit symbol

            # Get speed unit

            return WeatherData(
                city=location,
                units=units,
                status=weather["main"],
                detailed_status=weather["description"].capitalize(),
                temperature=round(main["temp"], 1),
                feels_like=round(main["feels_like"], 1),
                humidity=main["humidity"],
                wind_speed=round(wind.get("speed", 0), 2),
                wind_direction_deg=wind.get("deg"),
                precipitation_probability=data.get(
                    "pop"
                ),  # Probability of precipitation
                clouds=clouds.get("all", 0),
                visibility_distance=data.get("visibility"),
                pressure_hpa=main["pressure"],
                icon_code=weather["id"],
            )

        except (KeyError, TypeError, IndexError) as e:
            logger.error("Failed to parse weather data: %s", e, exc_info=True)
            raise DataParsingError(f"Failed to parse weather data: {e}")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Get or create a shared aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            logger.debug("Created new aiohttp session")
        return self._session

    async def close(self) -> None:
        """Close any open connections and save cache if persistence is enabled."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed aiohttp session")

        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)

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

    def save_cache(self) -> None:
        """Explicitly save cache to disk."""
        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)

    def __del__(self):
        """Save cache to disk when service is destroyed."""
        # Note: __del__ methods are unreliable for persistence
        # Use save_cache() method explicitly instead
        pass
