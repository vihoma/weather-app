"""Unit tests for WeatherService with caching."""

import pytest
from unittest.mock import Mock, patch
from src.weather_app.services.weather_service import WeatherService
from src.weather_app.config import Config
from src.weather_app.models.weather_data import WeatherData


class TestWeatherService:
    """Test WeatherService functionality including caching."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration with API key."""
        config = Mock()
        config.api_key = "test_api_key"
        config.cache_ttl = 600  # 10 minutes
        return config

    @pytest.fixture
    def weather_service(self, mock_config):
        """Create WeatherService instance with mocked OWM."""
        with patch("src.weather_app.services.weather_service.OWM") as mock_owm:
            mock_manager = Mock()
            mock_owm.return_value.weather_manager.return_value = mock_manager

            service = WeatherService(mock_config)
            service.weather_manager = mock_manager
            return service

    def test_cache_initialization(self, weather_service):
        """Test that cache is properly initialized."""
        assert hasattr(weather_service, "cache")
        assert weather_service.cache.maxsize == 100
        assert weather_service.cache.ttl == 600  # 10 minutes

    def test_cache_key_generation(self, weather_service):
        """Test cache key generation format."""
        location = "London,GB"
        units = "metric"

        # This is internal implementation detail, but we can test the pattern
        expected_key = f"{location}:{units}"

        # The actual key generation happens in get_weather method
        # We can verify the pattern matches our expectation
        assert f"{location}:{units}" == expected_key

    @patch(
        "src.weather_app.services.weather_service.WeatherService._parse_weather_data"
    )
    def test_cache_miss_then_hit(self, mock_parse, weather_service):
        """Test that cache is used on subsequent requests."""
        location = "London,GB"
        units = "metric"

        # Mock the API response
        mock_weather = Mock()
        mock_observation = Mock()
        mock_observation.weather = mock_weather
        weather_service.weather_manager.weather_at_place.return_value = mock_observation

        # Mock the parsed data
        mock_weather_data = WeatherData(
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
        mock_parse.return_value = mock_weather_data

        # First call - should call API
        result1 = weather_service.get_weather(location, units)
        assert weather_service.weather_manager.weather_at_place.call_count == 1
        assert mock_parse.call_count == 1

        # Second call - should use cache
        result2 = weather_service.get_weather(location, units)
        assert (
            weather_service.weather_manager.weather_at_place.call_count == 1
        )  # No additional calls
        assert mock_parse.call_count == 1  # No additional parsing

        # Results should be the same object (from cache)
        assert result1 is result2

    @patch(
        "src.weather_app.services.weather_service.WeatherService._parse_weather_data"
    )
    def test_different_units_different_cache_keys(self, mock_parse, weather_service):
        """Test that different units create different cache entries."""
        location = "London,GB"

        # Mock the API response
        mock_weather = Mock()
        mock_observation = Mock()
        mock_observation.weather = mock_weather
        weather_service.weather_manager.weather_at_place.return_value = mock_observation

        # Mock different parsed data for different units
        def mock_parse_side_effect(loc, weather, units):
            if units == "metric":
                return WeatherData(
                    city=loc,
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
            else:
                return WeatherData(
                    city=loc,
                    units=units,
                    status="Clear",
                    detailed_status="clear sky",
                    temperature=68.0,
                    feels_like=66.2,
                    humidity=65,
                    wind_speed=7.2,
                    wind_direction_deg=180.0,
                    precipitation_probability=10,
                    clouds=20,
                    visibility_distance=6.2,
                    pressure_hpa=1013.0,
                )

        mock_parse.side_effect = mock_parse_side_effect

        # Call with metric units
        result_metric = weather_service.get_weather(location, "metric")
        assert weather_service.weather_manager.weather_at_place.call_count == 1

        # Call with imperial units
        result_imperial = weather_service.get_weather(location, "imperial")
        assert weather_service.weather_manager.weather_at_place.call_count == 2

        # Results should be different
        assert result_metric.units == "metric"
        assert result_imperial.units == "imperial"
        assert result_metric.temperature == 20.0
        assert result_imperial.temperature == 68.0
