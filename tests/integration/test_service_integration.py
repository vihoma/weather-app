"""Integration tests for weather service components with real API calls.

These tests verify the integration between services and external APIs.
They require a valid OpenWeatherMap API key for testing.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from weather_app.config import Config
from weather_app.services.weather_service import WeatherService
from weather_app.services.async_weather_service import AsyncWeatherService
from weather_app.services.location_service import LocationService
from weather_app.exceptions import (
    LocationNotFoundError,
    APIRequestError,
    InvalidLocationError,
)


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests for service components with real API calls."""

    @pytest.fixture
    def test_api_key(self):
        """Get test API key from environment."""
        api_key = os.getenv("OWM_API_KEY")
        if not api_key or api_key == "test_api_key_placeholder":
            pytest.skip("OWM_API_KEY environment variable not set or is placeholder")
        return api_key

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary directory for cache files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def integration_config(self, test_api_key, temp_cache_dir):
        """Create configuration for integration tests."""
        # Set environment variables for Config to read
        os.environ["OWM_API_KEY"] = test_api_key
        os.environ["CACHE_TTL"] = "300"  # 5 minutes for tests
        os.environ["REQUEST_TIMEOUT"] = "30"
        os.environ["CACHE_PERSIST"] = "true"
        os.environ["CACHE_FILE"] = str(Path(temp_cache_dir) / "test_cache.json")
        
        config = Config()
        return config

    @pytest.mark.api
    def test_weather_service_with_real_api(self, integration_config):
        """Test WeatherService with real OpenWeatherMap API calls."""
        # Create service instance
        service = WeatherService(integration_config)
        
        # Test with known valid location
        location = "London,GB"
        units = "metric"
        
        # Fetch weather data
        weather_data = service.get_weather(location, units)
        
        # Verify data structure
        assert weather_data.city == location
        assert weather_data.units == units
        assert isinstance(weather_data.temperature, (int, float))
        assert isinstance(weather_data.humidity, int)
        assert isinstance(weather_data.pressure_hpa, (int, float))
        assert weather_data.detailed_status is not None
        assert weather_data.status is not None
        
        # Verify cache was populated
        cache_key = f"{location}:{units}"
        assert cache_key in service.cache
        assert service.cache[cache_key] == weather_data

    @pytest.mark.api
    def test_weather_service_invalid_location(self, integration_config):
        """Test WeatherService error handling with invalid location."""
        service = WeatherService(integration_config)
        
        # Test with invalid location
        invalid_location = "InvalidCity123,XX"
        
        with pytest.raises(LocationNotFoundError):
            service.get_weather(invalid_location, "metric")

    @pytest.mark.api
    def test_weather_service_cache_functionality(self, integration_config):
        """Test WeatherService caching functionality with real API."""
        service = WeatherService(integration_config)
        
        location = "Paris,FR"
        units = "metric"
        
        # First call - should hit API
        first_result = service.get_weather(location, units)
        
        # Second call - should use cache
        second_result = service.get_weather(location, units)
        
        # Results should be the same object (from cache)
        assert first_result is second_result
        
        # Verify data integrity
        assert first_result.city == second_result.city
        assert first_result.temperature == second_result.temperature

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_async_weather_service_with_real_api(self, integration_config):
        """Test AsyncWeatherService with real OpenWeatherMap API calls."""
        # Create service instance
        service = AsyncWeatherService(integration_config)
        
        try:
            # Test with known valid location
            location = "New York,US"
            units = "imperial"
            
            # Fetch weather data
            weather_data = await service.get_weather(location, units)
            
            # Verify data structure
            assert weather_data.city == location
            assert weather_data.units == units
            assert isinstance(weather_data.temperature, (int, float))
            assert isinstance(weather_data.humidity, int)
            assert isinstance(weather_data.pressure_hpa, (int, float))
            assert weather_data.detailed_status is not None
            assert weather_data.status is not None
            
            # Verify cache was populated
            cache_key = f"{location}:{units}"
            assert cache_key in service.cache
            assert service.cache[cache_key] == weather_data
            
        finally:
            # Clean up connections
            await service.close()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_async_weather_service_with_coordinates(self, integration_config):
        """Test AsyncWeatherService with coordinate-based location."""
        service = AsyncWeatherService(integration_config)
        
        try:
            # Test with coordinates (London coordinates)
            coordinates = "51.5074,-0.1278"
            units = "metric"
            
            # Fetch weather data
            weather_data = await service.get_weather(coordinates, units)
            
            # Verify data structure
            assert weather_data.city == coordinates
            assert weather_data.units == units
            assert isinstance(weather_data.temperature, (int, float))
            assert isinstance(weather_data.humidity, int)
            
        finally:
            await service.close()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_async_weather_service_invalid_location(self, integration_config):
        """Test AsyncWeatherService error handling with invalid location."""
        service = AsyncWeatherService(integration_config)
        
        try:
            # Test with invalid location
            invalid_location = "InvalidCity456,YY"
            
            with pytest.raises(LocationNotFoundError):
                await service.get_weather(invalid_location, "metric")
                
        finally:
            await service.close()

    def test_location_service_geocoding_valid_city(self):
        """Test LocationService geocoding with valid city name."""
        service = LocationService(timeout=10)
        
        # Test with valid city,country format
        location = "London,GB"
        
        # Geocode location
        coordinates = service.geocode_location(location)
        
        # Verify coordinates are valid
        assert coordinates is not None
        lat, lon = coordinates
        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

    def test_location_service_geocoding_coordinates(self):
        """Test LocationService geocoding with coordinate input."""
        service = LocationService(timeout=10)
        
        # Test with coordinates
        coordinates_input = "51.5074,-0.1278"
        
        # Geocode coordinates (should return same coordinates)
        coordinates = service.geocode_location(coordinates_input)
        
        # Verify coordinates are returned correctly
        assert coordinates is not None
        lat, lon = coordinates
        assert lat == 51.5074
        assert lon == -0.1278

    def test_location_service_geocoding_invalid_location(self):
        """Test LocationService geocoding with invalid location."""
        service = LocationService(timeout=10)
        
        # Test with invalid location
        invalid_location = "InvalidCity789,ZZ"
        
        # Geocode should return None for invalid locations
        coordinates = service.geocode_location(invalid_location)
        
        assert coordinates is None

    def test_location_service_validation(self):
        """Test LocationService location validation."""
        service = LocationService()
        
        # Test valid formats
        assert service.validate_location_format("London,GB") is True
        assert service.validate_location_format("51.5074,-0.1278") is True
        assert service.validate_location_format("-33.8688,151.2093") is True
        
        # Test invalid formats
        assert service.validate_location_format("London") is False  # Missing country
        assert service.validate_location_format("London,UKK") is False  # Invalid country code
        assert service.validate_location_format("91.0,181.0") is False  # Out of bounds
        assert service.validate_location_format("invalid") is False

    def test_location_service_normalization(self):
        """Test LocationService location normalization."""
        service = LocationService()
        
        # Test valid normalization
        normalized = service.normalize_location("  London,GB  ")
        assert normalized == "London,GB"
        
        normalized = service.normalize_location("51.5074, -0.1278")
        assert normalized == "51.5074, -0.1278"
        
        # Test invalid normalization
        with pytest.raises(InvalidLocationError):
            service.normalize_location("")
            
        with pytest.raises(InvalidLocationError):
            service.normalize_location("London")

    @pytest.mark.api
    def test_service_coordination_valid_location(self, integration_config):
        """Test coordination between LocationService and WeatherService."""
        location_service = LocationService()
        weather_service = WeatherService(integration_config)
        
        # Test location validation and weather fetching
        location = "Tokyo,JP"
        units = "metric"
        
        # Validate location format
        assert location_service.validate_location_format(location) is True
        
        # Normalize location
        normalized = location_service.normalize_location(location)
        assert normalized == location
        
        # Fetch weather data
        weather_data = weather_service.get_weather(normalized, units)
        
        # Verify data
        assert weather_data.city == location
        assert isinstance(weather_data.temperature, (int, float))

    @pytest.mark.api
    def test_service_coordination_invalid_location(self, integration_config):
        """Test coordination error handling with invalid location."""
        location_service = LocationService()
        weather_service = WeatherService(integration_config)
        
        # Test invalid location
        invalid_location = "InvalidCity,XX"
        
        # Location validation should pass (format is correct)
        assert location_service.validate_location_format(invalid_location) is True
        
        # Normalization should pass (format is correct)
        normalized = location_service.normalize_location(invalid_location)
        assert normalized == invalid_location
        
        # Weather service should raise error
        with pytest.raises(LocationNotFoundError):
            weather_service.get_weather(normalized, "metric")

    @pytest.mark.api
    def test_cache_persistence_integration(self, integration_config, temp_cache_dir):
        """Test cache persistence functionality."""
        cache_file = Path(temp_cache_dir) / "persistence_test_cache.json"
        integration_config.cache_file = str(cache_file)
        
        # Create first service instance and fetch data
        service1 = WeatherService(integration_config)
        location = "Berlin,DE"
        units = "metric"
        
        # Fetch and cache data
        weather_data1 = service1.get_weather(location, units)
        
        # Save cache to disk
        service1.save_cache()
        
        # Verify cache file was created
        assert cache_file.exists()
        
        # Create second service instance (should load cache)
        service2 = WeatherService(integration_config)
        
        # Fetch same data - should come from cache
        weather_data2 = service2.get_weather(location, units)
        
        # Data should be the same
        assert weather_data1.city == weather_data2.city
        assert weather_data1.temperature == weather_data2.temperature
        assert weather_data1.humidity == weather_data2.humidity

    @pytest.mark.api
    def test_cache_ttl_functionality(self, integration_config):
        """Test cache TTL functionality with real API."""
        # Set very short TTL for testing
        integration_config.cache_ttl = 1  # 1 second
        
        service = WeatherService(integration_config)
        location = "Rome,IT"
        units = "metric"
        
        # First call - should hit API
        first_result = service.get_weather(location, units)
        
        # Second call immediately - should use cache
        second_result = service.get_weather(location, units)
        assert first_result is second_result
        
        # Wait for cache to expire
        import time
        time.sleep(1.1)
        
        # Third call after TTL - should hit API again
        third_result = service.get_weather(location, units)
        
        # Results should have same data but different objects
        assert first_result is not third_result
        assert first_result.city == third_result.city
        assert first_result.temperature == third_result.temperature

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_async_cache_persistence_integration(self, integration_config, temp_cache_dir):
        """Test async cache persistence functionality."""
        cache_file = Path(temp_cache_dir) / "async_persistence_test_cache.json"
        integration_config.cache_file = str(cache_file)
        
        # Create first service instance and fetch data
        service1 = AsyncWeatherService(integration_config)
        location = "Sydney,AU"
        units = "metric"
        
        try:
            # Fetch and cache data
            weather_data1 = await service1.get_weather(location, units)
            
            # Save cache to disk
            service1.save_cache()
            
            # Verify cache file was created
            assert cache_file.exists()
            
            # Create second service instance (should load cache)
            service2 = AsyncWeatherService(integration_config)
            
            try:
                # Fetch same data - should come from cache
                weather_data2 = await service2.get_weather(location, units)
                
                # Data should be the same
                assert weather_data1.city == weather_data2.city
                assert weather_data1.temperature == weather_data2.temperature
                assert weather_data1.humidity == weather_data2.humidity
                
            finally:
                await service2.close()
                
        finally:
            await service1.close()