#!python
import os
from dotenv import load_dotenv
from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import PyOWMError

# Load environment variables from .env file
load_dotenv()

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
    def __init__(self):
        """
        Initialize the WeatherApp with the API key and units from environment variables.
        Configures PyOWM to use SSL.
        Raises ValueError if the API key is not found.
        """
        self._api_key = os.getenv("OWM_API_KEY")
        if not self._api_key:
            raise ValueError("API key not found in environment variables.")

        self._units = os.getenv("OWM_UNITS")
        if not self._units:
            print("No units from environment, initially using default units (°K, m/s & m).")
            self._units = "default"

        config_dict = get_default_config()
        config_dict["use_ssl"] = True
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
        valid_units = ["metric", "imperial", "default"]
        if new_units.lower() not in valid_units:
            raise ValueError(f"Invalid units: '{new_units}'. Must be one of {valid_units}.")
        self._units = new_units.lower()
        print(f"Units updated to '{self.get_units()}'.")

    def get_weather(self, city):
        """
        Fetch the current weather data for a specified city.

        :param city: The name of the city to fetch weather data for
        :return: A dictionary containing the weather data, or None if an error occurs
        """
        try:
            weather_manager = self.owm.weather_manager()
            observation = weather_manager.weather_at_place(city)
            weather = observation.weather
        except PyOWMError as e:
            print(f"An error occurred while fetching weather data for '{city}': {e}")
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
                print(f"Warning: Invalid units '{self._units}'. Using default units.")
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
                "wind_speed": round(weather.wind(speed_unit).get("speed", 0), 2),
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

    def display_weather(self, city, weather_data):
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
        wind_direction = self.get_wind_direction(weather_data["wind_direction"])
        letters = wind_direction[0]
        arrow = wind_direction[1]

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
            temp_unit = "°K"
            speed_unit = "m/s"
            dist_unit = "m"

        print(f"{emoji} Weather in 🏙️ {city}:")
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

    def get_wind_direction(self, wind_deg):
        """
        Convert wind direction degrees to a cardinal direction.

        :param wind_deg: An integer representing the wind direction in degrees
        :return: A string containing the formatted cardinal direction (e.g., SW) and an arrow.
        """
        if wind_deg is None:
            return ["?", "?"]

        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((wind_deg + 22.5) / 45) % 8
        #arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➞ ", "↘️"]
        arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➡️", "↘️"]
        return [directions[index], arrows[index]]

    def run(self):
        while True:
            city = input("Enter the name of the city: ").strip()
            if city:
                break
            else:
                print("City name cannot be empty. Please try again.")

        while True:
            unit_choice = input("Enter units ([M]etric/[I]mperial/[D]efault/[S]cientific): ").strip().lower()
            if unit_choice == "m":
                print("You chose metric units (°C, m/s & km)")
                self.set_units("metric")
                break
            elif unit_choice == "i":
                print("You chose imperial units (°F, mph & mi)")
                self.set_units("imperial")
                break
            elif unit_choice == "d" or unit_choice == "s":
                print("You chose default/scientific units (°K, m/s & m)")
                self.set_units("default")
                break
            elif not unit_choice and self.get_units():
                if self.get_units() == "metric":
                    print("No unit chosen, using defaults from environment (Metric: °C, m/s & km).")
                elif self.get_units() == "imperial":
                    print("No unit chosen, using defaults from environment (Imperial: °F, mph & mi).")
                elif self.get_units() == "default":
                    print("No unit chosen, using defaults from environment (Default/Scientific: °K, m/s & m).")
                break
            elif not unit_choice and not self.get_units():
                print("No unit chosen and no default in environment, using default units (Default/Scientific: °K, m/s & m).")
                self.set_units("default")
                break
            else:
                print("Invalid unit choice. Please enter 'M', 'I', or 'D'.")

        weather_data = self.get_weather(city)

        if not weather_data:
            print(
                "Failed to fetch weather data. Please check the city name and your API key (if the issue persists)."
            )
            return

        self.display_weather(city, weather_data)


if __name__ == "__main__":
    try:
        app = WeatherApp()
        # Example of using the getter and setter methods:
        # print(f"Current API Key: {app.get_api_key()}")
        # app.set_api_key("YOUR_NEW_API_KEY")
        # print(f"New API Key: {app.get_api_key()}")
        # print(f"Current Units: {app.get_units()}")
        # app.set_units("imperial")
        # print(f"New Units: {app.get_units()}")
        app.run()
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while running WeatherApp: {e}")
