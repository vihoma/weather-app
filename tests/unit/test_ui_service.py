"""Unit tests for UI service components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.weather_app.services.ui_service import UIService
from src.weather_app.models.weather_data import WeatherData
from src.weather_app.services.async_weather_service import AsyncWeatherService
from src.weather_app.services.weather_service import WeatherService
from src.weather_app.exceptions import (
    InvalidLocationError,
    LocationNotFoundError,
    APIRequestError,
    NetworkError,
    RateLimitError,
    DataParsingError,
)


class TestUIService:
    """Test cases for UIService class."""

    def test_ui_service_initialization_sync(self):
        """Test UIService initialization in sync mode."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"  # Add cache_file
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService(use_async=False)
            
            assert ui_service.use_async is False
            assert ui_service.current_units == "metric"
            assert ui_service.query_history == []
            mock_config.validate.assert_called_once()
            MockWeatherService.assert_called_once_with(mock_config)

    def test_ui_service_initialization_async(self):
        """Test UIService initialization in async mode."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.AsyncWeatherService') as MockAsyncWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"  # Add cache_file
            MockConfig.return_value = mock_config
            
            mock_async_weather_service = Mock()
            MockAsyncWeatherService.return_value = mock_async_weather_service
            
            ui_service = UIService(use_async=True)
            
            assert ui_service.use_async is True
            assert ui_service.current_units == "metric"
            assert ui_service.query_history == []
            mock_config.validate.assert_called_once()
            MockAsyncWeatherService.assert_called_once_with(mock_config)

    def test_temp_unit_method(self):
        """Test temperature unit symbol generation."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService()
            
            # Test metric units
            ui_service.current_units = "metric"
            assert ui_service._temp_unit() == "°C"
            
            # Test imperial units
            ui_service.current_units = "imperial"
            assert ui_service._temp_unit() == "°F"
            
            # Test default units
            ui_service.current_units = "default"
            assert ui_service._temp_unit() == "K"
            
            # Test unknown units
            ui_service.current_units = "unknown"
            assert ui_service._temp_unit() == "K"

    def test_speed_unit_method(self):
        """Test speed unit symbol generation."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService()
            
            # Test metric units
            ui_service.current_units = "metric"
            assert ui_service._speed_unit() == "m/s"
            
            # Test imperial units
            ui_service.current_units = "imperial"
            assert ui_service._speed_unit() == "mph"
            
            # Test default units
            ui_service.current_units = "default"
            assert ui_service._speed_unit() == "m/s"

    def test_add_table_row_method(self):
        """Test adding rows to Rich table."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService()
            
            # Mock table
            mock_table = Mock()
            
            ui_service._add_table_row(mock_table, "Temperature", "25°C")
            
            # Verify table.add_row was called with Text objects
            mock_table.add_row.assert_called_once()
            args = mock_table.add_row.call_args[0]
            assert len(args) == 2
            # Check that Text objects were created with correct content
            assert str(args[0]) == "Temperature"
            assert str(args[1]) == "25°C"

    def test_prompt_units_method(self):
        """Test unit system selection prompt."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Prompt') as MockPrompt, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            ui_service = UIService()
            
            # Test metric selection
            MockPrompt.ask.return_value = "1"
            ui_service._prompt_units()
            
            assert ui_service.current_units == "metric"
            mock_console.print.assert_called_with("✅ Switched to °C units")
            
            # Test imperial selection
            MockPrompt.ask.return_value = "2"
            ui_service._prompt_units()
            
            assert ui_service.current_units == "imperial"
            mock_console.print.assert_called_with("✅ Switched to °F units")
            
            # Test default selection
            MockPrompt.ask.return_value = "3"
            ui_service._prompt_units()
            
            assert ui_service.current_units == "default"
            mock_console.print.assert_called_with("✅ Switched to K units")

    def test_prompt_continue_method(self):
        """Test continue prompt method."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Confirm') as MockConfirm:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService()
            
            # Test True response
            MockConfirm.ask.return_value = True
            result = ui_service._prompt_continue()
            assert result is True
            MockConfirm.ask.assert_called_with("\n🔍 Check another location?", default=True)
            
            # Test False response
            MockConfirm.ask.return_value = False
            result = ui_service._prompt_continue()
            assert result is False

    def test_prompt_location_valid_input(self):
        """Test location prompt with valid input."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Prompt') as MockPrompt, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            ui_service = UIService()
            
            # Mock location service
            mock_location_service = Mock()
            mock_location_service.normalize_location.return_value = "London,GB"
            ui_service.location_service = mock_location_service
            
            # Test valid location
            MockPrompt.ask.return_value = "London,GB"
            result = ui_service._prompt_location()
            
            assert result == "London,GB"
            mock_location_service.normalize_location.assert_called_once_with("London,GB")

    def test_prompt_location_empty_input(self):
        """Test location prompt with empty input."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Prompt') as MockPrompt, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            ui_service = UIService()
            
            # Mock location service
            mock_location_service = Mock()
            ui_service.location_service = mock_location_service
            
            # Test empty location followed by valid location
            MockPrompt.ask.side_effect = ["", "London,GB"]
            mock_location_service.normalize_location.return_value = "London,GB"
            
            result = ui_service._prompt_location()
            
            assert result == "London,GB"
            mock_console.print.assert_called_with("[red]⚠️ Location cannot be empty![/red]")

    def test_prompt_location_invalid_input(self):
        """Test location prompt with invalid input."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Prompt') as MockPrompt, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            ui_service = UIService()
            
            # Mock location service
            mock_location_service = Mock()
            mock_location_service.normalize_location.side_effect = [
                InvalidLocationError("Invalid location format"),
                "London,GB"
            ]
            ui_service.location_service = mock_location_service
            
            # Test invalid location followed by valid location
            MockPrompt.ask.side_effect = ["InvalidLocation", "London,GB"]
            
            result = ui_service._prompt_location()
            
            assert result == "London,GB"
            mock_console.print.assert_any_call("[red]⚠️ Invalid location format[/red]")

    def test_display_weather_method(self):
        """Test weather data display method."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole, \
             patch('src.weather_app.services.ui_service.Table') as MockTable, \
             patch('src.weather_app.services.ui_service.Confirm') as MockConfirm:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            mock_table = Mock()
            MockTable.return_value = mock_table
            
            ui_service = UIService()
            ui_service.current_units = "metric"
            
            # Create mock weather data
            mock_weather_data = Mock(spec=WeatherData)
            mock_weather_data.city = "London"
            mock_weather_data.get_emoji.return_value = "☀️"
            mock_weather_data.detailed_status = "Clear sky"
            mock_weather_data.temperature = 25.0
            mock_weather_data.feels_like = 26.0
            mock_weather_data.humidity = 65
            mock_weather_data.precipitation_probability = 10
            mock_weather_data.wind_speed = 5.0
            mock_weather_data.wind_direction_deg = 180  # South
            mock_weather_data.pressure_hpa = 1013
            
            # Mock confirm to not show comparison
            MockConfirm.ask.return_value = False
            
            ui_service._display_weather(mock_weather_data)
            
            # Verify table was created and printed
            MockTable.assert_called_once_with(title="🌤️ Weather in London", show_header=False)
            assert mock_table.add_column.call_count == 2
            assert len(ui_service.query_history) == 1
            mock_console.print.assert_called_with(mock_table)

    def test_show_history_comparison_method(self):
        """Test weather history comparison method."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Console') as MockConsole, \
             patch('src.weather_app.services.ui_service.Table') as MockTable:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            mock_console = Mock()
            MockConsole.return_value = mock_console
            
            mock_table = Mock()
            MockTable.return_value = mock_table
            
            ui_service = UIService()
            ui_service.current_units = "metric"
            
            # Create mock weather data for history
            current_data = Mock(spec=WeatherData)
            current_data.temperature = 25.0
            current_data.detailed_status = "Clear sky"
            
            previous_data = Mock(spec=WeatherData)
            previous_data.temperature = 20.0
            previous_data.detailed_status = "Cloudy"
            
            ui_service.query_history = [previous_data, current_data]
            
            ui_service._show_history_comparison()
            
            # Verify comparison table was created and printed
            MockTable.assert_called_once_with(title="🕰️ Weather Comparison")
            assert mock_table.add_column.call_count == 3
            mock_console.print.assert_called_with(mock_table)

    @pytest.mark.asyncio
    async def test_get_weather_with_progress_async_success(self):
        """Test async weather fetching with progress indicator (success case)."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.AsyncWeatherService') as MockAsyncWeatherService, \
             patch('src.weather_app.services.ui_service.Progress') as MockProgress:
    
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
    
            # Create a proper mock that can pass isinstance checks
            mock_async_weather_service = AsyncMock(spec=AsyncWeatherService)
            mock_weather_data = Mock(spec=WeatherData)
            mock_async_weather_service.get_weather.return_value = mock_weather_data
            MockAsyncWeatherService.return_value = mock_async_weather_service
    
            ui_service = UIService(use_async=True)
    
            # The weather service should already be properly mocked
            assert isinstance(ui_service.weather_service, AsyncMock)
    
            # Mock progress context manager
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress.add_task.return_value = mock_task
            MockProgress.return_value = mock_progress
    
            result = await ui_service._get_weather_with_progress("London,GB")
    
            assert result == mock_weather_data
            mock_async_weather_service.get_weather.assert_called_once_with("London,GB", mock_config.units)
            mock_progress.update.assert_called_with(mock_task, completed=True, description="[green]Data received!")

    @pytest.mark.asyncio
    async def test_get_weather_with_progress_async_error(self):
        """Test async weather fetching with progress indicator (error case)."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.AsyncWeatherService') as MockAsyncWeatherService, \
             patch('src.weather_app.services.ui_service.Progress') as MockProgress:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            # Create a proper mock that can pass isinstance checks
            mock_async_weather_service = AsyncMock(spec=AsyncWeatherService)
            mock_async_weather_service.get_weather.side_effect = LocationNotFoundError("Location not found")
            MockAsyncWeatherService.return_value = mock_async_weather_service
            
            ui_service = UIService(use_async=True)
            
            # The weather service should already be properly mocked
            assert isinstance(ui_service.weather_service, AsyncMock)
            
            # Mock progress context manager
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress.add_task.return_value = mock_task
            MockProgress.return_value = mock_progress
            
            with pytest.raises(LocationNotFoundError):
                await ui_service._get_weather_with_progress("InvalidLocation")
            
            mock_progress.update.assert_called_with(mock_task, completed=True, description="[red]Error: Location not found")

    def test_get_weather_sync_with_progress_success(self):
        """Test sync weather fetching with progress indicator (success case)."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService, \
             patch('src.weather_app.services.ui_service.Progress') as MockProgress:
    
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.units = "metric"
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
    
            # Create a proper mock that can pass isinstance checks
            mock_weather_service = Mock(spec=WeatherService)
            mock_weather_data = Mock(spec=WeatherData)
            mock_weather_service.get_weather.return_value = mock_weather_data
            MockWeatherService.return_value = mock_weather_service
    
            ui_service = UIService(use_async=False)
    
            # The weather service should already be properly mocked
            assert isinstance(ui_service.weather_service, Mock)
    
            # Mock progress context manager
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress.add_task.return_value = mock_task
            MockProgress.return_value = mock_progress
    
            result = ui_service._get_weather_sync_with_progress("London,GB")
    
            assert result == mock_weather_data
            mock_weather_service.get_weather.assert_called_once_with("London,GB", mock_config.units)
            mock_progress.update.assert_called_with(mock_task, completed=True, description="[green]Data received!")

    @pytest.mark.asyncio
    async def test_cleanup_method_async(self):
        """Test cleanup method in async mode."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.AsyncWeatherService') as MockAsyncWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_async_weather_service = Mock()
            MockAsyncWeatherService.return_value = mock_async_weather_service
            
            ui_service = UIService(use_async=True)
            
            # Mock async weather service with close method
            mock_weather_service = AsyncMock()
            mock_weather_service.close = AsyncMock()
            ui_service.weather_service = mock_weather_service
            
            await ui_service._cleanup()
            
            mock_weather_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_method_sync(self):
        """Test cleanup method in sync mode."""
        with patch('src.weather_app.services.ui_service.Config') as MockConfig, \
             patch('src.weather_app.services.ui_service.WeatherService') as MockWeatherService:
            
            mock_config = Mock()
            mock_config.validate.return_value = None
            mock_config.cache_file = "/tmp/test_cache.json"
            MockConfig.return_value = mock_config
            
            mock_weather_service = Mock()
            MockWeatherService.return_value = mock_weather_service
            
            ui_service = UIService(use_async=False)
            
            # Mock sync weather service without close method
            mock_weather_service = Mock()
            ui_service.weather_service = mock_weather_service
            
            # This should not raise an error
            await ui_service._cleanup()
            
            # Verify no close method was called on sync service
            assert not hasattr(mock_weather_service, 'close') or not mock_weather_service.close.called