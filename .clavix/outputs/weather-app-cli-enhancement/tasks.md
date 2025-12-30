# Implementation Plan

**Project**: weather-app-cli-enhancement
**Generated**: 2025-12-30T11:03:48+02:00

## Technical Context & Standards
*Detected Stack & Patterns*
- **Architecture**: Layered with services, models, config; dependency injection (config passed to services)
- **Framework**: Pure Python CLI with Rich TUI, async/sync support via asyncio, Click for CLI parsing
- **Styling**: Rich terminal formatting (no CSS)
- **State**: No state management framework, service instances
- **API**: PyOWM for weather, geopy for location, aiohttp for async
- **Conventions**: Google-style docstrings, type hints, absolute imports within src/, snake_case vars/functions, PascalCase classes, Pydantic for config, pytest for testing, Poetry for dependencies
- **Existing CLI**: Click-based CLI fully implemented with subcommands (weather, setup, cache, config), output formatters (JSON, Markdown, TUI), configuration override, error mapping.

---

## Phase 1: Setup and Dependencies

- [x] **Add Click dependency to pyproject.toml** (ref: Technical Requirements)
  Task ID: phase-1-setup-01
  > **Implementation**: Edit `pyproject.toml` in project root.
  > **Details**: Add `"click (>=8.1.0,<9.0.0)"` to `dependencies` list. Ensure version compatible with Python 3.13+.

- [x] **Create CLI module structure** (ref: Architecture & Design)
  Task ID: phase-1-setup-02
  > **Implementation**: Create directory `src/weather_app/cli/` with `__init__.py` and `commands/` subdirectory.
  > **Details**: Follow existing package patterns: `__init__.py` exports public interfaces. Create `commands/__init__.py` to group subcommand modules.

- [x] **Update entry point to use Click** (ref: Architecture & Design)
  Task ID: phase-1-setup-03
  > **Implementation**: Modify `src/weather_app/main.py` to delegate to Click command group.
  > **Details**: Keep existing `main()` function but replace argv parsing with Click invocation. Ensure backward compatibility: if no CLI args, fall back to interactive TUI (existing flow). Use `click.Group` for command grouping.

## Phase 2: Core CLI Framework

- [x] **Create Click command group and base arguments** (ref: Command pattern)
  Task ID: phase-2-framework-01
  > **Implementation**: Create `src/weather_app/cli/group.py` defining `@click.group()` with common options (--verbose, --config-file, etc.).
  > **Details**: Define group function `cli()` that sets up context and passes config overrides. Use `click.option` for global flags.

- [x] **Implement configuration override mechanism** (ref: Configuration precedence)
  Task ID: phase-2-framework-02
  > **Implementation**: Create `src/weather_app/cli/config_override.py` with function `apply_cli_overrides(config, **kwargs)`.
  > **Details**: Override `Config` attributes based on CLI arguments (e.g., `units`, `use_async`, `cache_ttl`). Ensure precedence: CLI > env > YAML > keyring. Use `config.units = value` etc.

- [x] **Define common CLI options for weather commands** (ref: Must-Have Features)
  Task ID: phase-2-framework-03
  > **Implementation**: Create `src/weather_app/cli/options.py` with reusable decorators for `--city`, `--coordinates`, `--units`, `--output`, `--async`, `--no-cache`.
  > **Details**: Use `click.option` with appropriate type validation (e.g., tuple for coordinates). Ensure mutual exclusivity between city and coordinates.

## Phase 3: Output Formatters

- [x] **Create formatter factory** (ref: Factory pattern)
  Task ID: phase-3-formatters-01
  > **Implementation**: Create `src/weather_app/cli/output_formatters.py` with `FormatterFactory` class.
  > **Details**: Factory method `get_formatter(output_format: str)` returns instance of `BaseFormatter`. Support `tui` (Rich), `json`, `markdown`.

- [x] **Implement JSON formatter** (ref: Multiple output formats)
  Task ID: phase-3-formatters-02
  > **Implementation**: Create `src/weather_app/cli/formatters/json_formatter.py` extending `BaseFormatter`.
  > **Details**: Convert `WeatherData` model to JSON string with indentation. Use `json.dumps` with default=str for datetime fields.

- [x] **Implement Markdown formatter** (ref: Multiple output formats)
  Task ID: phase-3-formatters-03
  > **Implementation**: Create `src/weather_app/cli/formatters/markdown_formatter.py` extending `BaseFormatter`.
  > **Details**: Format weather data as Markdown with headings, tables, and emojis. Use consistent styling matching existing Rich output.

- [x] **Integrate existing Rich TUI as formatter** (ref: Maintain existing Rich TUI)
  Task ID: phase-3-formatters-04
  > **Implementation**: Adapt `UIService` display methods into `TUIFormatter` in `src/weather_app/cli/formatters/tui_formatter.py`.
  > **Details**: Reuse `UIService` rendering logic but extract display methods to work without interactive prompts.

## Phase 4: Subcommands Implementation

- [x] **Implement weather subcommand (one-shot)** (ref: One-shot execution mode)
  Task ID: phase-4-subcommands-01
  > **Implementation**: Create `src/weather_app/cli/commands/weather.py` with `@cli.command()`.
  > **Details**: Command `weather` takes location arguments, fetches weather via appropriate service (async/sync), uses formatter factory to output, then exits. Handle errors with appropriate exit codes.

- [x] **Implement setup subcommand (API key management)** (ref: API key management)
  Task ID: phase-4-subcommands-02
  > **Implementation**: Create `src/weather_app/cli/commands/setup.py` with subcommands `setup api-key set|view|remove`.
  > **Details**: Use `click.group` within setup. Integrate with existing `setup_api_key()` and `SecureConfig` from security module.

