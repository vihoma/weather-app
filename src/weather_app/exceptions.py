"""Custom exceptions for the Weather Application."""


class WeatherAppError(Exception):
    """Base exception for all Weather Application errors."""


class ConfigurationError(WeatherAppError):
    """Raised when there are issues with application configuration."""


class APIKeyError(ConfigurationError):
    """Raised when API key is missing or invalid."""


class WeatherServiceError(WeatherAppError):
    """Raised when there are issues with weather service operations."""


class LocationNotFoundError(WeatherServiceError):
    """Raised when the requested location cannot be found."""


class APIRequestError(WeatherServiceError):
    """Raised when there are issues with API requests."""


class NetworkError(APIRequestError):
    """Raised when there are network connectivity issues."""


class RateLimitError(APIRequestError):
    """Raised when API rate limits are exceeded."""


class InvalidLocationError(WeatherAppError):
    """Raised when an invalid location format is provided."""


class DataParsingError(WeatherServiceError):
    """Raised when there are issues parsing weather data."""


class LocationServiceError(WeatherAppError):
    """Base exception for location service errors."""


class GeocodingError(LocationServiceError):
    """Raised when there are issues with geocoding operations."""
