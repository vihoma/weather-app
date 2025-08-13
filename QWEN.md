# Weather CLI Application - Development Context

## Project Overview

This is a command-line weather application built with Python 3 that provides current weather conditions for any location worldwide with a beautiful terminal interface using the Rich library.

### Key Features
- Current weather conditions (temperature, humidity, wind speed, etc.)
- Location search by city name or coordinates
- Beautiful terminal UI with Rich formatting and colors
- Configurable units (metric/imperial)
- Weather history comparisons
- Secure API key management via environment variables

### Technologies Used
- **Python 3.8+**: Main programming language
- **Rich**: For enhanced terminal output and UI
- **PyOWM**: Python wrapper for OpenWeatherMap API
- **python-dotenv**: For environment variable management
- **Ruff**: For code linting (configured in GitHub Actions)

## Project Structure

```
weather-app/
├── src/
│   └── weather_app/
│       ├── __init__.py
│       ├── config.py           # Configuration handling
│       ├── main.py             # Application entry point
│       ├── models/
│       │   ├── __init__.py
│       │   └── weather_data.py # Weather data model
│       └── services/
│           ├── __init__.py
│           ├── ui_service.py   # Terminal UI components
│           └── weather_service.py # Weather API interactions
├── tests/                      # (Currently empty)
├── .github/
│   ├── copilot-instructions.md # Development guidelines
│   └── workflows/
│       └── ruff.yml           # Code linting workflow
├── .weather.env.example       # API key configuration example
├── LICENSE.txt                # BSD 3-Clause License
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## Core Components

### 1. Main Entry Point (`src/weather_app/main.py`)
- Initializes the application
- Sets up Rich traceback handler for better error reporting
- Handles top-level exceptions and user interruptions

### 2. Configuration (`src/weather_app/config.py`)
- Manages environment variables using python-dotenv
- Validates API key configuration
- Supports configurable units (metric/imperial/default)

### 3. Data Models (`src/weather_app/models/weather_data.py`)
- `WeatherData` dataclass for structured weather information
- Contains properties for all weather metrics (temperature, humidity, wind, etc.)
- Maps weather conditions to appropriate emojis

### 4. Services

#### Weather Service (`src/weather_app/services/weather_service.py`)
- Interacts with OpenWeatherMap API via PyOWM
- Parses API responses into our data model
- Handles unit conversions for different measurement systems

#### UI Service (`src/weather_app/services/ui_service.py`)
- Manages all user interactions using Rich components
- Displays weather data in formatted tables
- Handles location input validation
- Provides unit conversion options
- Shows historical weather comparisons

## Building and Running

### Requirements
- Python 3.8+
- OpenWeatherMap API key (free tier available)

### Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API key:
   Create a `.weather.env` file in the project root with:
   ```ini
   OWM_API_KEY=your_api_key_here
   ```

### Running the Application
```bash
python src/weather_app/main.py
```

### Development Workflow
1. Follow prompts to enter location and select units
2. View current weather conditions
3. Option to change units or compare with previous queries

## Development Practices

### Code Quality
- Uses Ruff for linting (configured in `.github/workflows/ruff.yml`)
- Follows PEP 8 coding standards and PEP 257 docstring conventions
- Object-oriented design with clear separation of concerns

### Testing
- Currently no automated tests (tests directory is empty)
- Manual testing recommended for new features

### Documentation
- Inline code documentation with docstrings
- Comprehensive README with usage instructions
- Example configuration files

## Configuration Files

### Environment Variables (`.weather.env`)
- `OWM_API_KEY`: Your OpenWeatherMap API key
- `OWM_UNITS`: Default measurement units (metric/imperial/default)

### GitHub Actions
- Ruff linting on push/pull request to master branch
- Separate configurations for GitHub-hosted (ubuntu) and local (windows) environments

## Development Guidelines

As specified in `.github/copilot-instructions.md`:
1. Use Python 3 with object-oriented design paradigm
2. Follow PEP 8 and PEP 257 conventions
3. Use type hints
4. Write complete, well-documented code
5. Maintain a positive, patient, and supportive tone
6. Focus exclusively on coding and software development topics
