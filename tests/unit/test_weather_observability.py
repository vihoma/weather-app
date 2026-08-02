"""Tests for privacy-safe weather-fetch spans."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

import weather_app.observability as observability
from weather_app.exceptions import NetworkError
from weather_app.models.weather_data import WeatherData
from weather_app.services.async_weather_service import AsyncWeatherService
from weather_app.services.weather_service import WeatherService


class CapturedSpan:
    """In-memory span used to make remote Logfire export impossible in tests."""

    def __init__(self, name: str, attributes: dict[str, str]) -> None:
        self.name = name
        self.attributes = attributes
        self.exit_arguments: tuple[object, object, object] | None = None

    def __enter__(self) -> "CapturedSpan":
        return self

    def __exit__(self, *arguments: object) -> None:
        self.exit_arguments = arguments

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


@pytest.fixture
def captured_spans(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[list[CapturedSpan], None, None]:
    """Replace Logfire's span factory so no test can export telemetry remotely."""
    spans: list[CapturedSpan] = []

    def create_span(name: str, **attributes: str) -> CapturedSpan:
        span = CapturedSpan(name, attributes)
        spans.append(span)
        return span

    monkeypatch.setattr(observability.logfire, "span", create_span)
    yield spans


def _weather_data(city: str, units: str) -> WeatherData:
    """Create a representative weather result."""
    return WeatherData(
        city=city,
        units=units,
        status="Clear",
        detailed_status="Clear sky",
        temperature=20.0,
        feels_like=19.0,
        humidity=60,
        wind_speed=2.0,
        wind_direction_deg=180.0,
        precipitation_probability=None,
        clouds=0,
        visibility_distance=10000.0,
        pressure_hpa=1013.0,
    )


class TestWeatherFetchSpans:
    """Verify weather services emit only safe, application-level span data."""

    def test_sync_cache_hit_span_has_only_safe_attributes(
        self, captured_spans: list[CapturedSpan]
    ) -> None:
        config = MagicMock(api_key="test-key", cache_ttl=60, cache_persist=False)
        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr("weather_app.services.weather_service.OWM", MagicMock())
            service = WeatherService(config)

        city = "Sensitive City,ZZ"
        service.cache[f"{city}:metric"] = _weather_data(city, "metric")

        result = service.get_weather(city, "metric")

        assert result.city == city
        assert len(captured_spans) == 1
        span = captured_spans[0]
        assert span.name == "weather.fetch"
        assert span.attributes == {
            "request_mode": "sync",
            "unit_system": "metric",
            "cache_outcome": "hit",
            "outcome": "success",
        }
        assert span.exit_arguments == (None, None, None)

    @pytest.mark.asyncio
    async def test_async_failure_span_has_safe_category_only(
        self, captured_spans: list[CapturedSpan]
    ) -> None:
        config = MagicMock(
            api_key="test-key",
            cache_ttl=60,
            request_timeout=30,
            cache_persist=False,
        )
        service = AsyncWeatherService(config)
        service._fetch_weather_data = AsyncMock(
            side_effect=NetworkError("request to Sensitive City,ZZ failed")
        )

        with pytest.raises(NetworkError):
            await service.get_weather("Sensitive City,ZZ", "imperial")

        assert len(captured_spans) == 1
        span = captured_spans[0]
        assert span.name == "weather.fetch"
        assert span.attributes == {
            "request_mode": "async",
            "unit_system": "imperial",
            "cache_outcome": "miss",
            "outcome": "failure",
            "failure_category": "network",
        }
        assert span.exit_arguments == (None, None, None)
