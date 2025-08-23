# Agent Guidelines for Weather App

## Build/Lint/Test Commands
- **Run application**: `poetry run python -m src.weather_app.main`
- **Lint with ruff**: `poetry run ruff check src/`
- **Format imports**: `poetry run isort src/`
- **Build package**: `poetry build`
- **Install deps**: `poetry install`

## Code Style Guidelines
- **Python version**: 3.13+
- **Design**: Object-oriented with classes and type hints
- **Formatting**: PEP 8 compliance, enforced by ruff
- **Imports**: Absolute imports within src/ (e.g., `from src.weather_app.models import WeatherData`)
- **Naming**: snake_case for vars/functions, PascalCase for classes
- **Error handling**: Specific exceptions with validation
- **Documentation**: Google-style docstrings for public methods
- **Dependencies**: Managed via Poetry in pyproject.toml

## Project Structure
- Source code in `src/weather_app/` with package structure
- Models in `models/`, services in `services/`
- Tests in `tests/` with pytest structure
- Configuration handled via environment variables (.weather.env)
- Uses Rich for terminal UI, PyOWM for weather data
