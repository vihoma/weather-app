"""Rich-based user interface components with async support."""

import asyncio
from rich.prompt import Prompt, Confirm
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..models.weather_data import WeatherData
from ..config import Config
from .weather_service import WeatherService
from .async_weather_service import AsyncWeatherService
from .location_service import LocationService
from ..exceptions import InvalidLocationError


class UIService:
    """Handles all user interaction and display."""

    def __init__(self, use_async: bool = True):
        self.console = Console()
        self.config = Config()
        self.config.validate()
        self.use_async = use_async

        if use_async:
            self.weather_service = AsyncWeatherService(self.config)
        else:
            self.weather_service = WeatherService(self.config)

        self.location_service = LocationService()
        self.current_units = self.config.units
        self.query_history = []

    async def run_async(self) -> None:
        """Main async application loop."""
        self.console.print(
            "[bold green]🌦️ Welcome to Weather App! (Async Mode)[/bold green]"
        )

        while True:
            location = self._prompt_location()
            while True:  # Inner loop for unit changes
                weather_data = await self._get_weather_with_progress(location)
                self._display_weather(weather_data)

                if not Confirm.ask("\n🔄 Change units?"):
                    break
                self._prompt_units()

            if not self._prompt_continue():
                break

    def run(self) -> None:
        """Main synchronous application loop."""
        if self.use_async:
            asyncio.run(self.run_async())
        else:
            self.console.print(
                "[bold green]🌦️ Welcome to Weather App! (Sync Mode)[/bold green]"
            )
            while True:
                location = self._prompt_location()
                while True:  # Inner loop for unit changes
                    weather_data = self.weather_service.get_weather(
                        location, self.current_units
                    )
                    self._display_weather(weather_data)

                    if not Confirm.ask("\n🔄 Change units?"):
                        break
                    self._prompt_units()

                if not self._prompt_continue():
                    break

    async def _get_weather_with_progress(self, location: str) -> WeatherData:
        """Get weather data with progress indicator."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching weather for {location}...", total=None
            )

            try:
                weather_data = await self.weather_service.get_weather(
                    location, self.current_units
                )
                progress.update(
                    task, completed=True, description="[green]Data received!"
                )
                return weather_data
            except Exception as e:
                progress.update(task, completed=True, description=f"[red]Error: {e}")
                raise

    def _prompt_location(self) -> str:
        """Get validated location input."""
        while True:
            location = Prompt.ask(
                "📌 Enter location (e.g. [bold]London,GB[/bold] or [bold]51.5074,-0.1278[/bold])"
            )

            if not location.strip():
                self.console.print("[red]⚠️ Location cannot be empty![/red]")
                continue

            try:
                normalized_location = self.location_service.normalize_location(location)
                return normalized_location
            except InvalidLocationError as e:
                self.console.print(f"[red]⚠️ {e}[/red]")
                self.console.print(
                    "[yellow]💡 Examples: 'London,GB' or '51.5074,-0.1278'[/yellow]"
                )

    def _display_weather(self, data: WeatherData) -> None:
        """Display weather data in a rich table."""
        table = Table(title=f"🌤️ Weather in {data.city}", show_header=False)

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")

        self._add_table_row(
            table, "Condition", f"{data.get_emoji()} {data.detailed_status}"
        )
        self._add_table_row(
            table, "Temperature", f"{data.temperature} {self._temp_unit()}"
        )
        self._add_table_row(
            table, "Feels Like", f"{data.feels_like} {self._temp_unit()}"
        )
        self._add_table_row(table, "Humidity", f"{data.humidity}% 💧")

        if data.precipitation_probability:
            self._add_table_row(
                table, "Precipitation", f"{data.precipitation_probability}% ☔"
            )

        if data.wind_direction_deg:
            # 16-point compass directions (0°-360° in 22.5° increments)
            wind_arrows = [
                "↓",  # N    (0°)
                "↙",  # NNE  (22.5°)
                "←",  # NE   (45°)
                "↖",  # ENE  (67.5°)
                "←",  # E    (90°)
                "↖",  # ESE  (112.5°)
                "↑",  # SE   (135°)
                "↗",  # SSE  (157.5°)
                "↑",  # S    (180°)
                "↗",  # SSW  (202.5°)
                "→",  # SW   (225°)
                "↘",  # WSW  (247.5°)
                "→",  # W    (270°)
                "↘",  # WNW  (292.5°)
                "↓",  # NW   (315°)
                "↙",  # NNW  (337.5°)
            ]
            wind_directions = [
                "N",
                "NNE",
                "NE",
                "ENE",
                "E",
                "ESE",
                "SE",
                "SSE",
                "S",
                "SSW",
                "SW",
                "WSW",
                "W",
                "WNW",
                "NW",
                "NNW",
            ]
            dir_index = int((data.wind_direction_deg + 11.25) / 22.5) % 16
            wind_info = f"{data.wind_speed} {self._speed_unit()} {wind_arrows[dir_index]} ({wind_directions[dir_index]})"
        else:
            wind_info = f"{data.wind_speed} {self._speed_unit()}"
        self._add_table_row(table, "Wind", wind_info)

        pressure_bar = "█" * int(data.pressure_hpa / 10)  # Simple bar visualization
        self._add_table_row(
            table, "Pressure", f"{data.pressure_hpa} hPa {pressure_bar}"
        )

        self.console.print(table)

        self.query_history.append(data)
        if len(self.query_history) > 1:
            if Confirm.ask("\n📜 Show comparison with previous query?"):
                self._show_history_comparison()

    def _show_history_comparison(self) -> None:
        """Show comparison between current and previous query."""
        comp_table = Table(title="🕰️ Weather Comparison")
        comp_table.add_column("Metric", style="cyan")
        comp_table.add_column("Current", style="bold green")
        comp_table.add_column("Previous", style="bold yellow")

        current = self.query_history[-1]
        previous = self.query_history[-2]

        comp_table.add_row(
            "Temperature",
            f"{current.temperature}{self._temp_unit()}",
            f"{previous.temperature}{self._temp_unit()}",
        )
        comp_table.add_row(
            "Conditions", current.detailed_status, previous.detailed_status
        )

        self.console.print(comp_table)

    def _add_table_row(self, table: Table, metric: str, value: str) -> None:
        """Helper to add styled rows to table."""
        table.add_row(Text(metric, style="bold cyan"), Text(value))

    def _temp_unit(self) -> str:
        """Get temperature unit symbol."""
        return {"metric": "°C", "imperial": "°F", "default": "K"}.get(
            self.current_units, "K"
        )

    def _speed_unit(self) -> str:
        """Get speed unit symbol."""
        return {"metric": "m/s", "imperial": "mph", "default": "m/s"}[
            self.current_units
        ]

    def _prompt_units(self) -> None:
        """Handle unit system selection."""
        self.console.print("\n[bold]🌡️ Measurement Units[/bold]")
        choice = Prompt.ask(
            "Choose units ([1] Metric °C/[2] Imperial °F/[3] Kelvin)",
            choices=["1", "2", "3"],
            default="1",
        )
        self.current_units = {"1": "metric", "2": "imperial", "3": "default"}[choice]
        self.console.print(f"✅ Switched to {self._temp_unit()} units")

    def _prompt_continue(self) -> bool:
        """Ask user if they want to continue."""
        return Confirm.ask("\n🔍 Check another location?", default=True)
