"""Unit tests for main application module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from weather_app.main import main_async, main
from weather_app.exceptions import (
    ConfigurationError,
    LocationNotFoundError,
    APIRequestError,
    WeatherAppError,
)


class TestMainModule:
    """Test cases for main application module."""

    @pytest.mark.asyncio
    async def test_main_async_success_async_mode(self):
        """Test main_async function in async mode (success case)."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
    
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
    
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
    
            # Mock UI service
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock()
            MockUIService.return_value = mock_ui
    
            await main_async()
    
            # Verify setup
            MockConfig.assert_called_once()
            mock_config.validate.assert_called_once()
            MockSetupLogging.assert_called_once_with(mock_config)
            MockInstall.assert_called_once_with(show_locals=True)
    
            # Verify async mode was used
            MockUIService.assert_called_once_with(use_async=True)
            mock_ui.run_async.assert_called_once()
    
            # Verify logging
            assert MockLogWithContext.call_count >= 2  # Start and completion

    @pytest.mark.asyncio
    async def test_main_async_success_sync_mode(self):
        """Test main_async function in sync mode (success case)."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
    
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = False
            MockConfig.return_value = mock_config
    
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
    
            # Mock UI service
            mock_ui = Mock()
            mock_ui.run = Mock()
            MockUIService.return_value = mock_ui
    
            await main_async()
    
            # Verify sync mode was used
            MockUIService.assert_called_once_with(use_async=False)
            mock_ui.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_keyboard_interrupt(self):
        """Test main_async function handling KeyboardInterrupt."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext, \
             patch('builtins.print') as MockPrint:
    
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
    
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
    
            # Mock UI service that raises KeyboardInterrupt
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=KeyboardInterrupt)
            MockUIService.return_value = mock_ui
    
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
    
            await main_async()
    
            # Verify KeyboardInterrupt was handled gracefully
            MockLogWithContext.assert_called()
            MockPrint.assert_called_once_with("\n[bold yellow]Operation cancelled by user.[/bold yellow]")

    @pytest.mark.asyncio
    async def test_main_async_configuration_error(self):
        """Test main_async function handling ConfigurationError."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config that raises ConfigurationError
            mock_config = Mock()
            mock_config.validate.side_effect = ConfigurationError("API key missing")
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            # ConfigurationError should propagate since it happens before try-except
            with pytest.raises(ConfigurationError, match="API key missing"):
                await main_async()
            
            # Verify no logging or console output since error happens before setup
            MockLogWithContext.assert_not_called()
            mock_console.print.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_async_location_not_found_error(self):
        """Test main_async function handling LocationNotFoundError."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service that raises LocationNotFoundError
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=LocationNotFoundError("Unknown location"))
            MockUIService.return_value = mock_ui
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            await main_async()
            
            # Verify LocationNotFoundError was handled gracefully
            MockLogWithContext.assert_called()
            mock_console.print.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_api_request_error(self):
        """Test main_async function handling APIRequestError."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service that raises APIRequestError
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=APIRequestError("Network error"))
            MockUIService.return_value = mock_ui
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            await main_async()
            
            # Verify APIRequestError was handled gracefully
            MockLogWithContext.assert_called()
            mock_console.print.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_weather_app_error(self):
        """Test main_async function handling WeatherAppError."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service that raises WeatherAppError
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=WeatherAppError("Application error"))
            MockUIService.return_value = mock_ui
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            await main_async()
            
            # Verify WeatherAppError was handled gracefully
            MockLogWithContext.assert_called()
            mock_console.print.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_system_error(self):
        """Test main_async function handling system-level errors."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service that raises OSError
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=OSError("System error"))
            MockUIService.return_value = mock_ui
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            await main_async()
            
            # Verify system error was handled gracefully
            MockLogWithContext.assert_called()
            mock_console.print.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_unexpected_error(self):
        """Test main_async function handling unexpected errors."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.Console') as MockConsole, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service that raises unexpected error
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock(side_effect=ValueError("Unexpected error"))
            MockUIService.return_value = mock_ui
            
            # Mock console
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            await main_async()
            
            # Verify unexpected error was handled gracefully
            MockLogWithContext.assert_called()
            mock_console.print.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_async_cache_save_success(self):
        """Test main_async function successfully saves cache."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service with weather_service that has save_cache method
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock()
            mock_ui.weather_service = Mock()
            mock_ui.weather_service.save_cache = Mock()
            MockUIService.return_value = mock_ui
            
            await main_async()
            
            # Verify cache was saved
            mock_ui.weather_service.save_cache.assert_called_once()
            MockLogWithContext.assert_called()

    @pytest.mark.asyncio
    async def test_main_async_cache_save_failure(self):
        """Test main_async function handles cache save failure."""
        with patch('weather_app.main.Config') as MockConfig, \
             patch('weather_app.main.UIService') as MockUIService, \
             patch('weather_app.main.setup_default_logging') as MockSetupLogging, \
             patch('weather_app.main.LoggingConfig') as MockLoggingConfig, \
             patch('weather_app.main.install') as MockInstall, \
             patch('weather_app.main.log_with_context') as MockLogWithContext:
            
            # Mock config
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.use_async = True
            MockConfig.return_value = mock_config
            
            # Mock logger
            mock_logger = Mock()
            MockLoggingConfig.get_logger.return_value = mock_logger
            
            # Mock UI service with weather_service that fails to save cache
            mock_ui = AsyncMock()
            mock_ui.run_async = AsyncMock()
            mock_ui.weather_service = Mock()
            mock_ui.weather_service.save_cache = Mock(side_effect=Exception("Cache save failed"))
            MockUIService.return_value = mock_ui
            
            await main_async()
            
            # Verify cache save failure was handled gracefully
            mock_ui.weather_service.save_cache.assert_called_once()
            MockLogWithContext.assert_called()

    def test_main_function(self):
        """Test main function wrapper."""
        with patch('weather_app.main.asyncio') as MockAsyncio:
            main()
            MockAsyncio.run.assert_called_once()
            # Verify main_async was called
            call_args = MockAsyncio.run.call_args[0]
            assert len(call_args) == 1
            assert call_args[0].__name__ == 'main_async'