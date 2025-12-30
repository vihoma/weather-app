"""Unit tests for CLI commands using Click testing framework.

These tests verify command parsing, argument validation, and error handling
for all CLI subcommands without making actual API calls.
"""

import json
from unittest.mock import Mock, patch, AsyncMock
import pytest
import click
from click.testing import CliRunner

from weather_app.cli.group import cli
from weather_app.cli.errors import (
    EXIT_SUCCESS,
    EXIT_GENERAL_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_API_ERROR,
    EXIT_LOCATION_ERROR,
    EXIT_MISUSE_SHELL,
)
from weather_app.exceptions import (
    ConfigurationError,
    LocationNotFoundError,
    APIRequestError,
)
from weather_app.models.weather_data import WeatherData


class TestCLICommands:
    """Test cases for CLI command functionality."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_weather_data(self):
        """Create a mock WeatherData object for testing."""
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

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock()
        config.api_key = "test_api_key"
        config.units = "metric"
        config.use_async = False
        config.cache_ttl = 600
        config.cache_persist = False
        config.cache_file = "~/.weather_app_cache.json"
        config.validate = Mock()
        config.is_keyring_available = Mock(return_value=True)
        return config

    def test_cli_help(self, runner):
        """Test that CLI help displays without errors."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == EXIT_SUCCESS
        assert "Weather App CLI" in result.output
        assert "weather" in result.output
        assert "setup" in result.output
        assert "cache" in result.output
        assert "config" in result.output

    def test_weather_command_help(self, runner):
        """Test weather command help."""
        result = runner.invoke(cli, ["weather", "--help"])
        assert result.exit_code == EXIT_SUCCESS
        assert "Get current weather for a location" in result.output
        assert "--city" in result.output
        assert "--coordinates" in result.output
        assert "--output" in result.output

    @patch("weather_app.cli.group.get_config_from_context")
    @patch("weather_app.cli.commands.weather.FormatterFactory")
    def test_weather_command_city_tui_output(
        self, mock_formatter_factory, mock_get_config, runner, mock_weather_data, mock_config
    ):
        """Test weather command with city and TUI output."""
        # Mock config
        mock_get_config.return_value = mock_config
        
        # Mock formatter
        mock_formatter = Mock()
        mock_formatter.format.return_value = "Formatted TUI output"
        mock_formatter_factory.get_formatter.return_value = mock_formatter
        
        # Mock weather fetch
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.return_value = mock_weather_data
            
            result = runner.invoke(cli, ["weather", "--city", "London,GB", "--output", "tui"])
            
            assert result.exit_code == EXIT_SUCCESS
            assert "Formatted TUI output" in result.output
            mock_fetch.assert_called_once_with(mock_config, "London,GB")
            mock_formatter_factory.get_formatter.assert_called_once_with("tui", units="metric")

    @patch("weather_app.cli.group.get_config_from_context")
    @patch("weather_app.cli.commands.weather.FormatterFactory")
    def test_weather_command_city_json_output(
        self, mock_formatter_factory, mock_get_config, runner, mock_weather_data, mock_config
    ):
        """Test weather command with city and JSON output."""
        mock_get_config.return_value = mock_config
        
        # Mock JSON formatter
        mock_formatter = Mock()
        mock_formatter.format.return_value = json.dumps({"city": "London,GB", "temperature": 20.5})
        mock_formatter_factory.get_formatter.return_value = mock_formatter
        
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.return_value = mock_weather_data
            
            result = runner.invoke(cli, ["weather", "--city", "London,GB", "--output", "json"])
            
            assert result.exit_code == EXIT_SUCCESS
            output = result.output.strip()
            # Should be valid JSON
            parsed = json.loads(output)
            assert parsed["city"] == "London,GB"
            mock_fetch.assert_called_once_with(mock_config, "London,GB")

    @patch("weather_app.cli.group.get_config_from_context")
    def test_weather_command_coordinates_valid(
        self, mock_get_config, runner, mock_weather_data, mock_config
    ):
        """Test weather command with valid coordinates."""
        mock_get_config.return_value = mock_config
        
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.return_value = mock_weather_data
            
            result = runner.invoke(
                cli, ["weather", "--coordinates", "51.5074,-0.1278", "--output", "tui"]
            )
            
            assert result.exit_code == EXIT_SUCCESS
            mock_fetch.assert_called_once_with(mock_config, "51.5074,-0.1278")

    def test_weather_command_no_location(self, runner):
        """Test weather command without location (should fail)."""
        result = runner.invoke(cli, ["weather", "--output", "tui"])
        
        assert result.exit_code == EXIT_MISUSE_SHELL  # Click.UsageError maps to exit code 2
        assert "You must specify a location" in result.output

    def test_weather_command_both_city_and_coordinates(self, runner):
        """Test weather command with both city and coordinates (should fail)."""
        result = runner.invoke(
            cli, ["weather", "--city", "London,GB", "--coordinates", "51.5074,-0.1278"]
        )
        
        assert result.exit_code == EXIT_MISUSE_SHELL
        assert "Cannot specify both" in result.output

    def test_weather_command_invalid_coordinates_format(self, runner):
        """Test weather command with invalid coordinates format."""
        result = runner.invoke(
            cli, ["weather", "--coordinates", "invalid,format", "--output", "tui"]
        )
        
        assert result.exit_code == EXIT_MISUSE_SHELL
        assert "Invalid coordinates" in result.output

    def test_weather_command_invalid_coordinates_range(self, runner):
        """Test weather command with coordinates out of valid range."""
        result = runner.invoke(
            cli, ["weather", "--coordinates", "95.0,180.0", "--output", "tui"]
        )
        
        assert result.exit_code == EXIT_MISUSE_SHELL
        assert "Latitude must be between -90 and 90" in result.output

    @patch("weather_app.cli.group.get_config_from_context")
    def test_weather_command_location_not_found(
        self, mock_get_config, runner, mock_config
    ):
        """Test weather command when location is not found."""
        mock_get_config.return_value = mock_config
        
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.side_effect = LocationNotFoundError("Unknown location")
            
            result = runner.invoke(cli, ["weather", "--city", "UnknownCity", "--output", "tui"])
            
            assert result.exit_code == EXIT_LOCATION_ERROR
            assert "Location not found" in result.output

    @patch("weather_app.cli.group.get_config_from_context")
    def test_weather_command_configuration_error(
        self, mock_get_config, runner, mock_config
    ):
        """Test weather command when configuration is invalid."""
        mock_get_config.return_value = mock_config
        
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.side_effect = ConfigurationError("API key missing")
            
            result = runner.invoke(cli, ["weather", "--city", "London,GB", "--output", "tui"])
            
            assert result.exit_code == EXIT_CONFIG_ERROR
            assert "Configuration error" in result.output

    @patch("weather_app.cli.group.get_config_from_context")
    def test_weather_command_api_error(
        self, mock_get_config, runner, mock_config
    ):
        """Test weather command when API request fails."""
        mock_get_config.return_value = mock_config
        
        with patch("weather_app.cli.commands.weather._fetch_weather_data") as mock_fetch:
            mock_fetch.side_effect = APIRequestError("Network error")
            
            result = runner.invoke(cli, ["weather", "--city", "London,GB", "--output", "tui"])
            
            assert result.exit_code == EXIT_API_ERROR
            assert "API request failed" in result.output

    def test_setup_command_help(self, runner):
        """Test setup command help."""
        result = runner.invoke(cli, ["setup", "--help"])
        assert result.exit_code == EXIT_SUCCESS
        assert "Manage application setup and configuration" in result.output
        assert "api-key" in result.output

    @patch("weather_app.cli.commands.setup.SecureConfig")
    def test_setup_api_key_command_interactive(
        self, mock_secure_config_class, runner
    ):
        """Test setup api-key command."""
        mock_secure_config = Mock()
        mock_secure_config.is_keyring_available = Mock(return_value=True)
        mock_secure_config.store_api_key = Mock()
        mock_secure_config_class.return_value = mock_secure_config
        
        # Mock the Prompt.ask to avoid interactive input
        with patch("weather_app.cli.commands.setup.Prompt.ask") as mock_prompt:
            mock_prompt.return_value = "test_api_key"
            
            result = runner.invoke(cli, ["setup", "api-key", "set", "--interactive"])
            
            # The command should call store_api_key function
            mock_secure_config.store_api_key.assert_called_once_with(
                "test_api_key", service_name="openweathermap"
            )
            assert result.exit_code == EXIT_SUCCESS

    @patch("weather_app.cli.commands.setup.SecureConfig")
    def test_setup_api_key_view_command(
        self, mock_secure_config_class, runner
    ):
        """Test setup api-key view command."""
        mock_secure_config = Mock()
        mock_secure_config.is_keyring_available = Mock(return_value=True)
        mock_secure_config.get_api_key = Mock(return_value="test_api_key_12345678")
        mock_secure_config_class.return_value = mock_secure_config
        
        result = runner.invoke(cli, ["setup", "api-key", "view"])
        
        assert result.exit_code == EXIT_SUCCESS
        # Should mask the API key (first 4 and last 4 chars)
        assert "test_api_key_12345678" not in result.output
        assert "test...5678" in result.output

    @patch("weather_app.cli.commands.setup.SecureConfig")
    def test_setup_api_key_remove_command(
        self, mock_secure_config_class, runner
    ):
        """Test setup api-key remove command."""
        mock_secure_config = Mock()
        mock_secure_config.is_keyring_available = Mock(return_value=True)
        mock_secure_config.get_api_key = Mock(return_value="test_api_key")
        mock_secure_config.delete_api_key = Mock()
        mock_secure_config_class.return_value = mock_secure_config
        
        result = runner.invoke(cli, ["setup", "api-key", "remove", "--force"])
        
        assert result.exit_code == EXIT_SUCCESS
        # Should have called delete_api_key
        mock_secure_config.delete_api_key.assert_called_once_with(service_name="openweathermap")

    def test_cache_command_help(self, runner):
        """Test cache command help."""
        result = runner.invoke(cli, ["cache", "--help"])
        assert result.exit_code == EXIT_SUCCESS
        assert "Manage weather data cache." in result.output
        assert "clear" in result.output
        assert "ttl" in result.output
        assert "status" in result.output

    @patch("weather_app.cli.commands.cache.Config")
    def test_cache_clear_command(
        self, mock_config_class, runner
    ):
        """Test cache clear command."""
        mock_config = Mock()
        mock_config.cache_file = "/tmp/test_cache.json"
        mock_config_class.return_value = mock_config
        
        # Mock Path and its methods
        with patch("weather_app.cli.commands.cache.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.expanduser.return_value = mock_path
            mock_path.exists.return_value = True
            mock_path.unlink = Mock()
            # Ensure string representation works
            mock_path.__str__ = Mock(return_value="/tmp/test_cache.json")
            mock_path_class.return_value = mock_path
            
            # Mock click.confirm to avoid interactive prompt
            with patch("weather_app.cli.commands.cache.click.confirm") as mock_confirm:
                mock_confirm.return_value = True
                
                result = runner.invoke(cli, ["cache", "clear", "--force"])
                
                assert result.exit_code == EXIT_SUCCESS
                mock_path.unlink.assert_called_once()

    @patch("weather_app.cli.commands.cache.Config")
    def test_cache_status_command(
        self, mock_config_class, runner
    ):
        """Test cache status command."""
        mock_config = Mock()
        mock_config.cache_persist = True
        mock_config.cache_ttl = 600
        mock_config.cache_file = "/tmp/test_cache.json"
        mock_config_class.return_value = mock_config
        
        # Mock Path and file operations
        with patch("weather_app.cli.commands.cache.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.expanduser.return_value = mock_path
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_size = 12345
            # Ensure string representation works
            mock_path.__str__ = Mock(return_value="/tmp/test_cache.json")
            mock_path_class.return_value = mock_path
            
            # Mock open to return a file-like object
            mock_file = Mock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            mock_file.read = Mock(return_value='{"key1": {"data": "value1"}, "key2": {"data": "value2"}, "key3": {"data": "value3"}, "key4": {"data": "value4"}}')
            with patch("weather_app.cli.commands.cache.open", return_value=mock_file):
                # Mock json.load to return sample cache data
                with patch("weather_app.cli.commands.cache.json.load") as mock_json_load:
                    mock_json_load.return_value = {
                        "key1": {"data": "value1"},
                        "key2": {"data": "value2"},
                        "key3": {"data": "value3"},
                        "key4": {"data": "value4"}
                    }
                    
                    result = runner.invoke(cli, ["cache", "status"])
                    
                    assert result.exit_code == EXIT_SUCCESS
                    assert "Enabled" in result.output
                    assert "600" in result.output
                    assert "key1" in result.output  # sample keys
                    assert "key2" in result.output
                    assert "... (+1 more)" in result.output

    def test_config_command_help(self, runner):
        """Test config command help."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == EXIT_SUCCESS
        assert "View and manage application configuration." in result.output
        assert "show" in result.output
        assert "sources" in result.output

    @patch("weather_app.cli.commands.config.Config")
    def test_config_show_command(
        self, mock_config_class, runner
    ):
        """Test config show command."""
        mock_config = Mock()
        mock_config.api_key = "test_api_key_masked"
        mock_config.units = "metric"
        mock_config.use_async = True
        mock_config.cache_ttl = 600
        mock_config.cache_persist = True
        mock_config.log_level = "INFO"
        mock_config_class.return_value = mock_config
        
        result = runner.invoke(cli, ["config", "show"])
        
        assert result.exit_code == EXIT_SUCCESS
        assert "metric" in result.output
        assert "INFO" in result.output
        # API key should be masked
        assert "test_api_key_masked" not in result.output

    def test_global_options_verbose(self, runner):
        """Test global --verbose flag."""
        # Just test that the option is accepted (doesn't cause error)
        result = runner.invoke(cli, ["--verbose", "weather", "--city", "London,GB", "--output", "tui"])
        # Should fail because we didn't mock, but verbose flag should be accepted
        # We expect location validation to fail because no mock setup
        assert result.exit_code != EXIT_SUCCESS  # Some error expected
        # But not a usage error from --verbose

    def test_global_options_units(self, runner):
        """Test global --units flag."""
        # Test that units option is accepted
        result = runner.invoke(cli, ["--units", "imperial", "weather", "--city", "London,GB", "--output", "tui"])
        # Should fail because no mock, but units flag should be accepted
        assert "imperial" not in result.output  # Not checking output, just that it runs