- [x] **Implement cache subcommand** (ref: Cache control)
  Task ID: phase-4-subcommands-03
  > **Implementation**: Create `src/weather_app/cli/commands/cache.py` with subcommands `cache clear|ttl|status`.
  > **Details**: Clear cache file, set TTL, show cache stats. Use `WeatherService` cache persistence.

- [x] **Implement config subcommand** (ref: Configuration precedence)
  Task ID: phase-4-subcommands-04
  > **Implementation**: Create `src/weather_app/cli/commands/config.py` with `config show` to display current configuration sources.
  > **Details**: Show values with source indication (cli, env, yaml, keyring). Use `Config` fields.

## Phase 5: Integration and Fallback

- [x] **Integrate CLI with existing services** (ref: Separation of concerns)
  Task ID: phase-5-integration-01
  > **Implementation**: Modify `UIService` and `WeatherService` to accept config overrides from CLI.
  > **Details**: Ensure services can be instantiated with overridden config values. No duplication of business logic.

- [x] **Implement fallback to interactive TUI when no args** (ref: Maintain existing Rich TUI)
  Task ID: phase-5-integration-02
  > **Implementation**: Update `main.py` to detect if any CLI arguments were provided; if not, run existing `main_async()`.
  > **Details**: Use `len(sys.argv) == 1` or Click's context to determine if command invoked. Preserve exact current behavior.

- [x] **Add POSIX error codes and error handling** (ref: POSIX-compliant error handling)
  Task ID: phase-5-integration-03
  > **Implementation**: Define exit codes in `src/weather_app/cli/errors.py` and map exceptions to codes.
  > **Details**: Use standard codes: 0 success, 1 general error, 2 misuse of shell builtins, etc. Document in help.

- [x] **Update main entry point to use Click group** (ref: Architecture & Design)
  Task ID: phase-5-integration-04
  > **Implementation**: Finalize `main.py` to invoke Click group and handle exceptions.
  > **Details**: Wrap `cli()` invocation with try/except, convert exceptions to exit codes, ensure cache saving on exit.

---

## Phase 6: Testing and Documentation

- [ ] **Add unit tests for CLI commands** (ref: Testing)
  Task ID: phase-6-testing-01
  > **Implementation**: Create `tests/unit/test_cli_commands.py` and `tests/integration/test_cli_integration.py`.
  > **Details**: Use `click.testing.CliRunner` to test command outputs, error codes, and argument parsing. Test each subcommand (weather, setup api-key, cache, config). Mock external services (PyOWM, geopy) to avoid API calls. Ensure coverage for location validation, output formats, error handling.

- [ ] **Update README with new CLI usage** (ref: Documentation)
  Task ID: phase-6-testing-02
  > **Implementation**: Edit `README.md` to include CLI examples, subcommand reference, and migration notes.
  > **Details**: Replace interactive usage section with CLI examples. Show `weather --city "London,GB" --output json`, `setup api-key set --interactive`, `cache clear`, `config show`. Include table of subcommands and options. Keep existing installation/config details.

- [ ] **Generate comprehensive help with examples** (ref: Comprehensive help system)
  Task ID: phase-6-testing-03
  > **Implementation**: Add detailed docstrings and `click.help_option` to commands, with examples in epilog.
  > **Details**: Ensure `weather --help` shows examples for each subcommand. Add `@click.epilog` with usage examples. Consider generating man pages (optional). Verify that `--help` works for all subcommands and groups.

- [ ] **Run existing test suite and ensure no regressions** (ref: Testing requirements)
  Task ID: phase-6-testing-04
  > **Implementation**: Execute `pytest` and fix any failures introduced by changes.
  > **Details**: Ensure all existing unit, integration, and functional tests pass. Add new tests for CLI features. Run `poetry run pytest tests/ -v`. Address any linting issues (`ruff check src/`).

---

## Phase 7: Final Validation and Release

- [ ] **Verify CLI works in one-shot mode** (ref: One-shot execution mode)
  Task ID: phase-7-validation-01
  > **Implementation**: Manual testing of CLI commands with real API key (or mocked).
  > **Details**: Test `weather --city "Kuopio,FI" --once` (note: `--once` flag not yet implemented). Actually, the `--once` flag is not needed; the CLI already exits after output. Verify that command exits with code 0 and outputs weather data. Test all output formats (tui, json, markdown). Test coordinates.

- [ ] **Test configuration precedence** (ref: Configuration precedence)
  Task ID: phase-7-validation-02
  > **Implementation**: Create integration test to verify CLI arguments override env variables, YAML, keyring.
  > **Details**: Write test in `tests/integration/test_config_integration.py` that sets env var, then CLI arg, and ensures CLI arg wins. Use `monkeypatch` for env vars.

- [ ] **Update version and package metadata** (ref: Packaging)
  Task ID: phase-7-validation-03
  > **Implementation**: Update `pyproject.toml` version (maybe 0.6.0) and ensure entry points work correctly.
  > **Details**: Bump version, verify `weather` entry point works after reinstall. Build package with `poetry build` and test installation.

- [ ] **Create changelog entry** (ref: Documentation)
  Task ID: phase-7-validation-04
  > **Implementation**: Add CHANGELOG.md entry describing CLI enhancement.
  > **Details**: Document new features, breaking changes (if any), migration steps for users of previous interactive-only version.

---

*Generated by Clavix /clavix-plan*