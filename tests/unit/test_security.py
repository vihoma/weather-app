"""Unit tests for security features."""

import pytest
import logging
from unittest.mock import Mock, patch
from src.weather_app.security import (
    SecureConfig,
    SensitiveDataFilter,
    mask_sensitive_string,
    SecurityError,
    KeyringUnavailableError,
)

# Mock keyring.errors for testing
try:
    from keyring.errors import KeyringError
except ImportError:

    class KeyringError(Exception):
        """Mock KeyringError for testing."""

        pass


class TestSensitiveDataFilter:
    """Test sensitive data masking functionality."""

    def test_mask_sensitive_string_api_key(self):
        """Test masking of API keys."""
        test_input = "API_KEY=abc123def456ghi789jkl012mno345pqr678"
        expected = "API_KEY=abc1...r678"
        result = mask_sensitive_string(test_input)
        assert result == expected

    def test_mask_sensitive_string_password(self):
        """Test masking of passwords."""
        test_input = "password=super_secret_password123"
        expected = "password=supe...d123"
        result = mask_sensitive_string(test_input)
        assert result == expected

    def test_mask_sensitive_string_token(self):
        """Test masking of tokens."""
        test_input = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        expected = "token=eyJh...VCJ9"
        result = mask_sensitive_string(test_input)
        assert result == expected

    def test_mask_sensitive_string_hash(self):
        """Test masking of hash values."""
        test_input = "md5_hash=5d41402abc4b2a76b9719d911017c592"
        expected = "md5_hash=5d41...c592"
        result = mask_sensitive_string(test_input)
        assert result == expected

    def test_mask_sensitive_string_no_match(self):
        """Test that non-sensitive strings are not modified."""
        test_input = "This is a normal message without sensitive data"
        result = mask_sensitive_string(test_input)
        assert result == test_input

    def test_filter_log_record(self):
        """Test that log records are properly filtered."""
        filter = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API_KEY=secret123",
            args=(),
            exc_info=None,
        )

        result = filter.filter(record)
        assert result is True
        assert "API_KEY=secr...t123" in record.msg


class TestSecureConfig:
    """Test secure configuration functionality."""

    @pytest.fixture
    def mock_keyring(self):
        """Mock keyring module."""
        with patch("src.weather_app.security.keyring") as mock:
            # Mock the availability check to return True
            mock.set_password.return_value = None
            mock.get_password.return_value = "test_value"
            mock.delete_password.return_value = None

            # Also patch the SecureConfig._check_keyring_availability to return True
            with patch(
                "src.weather_app.security.SecureConfig._check_keyring_availability",
                return_value=True,
            ):
                yield mock

    def test_keyring_availability_check(self, mock_keyring):
        """Test keyring availability detection."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "test_value"
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()
        assert secure_config.is_keyring_available() is True

    def test_keyring_unavailable(self):
        """Test behavior when keyring is unavailable."""
        with patch("src.weather_app.security.keyring.set_password") as mock_set:
            mock_set.side_effect = Exception("Keyring error")

            secure_config = SecureConfig()
            assert secure_config.is_keyring_available() is False

    def test_store_api_key_success(self, mock_keyring):
        """Test successful API key storage."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "test_value"
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()
        secure_config.store_api_key("test_api_key")

        # Should be called once for actual storage (availability check is bypassed by patch)
        mock_keyring.set_password.assert_called_once_with(
            "weather-app", "openweathermap", "test_api_key"
        )

    def test_store_api_key_failure(self, mock_keyring):
        """Test API key storage failure."""
        mock_keyring.set_password.side_effect = Exception("Storage failed")
        mock_keyring.get_password.return_value = "test_value"
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()

        with pytest.raises(SecurityError, match="Failed to store API key"):
            secure_config.store_api_key("test_api_key")

    def test_get_api_key_success(self, mock_keyring):
        """Test successful API key retrieval."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "stored_api_key"
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()
        result = secure_config.get_api_key()

        assert result == "stored_api_key"
        mock_keyring.get_password.assert_called_once_with(
            "weather-app", "openweathermap"
        )

    def test_get_api_key_not_found(self, mock_keyring):
        """Test API key retrieval when not found."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = None
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()
        result = secure_config.get_api_key()

        assert result is None

    def test_delete_api_key_success(self, mock_keyring):
        """Test successful API key deletion."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "test_value"
        mock_keyring.delete_password.return_value = None

        secure_config = SecureConfig()
        secure_config.delete_api_key()

        mock_keyring.delete_password.assert_called_once_with(
            "weather-app", "openweathermap"
        )

    def test_delete_api_key_failure(self, mock_keyring):
        """Test API key deletion failure."""
        mock_keyring.set_password.return_value = None
        mock_keyring.get_password.return_value = "test_value"
        mock_keyring.delete_password.side_effect = Exception("Deletion failed")

        secure_config = SecureConfig()

        with pytest.raises(SecurityError, match="Failed to delete API key"):
            secure_config.delete_api_key()


class TestSecurityIntegration:
    """Test integration of security features."""

    def test_setup_secure_logging(self):
        """Test that secure logging setup works."""
        from src.weather_app.security import setup_secure_logging

        # This should not raise any exceptions
        setup_secure_logging()

        # Verify that root logger has the filter
        root_logger = logging.getLogger()
        has_security_filter = any(
            isinstance(f, SensitiveDataFilter) for f in root_logger.filters
        )
        assert has_security_filter is True
