"""Async weather data operations using aiohttp and OpenWeatherMap API."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiohttp
from async_timeout import timeout
from cachetools import TTLCache

from ..config import Config
from ..exceptions import (
    APIRequestError,
    DataParsingError,
    LocationNotFoundError,
    NetworkError,
    RateLimitError,
)
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
        api_key = config.api_key
        if not api_key:
            logger.error("API key is required but not provided")
            raise ValueError("API key is required")
        self.api_key: str = api_key

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = config.request_timeout

        # Store config reference for cache persistence
        self.config = config

        # Initialize cache with configurable TTL and max 100 items
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=config.cache_ttl)
        # Track when each cache entry was originally fetched (for persistence)
        self._cache_metadata: dict[str, datetime] = {}

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
            sanitize_string_for_logging(location),
            units,
        )

        try:
            weather_data = await self._fetch_weather_data(location, units)

            # Cache the result
            self.cache[cache_key] = weather_data
            self._cache_metadata[cache_key] = datetime.now(timezone.utc)
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
        url = f"{self.base_url}/weather"
        # NOTE: OpenWeatherMap 2.5 API requires the API key as a query parameter
        # (``appid``). The free-tier API does not support bearer-token or
        # ``x-api-key`` header authentication.  This means the key appears in
        # request URLs — mitigated by HTTPS encryption in transit.
        params: Dict[str, str] = {"appid": self.api_key, "units": units}

        if self._is_coordinates(location):
            lat, lon = location.split(",")
            params["lat"] = lat.strip()
            params["lon"] = lon.strip()
        else:
            params["q"] = location.strip()

        try:
            session = await self._ensure_session()
            async with timeout(self.timeout):
                safe_params = {
                    k: ("***" if k == "appid" else v) for k, v in params.items()
                }
                logger.debug("Making API request to: %s params=%s", url, safe_params)

                async with session.get(url, params=params) as response:
                    return await self._handle_response(response, location, units)

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

    async def _handle_response(
        self, response: aiohttp.ClientResponse, location: str, units: str
    ) -> WeatherData:
        """Handle API response and convert to WeatherData."""
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
            logger.error("API request failed with status %d", response.status)
            raise APIRequestError(f"API request failed with status {response.status}")

        data = await response.json()
        return self._parse_weather_data(location, data, units)

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
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
            )
            client_timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=client_timeout,
            )
            logger.debug("Created new aiohttp session with pool limits and timeout")
        return self._session

    async def close(self) -> None:
        """Close any open connections and save cache if persistence is enabled."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed aiohttp session")

        if hasattr(self, "config") and self.config.cache_persist:
            self._save_cache_to_disk(self.config.cache_file)

    async def __aenter__(self) -> "AsyncWeatherService":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager, closing resources."""
        await self.close()

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
