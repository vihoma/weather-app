"""Tests for handler-boundary sensitive-data redaction."""

import logging
from typing import ClassVar
from unittest.mock import patch

import click

from weather_app.cli.command_logging import log_command_failure
from weather_app.logging_config import LoggingConfig, log_with_context
from weather_app.security import SensitiveDataFilter


class CapturingHandler(logging.Handler):
    """Capture emitted records without formatting or exporting them."""

    records: ClassVar[list[logging.LogRecord]]

    def __init__(self) -> None:
        """Initialize an empty record capture."""
        super().__init__()
        self.records = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store the record after handler filtering."""
        self.records.append(record)


class TestHandlerBoundaryRedaction:
    """Verify every configured handler receives redacted records."""

    def test_redacts_message_args_and_nested_context_before_logfire(self) -> None:
        """Sensitive values must not reach the Logfire handler record."""
        logfire_handler = CapturingHandler()
        config = LoggingConfig(enable_console=False, enable_logfire=True)

        with patch(
            "weather_app.logging_config.logfire.LogfireLoggingHandler",
            return_value=logfire_handler,
        ):
            config.setup_logging()

        logger = logging.getLogger("weather_app.test_logging_redaction")
        logger.info(
            "request API_KEY=message-secret-value %s",
            "token=argument-secret-value",
            extra={
                "context": {
                    "request": {
                        "api_key": "context-api-key-value",
                        "credentials": {
                            "access_token": "context-token-value",
                        },
                    }
                }
            },
        )

        assert len(logfire_handler.records) == 1
        record = logfire_handler.records[0]
        assert "message-secret-value" not in record.msg
        assert "argument-secret-value" not in record.args[0]
        assert record.context["request"]["api_key"] == "cont...alue"
        assert record.context["request"]["credentials"]["access_token"] == "cont...alue"

    def test_attaches_sensitive_filter_to_logfire_handler(self) -> None:
        """Logfire handlers must receive the boundary redaction filter."""
        logfire_handler = CapturingHandler()

        with patch(
            "weather_app.logging_config.logfire.LogfireLoggingHandler",
            return_value=logfire_handler,
        ):
            LoggingConfig(enable_console=False, enable_logfire=True).setup_logging()

        assert any(
            isinstance(log_filter, SensitiveDataFilter)
            for log_filter in logfire_handler.filters
        )

    def test_removes_failed_location_error_from_logfire_only(self) -> None:
        """Location-bearing errors remain local but are removed from telemetry."""
        logfire_handler = CapturingHandler()
        local_handler = CapturingHandler()
        sensitive_location = "43.6426,-79.3871"

        with patch(
            "weather_app.logging_config.logfire.LogfireLoggingHandler",
            return_value=logfire_handler,
        ):
            LoggingConfig(enable_console=False, enable_logfire=True).setup_logging()

        root_logger = logging.getLogger()
        root_logger.addHandler(local_handler)
        try:
            ctx = click.Context(click.Command("weather"))
            log_command_failure(
                logging.getLogger("weather_app.test_logging_redaction"),
                ctx,
                ValueError(f"Location lookup failed for {sensitive_location}"),
                exc_info=True,
            )
        finally:
            root_logger.removeHandler(local_handler)

        assert len(logfire_handler.records) == 1
        logfire_record = logfire_handler.records[0]
        assert sensitive_location not in str(logfire_record.__dict__)
        assert logfire_record.context["error_type"] == "ValueError"
        assert "error_message" not in logfire_record.context
        assert logfire_record.exc_info is None

        assert len(local_handler.records) == 1
        assert sensitive_location in local_handler.records[0].getMessage()
        assert local_handler.records[0].exc_info is not None

    def test_sanitizes_unmarked_structured_failure_for_logfire_only(self) -> None:
        """Unmarked structured exceptions must not expose telemetry diagnostics."""
        logfire_handler = CapturingHandler()
        local_handler = CapturingHandler()
        sensitive_location = "43.6426,-79.3871"

        with patch(
            "weather_app.logging_config.logfire.LogfireLoggingHandler",
            return_value=logfire_handler,
        ):
            LoggingConfig(enable_console=False, enable_logfire=True).setup_logging()

        root_logger = logging.getLogger()
        root_logger.addHandler(local_handler)
        try:
            try:
                raise ValueError(f"Location lookup failed for {sensitive_location}")
            except ValueError:
                log_with_context(
                    logging.getLogger("weather_app.test_logging_redaction"),
                    logging.ERROR,
                    "Interactive weather lookup failed",
                    exc_info=True,
                    error_type="ValueError",
                    failure_category="location_lookup",
                    error_message=sensitive_location,
                    location=sensitive_location,
                )
        finally:
            root_logger.removeHandler(local_handler)

        assert len(logfire_handler.records) == 1
        logfire_record = logfire_handler.records[0]
        assert logfire_record.getMessage() == "Weather application failure"
        assert logfire_record.context == {
            "error_type": "ValueError",
            "failure_category": "location_lookup",
        }
        assert sensitive_location not in str(logfire_record.__dict__)
        assert logfire_record.exc_info is None
        assert logfire_record.exc_text is None
        assert logfire_record.stack_info is None

        assert len(local_handler.records) == 1
        local_record = local_handler.records[0]
        assert sensitive_location in local_record.getMessage()
        assert local_record.exc_info is not None

    def test_sanitizes_service_style_failure_for_logfire_only(self) -> None:
        """Direct service errors retain local detail but export a generic event."""
        logfire_handler = CapturingHandler()
        local_handler = CapturingHandler()
        sensitive_location = "51.5072,-0.1276"

        with patch(
            "weather_app.logging_config.logfire.LogfireLoggingHandler",
            return_value=logfire_handler,
        ):
            LoggingConfig(enable_console=False, enable_logfire=True).setup_logging()

        root_logger = logging.getLogger()
        root_logger.addHandler(local_handler)
        try:
            try:
                raise RuntimeError(f"Weather provider rejected {sensitive_location}")
            except RuntimeError:
                logging.getLogger("weather_app.services.weather_service").error(
                    "API request failed for %s: %s",
                    sensitive_location,
                    "provider request details",
                    exc_info=True,
                    extra={
                        "location": sensitive_location,
                        "failure_category": "api_request",
                    },
                )
        finally:
            root_logger.removeHandler(local_handler)

        assert len(logfire_handler.records) == 1
        logfire_record = logfire_handler.records[0]
        assert logfire_record.getMessage() == "Weather application failure"
        assert logfire_record.context == {"failure_category": "api_request"}
        assert sensitive_location not in str(logfire_record.__dict__)
        assert "provider request details" not in str(logfire_record.__dict__)
        assert logfire_record.exc_info is None
        assert logfire_record.exc_text is None
        assert logfire_record.stack_info is None

        assert len(local_handler.records) == 1
        local_record = local_handler.records[0]
        assert sensitive_location in local_record.getMessage()
        assert "provider request details" in local_record.getMessage()
        assert local_record.exc_info is not None
