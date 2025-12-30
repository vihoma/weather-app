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
  available or via a YAML configuration file or environment variables
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
3. **Configuration Files**: `.weather.yaml` file in project root or user home
   directory

#### Priority Order

API keys are checked in this order (first match wins):

1. Environment variable `OWM_API_KEY` (will be moved to keyring if available)
2. System keyring secure storage
3. `.weather.yaml` file in project root
4. `~/.weather.yaml` in your home directory

#### YAML configuration file (recommended)

The application now prefers a single YAML file named `.weather.yaml` placed
either in the project root or in your home directory (`~/.weather.yaml`).
All keys are **lower‑case**.

```yaml
# weather.yaml
owm_api_key: your_api_key_here
owm_units: metric          # options: metric, imperial, kelvin
cache_persist: true        # default: false
cache_ttl: 120             # seconds, default: 600
log_level: INFO            # DEBUG, INFO, WARNING, ERROR
log_format: json           # text or json (default: text)
```

> **Note:** The same settings can still be provided via environment variables;
> the YAML file simply offers a more structured, version‑controlled alternative.

### Environment Variables (optional if using `weather.yaml`)

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
3. `.weather.yaml` in project root
4. `~/.weather.yaml` in home directory
6. Default values

## Usage

The weather application now supports both **interactive TUI mode** and **one-shot CLI mode**.

### Interactive Mode (Traditional)

Run without arguments for the interactive terminal UI:
```bash
weather
```

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

### CLI Mode (One-shot Commands)

Get weather data directly from the command line:

```bash
# Get weather by city name
weather weather --city "London,GB" --output json

# Get weather by coordinates
weather weather --coordinates "51.5074,-0.1278" --output markdown

# Use metric units with TUI output (default)
weather weather --city "Paris,FR" --units metric --output tui

# Force async mode and disable caching
weather weather --city "Tokyo,JP" --use-async --no-cache
```

### Subcommands Reference

| Command | Description | Examples |
|---------|-------------|----------|
| **`weather weather`** | Get current weather for a location | `weather weather --city "London,GB" --output json` |
| **`weather setup api-key set`** | Store API key securely | `weather setup api-key set --interactive` |
| **`weather setup api-key view`** | View stored API key (masked) | `weather setup api-key view` |
| **`weather setup api-key remove`** | Remove stored API key | `weather setup api-key remove --force` |
| **`weather cache clear`** | Clear weather cache | `weather cache clear --force` |
| **`weather cache status`** | Show cache statistics | `weather cache status` |
| **`weather cache ttl`** | Show or set cache TTL | `weather cache ttl --set 300` |
| **`weather config show`** | Show configuration with sources | `weather config show` |
| **`weather config sources`** | Detailed source analysis | `weather config sources` |
| **`weather version`** | Show application version information | `weather version` |

### Global Options

All commands support these global options:

- `--verbose, -v` - Enable verbose output (debug logging)
- `--config-file FILE` - Path to custom configuration file (YAML)
- `--units [metric|imperial|standard]` - Temperature units
- `--use-async` - Force asynchronous mode
- `--no-cache` - Disable caching for this request

### Output Formats

The `weather` command supports three output formats:

1. **`tui`** (default) - Rich terminal UI with colors and formatting
2. **`json`** - Structured JSON output for scripting
3. **`markdown`** - Markdown formatted output for documentation

### Configuration Precedence

CLI arguments follow this precedence order:
1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **YAML configuration file** (`.weather.yaml`)
4. **Keyring storage** (for API keys)
5. **Default values** (lowest priority)

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
├── models/                     # Data models
│   ├── __init__.py              # Initialization
│   └── weather_data.py          # Data models
├── services/                   # Business logic services
│   ├── __init__.py              # Initialization
│   ├── async_weather_service.py # Async weather data operations
│   ├── location_service.py      # Location validation and geocoding
│   ├── ui_service.py            # Rich-based user interface components
│   └── weather_service.py       # Core weather data operations
├── cli/                        # CLI interface
│   ├── __init__.py              # Initialization
│   ├── group.py                 # Main CLI command group
│   ├── config_override.py       # CLI configuration overrides
│   ├── options.py               # Reusable CLI options
│   ├── output_formatters.py     # Output formatter factory
│   ├── errors.py                # CLI error handling
│   ├── commands/                # CLI subcommands
│   │   ├── __init__.py
│   │   ├── weather.py           # Weather command
│   │   ├── setup.py             # Setup command
│   │   ├── cache.py             # Cache command
│   │   └── config.py            # Config command
│   └── formatters/              # Output formatters
│       ├── __init__.py
│       ├── json_formatter.py    # JSON output
│       ├── markdown_formatter.py # Markdown output
│       └── tui_formatter.py     # TUI output
├── __init__.py                 # Initialization
├── config.py                   # Configuration handling
├── exceptions.py               # Custom exceptions
├── main.py                     # Application entry point
├── logging_config.py           # Logging configuration
├── security.py                 # Security utilities (keyring, data masking)
└── utils.py                    # Utility functions

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── functional/      # Functional tests
```

## License

BSD 3-Clause - See [LICENSE.txt](LICENSE.txt) for details.
