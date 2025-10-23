"""Unit tests for utility functions."""

import pytest
from src.weather_app.utils import sanitize_string_for_logging, validate_api_key_format


class TestSanitizeStringForLogging:
    """Test cases for sanitize_string_for_logging function."""

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string returns placeholder."""
        result = sanitize_string_for_logging("")
        assert result == "[empty]"

    def test_sanitize_none_string(self):
        """Test sanitizing None returns placeholder."""
        result = sanitize_string_for_logging(None)
        assert result == "[empty]"

    def test_sanitize_normal_string(self):
        """Test sanitizing normal string without special characters."""
        text = "This is a normal log message"
        result = sanitize_string_for_logging(text)
        assert result == text

    def test_sanitize_string_with_newlines(self):
        """Test sanitizing string with newlines."""
        text = "Line 1\nLine 2\nLine 3"
        result = sanitize_string_for_logging(text)
        assert result == "Line 1\\nLine 2\\nLine 3"

    def test_sanitize_string_with_carriage_returns(self):
        """Test sanitizing string with carriage returns."""
        text = "Line 1\rLine 2\rLine 3"
        result = sanitize_string_for_logging(text)
        assert result == "Line 1\\rLine 2\\rLine 3"

    def test_sanitize_string_with_tabs(self):
        """Test sanitizing string with tabs."""
        text = "Column1\tColumn2\tColumn3"
        result = sanitize_string_for_logging(text)
        assert result == "Column1\\tColumn2\\tColumn3"

    def test_sanitize_string_with_mixed_whitespace(self):
        """Test sanitizing string with mixed whitespace characters."""
        text = "Line 1\n\r\tLine 2"
        result = sanitize_string_for_logging(text)
        assert result == "Line 1\\n\\r\\tLine 2"

    def test_sanitize_string_truncation(self):
        """Test string truncation for very long strings."""
        long_text = "A" * 150  # 150 characters
        result = sanitize_string_for_logging(long_text, max_length=100)
        assert len(result) == 103  # 100 chars + "..."
        assert result.endswith("...")

    def test_sanitize_string_custom_max_length(self):
        """Test string truncation with custom max length."""
        long_text = "A" * 60
        result = sanitize_string_for_logging(long_text, max_length=50)
        assert len(result) == 53  # 50 chars + "..."
        assert result.endswith("...")

    def test_sanitize_string_no_truncation_needed(self):
        """Test that strings shorter than max length are not truncated."""
        text = "Short message"
        result = sanitize_string_for_logging(text, max_length=50)
        assert result == text

    def test_sanitize_string_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        text = "   Message with spaces   "
        result = sanitize_string_for_logging(text)
        assert result == "Message with spaces"


class TestValidateApiKeyFormat:
    """Test cases for validate_api_key_format function."""

    def test_validate_valid_api_key(self):
        """Test validation of a valid API key."""
        valid_key = "abcdef1234567890abcdef1234567890"  # 32 chars
        assert validate_api_key_format(valid_key) is True

    def test_validate_api_key_minimum_length(self):
        """Test validation of API key with minimum acceptable length."""
        min_key = "a" * 16  # 16 chars
        assert validate_api_key_format(min_key) is True

    def test_validate_api_key_maximum_length(self):
        """Test validation of API key with maximum acceptable length."""
        max_key = "a" * 64  # 64 chars
        assert validate_api_key_format(max_key) is True

    def test_validate_api_key_too_short(self):
        """Test validation of API key that is too short."""
        short_key = "a" * 15  # 15 chars
        assert validate_api_key_format(short_key) is False

    def test_validate_api_key_too_long(self):
        """Test validation of API key that is too long."""
        long_key = "a" * 65  # 65 chars
        assert validate_api_key_format(long_key) is False

    def test_validate_empty_api_key(self):
        """Test validation of empty API key."""
        assert validate_api_key_format("") is False

    def test_validate_none_api_key(self):
        """Test validation of None API key."""
        assert validate_api_key_format(None) is False

    def test_validate_api_key_with_whitespace(self):
        """Test validation of API key containing whitespace."""
        key_with_space = "abc def1234567890"
        assert validate_api_key_format(key_with_space) is False

    def test_validate_api_key_with_newline(self):
        """Test validation of API key containing newline."""
        key_with_newline = "abc\ndef1234567890"
        assert validate_api_key_format(key_with_newline) is False

    def test_validate_api_key_with_tab(self):
        """Test validation of API key containing tab."""
        key_with_tab = "abc\tdef1234567890"
        assert validate_api_key_format(key_with_tab) is False

    def test_validate_api_key_with_carriage_return(self):
        """Test validation of API key containing carriage return."""
        key_with_cr = "abc\rdef1234567890"
        assert validate_api_key_format(key_with_cr) is False

    def test_validate_api_key_with_mixed_whitespace(self):
        """Test validation of API key with multiple whitespace types."""
        key_with_whitespace = "abc \n\r\t def"
        assert validate_api_key_format(key_with_whitespace) is False

    def test_validate_api_key_valid_characters(self):
        """Test validation of API key with valid special characters."""
        # API keys can contain letters, numbers, and some special chars
        # The current implementation only blocks whitespace, so these should pass
        valid_special_key = "abc-123_456.7890"  # 16 characters
        assert validate_api_key_format(valid_special_key) is True

    def test_validate_api_key_edge_case_lengths(self):
        """Test validation of API keys at edge case lengths."""
        # Test exactly 16 characters
        assert validate_api_key_format("a" * 16) is True
        # Test exactly 64 characters
        assert validate_api_key_format("a" * 64) is True
        # Test 15 characters (too short)
        assert validate_api_key_format("a" * 15) is False
        # Test 65 characters (too long)
        assert validate_api_key_format("a" * 65) is False