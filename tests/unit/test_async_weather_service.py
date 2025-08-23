"""Unit tests for AsyncWeatherService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.weather_app.services.async_weather_service import AsyncWeatherService
from src.weather_app.config import Config
from src.weather_app.exceptions import (
    LocationNotFoundError,
    APIRequestError,
    NetworkError,
    DataParsingError,
)


class TestAsyncWeatherService:
    """Test cases for AsyncWeatherService."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = MagicMock()
        config.api_key = "test_api_key"
        config.cache_ttl = 600
        config.request_timeout = 30
        return config

    @pytest.fixture
    def weather_service(self, mock_config):
        """Create an AsyncWeatherService instance."""
        return AsyncWeatherService(mock_config)

    @pytest.mark.asyncio
    async def test_get_weather_cached(self, weather_service):
        """Test that cached weather data is returned."""
        # Mock data
        mock_weather_data = MagicMock()
        cache_key = "London,GB:metric"

        # Add to cache
        weather_service.cache[cache_key] = mock_weather_data

        # Call method
        result = await weather_service.get_weather("London,GB", "metric")

        # Verify cached data is returned
        assert result == mock_weather_data

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_success(self, mock_get, weather_service):
        """Test successful weather data retrieval."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "weather": [{"main": "Clear", "description": "clear sky", "id": 800}],
                "main": {
                    "temp": 20.5,
                    "feels_like": 21.0,
                    "humidity": 65,
                    "pressure": 1013,
                },
                "wind": {"speed": 3.5, "deg": 180},
                "clouds": {"all": 0},
                "visibility": 10000,
                "name": "London",
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        # Call method
        result = await weather_service.get_weather("London,GB", "metric")

        # Verify result
        assert result.city == "London,GB"
        assert result.temperature == 20.5
        assert result.detailed_status == "Clear sky"
        assert result.humidity == 65

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_location_not_found(self, mock_get, weather_service):
        """Test handling of location not found error."""
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        # Verify exception is raised
        with pytest.raises(LocationNotFoundError):
            await weather_service.get_weather("InvalidCity,XX", "metric")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_api_error(self, mock_get, weather_service):
        """Test handling of API error."""
        # Mock 500 response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        # Verify exception is raised
        with pytest.raises(APIRequestError):
            await weather_service.get_weather("London,GB", "metric")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_timeout(self, mock_get, weather_service):
        """Test handling of timeout error."""
        # Mock timeout
        mock_get.side_effect = asyncio.TimeoutError()

        # Verify exception is raised
        with pytest.raises(NetworkError):
            await weather_service.get_weather("London,GB", "metric")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_network_error(self, mock_get, weather_service):
        """Test handling of network error."""
        # Mock network error
        mock_get.side_effect = ConnectionError("Network error")

        # Verify exception is raised
        with pytest.raises(NetworkError):
            await weather_service.get_weather("London,GB", "metric")

    def test_is_coordinates_valid(self, weather_service):
        """Test coordinate validation with valid coordinates."""
        assert weather_service._is_coordinates("51.5074,-0.1278") is True
        assert weather_service._is_coordinates("-33.8688,151.2093") is True

    def test_is_coordinates_invalid(self, weather_service):
        """Test coordinate validation with invalid coordinates."""
        assert weather_service._is_coordinates("London,GB") is False
        assert weather_service._is_coordinates("invalid") is False
        assert weather_service._is_coordinates("91.0,181.0") is False  # Out of bounds

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_weather_with_coordinates(self, mock_get, weather_service):
        """Test weather retrieval using coordinates."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "weather": [{"main": "Clear", "description": "clear sky", "id": 800}],
                "main": {
                    "temp": 20.5,
                    "feels_like": 21.0,
                    "humidity": 65,
                    "pressure": 1013,
                },
                "wind": {"speed": 3.5, "deg": 180},
                "clouds": {"all": 0},
                "visibility": 10000,
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        # Call method with coordinates
        result = await weather_service.get_weather("51.5074,-0.1278", "metric")

        # Verify result
        assert result.city == "51.5074,-0.1278"
        assert result.temperature == 20.5
