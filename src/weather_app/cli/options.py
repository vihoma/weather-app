"""Reusable CLI options for weather commands.

This module provides Click decorators for common weather command options,
including location specification, output format, and caching behavior.
"""

import click


def city_option():
    """Decorator for adding a --city option to a command.

    The option expects a string in the format "City,CountryCode" (e.g., "London,GB").
    """
    return click.option(
        "--city",
        type=str,
        help="City name with optional country code (e.g., 'London,GB' or 'New York').",
    )


def coordinates_option():
    """Decorator for adding a --coordinates option to a command.

    The option expects two floats separated by a comma: latitude,longitude.
    """
    return click.option(
        "--coordinates",
        "--coords",
        type=str,
        help="Geographic coordinates as 'latitude,longitude' (e.g., '51.5074,-0.1278').",
    )


def units_option():
    """Decorator for adding a --units option to a command.

    Overrides the global units setting for this specific command.
    """
    return click.option(
        "--units",
        type=click.Choice(["metric", "imperial", "standard"]),
        help="Temperature units: metric (°C), imperial (°F), standard (K).",
    )


def output_option():
    """Decorator for adding an --output option to a command.

    Specifies the output format for weather data.
    """
    return click.option(
        "--output",
        "--format",
        "output_format",
        type=click.Choice(["tui", "json", "markdown"]),
        default="tui",
        show_default=True,
        help="Output format: tui (Rich terminal UI), json, markdown.",
    )


def async_option():
    """Decorator for adding an --async option to a command.

    Overrides the global async setting for this specific command.
    """
    return click.option(
        "--async",
        "use_async",
        is_flag=True,
        help="Force asynchronous mode for this command.",
    )


def no_cache_option():
    """Decorator for adding a --no-cache option to a command.

    Disables caching for this specific request.
    """
    return click.option(
        "--no-cache",
        is_flag=True,
        help="Disable caching for this request.",
    )


def location_options():
    """Composite decorator that adds both city and coordinates options.

    Ensures mutual exclusivity: only one of city or coordinates may be provided.
    """

    def decorator(f):
        f = city_option()(f)
        f = coordinates_option()(f)
        # Add callback to validate mutual exclusivity
        original_callback = f.__click_params__[0].callback

        def validate_location(ctx, param, value):
            # Get the other parameter's value
            other_param = "city" if param.name == "coordinates" else "coordinates"
            other_value = ctx.params.get(other_param)
            if value and other_value:
                raise click.UsageError(
                    f"Cannot specify both --{param.name} and --{other_param}. "
                    "Please choose one location method."
                )
            if original_callback:
                return original_callback(ctx, param, value)
            return value

        # Attach validation callback to both options
        for param in f.__click_params__:
            if param.name in ("city", "coordinates"):
                param.callback = validate_location
        return f

    return decorator
