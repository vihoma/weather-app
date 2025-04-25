#!python
# -*- coding: utf-8 -*-
"""
weather.py
A simple weather application using the OpenWeatherMap API.
This script fetches and displays current weather data for a specified city.
It allows the user to set the API key and choose between metric, imperial,
or default units.
"""

# Import necessary libraries
import os
from dotenv import load_dotenv
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import PyOWMError

# Load environment variables from .weather.env file
# This file should contain the OWM_API_KEY and OWM_UNITS variables
# Example:
# OWM_API_KEY=your_api_key_here
# OWM_UNITS=metric
# Make sure to create a .weather.env file in the home directory
# or the same directory as this script with the above content.
load_dotenv(dotenv_path=".weather.env")

# Define a mapping of weather conditions to emojis
# This mapping is used to display a corresponding emoji for each weather condition
# The emojis are chosen to represent the weather conditions visually
# The mapping is a dictionary where the keys are the weather conditions
# and the values are the corresponding emojis.
# The keys are in lowercase to ensure consistency and avoid case sensitivity issues
# when comparing or using them in the application.
WEATHER_EMOJI_MAP = {
    "clear": "☀️",
    "scattered clouds": "🌤️",
    "broken clouds": "🌥️",
    "few clouds": "🌥️",
    "overcast clouds": "☁️",
    "light rain": "🌦️",
    "rain": "🌧️",
    "drizzle": " drizzle",
    "snow": "❄️",
    "sleet": " sleet",
    "mist": "🌫️",
    "haze": "🌫️",
    "fog": "🌫️",
    "thunderstorm": "⛈️",
    "windy": "💨",
    "sunny": "☀️",
    "clouds": "☁️",
}

