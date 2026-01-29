# Agent Guidelines for Weather App

## Build/Lint/Test Commands
- **Run application**: `poetry run weather`
- **Lint with ruff**: `poetry run ruff check src/`
- **Format imports**: `poetry run isort src/`
- **Format code**: `poetry run black src/`
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

## Code Correctness Guidelines
- If available, use the context7 MCP server for the latest
  Rich/Click/PyOWM API Documentation and for other APIs as needed
- Run the code formatter (black) after code generation and before
  commits for consistent coding style

## Project Structure
- Source code in `src/weather_app/` with package structure
- Models in `models/`, services in `services/`
- Tests in `tests/` with pytest structure
- Configuration handled via CLI arguments, environment variables
  and a YAML configuration file, in the precedence order, CLI
  arguments override anything else in configuration
- Uses Rich for terminal UI, PyOWM for weather data


<!-- CLAVIX:START -->
## Clavix Integration

This project uses Clavix for prompt improvement and PRD generation.

### Setup Commands (CLI)
| Command | Purpose |
|---------|---------|
| `clavix init` | Initialize Clavix in a project |
| `clavix update` | Update templates after package update |
| `clavix diagnose` | Check installation health |
| `clavix version` | Show version |

### Workflow Commands (Slash Commands)
| Slash Command | Purpose |
|---------------|---------|
| `/clavix:improve` | Optimize prompts (auto-selects depth) |
| `/clavix:prd` | Generate PRD through guided questions |
| `/clavix:plan` | Create task breakdown from PRD |
| `/clavix:implement` | Execute tasks or prompts (auto-detects source) |
| `/clavix:start` | Begin conversational session |
| `/clavix:summarize` | Extract requirements from conversation |
| `/clavix:verify` | Verify implementation |
| `/clavix:archive` | Archive completed projects |

Learn more: https://github.com/clavixdev/clavix
<!-- CLAVIX:END -->
