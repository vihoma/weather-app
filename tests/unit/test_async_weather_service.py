"""Unit tests for AsyncWeatherService."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from weather_app.services.async_weather_service import AsyncWeatherService
from weather_app.config import Config
from weather_app.models.weather_data import WeatherData
from weather_app.exceptions import (
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

        # Verify params dict is used instead of embedding key in URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        called_url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert "appid" not in called_url, "API key should not be in the URL string"
        call_kwargs = call_args[1] if call_args[1] else {}
        assert "params" in call_kwargs, "params dict should be passed to session.get"
        assert call_kwargs["params"]["appid"] == "test_api_key"
        assert call_kwargs["params"]["q"] == "London,GB"
        assert call_kwargs["params"]["units"] == "metric"

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

        # Verify params dict uses lat/lon for coordinates
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert "params" in call_kwargs, "params dict should be passed to session.get"
        assert call_kwargs["params"]["lat"] == "51.5074"
        assert call_kwargs["params"]["lon"] == "-0.1278"
        assert call_kwargs["params"]["appid"] == "test_api_key"
        assert call_kwargs["params"]["units"] == "metric"
        assert "q" not in call_kwargs["params"], "City query param should not be present for coordinates"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_config):
        """Test AsyncWeatherService as async context manager."""
        async with AsyncWeatherService(mock_config) as svc:
            assert isinstance(svc, AsyncWeatherService)
        # After exiting, any open session should be closed

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_session(self, mock_config):
        """Test that __aexit__ closes the aiohttp session."""
        svc = AsyncWeatherService(mock_config)
        mock_session = AsyncMock()
        mock_session.closed = False
        svc._session = mock_session

        await svc.__aexit__(None, None, None)
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_session_uses_connector_and_timeout(self, weather_service):
        """Test that _ensure_session creates session with TCPConnector and ClientTimeout."""
        with patch("weather_app.services.async_weather_service.aiohttp.ClientSession") as mock_session_cls, \
             patch("weather_app.services.async_weather_service.aiohttp.TCPConnector") as mock_connector_cls, \
             patch("weather_app.services.async_weather_service.aiohttp.ClientTimeout") as mock_timeout_cls:
            mock_session_cls.return_value = MagicMock()
            mock_connector = MagicMock()
            mock_connector_cls.return_value = mock_connector
            mock_timeout = MagicMock()
            mock_timeout_cls.return_value = mock_timeout

            # Force new session creation
            weather_service._session = None
            await weather_service._ensure_session()

            mock_connector_cls.assert_called_once_with(limit=10, limit_per_host=5)
            mock_timeout_cls.assert_called_once_with(total=weather_service.timeout)
            mock_session_cls.assert_called_once_with(
                connector=mock_connector,
                timeout=mock_timeout,
            )

    # ------------------------------------------------------------------
    # Cache persistence with fetched_at timestamps
    # ------------------------------------------------------------------

    @staticmethod
    def _make_weather_data(location: str = "London,GB", units: str = "metric") -> WeatherData:
        """Create a minimal WeatherData fixture for cache tests."""
        return WeatherData(
            city=location,
            units=units,
            status="Clear",
            detailed_status="clear sky",
            temperature=20.0,
            feels_like=19.0,
            humidity=65,
            wind_speed=3.2,
            wind_direction_deg=180.0,
            precipitation_probability=10,
            clouds=20,
            visibility_distance=10000.0,
            pressure_hpa=1013.0,
        )

    def test_save_cache_writes_timestamped_format(self, mock_config):
        """_save_cache_to_disk writes entries in {data, fetched_at} format."""
        mock_config.cache_persist = False
        service = AsyncWeatherService(mock_config)
        wd = self._make_weather_data()
        cache_key = "London,GB:metric"
        service.cache[cache_key] = wd
        service._cache_metadata[cache_key] = datetime.now(timezone.utc)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name

        try:
            service.config.cache_persist = True
            service.config.cache_file = path
            service._save_cache_to_disk(path)

            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            assert cache_key in saved
            entry = saved[cache_key]
            assert "data" in entry
            assert "fetched_at" in entry
            assert entry["data"]["city"] == "London,GB"
        finally:
            Path(path).unlink()

    def test_load_cache_loads_fresh_entries(self, mock_config):
        """Fresh entries (within TTL) are loaded with their metadata."""
        mock_config.cache_persist = False
        service = AsyncWeatherService(mock_config)
        wd = self._make_weather_data()
        cache_key = "London,GB:metric"
        now = datetime.now(timezone.utc)

        cache_content = {
            cache_key: {
                "data": wd.model_dump(),
                "fetched_at": now.isoformat(),
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(cache_content, f)
            path = f.name

        try:
            service.config.cache_file = path
            service.config.cache_ttl = 600
            service._load_cache_from_disk(path)

            assert cache_key in service.cache
            assert cache_key in service._cache_metadata
            loaded = service.cache[cache_key]
            assert loaded.city == "London,GB"
            assert loaded.temperature == 20.0
        finally:
            Path(path).unlink()

    def test_load_cache_skips_expired_entries(self, mock_config):
        """Entries older than TTL are skipped on load."""
        mock_config.cache_persist = False
        service = AsyncWeatherService(mock_config)
        wd = self._make_weather_data()
        cache_key = "London,GB:metric"
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=1200)

        cache_content = {
            cache_key: {
                "data": wd.model_dump(),
                "fetched_at": expired_time.isoformat(),
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(cache_content, f)
            path = f.name

        try:
            service.config.cache_file = path
            service.config.cache_ttl = 600
            service._load_cache_from_disk(path)

            assert cache_key not in service.cache
            assert cache_key not in service._cache_metadata
        finally:
            Path(path).unlink()

    def test_load_cache_skips_legacy_format(self, mock_config):
        """Old-format entries (bare dict, no 'data' key) are discarded."""
        mock_config.cache_persist = False
        service = AsyncWeatherService(mock_config)
        wd = self._make_weather_data()
        cache_key = "London,GB:metric"

        cache_content = {cache_key: wd.model_dump()}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(cache_content, f)
            path = f.name

        try:
            service.config.cache_file = path
            service.config.cache_ttl = 600
            service._load_cache_from_disk(path)

            assert cache_key not in service.cache
        finally:
            Path(path).unlink()

    def test_save_cache_skips_expired_entries(self, mock_config):
        """_save_cache_to_disk filters out already-expired entries."""
        mock_config.cache_persist = False
        service = AsyncWeatherService(mock_config)
        wd = self._make_weather_data()
        fresh_key = "London,GB:metric"
        expired_key = "Paris,FR:metric"
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=1200)

        service.cache[fresh_key] = wd
        service._cache_metadata[fresh_key] = datetime.now(timezone.utc)
        service.cache[expired_key] = wd
        service._cache_metadata[expired_key] = expired_time

        service.config.cache_ttl = 600

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name

        try:
            service.config.cache_file = path
            service._save_cache_to_disk(path)

            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            assert fresh_key in saved
            assert expired_key not in saved
        finally:
            Path(path).unlink()
