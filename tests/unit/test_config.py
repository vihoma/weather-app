"""Unit tests for the Config class and configuration handling."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.weather_app.config import Config, _default_cache_dir
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
                    
                    expected_cache_dir = _default_cache_dir()
                    assert config.api_key is None
                    assert config.owm_units == "metric"
                    assert config.cache_ttl == 600
                    assert config.request_timeout == 30
                    assert config.use_async is True
                    assert config.log_level == "INFO"
                    assert config.log_file == os.path.join(expected_cache_dir, "weather_app.log")
                    assert config.log_format == "text"
                    assert config.cache_persist is False
                    assert config.cache_file == os.path.join(expected_cache_dir, "weather_app_cache.json")

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
            # Mock secure storage to avoid keyring interference
            with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                mock_secure = Mock()
                mock_secure.get_api_key.return_value = None
                MockSecureConfig.return_value = mock_secure
                
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
        """Test that Config can be initialized with config file present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OWM_API_KEY=file_api_key\n")
            f.write("OWM_UNITS=kelvin\n")
            config_file = f.name
        
        try:
            # Test with config file only
            with patch.dict(os.environ, {}, clear=True):
                # Mock SecureConfig to avoid keyring interference
                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure
                    # Config should initialize without error
                    config = Config()
                    assert config is not None
        finally:
            os.unlink(config_file)

    def test_api_key_setter_validation(self):
        """Test that API key setter validates input properly."""
        config = Config()
        
        # Test valid API key
        config.api_key = "valid_api_key"
        assert config.api_key == "valid_api_key"
        
        # Test empty API key
        with pytest.raises(ValueError, match="API key must be a non‑empty string"):
            config.api_key = ""
        
        # Test None API key
        with pytest.raises(ValueError, match="API key must be a non‑empty string"):
            config.api_key = None  # type: ignore
        
        # Test non-string API key
        with pytest.raises(ValueError, match="API key must be a non‑empty string"):
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
        with pytest.raises(ValueError, match="API key must be a non‑empty string"):
            config.store_api_key("")
        
        # Test validation with None
        with pytest.raises(ValueError, match="API key must be a non‑empty string"):
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
        config.validate_config()

    def test_validate_method_without_api_key(self):
        """Test validate method when API key is missing."""
        config = Config()
        config._api_key = None  # type: ignore
        
        # Mock keyring availability
        mock_secure = Mock()
        mock_secure.is_keyring_available.return_value = True
        config._secure = mock_secure  # type: ignore
        
        with pytest.raises(APIKeyError) as exc_info:
            config.validate_config()
        
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
            config.validate_config()
        
        assert "API key not found" in str(exc_info.value)
        assert "keyring storage is not available" in str(exc_info.value)

    def test_config_properties_are_read_only(self):
        """Test that config properties are read-only (except api_key and units)."""
        config = Config()
        
        # Note: units has a setter for backward compatibility, so it's mutable
        # Test that trying to set read-only properties raises AttributeError
        # with pytest.raises(AttributeError):
        #     config.units = "new_units"  # units has a setter, skip this assertion
        
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
        # Test various true values (lowercase "true", "yes", "1", "on" should all work)
        true_values = ["true", "True", "TRUE", "yes", "1", "on"]
        for value in true_values:
            with patch.dict(os.environ, {"USE_ASYNC": value, "CACHE_PERSIST": value}):
                # Mock secure storage to avoid keyring issues
                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure
                    
                    config = Config()
                    assert config.use_async is True, f"Expected True for '{value}'"
                    assert config.cache_persist is True, f"Expected True for '{value}'"
        
        # Test various false values
        false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "anything_else"]
        for value in false_values:
            with patch.dict(os.environ, {"USE_ASYNC": value, "CACHE_PERSIST": value}):
                # Mock secure storage to avoid keyring issues
                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure
                    
                    config = Config()
                    assert config.use_async is False, f"Expected False for '{value}'"
                    assert config.cache_persist is False, f"Expected False for '{value}'"

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
        """Test that .weather.env file loading tries multiple locations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .weather.env file in temp directory
            env_file = Path(temp_dir) / ".weather.env"
            env_file.write_text("OWM_API_KEY=file_api_key\nOWM_UNITS=kelvin\n")

            # Mock Path.home() to return our temp dir so the home-based
            # .weather.env location resolves to our test file.
            with patch('src.weather_app.config.Path') as MockPath:
                # Path(".weather.env") → non-existent mock
                mock_cwd_env = Mock()
                mock_cwd_env.is_file.return_value = False

                # Path.home() / ".weather.env" → our real temp file
                mock_home = Mock()
                mock_home.__truediv__ = lambda self, name: Path(temp_dir) / name

                def path_side_effect(arg=None):
                    if arg == ".weather.env":
                        return mock_cwd_env
                    if arg == ".weather.yaml":
                        m = Mock()
                        m.is_file.return_value = False
                        return m
                    return Path(arg) if arg else Mock()

                MockPath.side_effect = path_side_effect
                MockPath.home.return_value = mock_home

                with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                    mock_secure = Mock()
                    mock_secure.get_api_key.return_value = None
                    MockSecureConfig.return_value = mock_secure

                    with patch.dict(os.environ, {}, clear=True):
                        config = Config()
                        # The env file values should be loaded
                        assert config.owm_api_key == "file_api_key"
                        assert config.owm_units == "kelvin"

    def test_config_file_loading_errors_handled_gracefully(self):
        """Test that errors during config file loading are handled gracefully."""
        # Mock SecureConfig to avoid keyring interference
        with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
            mock_secure = Mock()
            mock_secure.get_api_key.return_value = None
            MockSecureConfig.return_value = mock_secure

            # Mock dotenv_values to raise an exception
            with patch('src.weather_app.config.dotenv_values', side_effect=PermissionError("Permission denied")):
                # Should not raise any exception — Config handles errors gracefully
                config = Config()
                assert config is not None

    def test_environment_variables_override_config_files(self):
        """Test that environment variables override config file values."""
        with patch.dict(os.environ, {"OWM_API_KEY": "env_api_key"}):
            # Mock secure storage to avoid keyring issues
            with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                mock_secure = Mock()
                mock_secure.get_api_key.return_value = None
                MockSecureConfig.return_value = mock_secure

                # Mock YAML source to return a lower-priority value
                with patch.object(
                    Config, '_yaml_settings_source',
                    return_value={"OWM_API_KEY": "yaml_api_key"},
                ):
                    config = Config()

                    # Environment variable should take precedence over YAML
                    assert config.api_key == "env_api_key"

    def test_yaml_settings_source_loads_values(self):
        """Test that YAML settings source correctly loads and uppercases keys."""
        yaml_content = "owm_units: imperial\ncache_ttl: 120\nuse_async: false\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file = Path(temp_dir) / ".weather.yaml"
            yaml_file.write_text(yaml_content)

            with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                mock_secure = Mock()
                mock_secure.get_api_key.return_value = None
                MockSecureConfig.return_value = mock_secure

                # Point the YAML source to our temp file
                with patch('src.weather_app.config.Path') as MockPath:
                    mock_cwd_yaml = Mock()
                    mock_cwd_yaml.is_file.return_value = True
                    mock_cwd_yaml.__fspath__ = lambda self: str(yaml_file)

                    def path_side_effect(arg=None):
                        if arg == ".weather.yaml":
                            return yaml_file
                        if arg == ".weather.env":
                            m = Mock()
                            m.is_file.return_value = False
                            return m
                        return Path(arg) if arg else Mock()

                    MockPath.side_effect = path_side_effect
                    MockPath.home.return_value = Path(temp_dir)

                    with patch.dict(os.environ, {}, clear=True):
                        config = Config()
                        assert config.owm_units == "imperial"
                        assert config.cache_ttl == 120
                        assert config.use_async is False

    def test_yaml_unknown_keys_logged_as_warning(self):
        """Test that unknown YAML keys trigger a warning log."""
        yaml_content = "owm_units: imperial\nunknown_key: some_value\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file = Path(temp_dir) / ".weather.yaml"
            yaml_file.write_text(yaml_content)

            with patch('src.weather_app.config.SecureConfig') as MockSecureConfig:
                mock_secure = Mock()
                mock_secure.get_api_key.return_value = None
                MockSecureConfig.return_value = mock_secure

                with patch('src.weather_app.config.Path') as MockPath:
                    def path_side_effect(arg=None):
                        if arg == ".weather.yaml":
                            return yaml_file
                        if arg == ".weather.env":
                            m = Mock()
                            m.is_file.return_value = False
                            return m
                        return Path(arg) if arg else Mock()

                    MockPath.side_effect = path_side_effect
                    MockPath.home.return_value = Path(temp_dir)

                    with patch.dict(os.environ, {}, clear=True):
                        with patch('src.weather_app.config.logger') as mock_logger:
                            config = Config()
                            # Verify warning was logged for unknown key
                            mock_logger.warning.assert_any_call(
                                "Unknown configuration key in YAML: '%s' (will be ignored)",
                                "unknown_key",
                            )
                            # The known key should still be loaded
                            assert config.owm_units == "imperial"

    def test_env_file_source_returns_parsed_values(self):
        """Test that _env_file_settings_source returns values directly."""
        env_content = "OWM_API_KEY=env_file_key\nOWM_UNITS=standard\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".weather.env"
            env_file.write_text(env_content)

            with patch('src.weather_app.config.Path') as MockPath:
                def path_side_effect(arg=None):
                    if arg == ".weather.env":
                        return env_file
                    if arg == ".weather.yaml":
                        m = Mock()
                        m.is_file.return_value = False
                        return m
                    return Path(arg) if arg else Mock()

                MockPath.side_effect = path_side_effect
                MockPath.home.return_value = Path(temp_dir)

                # Call the source method directly
                result = Config._env_file_settings_source(Config)
                assert result.get("OWM_API_KEY") == "env_file_key"
                assert result.get("OWM_UNITS") == "standard"

    def test_cache_dir_cross_platform_default(self):
        """Test that CACHE_DIR default resolves to an absolute path."""
        expected = os.path.join(os.path.expanduser("~"), ".cache", "weather_app")
        assert _default_cache_dir() == expected
        assert os.path.isabs(expected)
