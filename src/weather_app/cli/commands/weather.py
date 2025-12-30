"""Weather subcommand for one-shot weather retrieval."""

import asyncio

import click

from weather_app.cli.options import location_options, output_option
from weather_app.cli.output_formatters import FormatterFactory
from weather_app.cli.errors import (
    ConfigurationClickException,
    APIClickException,
    LocationClickException,
)
from weather_app.exceptions import (
    APIRequestError,
    ConfigurationError,
    LocationNotFoundError,
    NetworkError,
    DataParsingError,
    RateLimitError,
)


@click.command(
    name="weather",
    help="Get current weather for a location.",
    epilog="""
Examples:
  # Get weather by city name with TUI output (default)
  weather weather --city "London,GB"
  
  # Get weather by coordinates with JSON output
  weather weather --coordinates "51.5074,-0.1278" --output json
  
  # Get weather with Markdown output
  weather weather --city "Paris,FR" --output markdown
  
  # Use imperial units
  weather weather --city "New York" --units imperial
  
  # Combine with global options
  weather --verbose --no-cache weather --city "Tokyo,JP" --output json
  
Output Formats:
  • tui: Rich terminal UI with colors and formatting (default)
  • json: Structured JSON output for scripting
  • markdown: Markdown formatted output for documentation
""",
)
@location_options()
@output_option()
@click.pass_context
def weather_command(
    ctx: click.Context,
    city: str | None,
    coordinates: str | None,
    output_format: str,
) -> None:
    """Get current weather for a location and output in specified format.

    This command fetches current weather data from OpenWeatherMap API
    and formats it according to the specified output format.

    You must provide either --city or --coordinates to specify the location.

    Args:
        ctx: Click context containing global options and configuration overrides.
        city: City name with optional country code (e.g., 'London,GB').
        coordinates: Geographic coordinates as 'latitude,longitude'.
        output_format: Output format (tui, json, markdown).
    """
    # Get configuration with CLI overrides
    from weather_app.cli.group import get_config_from_context

    config = get_config_from_context(ctx)

    # Validate that at least one location method is provided
    if not city and not coordinates:
        raise click.UsageError(
            "You must specify a location using --city or --coordinates."
        )

    try:
        # Determine location string for API
        if city:
            location = city.strip()
        else:
            # coordinates is guaranteed to be not None due to validation above
            assert coordinates is not None
            # Validate coordinates format
            try:
                lat_str, lon_str = coordinates.split(",")
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
                # Ensure values are within valid ranges
                if not (-90 <= latitude <= 90):
                    raise ValueError("Latitude must be between -90 and 90.")
                if not (-180 <= longitude <= 180):
                    raise ValueError("Longitude must be between -180 and 180.")
                location = f"{latitude},{longitude}"
            except ValueError as e:
                raise click.BadParameter(
                    f"Invalid coordinates: {e}. "
                    "Expected format 'latitude,longitude' with valid numbers."
                )

        # Fetch weather data using appropriate service (async/sync)
        weather_data = _fetch_weather_data(config, location)

        # Format output
        formatter = FormatterFactory.get_formatter(output_format, units=config.units)
        output = formatter.format(weather_data)

        # Print output
        click.echo(output)

    except LocationNotFoundError as e:
        raise LocationClickException(f"Location not found: {e}")
    except ConfigurationError as e:
        raise ConfigurationClickException(f"Configuration error: {e}")
    except (APIRequestError, NetworkError, DataParsingError, RateLimitError) as e:
        raise APIClickException(f"API request failed: {e}")
    except click.BadParameter:
        raise  # Re-raise click.BadParameter to preserve its exit code
    except Exception as e:
        raise click.ClickException(f"Unexpected error: {e}")


def _fetch_weather_data(config, location: str):
    """Fetch weather data using appropriate service based on config."""
    # Use async service if config.use_async is True or if location is coordinates
    # (since sync service doesn't support coordinates)
    # Simple check: if location contains a comma and both parts are numeric
    is_coordinates = False
    if "," in location:
        parts = location.split(",")
        if len(parts) == 2:
            try:
                float(parts[0].strip())
                float(parts[1].strip())
                is_coordinates = True
            except ValueError:
                pass

    use_async = config.use_async or is_coordinates

    if use_async:
        from weather_app.services.async_weather_service import AsyncWeatherService

        async def async_fetch():
            service = AsyncWeatherService(config)
            try:
                return await service.get_weather(location, config.units)
            finally:
                await service.close()

        return asyncio.run(async_fetch())
    else:
        from weather_app.services.weather_service import WeatherService

        service = WeatherService(config)
        return service.get_weather(location, config.units)
