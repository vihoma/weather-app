"""Logging configuration with structured logging support."""

import copy
import logging
import logging.handlers
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import logfire

from weather_app.security import setup_secure_logging

_module_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from weather_app.config import Config

# Try to import python-json-logger, fallback to standard logging if not
# available.
try:
    from pythonjsonlogger import json as jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False
    jsonlogger = None  # type: ignore


class LoggingConfig:
    """Configure application logging with structured formatting."""

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_file: str | None = None,
        log_format: str = "text",
        enable_console: bool = True,
        enable_logfire: bool = True,
    ):
        """Initialize logging configuration.

        Args:
            log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
            log_file: Optional path to log file
            log_format: Log format ("text" or "json")
            enable_console: Whether to attach a console handler

        """
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format.lower()
        self.enable_console = enable_console
        self.enable_logfire = enable_logfire

    def setup_logging(self) -> None:
        """Configure the root logger with console and optional handlers."""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatters based on format preference
        if self.log_format == "json" and JSON_LOGGER_AVAILABLE:
            console_formatter = self._create_json_formatter()
            file_formatter = self._create_json_formatter()
        else:
            console_formatter = self._create_text_formatter()
            file_formatter = self._create_text_formatter(include_file_info=True)

        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        if self.enable_logfire:
            logfire_handler = logfire.LogfireLoggingHandler()
            logfire_handler.setLevel(self.log_level)
            logfire_handler.addFilter(LogfireTelemetryFilter())
            root_logger.addHandler(logfire_handler)

        # File handler (if specified)
        if self.log_file:
            self._setup_file_handler(root_logger, file_formatter)

        setup_secure_logging()

    def _create_text_formatter(
        self, include_file_info: bool = False
    ) -> logging.Formatter:
        """Create a text formatter for console output."""
        if include_file_info:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        else:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        return logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")

    def _create_json_formatter(self) -> logging.Formatter:
        """Create a JSON formatter for structured logging."""
        if not JSON_LOGGER_AVAILABLE:
            # Fallback to text format if JSON logger is not available
            return self._create_text_formatter(include_file_info=True)

        # Safe access to JsonFormatter
        JsonFormatter = getattr(jsonlogger, "JsonFormatter", None)
        if JsonFormatter:
            return JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(message)s %(funcName)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
                rename_fields={
                    "asctime": "timestamp",
                    "name": "logger",
                    "levelname": "level",
                    "filename": "file",
                    "lineno": "line",
                    "funcName": "function",
                },
            )
        else:
            return self._create_text_formatter(include_file_info=True)

    def _setup_file_handler(
        self, root_logger: logging.Logger, formatter: logging.Formatter
    ) -> None:
        """Set up file logging handler with rotation."""
        if not self.log_file:
            return

        try:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        except (OSError, PermissionError) as e:
            _module_logger.warning("Failed to setup file logging: %s", e)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a named logger with proper configuration.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance

        """
        return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    exc_info: bool = False,
    telemetry_redact_fields: frozenset[str] = frozenset(),
    **context: Any,
) -> None:
    """Log a message with structured context data.

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        exc_info: Whether to include exception info
        telemetry_redact_fields: Context keys excluded from Logfire telemetry
        **context: Additional context data to include in log

    """
    extra_data: dict[str, Any] = {"context": context} if context else {}
    if telemetry_redact_fields:
        extra_data["_logfire_redact_fields"] = telemetry_redact_fields
        extra_data["_logfire_event_message"] = message

    if _root_uses_json_formatter() and logger.isEnabledFor(level):
        # For JSON logging, include context as extra data
        logger.log(level, message, extra=extra_data, exc_info=exc_info, stacklevel=2)
    else:
        # For text logging, append context to message
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} [{context_str}]"
        logger.log(
            level,
            message,
            extra=extra_data,
            exc_info=exc_info,
            stacklevel=2,
        )


def _root_uses_json_formatter() -> bool:
    """Return True when the configured root handlers use JSON formatting."""
    if not JSON_LOGGER_AVAILABLE:
        return False

    json_formatter_type = getattr(jsonlogger, "JsonFormatter", None)
    if json_formatter_type is None:
        return False

    root_logger = logging.getLogger()
    return any(
        isinstance(getattr(handler, "formatter", None), json_formatter_type)
        for handler in root_logger.handlers
    )


def setup_default_logging(
    config: Optional["Config"] = None, enable_console: bool = True
) -> None:
    """Set up logging configuration for the application.

    Args:
        config: Optional Config object for custom logging settings
        enable_console: Whether to attach a console handler

    """
    if config:
        # Convert string log level to numeric value
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        # Use weather_app.json as default if JSON logging is enabled and no
        # custom log file specified
        log_file = config.log_file
        if log_file is None and config.log_format == "json":
            log_file = "weather_app.json"
        logging_config = LoggingConfig(
            log_level=log_level,
            log_file=log_file,
            log_format=config.log_format,
            enable_console=enable_console,
        )
    else:
        logging_config = LoggingConfig(
            log_level=logging.INFO,
            log_file="weather_app.log",
            log_format="text",
            enable_console=enable_console,
        )

    logging_config.setup_logging()


class LogfireTelemetryFilter(logging.Filter):
    """Create a safe telemetry-only copy of failure log records."""

    _SAFE_FAILURE_FIELDS = frozenset(
        {
            "category",
            "error_category",
            "error_class",
            "error_code",
            "error_type",
            "failure_category",
            "failure_type",
            "outcome",
            "status",
            "status_code",
        }
    )
    _UNSAFE_FAILURE_FIELDS = frozenset(
        {
            "address",
            "coordinates",
            "error",
            "error_detail",
            "error_details",
            "error_message",
            "exception",
            "exception_detail",
            "exception_details",
            "exception_message",
            "latitude",
            "location",
            "locations",
            "longitude",
            "place",
            "query",
            "stack",
            "stack_info",
            "stacktrace",
            "traceback",
        }
    )
    _STANDARD_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)
    _FAILURE_MESSAGE = "Weather application failure"

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        """Return a Logfire-safe copy when the record represents a failure."""
        if not self._is_failure_record(record):
            return True

        sanitized_record = copy.copy(record)
        for key in tuple(sanitized_record.__dict__):
            if key not in self._STANDARD_RECORD_FIELDS:
                sanitized_record.__dict__.pop(key, None)

        safe_context = self._safe_failure_context(record)
        if safe_context:
            sanitized_record.context = safe_context

        sanitized_record.msg = self._FAILURE_MESSAGE
        sanitized_record.args = ()
        sanitized_record.exc_info = None
        sanitized_record.exc_text = None
        sanitized_record.stack_info = None
        return sanitized_record

    def _is_failure_record(self, record: logging.LogRecord) -> bool:
        """Return whether a record can expose failure diagnostics."""
        if (
            record.levelno >= logging.ERROR
            or record.exc_info is not None
            or record.stack_info is not None
            or bool(getattr(record, "_logfire_redact_fields", frozenset()))
        ):
            return True

        context = getattr(record, "context", {})
        context_fields = set(context) if isinstance(context, Mapping) else set()
        record_fields = {
            key for key in record.__dict__ if key not in self._STANDARD_RECORD_FIELDS
        }
        failure_fields = self._SAFE_FAILURE_FIELDS | self._UNSAFE_FAILURE_FIELDS
        return bool((context_fields | record_fields) & failure_fields)

    def _safe_failure_context(self, record: logging.LogRecord) -> dict[str, Any]:
        """Keep only explicit, non-diagnostic failure classifications."""
        context = getattr(record, "context", {})
        safe_context = (
            {
                key: value
                for key, value in context.items()
                if key in self._SAFE_FAILURE_FIELDS
            }
            if isinstance(context, Mapping)
            else {}
        )

        for key in self._SAFE_FAILURE_FIELDS:
            if key in record.__dict__:
                safe_context[key] = record.__dict__[key]

        return safe_context
