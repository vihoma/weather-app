# Weather CLI Application

A command-line weather application that provides current weather conditions for
any location worldwide, with a beautiful terminal interface.

## Features

- 🌦️ Get current weather conditions including temperature, humidity,
  wind speed, and more
- 🌍 Search by city name or coordinates with automatic validation
- 🎨 Beautiful terminal UI using Rich for formatting and colors
- ⚡ **Async operations** for faster API calls with progress indicators
- ⚙️ Configurable units (metric/imperial/kelvin)
- 📊 View weather history comparisons
- 🔐 Secure API key management via the system's keyring service when
  available or via environment variables
- 💾 Response caching with configurable TTL
- 📝 Structured logging with file and console output
- 🎯 Comprehensive error handling with helpful messages
- 🔧 Multiple configuration file support

## Requirements

- Python >= 3.13
- OpenWeatherMap API key (free tier available)

## Installation

1. Install wheel and dependencies using pip (recommended):
   Download the latest release from
   [https://github.com/vihoma/weather-app/releases](https://github.com/vihoma/weather-app/releases)
   ```bash
   pip install weather_app-<version>-py3-none-any.whl
   ```

**OR**

2. Clone the repository:
   ```bash
   git clone https://github.com/vihoma/weather-app.git
   cd weather-app
   ```

   Install using Poetry:
   ```bash
   poetry install
   ```


## Configuration

### API Key Setup

You need an OpenWeatherMap API key. Get one for free at
[https://openweathermap.org/api](https://openweathermap.org/api).

#### API Key Persistence Options

The application supports secure API key storage using your system's keyring

1. **System Keyring (Most Secure)**: API keys are stored encrypted in your
   system's credential store
2. **Environment Variables**: `OWM_API_KEY` environment variable
3. **Configuration Files**: `.weather.env` file in project root or user home
   directory

#### Priority Order

API keys are checked in this order (first match wins):

1. Environment variable `OWM_API_KEY` (will be moved to keyring if available)
2. System keyring secure storage
3. `.weather.env` file in project root
4. `~/.weather.env` in your home directory  

Example `.weather.env` file:
```env
OWM_API_KEY=your_api_key_here
OWM_UNITS=metric
CACHE_PERSIST=true # default = false
CACHE_TTL=120 # default = 600
LOG_LEVEL=INFO
LOG_FORMAT=json # default = text
```

### Environment Variables

- `OWM_API_KEY`: Your OpenWeatherMap API key (required). If keyring is available,
  this will be securely stored and removed from environment.
- `USE_KEYRING`: Enable secure keyring storage (`true`/`false`) - default: `true`
- `OWM_UNITS`: Measurement units (`metric`, `imperial`, `default`) - default: `metric`
- `CACHE_PERSIST`: Use persistent cache or not - default: `false`
- `CACHE_TTL`: Cache time-to-live in seconds - default: `600` (10 minutes)
- `REQUEST_TIMEOUT`: API request timeout in seconds - default: `30`
- `USE_ASYNC`: Enable async mode (`true`/`false`) - default: `true`
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) - default: `INFO`
- `LOG_FILE`: Path to log file - default: `weather_app.log` or `weather_app.json`
  (depends on `LOG_FORMAT`)
- `LOG_FORMAT`: Format of logs (`text` or `json`) - default : `text`

### Configuration Precedence

1. Environment variables (API keys are moved to secure storage if available)
2. System keyring secure storage
3. `.weather.env` in project root
4. `~/.weather.env` in home directory
6. Default values

## Usage

Run the application:
```bash
weather
```
Or on Windows:
```powershell
weather.exe
```
(Well, in fact Windows shells should not need the file extension either, so
just type ```weather```...)

Follow the interactive prompts to:
1. Enter your location:
   ```<City>,<CC>``` (i.e. ```London,GB```)
   ***or***
   ```<Longitude>,<Latitude>``` (i.e. ```51.5074,-0.1278```)
2. See current weather conditions in given location...
3. Change display units:
   1: Metric (Celsius/°C)
   2: Imperial (Fahrenheit/°F)
   3: Scientific (Kelvin/K)
4. Show comparison with previous query (y/n)
5. Check another location (y/n)

... That's it, this is a simple implementation over the OpenWeatherMap API (PyOWM)

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
```

### Building package
```bash
poetry build
```

### Security Features

The application includes several security enhancements:

- **Secure API Key Storage**: API keys are stored using the system's keyring
  service when available
- **Sensitive Data Masking**: Logs automatically mask API keys, passwords, and
  other sensitive information
- **Environment Variable Protection**: API keys provided via environment
  variables are automatically moved to secure storage
- **Error Handling**: Secure error messages that don't expose sensitive
  information

### Project Structure

```
src/weather_app/
└── models/                     # Data models
   |-- __init__.py              # Initialization
   └── weather_data.py          # Data models
└── services/                   # Business logic services
   |-- __init__.py              # Initialization
   |-- async_weather_service.py # Async weather data operations
   |-- location_service.py      # Location validation and geocoding
   |── ui_service.py            # Rich-based user interface components
   └── weather_service.py       # Core weather data operations
|-- __init__.py                 # Initialization
|-- config.py                   # Configuration handling
|-- exceptions.py               # Custom exceptions
|-- main.py                     # Application entry point
|-- logging_config.py           # Logging configuration
|-- security.py                 # Security utilities (keyring, data masking)
└── utils.py                    # Utility functions

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── functional/      # Functional tests
```

## License

BSD 3-Clause - See [LICENSE.txt](LICENSE.txt) for details.
