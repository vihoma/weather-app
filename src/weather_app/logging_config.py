"""Logging configuration for the Weather Application with structured logging support."""

import logging
import logging.handlers
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from weather_app.security import setup_secure_logging

if TYPE_CHECKING:
    from weather_app.config import Config

# Try to import python-json-logger, fallback to standard logging if not available
try:
    from pythonjsonlogger import jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False
    jsonlogger = None  # type: ignore


class LoggingConfig:
    """Configure application logging with structured JSON formatting."""

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_file: Optional[str] = None,
        log_format: str = "text",
    ):
        """Initialize logging configuration.

        Args:
            log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
            log_file: Optional path to log file
            log_format: Log format ("text" or "json")

        """
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format.lower()

    def setup_logging(self) -> None:
        """Configure the root logger with console and optional file handlers."""
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

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            self._setup_file_handler(root_logger, file_formatter)

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
            logging.warning(f"Failed to setup file logging: {e}")

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
    **context: Any,
) -> None:
    """Log a message with structured context data.

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        exc_info: Whether to include exception info
        **context: Additional context data to include in log

    """
    if JSON_LOGGER_AVAILABLE and logger.isEnabledFor(level):
        # For JSON logging, include context as extra data
        extra_data = {"context": context} if context else {}
        logger.log(level, message, extra=extra_data, exc_info=exc_info, stacklevel=2)
    else:
        # For text logging, append context to message
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} [{context_str}]"
        logger.log(level, message, exc_info=exc_info, stacklevel=2)


def setup_default_logging(config: Optional["Config"] = None) -> None:
    """Set up logging configuration for the application.

    Args:
        config: Optional Config object for custom logging settings

    """
    if config:
        # Convert string log level to numeric value
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        # Use weather_app.json as default if JSON logging is enabled and no custom log file specified
        log_file = config.log_file
        if log_file is None and config.log_format == "json":
            log_file = "weather_app.json"
        logging_config = LoggingConfig(
            log_level=log_level, log_file=log_file, log_format=config.log_format
        )
    else:
        logging_config = LoggingConfig(
            log_level=logging.INFO, log_file="weather_app.log", log_format="text"
        )

    logging_config.setup_logging()

    # Set up secure logging with sensitive data filtering
    setup_secure_logging()
