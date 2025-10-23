"""Unit tests for custom exceptions module."""

import pytest
from weather_app.exceptions import (
    WeatherAppError,
    ConfigurationError,
    APIKeyError,
    WeatherServiceError,
    LocationNotFoundError,
    APIRequestError,
    NetworkError,
    RateLimitError,
    InvalidLocationError,
    DataParsingError,
    LocationServiceError,
    GeocodingError,
)


class TestWeatherAppError:
    """Test cases for base WeatherAppError."""

    def test_weather_app_error_creation(self):
        """Test creating WeatherAppError with message."""
        error = WeatherAppError("Test error message")
        assert str(error) == "Test error message"

    def test_weather_app_error_inheritance(self):
        """Test WeatherAppError inheritance from Exception."""
        assert issubclass(WeatherAppError, Exception)


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_creation(self):
        """Test creating ConfigurationError with message."""
        error = ConfigurationError("Configuration error message")
        assert str(error) == "Configuration error message"

    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inheritance from WeatherAppError."""
        assert issubclass(ConfigurationError, WeatherAppError)


class TestAPIKeyError:
    """Test cases for APIKeyError."""

    def test_api_key_error_creation(self):
        """Test creating APIKeyError with message."""
        error = APIKeyError("API key is missing")
        assert str(error) == "API key is missing"

    def test_api_key_error_inheritance(self):
        """Test APIKeyError inheritance from ConfigurationError."""
        assert issubclass(APIKeyError, ConfigurationError)
        assert issubclass(APIKeyError, WeatherAppError)


class TestWeatherServiceError:
    """Test cases for WeatherServiceError."""

    def test_weather_service_error_creation(self):
        """Test creating WeatherServiceError with message."""
        error = WeatherServiceError("Weather service error message")
        assert str(error) == "Weather service error message"

    def test_weather_service_error_inheritance(self):
        """Test WeatherServiceError inheritance from WeatherAppError."""
        assert issubclass(WeatherServiceError, WeatherAppError)


class TestLocationNotFoundError:
    """Test cases for LocationNotFoundError."""

    def test_location_not_found_error_creation(self):
        """Test creating LocationNotFoundError with message."""
        error = LocationNotFoundError("Location 'Unknown City' not found")
        assert str(error) == "Location 'Unknown City' not found"

    def test_location_not_found_error_inheritance(self):
        """Test LocationNotFoundError inheritance from WeatherServiceError."""
        assert issubclass(LocationNotFoundError, WeatherServiceError)
        assert issubclass(LocationNotFoundError, WeatherAppError)


class TestAPIRequestError:
    """Test cases for APIRequestError."""

    def test_api_request_error_creation(self):
        """Test creating APIRequestError with message."""
        error = APIRequestError("API request failed")
        assert str(error) == "API request failed"

    def test_api_request_error_inheritance(self):
        """Test APIRequestError inheritance from WeatherServiceError."""
        assert issubclass(APIRequestError, WeatherServiceError)
        assert issubclass(APIRequestError, WeatherAppError)


class TestNetworkError:
    """Test cases for NetworkError."""

    def test_network_error_creation(self):
        """Test creating NetworkError with message."""
        error = NetworkError("Network connection failed")
        assert str(error) == "Network connection failed"

    def test_network_error_inheritance(self):
        """Test NetworkError inheritance from APIRequestError."""
        assert issubclass(NetworkError, APIRequestError)
        assert issubclass(NetworkError, WeatherServiceError)
        assert issubclass(NetworkError, WeatherAppError)


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_creation(self):
        """Test creating RateLimitError with message."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"

    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inheritance from APIRequestError."""
        assert issubclass(RateLimitError, APIRequestError)
        assert issubclass(RateLimitError, WeatherServiceError)
        assert issubclass(RateLimitError, WeatherAppError)


class TestInvalidLocationError:
    """Test cases for InvalidLocationError."""

    def test_invalid_location_error_creation(self):
        """Test creating InvalidLocationError with message."""
        error = InvalidLocationError("Invalid location format")
        assert str(error) == "Invalid location format"

    def test_invalid_location_error_inheritance(self):
        """Test InvalidLocationError inheritance from WeatherAppError."""
        assert issubclass(InvalidLocationError, WeatherAppError)


class TestDataParsingError:
    """Test cases for DataParsingError."""

    def test_data_parsing_error_creation(self):
        """Test creating DataParsingError with message."""
        error = DataParsingError("Failed to parse weather data")
        assert str(error) == "Failed to parse weather data"

    def test_data_parsing_error_inheritance(self):
        """Test DataParsingError inheritance from WeatherServiceError."""
        assert issubclass(DataParsingError, WeatherServiceError)
        assert issubclass(DataParsingError, WeatherAppError)


class TestLocationServiceError:
    """Test cases for LocationServiceError."""

    def test_location_service_error_creation(self):
        """Test creating LocationServiceError with message."""
        error = LocationServiceError("Location service error")
        assert str(error) == "Location service error"

    def test_location_service_error_inheritance(self):
        """Test LocationServiceError inheritance from WeatherAppError."""
        assert issubclass(LocationServiceError, WeatherAppError)


class TestGeocodingError:
    """Test cases for GeocodingError."""

    def test_geocoding_error_creation(self):
        """Test creating GeocodingError with message."""
        error = GeocodingError("Geocoding failed")
        assert str(error) == "Geocoding failed"

    def test_geocoding_error_inheritance(self):
        """Test GeocodingError inheritance from LocationServiceError."""
        assert issubclass(GeocodingError, LocationServiceError)
        assert issubclass(GeocodingError, WeatherAppError)


class TestExceptionHierarchy:
    """Test cases for exception hierarchy relationships."""

    def test_exception_hierarchy_structure(self):
        """Test the complete exception hierarchy structure."""
        # Base exception
        assert issubclass(WeatherAppError, Exception)

        # Configuration exceptions
        assert issubclass(ConfigurationError, WeatherAppError)
        assert issubclass(APIKeyError, ConfigurationError)

        # Weather service exceptions
        assert issubclass(WeatherServiceError, WeatherAppError)
        assert issubclass(LocationNotFoundError, WeatherServiceError)
        assert issubclass(APIRequestError, WeatherServiceError)
        assert issubclass(NetworkError, APIRequestError)
        assert issubclass(RateLimitError, APIRequestError)
        assert issubclass(DataParsingError, WeatherServiceError)

        # Location service exceptions
        assert issubclass(LocationServiceError, WeatherAppError)
        assert issubclass(GeocodingError, LocationServiceError)

        # Independent exceptions
        assert issubclass(InvalidLocationError, WeatherAppError)

    def test_exception_instances(self):
        """Test creating instances of all exception types."""
        exceptions = [
            WeatherAppError("test"),
            ConfigurationError("test"),
            APIKeyError("test"),
            WeatherServiceError("test"),
            LocationNotFoundError("test"),
            APIRequestError("test"),
            NetworkError("test"),
            RateLimitError("test"),
            InvalidLocationError("test"),
            DataParsingError("test"),
            LocationServiceError("test"),
            GeocodingError("test"),
        ]

        # All should be instances of WeatherAppError
        for exc in exceptions:
            assert isinstance(exc, WeatherAppError)
            assert isinstance(exc, Exception)

    def test_exception_message_preservation(self):
        """Test that exception messages are preserved correctly."""
        test_message = "Custom error message with details"
        
        exceptions = [
            WeatherAppError(test_message),
            ConfigurationError(test_message),
            APIKeyError(test_message),
            WeatherServiceError(test_message),
            LocationNotFoundError(test_message),
            APIRequestError(test_message),
            NetworkError(test_message),
            RateLimitError(test_message),
            InvalidLocationError(test_message),
            DataParsingError(test_message),
            LocationServiceError(test_message),
            GeocodingError(test_message),
        ]

        for exc in exceptions:
            assert str(exc) == test_message