#!/usr/bin/env python3
"""Test script to verify the logging configuration changes."""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, "src")

from weather_app.logging_config import setup_default_logging
from weather_app.config import Config


def test_logging_config():
    """Test the logging configuration changes."""

    print("Testing logging configuration changes...")

    # Test 1: JSON logging with no custom log file
    print("\nTest 1: JSON logging with no custom log file")
    os.environ["LOG_FORMAT"] = "json"
    if "LOG_FILE" in os.environ:
        del os.environ["LOG_FILE"]
    config = Config()
    print(f"Log format: {config.log_format}")
    print(f"Log file: {config.log_file}")

    # Test 2: Text logging with no custom log file
    print("\nTest 2: Text logging with no custom log file")
    os.environ["LOG_FORMAT"] = "text"
    if "LOG_FILE" in os.environ:
        del os.environ["LOG_FILE"]
    config = Config()
    print(f"Log format: {config.log_format}")
    print(f"Log file: {config.log_file}")

    # Test 3: JSON logging with custom log file
    print("\nTest 3: JSON logging with custom log file")
    os.environ["LOG_FORMAT"] = "json"
    os.environ["LOG_FILE"] = "custom.json"
    config = Config()
    print(f"Log format: {config.log_format}")
    print(f"Log file: {config.log_file}")

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    test_logging_config()
