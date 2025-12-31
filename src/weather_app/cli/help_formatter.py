"""Custom help formatter to preserve formatting in epilog sections.

This module provides a custom Click help formatter that preserves line breaks
and formatting in the epilog section, preventing Click's text wrapping from
breaking up multi-line examples.
"""

import click
from typing import Any


class PreserveEpilogFormatter(click.HelpFormatter):
    """Custom Click help formatter that preserves formatting in epilog sections.

    This formatter overrides the write_text method to preserve line breaks
    and formatting for epilog content, which is especially useful for displaying
    multi-line examples in command help text.

    The formatter maintains all other Click help formatting behavior while
    only customizing text that appears to be epilog content.
    """

    def write_text(self, text: str) -> None:
        """Write text without wrapping to preserve formatting for epilog content."""
        if not text:
            return

        # For epilog text (which contains examples), preserve formatting
        # Check if this looks like epilog content (contains "Examples:")
        if "Examples:" in text:
            # Write text directly without rewrapping to preserve line breaks
            self.write(text)
        else:
            # Use default behavior for other text
            super().write_text(text)


class PreserveEpilogContext(click.Context):
    """Custom Click context with PreserveEpilogFormatter."""

    formatter_class = PreserveEpilogFormatter


def get_preserve_epilog_context_settings() -> dict[str, Any]:
    """Get context settings dict to use PreserveEpilogFormatter.

    Returns:
        A dictionary suitable for use as context_settings in Click commands
        and groups that configures the custom formatter.
    """
    return {
        "help_option_names": ["-h", "--help"],
    }


def apply_preserve_epilog_formatting(command: click.Command) -> click.Command:
    """Apply PreserveEpilogContext to a Click command.

    This function modifies the command to use the custom context class
    that preserves epilog formatting.

    Args:
        command: The Click command to modify.

    Returns:
        The modified command.
    """
    command.context_class = PreserveEpilogContext
    return command
