"""Configuration handling for the Weather Application."""

import os
from dotenv import load_dotenv

class Config:
    """Handles application configuration and environment variables."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        load_dotenv(dotenv_path=".weather.env")
        self._api_key = os.getenv("OWM_API_KEY")
        self._units = os.getenv("OWM_UNITS", "metric")
        
    @property 
    def api_key(self):
        """Get the API key."""
        return self._api_key
        
    @api_key.setter
    def api_key(self, value):
        """Set the API key with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("API key must be a non-empty string")
        self._api_key = value

    @property
    def units(self):
        """Get the measurement units."""
        return self._units
        
    def validate(self):
        """Validate required configuration."""
        if not self.api_key:
            raise ValueError(
                "API key (OWM_API_KEY) not found in environment variables "
                "or .weather.env file."
            )
