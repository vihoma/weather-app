"""Process-local Logfire observability initialization."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock
from typing import Literal

import logfire

_configuration_lock = Lock()
_logfire_configured = False


def configure_logfire() -> None:
    """Configure Logfire and system metrics once for the current process."""
    global _logfire_configured

    if _logfire_configured:
        return

    with _configuration_lock:
        if _logfire_configured:
            return

        logfire.configure(
            service_name="weather-app",
            environment=os.environ.get("LOGFIRE_ENVIRONMENT", "development"),
            console=False,
            send_to_logfire="if-token-present",
        )
        logfire.instrument_system_metrics()
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
        span.__exit__(None, None, None)
