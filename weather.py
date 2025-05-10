#!python
# -*- coding: utf-8 -*-
"""
weather.py
A simple weather application using the OpenWeatherMap API.
This script fetches and displays current weather data for a specified city.
It allows the user to set the API key and choose between metric, imperial,
or default units.
"""

import os
import traceback
from dotenv import load_dotenv
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import PyOWMError

# Load environment variables (ensure .weather.env exists)
load_dotenv(dotenv_path=".weather.env")

WEATHER_EMOJI_MAP = {
	"clear": "☀️", "scattered clouds": "🌤️", "broken clouds": "🌥️",
    "few clouds": "🌥️", "overcast clouds": "☁️", "light rain": "🌦️",
    "rain": "🌧️", "drizzle": "💧", # Changed drizzle emoji
    "snow": "❄️", "sleet": "🌨️", # Changed sleet emoji
    "mist": "🌫️", "haze": "🌫️", "fog": "🌫️", "thunderstorm": "⛈️",
    "windy": "💨", "sunny": "☀️", "clouds": "☁️",
}

class WeatherApp:
    """
    A class to interact with the OpenWeatherMap API and fetch weather data.
    Includes improved input validation.
    """
    def __init__(self):
        """
        Initialize the WeatherApp with the API key from environment variable.
        Configures PyOWM to use SSL.
        Raises ValueError if the API key is not found.
        """
        self._api_key = os.getenv("OWM_API_KEY")
        if not self._api_key:
            raise ValueError("API key (OWM_API_KEY) not found in " +
                             "environment variables or .weather.env file.")

        # Default to metric if OWM_UNITS is not set
        #self._units = os.getenv("OWM_UNITS", "metric").lower()
        # Validate initial units from environment
        #valid_units = ["metric", "imperial", "default"]
        #if self._units not in valid_units:
        #    print(f"Warning: Invalid OWM_UNITS '{self._units}' in environment. "
        #          f"Defaulting to 'metric'. Valid are: {valid_units}")
        #    self._units = "metric" # Default to metric on invalid env var

        self._units = None
        self._city_name = None
        config_dict = get_default_config()
        config_dict["use_ssl"] = True
        self.owm = OWM(self._api_key, config_dict)
        #print(f"WeatherApp initialized. Units set to '{self._units}' from environment.")
        #print("OpenWeatherMap API initialized.")

    def get_api_key(self):
        """Getter method for the API key."""
        return self._api_key

    def set_api_key(self, new_api_key):
        """Setter method for the API key."""
        if not new_api_key:
            raise ValueError("API key cannot be empty.")
        self._api_key = new_api_key
        config_dict = get_default_config()
        config_dict["use_ssl"] = True
        self.owm = OWM(self._api_key, config_dict)
        print("API key updated.")

    def get_units(self):
        """Getter method for the units."""
        return self._units

    def set_units(self, new_units_code):
        """
        Setter method for the units using single letter codes.
        :param new_units_code: The new units code ('m', 'i', or 'd').
        :raises ValueError: If the provided units code is not valid.
        """
        valid_codes = ["metric", "imperial", "default"]
        code = new_units_code.lower().strip() # Normalize input
        units_map = {"m": "metric", "i": "imperial", "d": "default"}

        if not code:
            raise ValueError("Units code cannot be empty.")
        if units_map.get(code) not in valid_codes:
            raise ValueError(f"Invalid unit: '{units_map.get(code)}', "
                             f"Must be one of {valid_codes}")

        self._units = units_map.get(code)
        print(f"Units set to '{self.get_units()}'")


    def fetch_weather(self):
        """
        Fetch the current weather data for the stored city name.
        :return: A dictionary containing the weather data, or None if an error occurs.
        """
        if not self._city_name:
            print("Error: City name not set.")
            return None

        city = self._city_name # Use the stored city name

        try:
            weather_manager = self.owm.weather_manager()
            # Use the current units setting for the API call if possible
            # Note: PyOWM might handle units differently; consult its docs if needed.
            # For simplicity, we often fetch raw data and format units during display.
            observation = weather_manager.weather_at_place(city)
            weather = observation.weather
        except PyOWMError as e:
            # Handle common API errors more specifically
            if 'not found' in str(e).lower():
                print(f"Error: Could not find weather data for city '{city}'. "
                      "Please check the spelling and try again.")
            else:
                print(f"An API error occurred while fetching weather for '{city}': {e}")
            return None
        except Exception as e: # Catch other potential errors
            print(f"An unexpected error occurred during weather fetch: {e}")
            return None

        if not weather:
            # This case might be redundant due to exception handling, but keep for safety
            print(f"Could not retrieve weather information for '{city}'.")
            return None

        # Determine units for data extraction
        current_units = self.get_units() # Use the getter
        if current_units == "metric":
            temp_unit = "celsius"
            speed_unit = "meters_sec"
            dist_unit = "kilometers"
        elif current_units == "imperial":
            temp_unit = "fahrenheit"
            speed_unit = "miles_hour"
            dist_unit = "miles"
        else: # Default/Standard/Kelvin
            temp_unit = "kelvin"
            speed_unit = "meters_sec"
            dist_unit = "meters" # Visibility often defaults to meters

        try:
            # Safely get data using .get() with defaults
            return {
                "city": city, # Store city name in result
                "units": current_units,
                "status": weather.status,
                "temperature": weather.temperature(temp_unit).get("temp"),
                "feels_like": weather.temperature(temp_unit).get("feels_like"),
                "humidity": weather.humidity,
                "wind_speed": round(weather.wind(speed_unit).get("speed", 0), 2),
                "wind_direction": weather.wind().get("deg"),
                "detailed_status": weather.detailed_status,
                "icon_code": weather.weather_code, # Get code for emoji mapping
                "precipitation_probability":
                getattr(weather, 'precipitation_probability', None), # Use getattr for safe access
                "clouds": weather.clouds,
                "visibility": weather.visibility(unit=dist_unit),
                "pressure": weather.pressure.get("press"),
            }
        except Exception as e:
            print(f"An error occurred while processing weather data: {e}")
            return None

    def display_weather(self, weather_data):
        """
        Display the fetched weather data in a readable format.
        :param weather_data: A dictionary containing the weather information.
        """
        if not weather_data:
            # fetch_weather should print errors, so just return
            return

        display_city = weather_data.get("city", "Unknown City")
        display_units = weather_data.get("units", "default")
        detailed_status = weather_data.get("detailed_status", "N/A").capitalize()
        emoji = self.get_weather_emoji(detailed_status) # Use status for emoji

        wind_direction_deg = weather_data.get("wind_direction")
        wind_info = self.solve_wind_direction(wind_direction_deg) # Returns [letters, arrow]
        wind_dir_str = f"🧭 {wind_info[0]} {wind_info[1]}" if wind_info[0] != "?" else ""


        # Determine display units based on the 'units' field in weather_data
        temp_unit_sym = "°K"
        speed_unit_sym = "m/s"
        dist_unit_sym = "m"
        if display_units == "metric":
            temp_unit_sym = "°C"
            speed_unit_sym = "m/s"
            dist_unit_sym = "km"
        elif display_units == "imperial":
            temp_unit_sym = "°F"
            speed_unit_sym = "mph"
            dist_unit_sym = "mi"

        # Use .get() for safer access to dictionary keys
        temp = weather_data.get('temperature', 'N/A')
        feels_like = weather_data.get('feels_like', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        wind_speed = weather_data.get('wind_speed', 'N/A')
        visibility = weather_data.get('visibility', 'N/A')
        pressure = weather_data.get('pressure', 'N/A')
        precip_prob = weather_data.get('precipitation_probability') # May be None

        # Print the weather information
        print("-" * 30)
        print(f"{emoji} Weather in 🏙️  {display_city}:")
        print(f"> Condition: {emoji} {detailed_status}")
        print(f"> Temperature:🌡️ {temp}{temp_unit_sym}")
        print(f"> Feels Like:🌡️ {feels_like}{temp_unit_sym}")
        print(f"> Humidity:💧 {humidity}%")
        print(f"> Wind:🌬️ {wind_speed} {speed_unit_sym} {wind_dir_str}")
        # Only show precipitation probability if available
        if precip_prob is not None:
            print(f"> Precipitation Chance:☔ {precip_prob}%")
        print(f"> Visibility: {visibility} {dist_unit_sym}")
        print(f"> Pressure:⏲  {pressure} hPa") # Barometer emoji
        print("-" * 30)


    def get_weather_emoji(self, status):
        """
        Return an emoji for the weather condition using a predefined map.
        Compares lowercased status against map keys.
        :param status: A string describing the weather condition (e.g., "Clear sky").
        :return: An emoji string or a default rainbow emoji '🌈'.
        """
        if not status:
            return "🤷" # Emoji for unknown status

        status_lower = status.lower()
        # Prioritize more specific keys first if necessary (e.g., "light rain" before "rain")
        # This order seems okay for the current map.
        for key, emoji in WEATHER_EMOJI_MAP.items():
            if key in status_lower:
                return emoji
        # Check broader categories if no specific match
        if "cloud" in status_lower:
            return "☁️"
        if "rain" in status_lower:
            return "🌧️"
        if "snow" in status_lower:
            return "❄️"
        if "storm" in status_lower:
            return "⛈️"
        if "clear" in status_lower:
            return "☀️"
        if "sun" in status_lower:
            return "☀️"

        return "🌈"  # Default emoji if no keyword matches


    def solve_wind_direction(self, wind_deg):
        """
        Convert wind direction degrees to cardinal direction letters and arrow emoji.
        :param wind_deg: Wind direction in degrees (0-360).
        :return: A list containing [Cardinal direction string, Arrow emoji string].
                 Returns ["?", "?"] if input is None or invalid.
        """
        if wind_deg is None:
            return ["?", "?"]

        try:
            # Ensure degrees is a number and normalize
            deg = float(wind_deg) % 360
        except (ValueError, TypeError):
            return ["?", "?"] # Handle cases where deg is not a number

        # Simplified logic for mapping degrees to direction index
        # Add N at end for easier indexing
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
        # Add N's arrow at end, use white arrows on a blue background
        arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➞ ", "↘️", "⬇️"]

        # Calculate index: Each section is 45 degrees wide. Offset by 22.5 for centering.
        index = int( (deg + 22.5) / 45 )
        # Index should be between 0 and 7 (or 8 if we use the extra N)
        index = index % 8 # Ensure index wraps correctly for values near 360

        return [directions[index], arrows[index]]

    def read_city_name(self):
        """
        Get the name of the city from the user, validate minimally, and set it.
        Loops until non-empty input is provided.
        """
        while True:
            city = input("Enter city name (e.g., London, Tokyo, New York, US): ").strip()
            if city:  # Basic check: not empty after stripping whitespace
                self.set_city_name(city)
                break # Exit loop if city name is provided

            print("City name cannot be empty. Please try again.")

    def set_city_name(self, city):
        """
        Set the name of the city. (Internal helper)
        :param city: The name of the city to set.
        """
        # Basic validation already done in read_city_name
        self._city_name = city
        # No need to print here, confirmation happens after fetch/display

    def get_city_name(self):
        """
        Getter method for the city name.
        """
        return self._city_name

    def read_unit(self):
        """
        Get the unit choice from the user and set it.
        Loops until valid input ('m', 'i', 'd', or 's') is provided.
        """
        prompt = "Select units ([M]etric °C, [I]mperial °F, [D]efault/Standard °K): "
        valid_codes = ["m", "i", "d"]

        while True:
            unit_code = input(prompt).strip().lower()
            if unit_code in valid_codes:
                try:
                    self.set_units(unit_code) # Use the setter which also prints confirmation
                    break # Exit loop on valid input
                except ValueError as e:
                    # This shouldn't happen if valid_codes is correct, but good practice
                    print(f"Internal Error: {e}")
            else:
                print(f"Invalid choice '{unit_code}'. Please enter 'm', 'i' or 'd'")


    def run(self):
        """
        Main method to run the weather application loop.
        Prompts for city and units, fetches, and displays weather.
        """
        print("Welcome to the Weather App!")
        # Get initial city and units
        self.read_city_name()
        self.read_unit()

        # Fetch and display weather for the first time
        weather_data = self.fetch_weather()
        self.display_weather(weather_data)

        # check multiple cities or change units without restarting the script
        while True:
            action = input("Check another city (c), change units (u), or quit (q)? ").lower()
            if action == 'c':
                self.read_city_name()
                weather_data = self.fetch_weather()
                if weather_data:
                    self.display_weather(weather_data)
                else:
                    print("No weather data to re-display with new city.")
            elif action == 'u':
                self.read_unit()
                weather_data = self.fetch_weather()
                if weather_data:
                    self.display_weather(weather_data)
                else:
                    print("No weather data to re-display with new units.")
            elif action == 'q':
                break
            else:
                print("Invalid option.")


if __name__ == "__main__":
    try:
        app = WeatherApp()
        app.run()
    except ValueError as e:
        # Catch initialization or critical validation errors
        print(f"Configuration or Input Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except EOFError: # Handles end-of-file during input, e.g., piping input
        print("\nInput stream ended.")
    # Removed SystemExit catch as it's usually intentional
    except Exception as e:
        print(f"\nAn unexpected critical error occurred: {e}")
        # Consider logging the full traceback here for debugging
        traceback.print_exc()
    finally:
        print("\nWeatherApp finished.")
        # No specific cleanup needed for this script
