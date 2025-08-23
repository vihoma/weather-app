# Weather CLI Application

A command-line weather application that provides current weather conditions for any location worldwide, with a beautiful terminal interface.

## Features

- 🌦️ Get current weather conditions including temperature, humidity, wind speed, and more
- 🌍 Search by city name or coordinates with automatic validation
- 🎨 Beautiful terminal UI using Rich for formatting and colors
- ⚡ **Async operations** for faster API calls with progress indicators
- ⚙️ Configurable units (metric/imperial/kelvin)
- 📊 View weather history comparisons
- 🔐 Secure API key management via environment variables
- 💾 Response caching with configurable TTL
- 📝 Structured logging with file and console output
- 🎯 Comprehensive error handling with helpful messages
- 🔧 Multiple configuration file support

## Requirements

- Python 3.8+
- OpenWeatherMap API key (free tier available)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vihoma/weather-app.git
   cd weather-app
   ```

2. Install dependencies using Poetry (recommended):
   ```bash
   poetry install
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

## Configuration

### API Key Setup

You need an OpenWeatherMap API key. Get one for free at [https://openweathermap.org/api](https://openweathermap.org/api).

Store your API key in any of these locations (checked in order):

1. `.weather.env` file in the project root
2. `~/.weather.env` in your home directory  
3. `/etc/weather_app/.env` for system-wide configuration
4. Environment variables (highest precedence)

Example `.weather.env` file:
```ini
OWM_API_KEY=your_api_key_here
OWM_UNITS=metric
CACHE_TTL=600
LOG_LEVEL=INFO
LOG_FILE=weather_app.log
```

### Environment Variables

- `OWM_API_KEY`: Your OpenWeatherMap API key (required)
- `OWM_UNITS`: Measurement units (`metric`, `imperial`, `default`) - default: `metric`
- `CACHE_TTL`: Cache time-to-live in seconds - default: `600` (10 minutes)
- `REQUEST_TIMEOUT`: API request timeout in seconds - default: `30`
- `USE_ASYNC`: Enable async mode (`true`/`false`) - default: `true`
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) - default: `INFO`
- `LOG_FILE`: Path to log file - default: `weather_app.log`

### Configuration Precedence

1. Environment variables
2. `.weather.env` in project root
3. `~/.weather.env` in home directory
4. `/etc/weather_app/.env` system-wide
5. Default values

## Usage

Run the application with Poetry:
```bash
poetry run python -m src.weather_app.main
```

Or directly:
```bash
python -m src.weather_app.main
```

Follow the interactive prompts to:
1. Enter your location
2. Choose temperature units (Celsius/Fahrenheit/Kelvin)
3. View current weather conditions

## Screenshot

[Insert screenshot of the application in action here]

## Development

### Running Tests

```bash
poetry run pytest tests/ -v
```

### Code Quality

```bash
# Linting
poetry run ruff check src/

# Formatting imports  
poetry run isort src/

# Building package
poetry build
```

### Project Structure

```
src/weather_app/
├── models/           # Data models
├── services/         # Business logic services
├── exceptions.py     # Custom exceptions
├── config.py         # Configuration handling
├── logging_config.py # Logging configuration
└── main.py          # Application entry point

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── functional/      # Functional tests
```

## License

BSD 3-Clause - See [LICENSE.txt](LICENSE.txt) for details.
