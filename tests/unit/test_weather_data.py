"""Unit tests for WeatherData model."""

import pytest
from src.weather_app.models.weather_data import WeatherData


class TestWeatherData:
    """Test WeatherData model functionality."""

    def test_weather_data_creation(self):
        """Test WeatherData object creation with valid data."""
        weather_data = WeatherData(
            city="London,GB",
            units="metric",
            status="Clear",
            detailed_status="clear sky",
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

        assert weather_data.city == "London,GB"
        assert weather_data.temperature == 20.5
        assert weather_data.humidity == 65
        assert weather_data.pressure_hpa == 1013.0

    def test_get_emoji_clear_sky(self):
        """Test emoji mapping for clear sky."""
        weather_data = WeatherData(
            city="Test",
            units="metric",
            status="Clear",
            detailed_status="clear sky",
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            wind_speed=0.0,
            wind_direction_deg=None,
            precipitation_probability=None,
            clouds=None,
            visibility_distance=None,
            pressure_hpa=1013.0,
        )

        assert weather_data.get_emoji() == "☀️"

    def test_get_emoji_rain(self):
        """Test emoji mapping for rain."""
        weather_data = WeatherData(
            city="Test",
            units="metric",
            status="Rain",
            detailed_status="light rain",
            temperature=15.0,
            feels_like=15.0,
            humidity=80,
            wind_speed=0.0,
            wind_direction_deg=None,
            precipitation_probability=None,
            clouds=None,
            visibility_distance=None,
            pressure_hpa=1013.0,
        )

        assert weather_data.get_emoji() == "🌦️"

    def test_get_emoji_unknown_status(self):
        """Test emoji mapping for unknown weather status."""
        weather_data = WeatherData(
            city="Test",
            units="metric",
            status="Unknown",
            detailed_status="unknown weather phenomenon",
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            wind_speed=0.0,
            wind_direction_deg=None,
            precipitation_probability=None,
            clouds=None,
            visibility_distance=None,
            pressure_hpa=1013.0,
        )

        assert weather_data.get_emoji() == "🌈"

    def test_weather_data_with_none_values(self):
        """Test WeatherData handles None values properly."""
        weather_data = WeatherData(
            city="Test",
            units="metric",
            status="Clear",
            detailed_status="clear sky",
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            wind_speed=0.0,
            wind_direction_deg=None,
            precipitation_probability=None,
            clouds=None,
            visibility_distance=None,
            pressure_hpa=1013.0,
        )

        assert weather_data.wind_direction_deg is None
        assert weather_data.precipitation_probability is None
        assert weather_data.clouds is None
        assert weather_data.visibility_distance is None

    @pytest.mark.parametrize(
        "status,expected_emoji",
        [
            ("clear", "☀️"),
            ("scattered clouds", "🌤️"),
            ("broken clouds", "🌥️"),
            ("few clouds", "🌥️"),
            ("overcast clouds", "☁️"),
            ("light rain", "🌦️"),
            ("rain", "🌧️"),
            ("drizzle", "💧"),
            ("snow", "❄️"),
            ("sleet", "🌨️"),
            ("mist", "🌫️"),
            ("haze", "🌫️"),
            ("fog", "🌫️"),
            ("thunderstorm", "⛈️"),
            ("windy", "💨"),
            ("sunny", "☀️"),
            ("clouds", "☁️"),
        ],
    )
    def test_emoji_mapping_comprehensive(self, status, expected_emoji):
        """Test comprehensive emoji mapping for various weather statuses."""
        weather_data = WeatherData(
            city="Test",
            units="metric",
            status=status.split()[0].capitalize(),
            detailed_status=status,
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            wind_speed=0.0,
            wind_direction_deg=None,
            precipitation_probability=None,
            clouds=None,
            visibility_distance=None,
            pressure_hpa=1013.0,
        )

        assert weather_data.get_emoji() == expected_emoji
