"""POSIX error codes and exception mapping for CLI."""

from typing import ClassVar

import click

from weather_app.exceptions import (
    APIKeyError,
    APIRequestError,
    ConfigurationError,
    DataParsingError,
    InvalidLocationError,
    LocationNotFoundError,
    NetworkError,
    RateLimitError,
    WeatherAppError,
)

# POSIX exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_MISUSE_SHELL = 2
EXIT_CONFIG_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_API_ERROR = 5
EXIT_LOCATION_ERROR = 6


def map_exception_to_exit_code(exception: Exception) -> int:
    """Map an exception to a POSIX exit code.

    Args:
        exception: The exception to map.

    Returns:
        POSIX exit code.
    """
    if isinstance(exception, click.ClickException):
        # Click exceptions already have exit_code property
        return exception.exit_code

    if isinstance(exception, (ConfigurationError, APIKeyError)):
        return EXIT_CONFIG_ERROR
    elif isinstance(exception, LocationNotFoundError):
        return EXIT_LOCATION_ERROR
    elif isinstance(
        exception, (NetworkError, APIRequestError, DataParsingError, RateLimitError)
    ):
        return EXIT_API_ERROR
    elif isinstance(exception, InvalidLocationError):
        return EXIT_MISUSE_SHELL  # Invalid argument
    elif isinstance(exception, WeatherAppError):
        return EXIT_GENERAL_ERROR
    else:
        return EXIT_GENERAL_ERROR


class WeatherAppClickException(click.ClickException):
    """Base Click exception with POSIX exit codes."""

    exit_code: ClassVar[int] = EXIT_GENERAL_ERROR


class ConfigurationClickException(WeatherAppClickException):
    """Configuration error exception."""

    exit_code = EXIT_CONFIG_ERROR


class APIClickException(WeatherAppClickException):
    """API error exception."""

    exit_code = EXIT_API_ERROR


class LocationClickException(WeatherAppClickException):
    """Location error exception."""

    exit_code = EXIT_LOCATION_ERROR
