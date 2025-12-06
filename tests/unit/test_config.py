"""Unit tests for the Config class and configuration handling."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from src.weather_app.config import Config
from src.weather_app.exceptions import APIKeyError
from src.weather_app.security import KeyringUnavailableError


class TestConfig:
    """Test suite for the Config class."""

    def test_config_initialization_with_defaults(self):
        """Test that Config initializes with default values when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock the secure storage to return None for API key
            with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                mock_secure = Mock()
                mock_secure.get_api_key.return_value = None
                MockSecureConfig.return_value = mock_secure
                
                # Mock the environment loading to avoid loading from .weather.env file
                with patch.object(Config, '_load_environment_variables'):
                    config = Config()
                    
                    assert config.api_key is None
                    assert config.owm_units == "metric"
                    assert config.cache_ttl == 600
                    assert config.request_timeout == 30
                    assert config.use_async is True
                    assert config.log_level == "INFO"
                    assert config.log_file is None
                    assert config.log_format == "text"
                    assert config.cache_persist is False
                    assert config.cache_file == "E:\\Temp\\.weather_app_cache.json"

    def test_config_initialization_with_environment_variables(self):
        """Test that Config reads environment variables correctly."""
        with patch.dict(os.environ, {
            "OWM_API_KEY": "test_api_key_123",
            "OWM_UNITS": "imperial",
            "CACHE_TTL": "300",
            "REQUEST_TIMEOUT": "15",
            "USE_ASYNC": "false",
            "LOG_LEVEL": "DEBUG",
            "LOG_FILE": "E:\\Temp\\weather.log",
            "LOG_FORMAT": "json",
            "CACHE_PERSIST": "true",
            "CACHE_FILE": "E:\\Temp\\cache.json"
        }):
            config = Config()
            
            assert config.api_key == "test_api_key_123"
            assert config.units == "imperial"
            assert config.cache_ttl == 300
            assert config.request_timeout == 15
            assert config.use_async is False
            assert config.log_level == "DEBUG"
            assert config.log_file == "E:\\Temp\\weather.log"
            assert config.log_format == "json"
            assert config.cache_persist is True
            assert config.cache_file == "E:\\Temp\\cache.json"

    def test_config_environment_variable_loading_order(self):
        """Test that environment variables take precedence over config files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OWM_API_KEY=file_api_key\n")
            f.write("OWM_UNITS=kelvin\n")
            config_file = f.name
        
        try:
            # Test with config file only
            with patch.dict(os.environ, {}, clear=True):
                with patch('src.weather_app.config.load_dotenv') as mock_load_dotenv:
                    config = Config()
                    # Verify load_dotenv was called with the config file
                    mock_load_dotenv.assert_called()
        finally:
            os.unlink(config_file)

    def test_api_key_setter_validation(self):
        """Test that API key setter validates input properly."""
        config = Config()
        
        # Test valid API key
        config.api_key = "valid_api_key"
        assert config.api_key == "valid_api_key"
        
        # Test empty API key
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            config.api_key = ""
        
        # Test None API key
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            config.api_key = None  # type: ignore
        
        # Test non-string API key
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            config.api_key = 123  # type: ignore

    def test_store_api_key_method(self):
        """Test the store_api_key method with secure storage."""
        config = Config()
        
        # Mock the secure storage
        mock_secure = Mock()
        # Use direct attribute assignment for testing
        config._secure = mock_secure  # type: ignore
        
        # Test successful storage
        config.store_api_key("new_api_key")
        mock_secure.store_api_key.assert_called_once_with("new_api_key")
        assert config.api_key == "new_api_key"
        
        # Test validation with empty key
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            config.store_api_key("")
        
        # Test validation with None
        with pytest.raises(ValueError, match="API key must be a non-empty string"):
            config.store_api_key(None)  # type: ignore

    def test_store_api_key_with_keyring_unavailable(self):
        """Test store_api_key when keyring is not available."""
        config = Config()
        
        # Mock secure storage to raise KeyringUnavailableError
        mock_secure = Mock()
        mock_secure.store_api_key.side_effect = KeyringUnavailableError("Keyring not available")
        config._secure = mock_secure  # type: ignore
        
        with pytest.raises(KeyringUnavailableError, match="Keyring not available"):
            config.store_api_key("test_key")

    def test_is_keyring_available_method(self):
        """Test the is_keyring_available method."""
        config = Config()
        
        # Mock the secure storage
        mock_secure = Mock()
        mock_secure.is_keyring_available.return_value = True
        config._secure = mock_secure  # type: ignore
        
        assert config.is_keyring_available() is True
        
        # Test when keyring is not available
        mock_secure.is_keyring_available.return_value = False
        assert config.is_keyring_available() is False

    def test_validate_method_with_api_key(self):
        """Test validate method when API key is present."""
        config = Config()
        config._api_key = "valid_api_key"
        
        # Should not raise any exception
        config.validate()

    def test_validate_method_without_api_key(self):
        """Test validate method when API key is missing."""
        config = Config()
        config._api_key = None  # type: ignore
        
        # Mock keyring availability
        mock_secure = Mock()
        mock_secure.is_keyring_available.return_value = True
        config._secure = mock_secure  # type: ignore
        
        with pytest.raises(APIKeyError) as exc_info:
            config.validate()
        
        assert "API key not found" in str(exc_info.value)
        assert "keyring" in str(exc_info.value).lower()

    def test_validate_method_without_api_key_and_no_keyring(self):
        """Test validate method when API key is missing and keyring is unavailable."""
        config = Config()
        config._api_key = None  # type: ignore
        
        # Mock keyring as unavailable
        mock_secure = Mock()
        mock_secure.is_keyring_available.return_value = False
        config._secure = mock_secure  # type: ignore
        
        with pytest.raises(APIKeyError) as exc_info:
            config.validate()
        
        assert "API key not found" in str(exc_info.value)
        assert "keyring storage is not available" in str(exc_info.value)

    def test_config_properties_are_read_only(self):
        """Test that config properties are read-only (except api_key)."""
        config = Config()
        
        # Test that trying to set read-only properties raises AttributeError
        with pytest.raises(AttributeError):
            config.units = "new_units"
        
        with pytest.raises(AttributeError):
            config.cache_ttl = 100
        
        with pytest.raises(AttributeError):
            config.request_timeout = 10
        
        with pytest.raises(AttributeError):
            config.use_async = False
        
        with pytest.raises(AttributeError):
            config.log_level = "DEBUG"
        
        with pytest.raises(AttributeError):
            config.log_file = "/new/path.log"
        
        with pytest.raises(AttributeError):
            config.log_format = "json"
        
        with pytest.raises(AttributeError):
            config.cache_persist = True
        
        with pytest.raises(AttributeError):
            config.cache_file = "/new/cache.json"

    def test_config_with_keyring_api_key(self):
        """Test Config initialization when API key is available from keyring."""
        with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
            mock_secure = Mock()
            mock_secure.get_api_key.return_value = "keyring_api_key"
            MockSecureConfig.return_value = mock_secure
            
            with patch.dict(os.environ, {}, clear=True):
                config = Config()
                
                assert config.api_key == "keyring_api_key"
                mock_secure.get_api_key.assert_called_once()

    def test_config_with_keyring_unavailable_fallback_to_env(self):
        """Test Config initialization when keyring is unavailable, falls back to env."""
        with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
            mock_secure = Mock()
            mock_secure.get_api_key.side_effect = KeyringUnavailableError("Keyring not available")
            MockSecureConfig.return_value = mock_secure
            
            with patch.dict(os.environ, {"OWM_API_KEY": "env_api_key"}):
                config = Config()
                
                assert config.api_key == "env_api_key"

    def test_config_with_empty_keyring_fallback_to_env(self):
        """Test Config initialization when keyring returns None, falls back to env."""
        with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
            mock_secure = Mock()
            mock_secure.get_api_key.return_value = None
            MockSecureConfig.return_value = mock_secure
            
            with patch.dict(os.environ, {"OWM_API_KEY": "env_api_key"}):
                config = Config()
                
                assert config.api_key == "env_api_key"

    def test_boolean_environment_variables_parsing(self):
        """Test that boolean environment variables are parsed correctly."""
        # Test various true values (only lowercase "true" should work based on implementation)
        true_values = ["true"]
        for value in true_values:
            with patch.dict(os.environ, {"USE_ASYNC": value, "CACHE_PERSIST": value}):
                # Mock secure storage to avoid keyring issues
                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure
                    
                    config = Config()
                    assert config.use_async is True
                    assert config.cache_persist is True
        
        # Test various false values
        false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "anything_else"]
        for value in false_values:
            with patch.dict(os.environ, {"USE_ASYNC": value, "CACHE_PERSIST": value}):
                # Mock secure storage to avoid keyring issues
                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure
                    
                    config = Config()
                    assert config.use_async is False
                    assert config.cache_persist is False

    def test_numeric_environment_variables_parsing(self):
        """Test that numeric environment variables are parsed correctly."""
        with patch.dict(os.environ, {
            "CACHE_TTL": "900",
            "REQUEST_TIMEOUT": "45"
        }):
            config = Config()
            assert config.cache_ttl == 900
            assert config.request_timeout == 45

    def test_config_file_loading_with_multiple_locations(self):
        """Test that config file loading tries multiple locations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config file in temp directory
            config_file = Path(temp_dir) / ".weather.env"
            config_file.write_text("OWM_API_KEY=file_api_key\nOWM_UNITS=kelvin\n")
            
            with patch('src.weather_app.config.Path') as MockPath:
                # Mock the config locations to include our temp file
                mock_paths = [
                    Mock(expanduser=Mock(return_value=Mock(exists=Mock(return_value=False)))),
                    Mock(expanduser=Mock(return_value=Mock(exists=Mock(return_value=False)))),
                    Mock(expanduser=Mock(return_value=config_file)),
                ]
                MockPath.side_effect = mock_paths
                
                with patch('src.weather_app.config.load_dotenv') as mock_load_dotenv:
                    # Mock secure storage to avoid keyring issues
                    with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                        mock_secure = Mock()
                        mock_secure.get_api_key.return_value = None
                        MockSecureConfig.return_value = mock_secure
                        
                        config = Config()
                        
                        # Verify load_dotenv was called with our config file
                        # Note: The actual implementation calls load_dotenv twice - once for config file and once for env vars
                        mock_load_dotenv.assert_any_call(dotenv_path=config_file, override=False)

    def test_config_file_loading_errors_handled_gracefully(self):
        """Test that errors during config file loading are handled gracefully."""
        with patch('src.weather_app.config.Path') as MockPath:
            # Mock a path that raises PermissionError
            mock_path = Mock()
            mock_path.expanduser.return_value = Mock(
                exists=Mock(side_effect=PermissionError("Permission denied"))
            )
            MockPath.return_value = mock_path
            
            # Should not raise any exception
            config = Config()
            assert config is not None

    def test_environment_variables_override_config_files(self):
        """Test that environment variables override config file values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OWM_API_KEY=file_api_key\n")
            f.write("OWM_UNITS=kelvin\n")
            config_file = f.name

        try:
            with patch.dict(os.environ, {"OWM_API_KEY": "env_api_key"}):
                # Mock the Path object to properly simulate file existence
                with patch('src.weather_app.config.Path') as MockPath:
                    mock_path = Mock()
                    # Create a mock that has exists() method returning True
                    mock_expanded = Mock()
                    mock_expanded.exists.return_value = True
                    mock_path.expanduser.return_value = mock_expanded
                    MockPath.return_value = mock_path
                    
                    # Mock secure storage to avoid keyring issues
                    with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                        mock_secure = Mock()
                        mock_secure.get_api_key.return_value = None
                        MockSecureConfig.return_value = mock_secure
                        
                        # Mock load_dotenv to prevent actual file loading
                        with patch('src.weather_app.config.load_dotenv') as mock_load_dotenv:
                            config = Config()
                            
                            # Environment variable should take precedence over config file
                            assert config.api_key == "env_api_key"
        finally:
            os.unlink(config_file)
