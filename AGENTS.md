# Agent Guidelines for Weather App

## Build/Lint/Test Commands
- **Run application**: `poetry run weather`
- **Lint with ruff**: `poetry run ruff check src/`
- **Format imports**: `poetry run isort src/`
- **Build package**: `poetry build`
- **Install deps**: `poetry install`

## Code Style Guidelines
- **Python version**: 3.13+
- **Design**: Object-oriented with classes and type hints
- **Formatting**: PEP 8 compliance, enforced by ruff
- **Imports**: Absolute imports within src/, e.g.:
  ```python
    from weather_app.models.weather_data import WeatherData
  ```
- **Naming**: snake_case for vars/functions, PascalCase for classes
- **Error handling**: Specific exceptions with validation
- **Documentation**: Google-style docstrings for public methods
- **Dependencies**: Managed via Poetry in pyproject.toml

## Project Structure
- Source code in `src/weather_app/` with package structure
- Models in `models/`, services in `services/`
- Tests in `tests/` with pytest structure
- Configuration handled via CLI arguments, environment variables
  and a YAML configuration file, in the precedence order, CLI
  arguments override anything else in configuration
- Uses Rich for terminal UI, PyOWM for weather data


<!-- CLAVIX:START -->
# Clavix - Prompt Improvement Assistant

Clavix is installed in this project. Use the following slash commands:

- `/clavix:improve [prompt]` - Optimize prompts with smart depth auto-selection
- `/clavix:prd` - Generate a PRD through guided questions
- `/clavix:start` - Start conversational mode for iterative refinement
- `/clavix:summarize` - Extract optimized prompt from conversation

**When to use:**
- **Standard depth**: Quick cleanup for simple, clear prompts
- **Comprehensive depth**: Thorough analysis for complex requirements
- **PRD mode**: Strategic planning with architecture and business impact

Clavix automatically selects the appropriate depth based on your prompt quality.

For more information, run `clavix --help` in your terminal.
<!-- CLAVIX:END -->
