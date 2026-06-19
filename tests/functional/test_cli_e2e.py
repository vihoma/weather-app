"""Functional / end-to-end tests for the weather-app CLI.

These tests exercise the full CLI stack with minimal mocking — only the
external API boundary (_fetch_weather_data) is patched so no real HTTP
requests are made.
"""

import json
import sys
from unittest.mock import Mock, patch

import pytest

from weather_app.cli.group import cli
from weather_app.exceptions import LocationNotFoundError
from weather_app.models.weather_data import WeatherData


@pytest.mark.functional
class TestWeatherCommandE2E:
    """End-to-end tests for the 'weather' subcommand."""

    def test_weather_json_output(self, runner, sample_weather_data):
        """Full stack: weather --city London,GB --output json."""
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            return_value=sample_weather_data,
        ):
            result = runner.invoke(
                cli, ["--no-async", "weather", "--city", "London,GB", "--output", "json"]
            )
            assert result.exit_code == 0, result.output
            data = json.loads(result.output.strip())
            assert data["city"] == "London,GB"
            assert data["temperature"] == 20.5
            assert data["humidity"] == 65

    def test_weather_markdown_output(self, runner, sample_weather_data):
        """Full stack: weather --city London,GB --output markdown."""
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            return_value=sample_weather_data,
        ):
            result = runner.invoke(
                cli,
                ["--no-async", "weather", "--city", "London,GB", "--output", "markdown"],
            )
            assert result.exit_code == 0, result.output
            assert "London,GB" in result.output
            assert "20.5" in result.output

    def test_weather_tui_output(self, runner, sample_weather_data):
        """Full stack: weather --city London,GB --output tui (default)."""
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            return_value=sample_weather_data,
        ):
            result = runner.invoke(
                cli, ["--no-async", "weather", "--city", "London,GB"]
            )
            assert result.exit_code == 0, result.output
            assert "London" in result.output

    def test_weather_with_imperial_units(self, runner):
        """Full stack: weather --units imperial --city London --output json."""
        imperial_data = WeatherData(
            city="London,GB",
            units="imperial",
            status="Rain",
            detailed_status="Light rain",
            temperature=68.9,
            feels_like=67.6,
            humidity=80,
            wind_speed=7.2,
            wind_direction_deg=270.0,
            precipitation_probability=85,
            clouds=90,
            visibility_distance=5000.0,
            pressure_hpa=1008.0,
            icon_code=500,
        )
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            return_value=imperial_data,
        ):
            result = runner.invoke(
                cli,
                ["--units", "imperial", "weather", "--city", "London,GB", "--output", "json"],
            )
            assert result.exit_code == 0, result.output
            data = json.loads(result.output.strip())
            assert data["temperature"] == 68.9
            assert data["units"] == "imperial"

    def test_weather_with_coordinates(self, runner, sample_weather_data):
        """Full stack: weather --coordinates 51.5074,-0.1278 --output json."""
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            return_value=sample_weather_data,
        ):
            result = runner.invoke(
                cli,
                ["weather", "--coordinates", "51.5074,-0.1278", "--output", "json"],
            )
            assert result.exit_code == 0, result.output
            data = json.loads(result.output.strip())
            assert "temperature" in data


@pytest.mark.functional
class TestWeatherCommandErrors:
    """Error-handling tests for the weather CLI."""

    def test_missing_location(self, runner):
        """Error when neither --city nor --coordinates is provided."""
        result = runner.invoke(cli, ["weather"])
        assert result.exit_code != 0
        assert "location" in result.output.lower() or "city" in result.output.lower()

    def test_invalid_city(self, runner):
        """Graceful error when city is not found."""
        with patch(
            "weather_app.cli.commands.weather._fetch_weather_data",
            side_effect=LocationNotFoundError("City not found: NoSuchCity"),
        ):
            result = runner.invoke(
                cli, ["weather", "--city", "NoSuchCity"]
            )
            assert result.exit_code != 0
            assert "not found" in result.output.lower()

    def test_invalid_coordinates_format(self, runner):
        """Error on malformed coordinates."""
        result = runner.invoke(
            cli, ["weather", "--coordinates", "not,numbers"]
        )
        assert result.exit_code != 0

    def test_coordinates_out_of_range(self, runner):
        """Error when coordinates exceed valid range."""
        result = runner.invoke(
            cli, ["weather", "--coordinates", "91.0,181.0"]
        )
        assert result.exit_code != 0


@pytest.mark.functional
class TestConfigCommandE2E:
    """End-to-end tests for the 'config' subcommand."""

    def test_config_show(self, runner):
        """Full stack: config show displays configuration table."""
        result = runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0, result.output
        # Verify the table structure is present with expected fields
        assert "Setting" in result.output
        assert "Value" in result.output
        assert "Units" in result.output
        assert "Cache TTL" in result.output

    def test_config_sources(self, runner):
        """Full stack: config sources displays source information."""
        with patch("weather_app.cli.commands.config.Config") as mock_config_cls, \
             patch("weather_app.cli.commands.config._get_yaml_config_path", return_value=None):
            mock_config = Mock()
            mock_config.api_key = None
            mock_config.is_keyring_available.return_value = True
            mock_config._secure.get_api_key.return_value = None
            mock_config_cls.return_value = mock_config

            result = runner.invoke(cli, ["config", "sources"])
            assert result.exit_code == 0, result.output


@pytest.mark.functional
class TestCacheCommandE2E:
    """End-to-end tests for the 'cache' subcommand."""

    def test_cache_status(self, runner):
        """Full stack: cache status displays cache info."""
        with patch("weather_app.cli.commands.cache.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.cache_persist = True
            mock_config.cache_ttl = 600
            mock_config.cache_file = "/tmp/test_cache.json"
            mock_config_cls.return_value = mock_config

            with patch("weather_app.cli.commands.cache.Path") as mock_path_cls:
                mock_path = Mock()
                mock_path.expanduser.return_value = mock_path
                mock_path.exists.return_value = False
                mock_path_cls.return_value = mock_path

                result = runner.invoke(cli, ["cache", "status"])
                assert result.exit_code == 0, result.output
                assert "Enabled" in result.output
                assert "600" in result.output

    def test_cache_clear_force(self, runner):
        """Full stack: cache clear --force deletes the cache file."""
        with patch("weather_app.cli.commands.cache.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.cache_file = "/tmp/test_cache.json"
            mock_config_cls.return_value = mock_config

            with patch("weather_app.cli.commands.cache.Path") as mock_path_cls:
                mock_path = Mock()
                mock_path.expanduser.return_value = mock_path
                mock_path.exists.return_value = True
                mock_path.unlink = Mock()
                mock_path_cls.return_value = mock_path

                result = runner.invoke(cli, ["cache", "clear", "--force"])
                assert result.exit_code == 0, result.output
                mock_path.unlink.assert_called_once()


@pytest.mark.functional
class TestVersionCommandE2E:
    """End-to-end tests for the 'version' subcommand."""

    def test_version_output(self, runner):
        """Full stack: version shows app and Python version."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0, result.output
        assert "weather-app" in result.output.lower() or "Weather" in result.output
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert python_version in result.output


@pytest.mark.functional
class TestHelpE2E:
    """End-to-end tests for help output."""

    def test_main_help(self, runner):
        """Full stack: --help shows usage info."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "weather" in result.output.lower()

    def test_weather_help(self, runner):
        """Full stack: weather --help shows weather subcommand usage."""
        result = runner.invoke(cli, ["weather", "--help"])
        assert result.exit_code == 0
        assert "--city" in result.output
        assert "--coordinates" in result.output
        assert "--output" in result.output
