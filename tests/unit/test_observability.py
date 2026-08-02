"""Tests for Logfire observability initialization."""

from unittest.mock import patch

from click.testing import CliRunner

import weather_app.cli.group as cli_group
import weather_app.main as application_main
import weather_app.observability as observability


def _reset_logfire_configuration() -> None:
    """Reset the process-local initialization state for an isolated test."""
    with observability._configuration_lock:
        observability._logfire_configured = False


class TestLogfireBootstrap:
    """Test one-time Logfire configuration at application entry points."""

    def setup_method(self) -> None:
        """Reset bootstrap state before each test."""
        _reset_logfire_configuration()

    def teardown_method(self) -> None:
        """Reset bootstrap state after each test."""
        _reset_logfire_configuration()

    def test_configures_once_without_token(self, monkeypatch) -> None:
        """Configure local observability once when no Logfire token exists."""
        monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
        monkeypatch.delenv("LOGFIRE_ENVIRONMENT", raising=False)
        call_order: list[str] = []

        with (
            patch.object(
                observability.logfire,
                "configure",
                side_effect=lambda **_kwargs: call_order.append("configure"),
            ) as configure,
            patch.object(
                observability.logfire,
                "instrument_system_metrics",
                side_effect=lambda: call_order.append("metrics"),
            ) as instrument_system_metrics,
        ):
            observability.configure_logfire()
            observability.configure_logfire()

        configure.assert_called_once_with(
            service_name="weather-app",
            environment="development",
            console=False,
            send_to_logfire="if-token-present",
        )
        instrument_system_metrics.assert_called_once_with()
        assert call_order == ["configure", "metrics"]

    def test_uses_configured_logfire_environment(self, monkeypatch) -> None:
        """Pass the deployment environment through to Logfire configuration."""
        monkeypatch.setenv("LOGFIRE_ENVIRONMENT", "staging")

        with (
            patch.object(observability.logfire, "configure") as configure,
            patch.object(observability.logfire, "instrument_system_metrics"),
        ):
            observability.configure_logfire()

        configure.assert_called_once_with(
            service_name="weather-app",
            environment="staging",
            console=False,
            send_to_logfire="if-token-present",
        )

    def test_main_configures_before_invoking_click(self) -> None:
        """Main configures observability before dispatching to Click."""
        call_order: list[str] = []

        with (
            patch.object(
                application_main,
                "configure_logfire",
                side_effect=lambda: call_order.append("configure"),
            ),
            patch.object(
                application_main,
                "cli",
                side_effect=lambda: call_order.append("click"),
            ),
            patch.object(application_main.sys, "argv", ["weather", "version"]),
        ):
            application_main.main()

        assert call_order == ["configure", "click"]

    def test_direct_click_configures_before_logging_handlers(self, monkeypatch) -> None:
        """Direct Click commands configure Logfire before logging setup."""
        call_order: list[str] = []
        monkeypatch.setattr(
            cli_group,
            "configure_logfire",
            lambda: call_order.append("configure"),
        )
        monkeypatch.setattr(
            cli_group,
            "setup_default_logging",
            lambda *_args, **_kwargs: call_order.append("logging"),
        )

        result = CliRunner().invoke(cli_group.cli, ["version"])

        assert result.exit_code == 0
        assert call_order == ["configure", "logging"]
