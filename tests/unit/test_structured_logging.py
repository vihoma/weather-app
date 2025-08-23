#!/usr/bin/env python3
"""Test script for structured logging functionality."""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, "src")

from weather_app.logging_config import LoggingConfig, log_with_context


def test_text_logging():
    """Test text format logging."""
    print("Testing text format logging...")
    config = LoggingConfig(log_format="text")
    config.setup_logging()

    logger = logging.getLogger("test_text")
    logger.info("Simple text message")
    log_with_context(
        logger, logging.INFO, "Message with context", test_value="123", user="test_user"
    )


def test_json_logging():
    """Test JSON format logging."""
    print("\nTesting JSON format logging...")
    config = LoggingConfig(log_format="json")
    config.setup_logging()

    logger = logging.getLogger("test_json")
    logger.info("Simple JSON message")
    log_with_context(
        logger, logging.INFO, "Message with context", test_value="123", user="test_user"
    )


def test_error_logging():
    """Test error logging with context."""
    print("\nTesting error logging...")
    config = LoggingConfig(log_format="json")
    config.setup_logging()

    logger = logging.getLogger("test_error")
    try:
        raise ValueError("Test error for structured logging")
    except ValueError as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Error occurred",
            error_type="value_error",
            error_message=str(e),
            exc_info=True,
        )


if __name__ == "__main__":
    test_text_logging()
    test_json_logging()
    test_error_logging()
    print("\nTest completed!")
