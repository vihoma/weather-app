# Weather CLI Application

A command-line weather application that provides current weather conditions for any location worldwide, with a beautiful terminal interface.

## Features

- 🌦️ Get current weather conditions including temperature, humidity, wind speed, and more
- 🌍 Search by city name or coordinates
- 🎨 Beautiful terminal UI using Rich for formatting and colors
- ⚙️ Configurable units (metric/imperal)
- 📊 View weather history comparisons
- 🔐 Secure API key management via environment variables

## Requirements

- Python 3.8+
- OpenWeatherMap API key (free tier available)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/weather-app.git
   cd weather-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### API Key Setup

You need an OpenWeatherMap API key. Get one for free at [https://openweathermap.org/api](https://openweathermap.org/api).

Store your API key in either:

1. `.weather.env` file in the project root or your home directory:
   ```ini
   OWM_API_KEY=your_api_key_here
   ```

2. Or set as environment variable:
   - Linux/macOS:
     ```bash
     export OWM_API_KEY=your_api_key_here
     ```
   - Windows:
     ```powershell
     $env:OWM_API_KEY="your_api_key_here"
     ```

## Usage

Run the application:
```bash
python weather_app/main.py
```

Follow the interactive prompts to:
1. Enter your location
2. Choose temperature units (Celsius/Fahrenheit/Kelvin)
3. View current weather conditions

## Screenshot

[Insert screenshot of the application in action here]

## License

BSD 3-Clause - See [LICENSE.txt](LICENSE.txt) for details.
