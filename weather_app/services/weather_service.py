"""Core weather data operations using PyOWM."""

from pyowm.owm import OWM  
from pyowm.utils.config import get_default_config  
from pyowm.commons.exceptions import PyOWMError
from models.weather_data import WeatherData

class WeatherService:
    """Handles all interactions with OpenWeatherMap API."""
    
    def __init__(self, config):  
        self.config_dict = get_default_config()  
        self.config_dict["use_ssl"] = True  
        
        if not config.api_key:
            raise ValueError("API key is required")  
            
        self.owm = OWM(config.api_key, self.config_dict)
        self.weather_manager = self.owm.weather_manager()

    def get_weather(self, location: str, units: str) -> WeatherData:
        """
        Get current weather data for a location.
        
        Args:
            location: City name and country code (e.g., "London,GB")
            units: Measurement system (metric/imperial/default)
            
        Returns:
            WeatherData: Parsed weather data
        """
        try:
            observation = self.weather_manager.weather_at_place(location)
            weather = observation.weather
            return self._parse_weather_data(location, weather, units)
        except PyOWMError as e:
            raise RuntimeError(f"Failed to fetch weather data: {e}") from e

    def _parse_weather_data(self, location: str, weather, units: str) -> WeatherData:
        """Convert PyOWM weather object to our data model."""
        # Map our unit names to PyOWM's expected values
        temp_unit = {
            "metric": "celsius",
            "imperial": "fahrenheit",
            "default": "kelvin"
        }.get(units, "kelvin")
        
        return WeatherData(
            city=location,
            units=units,
            status=weather.status,
            detailed_status=weather.detailed_status.capitalize(),
            temperature=weather.temperature(temp_unit).get("temp"),
            feels_like=weather.temperature(temp_unit).get("feels_like"),
            humidity=weather.humidity,
            wind_speed=round(weather.wind().get("speed", 0), 2),
            wind_direction_deg=weather.wind().get("deg"),
            precipitation_probability=getattr(weather, 'precipitation_probability', None),
            clouds=weather.clouds,
            visibility_distance=weather.visibility().get("distance"),
            pressure_hpa=weather.pressure.get("press", 1013) if isinstance(weather.pressure, dict) else weather.pressure,
            icon_code=weather.weather_code
        )
