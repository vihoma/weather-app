"""Custom exceptions for the Weather Application."""


class WeatherAppError(Exception):
    """Base exception for all Weather Application errors."""

    pass


class ConfigurationError(WeatherAppError):
    """Raised when there are issues with application configuration."""

    pass


class APIKeyError(ConfigurationError):
    """Raised when API key is missing or invalid."""

    pass


class WeatherServiceError(WeatherAppError):
    """Raised when there are issues with weather service operations."""

    pass


class LocationNotFoundError(WeatherServiceError):
    """Raised when the requested location cannot be found."""

    pass


class APIRequestError(WeatherServiceError):
    """Raised when there are issues with API requests."""

    pass


class NetworkError(APIRequestError):
    """Raised when there are network connectivity issues."""

    pass


class RateLimitError(APIRequestError):
    """Raised when API rate limits are exceeded."""

    pass


class InvalidLocationError(WeatherAppError):
    """Raised when an invalid location format is provided."""

    pass


class DataParsingError(WeatherServiceError):
    """Raised when there are issues parsing weather data."""

    pass


class LocationServiceError(WeatherAppError):
    """Base exception for location service errors."""

    pass


class GeocodingError(LocationServiceError):
    """Raised when there are issues with geocoding operations."""

    pass