class WeatherApp:
    """
    A class to interact with the OpenWeatherMap API and fetch weather data.
    """
    def __init__(self):
        """
        Initialize the WeatherApp with the API key and units from environment
        variables. Configures PyOWM to use SSL.
        Raises ValueError if the API key is not found.
        """
        self._api_key = os.getenv("OWM_API_KEY")
        if not self._api_key:
            raise ValueError("API key not found in environment variables.")

        self._units = os.getenv("OWM_UNITS")
        if not self._units:
            print("No units from environment, initially using default " +
                  "units (°K, m/s & m).")
            self._units = "default"
        # The city name is initially set to None
        # and will be set later when the user provides it
        self._city_name = None
        # The config_dict is used to set the SSL configuration and other
        # settings for the OWM instance
        config_dict = get_default_config()
        # Set the use_ssl option to True for secure communication
        # with the OpenWeatherMap API
        # This is important for security reasons, as it ensures that the data
        # transmitted between the client and server is encrypted
        # and protected from eavesdropping or tampering.
        # The config_dict is a dictionary that contains various configuration
        # options for the OWM instance, such as the API key, language,
        # and units of measurement.
        # By default, the config_dict is set to use SSL, but it can be
        # modified to use HTTP instead if needed.
        # However, using HTTP is not recommended for production use,
        # as it exposes the data to potential security risks.
        config_dict["use_ssl"] = True
        # Initialize the OWM instance with the API key and config_dict
        # The OWM instance is the main entry point for interacting with
        # the OpenWeatherMap API and provides methods for fetching weather
        # data, forecasts, and other information.
        # The OWM instance is created with the API key and config_dict
        # as parameters, which are used to authenticate the client
        # and configure the settings for the API requests.
        # The OWM instance is then used to create a WeatherManager instance,
        # which is responsible for managing the weather data and providing
        # methods for fetching and processing the weather information.
        self.owm = OWM(self._api_key, config_dict)

    def get_api_key(self):
        """
        Getter method for the API key.
        :return: The current API key.
        """
        return self._api_key

    def set_api_key(self, new_api_key):
        """
        Setter method for the API key.
        :param new_api_key: The new API key to set.
        """
        if not new_api_key:
            raise ValueError("API key cannot be empty.")
        self._api_key = new_api_key
        # Re-initialize OWM with the new API key
        config_dict = get_default_config()
        config_dict["use_ssl"] = True
        self.owm = OWM(self._api_key, config_dict)
        print("API key updated.")

    def get_units(self):
        """
        Getter method for the units.
        :return: The current units setting.
        """
        return self._units

    def set_units(self, new_units):
        """
        Setter method for the units.
        :param new_units: The new units to set ('metric', 'imperial', or 'default').
        :raises ValueError: If the provided units are not valid.
        """
        valid_units = ["m", "i", "d", "s"]
        if not new_units:
            raise ValueError("Units cannot be empty.")
        if new_units.lower() not in valid_units:
            raise ValueError(f"Invalid units: '{new_units}'. " +
                             f"Must be one of {valid_units}.")
        if new_units.lower() in ["d", "s"]:
            self._units = "default"
            print("Default units (°K, m/s & m) are set.")
        elif new_units.lower() == "m":
            self._units = "metric"
            print("Metric units (°C, m/s & km) are set.")
        elif new_units.lower() == "i":
            self._units = "imperial"
            print("Imperial units (°F, mph & mi) are set.")
        # Set the new units
        # The units are stored in lowercase to ensure consistency
        # and avoid case sensitivity issues when comparing or using them
        # in the application.
        print(f"Units updated to '{self.get_units().capitalize()}'.")

    def fetch_weather(self):
        """
        Fetch the current weather data for a specified city.
        :return: A dictionary containing the weather data, or None if an error occurs
        """
        city = self.get_city_name()

        try:
            weather_manager = self.owm.weather_manager()
            observation = weather_manager.weather_at_place(city)
            weather = observation.weather
        except PyOWMError as e:
            print("An error occurred while fetching weather data for " +
                  f"'{city}': {e}")
            return None

        if not weather:
            print(f"Could not retrieve weather information for '{city}'.")
            return None

        try:
            if self.get_units() == "metric":
                temp_unit = "celsius"
                speed_unit = "meters_sec"
                dist_unit = "kilometers"
            elif self.get_units() == "imperial":
                temp_unit = "fahrenheit"
                speed_unit = "miles_hour"
                dist_unit = "miles"
            elif self.get_units() == "default":
                temp_unit = "kelvin"
                speed_unit = "meters_sec"
                dist_unit = "meters"
            else:
                # Handle cases where self._units is not set or invalid
                print(f"Warning: Invalid units '{self._units}'. " +
                      "Using default units.")
                self.set_units("default")
                temp_unit = "kelvin"
                speed_unit = "meters_sec"
                dist_unit = "meters"

            return {
                "units": self.get_units(),
                "status": weather.status,
                "temperature": weather.temperature(temp_unit).get("temp"),
                "feels_like": weather.temperature(temp_unit).get("feels_like"),
                "humidity": weather.humidity,
                "wind_speed":
                    round(weather.wind(speed_unit).get("speed", 0), 2),
                "wind_direction": weather.wind().get("deg"),
                "detailed_status": weather.detailed_status,
                "icon": weather.weather_icon_url(),
                "precipitation_probability": weather.precipitation_probability,
                "clouds": weather.clouds,
                "visibility": weather.visibility(unit=dist_unit),
                "pressure": weather.pressure.get("press"),
            }
        except PyOWMError as e:
            print(f"An error occurred while processing weather data: {e}")
            return None

    def display_weather(self, weather_data):
        """
        Display the fetched weather data in a readable format.

        :param city: The city for which the weather is displayed
        :param weather_data: A dictionary containing the weather information
        """
        if not weather_data:
            print("No weather data to display.")
            return

        units = weather_data.get("units", "unknown")

        emoji = self.get_weather_emoji(weather_data["detailed_status"])
        wind_direction = self.solve_wind_direction(
            weather_data["wind_direction"]
            )
        letters = wind_direction[0]
        arrow = wind_direction[1]
        # Set default units for temperature, wind speed, and distance
        temp_unit = "°K"
        speed_unit = "m/s"
        dist_unit = "m"

        # Determine the units to display based on the user's choice
        # and the environment variable
        if units == "metric":
            temp_unit = "°C"
            speed_unit = "m/s"
            dist_unit = "km"
        elif units == "imperial":
            temp_unit = "°F"
            speed_unit = "mph"
            dist_unit = "mi"
        elif units == "default":
            temp_unit = "°K"
            speed_unit = "m/s"
            dist_unit = "m"
        elif units == "unknown":
            print("No units selected or found in environment, using default units.")

        # Print the weather information
        print(f"{emoji} Weather in 🏙️ {self._city_name}:")
        print(f"> Condition: {emoji} {weather_data['detailed_status'].capitalize()}")
        print(f"> Temperature:🌡️ {weather_data['temperature']}{temp_unit}")
        print(f"> Feels Like:🌡️ {weather_data['feels_like']}{temp_unit}")
        print(f"> Humidity:💧 {weather_data['humidity']}%")
        print(
            f"> Wind Speed:🌬️ {weather_data['wind_speed']} {speed_unit} 🧭 {letters} {arrow}"
        )
        print(f"> Visibility: {weather_data['visibility']} {dist_unit}")
        print(f"> Pressure:🌡️ {weather_data['pressure']} hPa")

    def get_weather_emoji(self, status):
        """
        Return an emoji for the weather condition using a predefined map.

        :param status: A string describing the weather condition
        :return: An emoji as a string corresponding to the weather condition,
                 or a default emoji if the status is not found.
        """
        status_lower = status.lower()
        for key, emoji in WEATHER_EMOJI_MAP.items():
            if key in status_lower:
                return emoji
        return "🌈"  # Default emoji

    def solve_wind_direction(self, wind_deg):
        """
        Convert wind direction degrees to a cardinal direction.

        :param wind_deg: An integer representing the wind direction in degrees
        :return: A string containing the formatted cardinal direction
        (e.g., SW) and an Unicode arrow (e.g., ↘️)
        """
        if wind_deg is None:
            return ["?", "?"]

        # Normalize the wind direction to a value between 0 and 360
        wind_deg = wind_deg % 360
        # Determine the cardinal direction based on the wind degree
        # The wind direction is divided into 8 sectors (N, NE, E, SE, S, SW, W, NW)
        # Each sector corresponds to a range of 45 degrees
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        # Calculate the index of the direction based on the wind degree
        # The index is calculated by dividing the wind degree by 45
        # and taking the modulus with 8 to ensure it wraps around
        index = int((wind_deg + 22.5) / 45) % 8
        # The index is used to get the corresponding direction from the list
        # The index is also used to get the corresponding arrow from the list
        # The arrows are chosen to represent the wind direction visually
        arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➡️", "↘️"]

        # Return the direction and the corresponding arrow
        return [directions[index], arrows[index]]

    def read_city_name(self):
        """
        Get the name of the city from the user, validate and set it.
        :raises ValueError: If the city name is invalid or empty.
        """
        city = input("Enter city name: ").strip()

        # Check if the city name is empty
        # and raise an error if it is
        if not city:
            raise ValueError("City name cannot be empty.")
        # Check if the city name contains only letters and spaces
        if not all(c.isalpha() or c.isspace() for c in city):
            raise ValueError("City name can only contain letters and spaces.")
        # Check if the city name is too long
        if len(city) > 100:
            raise ValueError("City name is too long. " +
                             "Please enter a shorter name.")
        # Check if the city name is too short
        if len(city) < 2:
            raise ValueError("City name is too short. " +
                             "Please enter a longer name.")
        # Check if the city name contains any special characters
        if not city.replace(" ", "").isalnum():
            raise ValueError("City name can only contain letters and spaces.")
        # Check if the city name contains any numbers
        if any(c.isdigit() for c in city):
            raise ValueError("City name cannot contain numbers.")
        # Check if the city name contains any special characters
        if any(c in "!@#$%^&*()_+-=[]{}|;':\".<>?/" for c in city):
            raise ValueError("City name cannot contain special characters " +
                             "except a colon (,) before area.")
        # Check if the city name contains any leading or trailing spaces
        if city != city.strip():
            raise ValueError("City name cannot contain leading or trailing spaces.")
        # Check if the city name contains any extra spaces
        if "  " in city:
            raise ValueError("City name cannot contain extra spaces.")
        # Check if the city name contains any non-ASCII characters
        # (e.g., emojis, non-ASCII characters)
        if not all(ord(c) < 128 for c in city):
            raise ValueError("City name cannot contain non-ASCII characters.")
        # Check if the city name contains any non-printable characters
        if not all(c.isprintable() for c in city):
            raise ValueError("City name cannot contain non-printable characters.")

        self.set_city_name(city)

    def set_city_name(self, city):
        """
        Set the name of the city.
        :param city: The name of the city to set.
        """
        if not city:
            raise ValueError("City name cannot be empty.")

        self._city_name = city
        print(f"City name updated to '{self._city_name}'.")

    def read_unit(self):
        """
        Get the unit of measurement from the user and set it.
        """
        prompt = "Enter unit ([M]etric, [I]mperial, [D]efault/[S]cientific): "
        # Prompt the user for the unit of measurement
        unit = input(prompt).strip().lower()
        # Check if the unit is one of the valid units
        # and raise an error if it is not
        valid_units = ["m", "i", "d", "s"]
        unit_strings = {
            "m": "metric",
            "i": "imperial",
            "d": "default",
            "s": "scientific"
        }

        while True:
            # Check if the unit is empty and raise an error if it is
            if not unit:
                raise ValueError("Unit cannot be empty, try again.")
            # Check if the unit is too long and raise an error if it is
            if len(unit) > 1:
                raise ValueError("Unit is too long. " +
                                 "Please enter a shorter name.")
            # Check if the unit is too short and raise an error if it is
            if len(unit) < 1:
                raise ValueError("Unit is too short. " +
                                 "Please enter a longer name.")
            # Check if the unit is valid and raise an error if it is not
            if unit not in valid_units:
                raise ValueError(f"Invalid unit: '{unit}'. " +
                                 f"Must be one of {unit_strings}.")
            break

        print(f"Unit '{unit}' selected (read_unit() complete).")
        self.set_units(unit)

    def get_city_name(self):
        """
        Getter method for the city name.
        :return: The current city name.
        """
        return self._city_name

    def run(self):
        """
        Main method to run the weather application.
        It prompts the user for a city name and unit choice, fetches the weather data,
        and displays the weather information.
        """
        # Prompt the user for the city name
        while True:
            try:
                self.read_city_name()
            except ValueError as e:
                print(f"Error: {e}. Please try again.")
            break

        while True:
            # Prompt the user for the unit of measurement
            try:
                self.read_unit()
            except ValueError as e:
                print(f"Error: {e}. Please try again.")
            break

        # Fetch the weather data for the specified city
        weather_data = self.fetch_weather()
        # Display the weather information
        self.display_weather(weather_data)

if __name__ == "__main__":
    # This block is executed when the script is run directly
    # It creates an instance of the WeatherApp class
    # and calls the run method to start the application
    # The run method is responsible for prompting the user for input,
    # fetching the weather data, and displaying the results
    # The try-except block is used to handle any exceptions that may occur
    # during the execution of the application and to ensure that the
    # application exits gracefully and cleans up any resources used during
    # the execution of the script.
    try:
        app = WeatherApp()
        app.run()
    except ValueError as e:
        print(f"Configuration error: {e}")
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except EOFError:
        print("\n\nGoodbye!")
    except SystemExit:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
    finally:
        print("Cleaning up resources...")
        # Add any necessary cleanup code here
        # For example, closing database connections, releasing file handles, etc.
        # In this case, we don't have any specific cleanup to do
        # but it's a good practice to include this in case of future modifications.
        print("Cleanup complete.")
