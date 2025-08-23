"""Async weather data operations using aiohttp and OpenWeatherMap API."""

import asyncio
import logging
from typing import Dict, Any
import aiohttp
from async_timeout import timeout
from cachetools import TTLCache
from ..models.weather_data import WeatherData
from ..config import Config
from ..exceptions import (
    LocationNotFoundError,
    APIRequestError,
    NetworkError,
    RateLimitError,
    DataParsingError,
)

logger = logging.getLogger(__name__)


class AsyncWeatherService:
    """Handles all async interactions with OpenWeatherMap API."""

    def __init__(self, config: Config):
        self.api_key = config.api_key
        if not self.api_key:
            logger.error("API key is required but not provided")
            raise ValueError("API key is required")

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = config.request_timeout

        # Initialize cache with configurable TTL and max 100 items
        self.cache = TTLCache(maxsize=100, ttl=config.cache_ttl)
        logger.debug("AsyncWeatherService initialized successfully with caching")

    async def get_weather(self, location: str, units: str) -> WeatherData:
        """
        Get current weather data for a location with caching.

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
            logger.info("Returning cached weather data for: %s", location)
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
            logger.info("Weather data cached successfully for %s", location)

            return weather_data

        except Exception as e:
            logger.error(
                "Failed to fetch weather data for %s: %s", location, e, exc_info=True
            )
            raise

    async def _fetch_weather_data(self, location: str, units: str) -> WeatherData:
        """Fetch weather data from OpenWeatherMap API."""
        # Determine if location is coordinates or city name
        if self._is_coordinates(location):
            lat, lon = location.split(",")
            url = f"{self.base_url}/weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
        else:
            url = f"{self.base_url}/weather?q={location}&appid={self.api_key}&units={units}"

        try:
            async with aiohttp.ClientSession() as session:
                async with timeout(self.timeout):
                    async with session.get(url) as response:
                        if response.status == 404:
                            logger.warning("Location not found: %s", location)
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
            logger.error("Request timeout for location: %s", location)
            raise NetworkError(
                "Request timeout. Please check your internet connection."
            )
        except (aiohttp.ClientError, ConnectionError) as e:
            logger.error("Network error for location %s: %s", location, e)
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

    async def close(self):
        """Close any open connections."""
        # aiohttp sessions are context managers, but this provides explicit cleanup
        pass
