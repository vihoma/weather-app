"""Regression tests for subcommand logging bootstrap and lifecycle logging."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from weather_app.cli.group import cli
from weather_app.models.weather_data import WeatherData


class TestCLILogging:
    """Test logging behavior for Click-based subcommands."""

    def test_version_subcommand_creates_log_file(self) -> None:
        """Version subcommand should initialize file logging."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            log_path = Path("subcommand.log")
            result = runner.invoke(
                cli,
                ["version"],
                env={"LOG_FILE": str(log_path), "LOG_FORMAT": "text"},
            )

            assert result.exit_code == 0
            assert log_path.exists()

            log_content = log_path.read_text(encoding="utf-8")
            assert "CLI command starting" in log_content
            assert "CLI command completed" in log_content
            assert "command_name=version" in log_content

    def test_weather_subcommand_creates_log_file(self) -> None:
        """Weather subcommand should emit command lifecycle log entries."""
        runner = CliRunner()
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

        with runner.isolated_filesystem():
            log_path = Path("weather.log")
            with patch(
                "weather_app.cli.commands.weather._fetch_weather_data",
                return_value=weather_data,
            ):
                result = runner.invoke(
                    cli,
                    ["weather", "--city", "London,GB", "--output", "json"],
                    env={"LOG_FILE": str(log_path), "LOG_FORMAT": "text"},
                )

            assert result.exit_code == 0
            assert log_path.exists()

            log_content = log_path.read_text(encoding="utf-8")
            assert "command_name=weather" in log_content
            assert "location_source=city" in log_content
            assert "CLI command completed" in log_content

    def test_help_only_subcommand_does_not_create_log_file(self) -> None:
        """Help-only output should not initialize subcommand logging."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            log_path = Path("help.log")
            result = runner.invoke(
                cli,
                ["weather", "--help"],
                env={"LOG_FILE": str(log_path), "LOG_FORMAT": "text"},
            )

            assert result.exit_code == 0
            assert not log_path.exists()

    def test_verbose_subcommand_emits_debug_log(self) -> None:
        """Verbose flag should enable debug-level subcommand logging."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            log_path = Path("verbose.log")
            result = runner.invoke(
                cli,
                ["--verbose", "version"],
                env={"LOG_FILE": str(log_path), "LOG_FORMAT": "text"},
            )

            assert result.exit_code == 0
            assert log_path.exists()

            log_content = log_path.read_text(encoding="utf-8")
            assert "CLI logging configured" in log_content
            assert "log_level=DEBUG" in log_content
