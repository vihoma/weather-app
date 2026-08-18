"""Process-local Logfire observability initialization."""

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock
from typing import Literal

import logfire
from yarl import URL

_configuration_lock = Lock()
_logfire_configured = False


def mask_url(url: URL) -> str:
    """Mask sensitive query parameters in a URL."""
    sensitive_keys = {
        "apikey",
        "appid",
        "api_key",
        "api_secret",
        "password",
        "token",
        "username",
    }

    masked_query = {
        key: "*****" if key in sensitive_keys else value
        for key, value in url.query.items()
    }
    return str(url.with_query(masked_query))


def configure_logfire() -> None:
    """Configure Logfire and system metrics once for the current process."""
    global _logfire_configured

    if _logfire_configured:
        return

    with _configuration_lock:
        logfire.configure(
            service_name="weather-app",
            environment=os.environ.get("LOGFIRE_ENVIRONMENT", "development"),
            console=False,
            send_to_logfire="if-token-present",
        )
        logfire.instrument_aiohttp_client(url_filter=mask_url)
        _logfire_configured = True


@contextmanager
def weather_fetch_span(
    request_mode: Literal["sync", "async"], unit_system: str
) -> Iterator[logfire.LogfireSpan]:
    """Create a weather-fetch span that never records exception contents."""
    span = logfire.span(
        "weather.fetch",
        request_mode=request_mode,
        unit_system=unit_system,
    )
    span.__enter__()
    try:
        yield span
    finally:
        span.__exit__(*sys.exc_info())
