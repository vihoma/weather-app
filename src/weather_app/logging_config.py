"""Logging configuration for the Weather Application."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from .security import setup_secure_logging

if TYPE_CHECKING:
    from .config import Config


class LoggingConfig:
    """Configure application logging with structured formatting."""

    def __init__(self, log_level: int = logging.INFO, log_file: Optional[str] = None):
        """
        Initialize logging configuration.

        Args:
            log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
            log_file: Optional path to log file
        """
        self.log_level = log_level
        self.log_file = log_file

    def setup_logging(self) -> None:
        """Configure the root logger with console and optional file handlers."""
        # Create formatters
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            self._setup_file_handler(root_logger, file_formatter)

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
        """
        Get a named logger with proper configuration.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)


def setup_default_logging(config: Optional["Config"] = None) -> None:
    """
    Set up logging configuration for the application.

    Args:
        config: Optional Config object for custom logging settings
    """
    if config:
        # Convert string log level to numeric value
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        logging_config = LoggingConfig(log_level=log_level, log_file=config.log_file)
    else:
        logging_config = LoggingConfig(
            log_level=logging.INFO, log_file="weather_app.log"
        )

    logging_config.setup_logging()

    # Set up secure logging with sensitive data filtering
    setup_secure_logging()
