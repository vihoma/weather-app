"""Fixtures for functional / e2e CLI tests."""

import pytest
from click.testing import CliRunner

from weather_app.models.weather_data import WeatherData


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_weather_data():
    """Create a realistic WeatherData instance for test assertions."""
    return WeatherData(
        city="London,GB",
        units="metric",
        status="Clear",
        detailed_status="Clear sky",
        temperature=20.5,
        feels_like=19.8,
        humidity=65,
        wind_speed=3.2,
        wind_direction_deg=180.0,
        precipitation_probability=10,
        clouds=20,
        visibility_distance=10000.0,
        pressure_hpa=1013.0,
        icon_code=800,
    )
