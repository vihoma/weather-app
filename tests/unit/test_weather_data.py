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


class TestWeatherDataSerialization:
    """Test Pydantic model_dump / model_validate serialization."""

    @pytest.fixture
    def sample_weather_data(self) -> WeatherData:
        """Create a fully populated WeatherData instance for testing."""
        return WeatherData(
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

    def test_model_dump_returns_all_fields(self, sample_weather_data):
        """Test that model_dump() returns a dict with all field values."""
        d = sample_weather_data.model_dump()

        assert d["city"] == "London,GB"
        assert d["temperature"] == 20.5
        assert d["humidity"] == 65
        assert d["icon_code"] == 800
        assert d["wind_direction_deg"] == 180.0
        assert "WEATHER_EMOJI_MAP" not in d

    def test_model_validate_round_trip(self, sample_weather_data):
        """Test model_dump -> model_validate produces an equal object."""
        d = sample_weather_data.model_dump()
        restored = WeatherData.model_validate(d)

        assert restored == sample_weather_data

    def test_model_validate_ignores_unknown_keys(self, sample_weather_data):
        """Test that unknown keys are silently ignored (forward-compat)."""
        d = sample_weather_data.model_dump()
        d["unknown_future_field"] = "should be ignored"
        d["another_extra"] = 42

        restored = WeatherData.model_validate(d)
        assert restored == sample_weather_data

    def test_model_validate_missing_optional_fields(self):
        """Test that missing Optional fields default to None."""
        minimal = {
            "city": "Oslo",
            "units": "metric",
            "status": "Clear",
            "detailed_status": "clear sky",
            "temperature": 5.0,
            "feels_like": 3.0,
            "humidity": 70,
            "wind_speed": 2.0,
            "wind_direction_deg": None,
            "precipitation_probability": None,
            "clouds": None,
            "visibility_distance": None,
            "pressure_hpa": 1013.0,
        }
        wd = WeatherData.model_validate(minimal)

        assert wd.icon_code is None

    def test_model_validate_missing_required_field_raises(self):
        """Test that omitting a required field raises ValidationError."""
        from pydantic import ValidationError

        incomplete = {
            "units": "metric",
            "status": "Clear",
            "detailed_status": "clear sky",
            "temperature": 5.0,
            "feels_like": 3.0,
            "humidity": 70,
            "wind_speed": 2.0,
            "wind_direction_deg": None,
            "precipitation_probability": None,
            "clouds": None,
            "visibility_distance": None,
            "pressure_hpa": 1013.0,
        }
        with pytest.raises(ValidationError, match="city"):
            WeatherData.model_validate(incomplete)

    def test_model_validate_type_coercion(self):
        """Test that int temperature is coerced to float."""
        data = {
            "city": "Oslo",
            "units": "metric",
            "status": "Clear",
            "detailed_status": "clear sky",
            "temperature": 5,  # int, should become float
            "feels_like": 3,
            "humidity": 70,
            "wind_speed": 2,
            "wind_direction_deg": None,
            "precipitation_probability": None,
            "clouds": None,
            "visibility_distance": None,
            "pressure_hpa": 1013,
        }
        wd = WeatherData.model_validate(data)

        assert isinstance(wd.temperature, float)
        assert wd.temperature == 5.0

    def test_model_validate_invalid_type_raises(self):
        """Test that a non-numeric temperature raises ValidationError."""
        from pydantic import ValidationError

        data = {
            "city": "Oslo",
            "units": "metric",
            "status": "Clear",
            "detailed_status": "clear sky",
            "temperature": "not_a_number",
            "feels_like": 3.0,
            "humidity": 70,
            "wind_speed": 2.0,
            "wind_direction_deg": None,
            "precipitation_probability": None,
            "clouds": None,
            "visibility_distance": None,
            "pressure_hpa": 1013.0,
        }
        with pytest.raises(ValidationError, match="temperature"):
            WeatherData.model_validate(data)

    def test_json_round_trip(self, sample_weather_data):
        """Test model_dump -> json.dumps -> json.loads -> model_validate."""
        import json

        d = sample_weather_data.model_dump()
        json_str = json.dumps(d)
        loaded = json.loads(json_str)
        restored = WeatherData.model_validate(loaded)

        assert restored == sample_weather_data
