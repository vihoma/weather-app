"""Shared helpers for structured CLI command logging."""

import logging
from typing import Any

import click

from weather_app.logging_config import LoggingConfig, log_with_context


def get_command_logger(name: str) -> logging.Logger:
    """Return a configured logger for a CLI command module."""
    return LoggingConfig.get_logger(name)


def _command_context(ctx: click.Context) -> dict[str, Any]:
    """Build common structured context for a Click command."""
    return {
        "command_name": ctx.command.name if ctx.command else None,
        "command_path": ctx.command_path,
    }


def log_command_start(
    logger: logging.Logger, ctx: click.Context, **context: Any
) -> None:
    """Log the start of a CLI command."""
    log_with_context(
        logger,
        logging.INFO,
        "CLI command starting",
        **_command_context(ctx),
        **context,
    )


def log_command_success(
    logger: logging.Logger, ctx: click.Context, **context: Any
) -> None:
    """Log successful completion of a CLI command."""
    log_with_context(
        logger,
        logging.INFO,
        "CLI command completed",
        **_command_context(ctx),
        **context,
    )


def log_command_failure(
    logger: logging.Logger,
    ctx: click.Context,
    error: BaseException,
    *,
    level: int = logging.ERROR,
    exc_info: bool = False,
    **context: Any,
) -> None:
    """Log a CLI command failure with structured error details."""
    log_with_context(
        logger,
        level,
        "CLI command failed",
        exc_info=exc_info,
        **_command_context(ctx),
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
    )
