"""Output formatters for weather data.

This module provides a factory pattern for converting WeatherData objects
into various output formats (TUI, JSON, Markdown).
"""

import abc
from typing import Dict, Type

from weather_app.models.weather_data import WeatherData


class BaseFormatter(abc.ABC):
    """Abstract base class for weather data formatters."""

    @abc.abstractmethod
    def format(self, weather_data: WeatherData) -> str:
        """Convert WeatherData to a formatted string.

        Args:
            weather_data: The weather data to format.

        Returns:
            Formatted string representation.
        """
        pass


class FormatterFactory:
    """Factory for obtaining formatter instances based on output format."""

    _formatters: Dict[str, Type[BaseFormatter]] = {}

    @classmethod
    def _load_formatters(cls) -> None:
        """Lazy load formatter classes to avoid circular imports."""
        if cls._formatters:
            return

        # Import here to avoid circular imports
        from weather_app.cli.formatters.json_formatter import JSONFormatter
        from weather_app.cli.formatters.markdown_formatter import MarkdownFormatter
        from weather_app.cli.formatters.tui_formatter import TUIFormatter

        cls._formatters.update(
            {
                "tui": TUIFormatter,
                "json": JSONFormatter,
                "markdown": MarkdownFormatter,
            }
        )

    @classmethod
    def get_formatter(cls, output_format: str, **kwargs) -> BaseFormatter:
        """Get a formatter instance for the specified output format.

        Args:
            output_format: One of "tui", "json", "markdown".
            **kwargs: Additional arguments to pass to formatter constructor.

        Returns:
            An instance of a BaseFormatter subclass.

        Raises:
            ValueError: If output_format is not supported.
        """
        cls._load_formatters()
        format_lower = output_format.lower()
        if format_lower not in cls._formatters:
            raise ValueError(
                f"Unsupported output format: {output_format}. "
                f"Supported formats: {list(cls._formatters.keys())}"
            )
        formatter_class = cls._formatters[format_lower]
        return formatter_class(**kwargs)
