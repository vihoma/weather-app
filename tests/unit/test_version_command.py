"""Unit tests for version CLI command."""

from unittest.mock import patch, Mock
from importlib.metadata import PackageNotFoundError
import pytest
from click.testing import CliRunner

from weather_app.cli.group import cli


class TestVersionCommand:
    """Test cases for version command functionality."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @patch('importlib.metadata.version')
    def test_version_command_displays_version(self, mock_version, runner):
        """Test that version command displays the correct version."""
        # Mock the version to a known value
        mock_version.return_value = "0.5.10"
        
        result = runner.invoke(cli, ["version"])
        
        assert result.exit_code == 0
        assert "0.5.10" in result.output
        assert "Weather Application" in result.output
        assert "Python" in result.output

    @patch('importlib.metadata.version')
    def test_version_command_displays_app_name(self, mock_version, runner):
        """Test that version command displays application name."""
        mock_version.return_value = "0.5.10"
        
        result = runner.invoke(cli, ["version"])
        
        assert result.exit_code == 0
        assert "weather-app" in result.output
        assert "Application" in result.output

    @patch('importlib.metadata.version')
    def test_version_command_exit_success(self, mock_version, runner):
        """Test that version command exits with success code."""
        mock_version.return_value = "0.5.10"
        
        result = runner.invoke(cli, ["version"])
        
        assert result.exit_code == 0

    @patch('importlib.metadata.version')
    def test_version_command_help_available(self, mock_version, runner):
        """Test that version command help is available."""
        mock_version.return_value = "0.5.10"
        
        result = runner.invoke(cli, ["version", "--help"])
        
        assert result.exit_code == 0
        assert "Show application version information" in result.output

    @patch('importlib.metadata.version')
    def test_version_command_package_not_found(self, mock_version, runner):
        """Test that version command handles missing package gracefully."""
        # Simulate PackageNotFoundError
        mock_version.side_effect = PackageNotFoundError
        
        result = runner.invoke(cli, ["version"])
        
        assert result.exit_code == 0
        assert "unknown" in result.output.lower()