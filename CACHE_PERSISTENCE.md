# Cache Persistence Implementation

## Overview

The Weather App now includes persistent cache functionality that saves weather query results to disk using JSON format. This allows the application to maintain cached data between sessions, reducing API calls and improving performance.

## Features

- **JSON-based cache storage**: Cache data is stored in human-readable JSON format
- **User home directory storage**: Cache files are stored in the user's home directory by default
- **Automatic loading**: Cache is automatically loaded on application startup
- **Automatic saving**: Cache is automatically saved when the application exits
- **Configurable**: All cache settings are configurable via environment variables

## Configuration Options

### Environment Variables

Add these to your `.weather.env` file or set as environment variables:

```bash
# Enable cache persistence (default: false)
CACHE_PERSIST=true

# Cache file path (default: ~/.weather_app_cache.json)
CACHE_FILE=~/.weather_app_cache.json

# Cache TTL in seconds (default: 600 - 10 minutes)
CACHE_TTL=600
```

### Default Values

- **CACHE_PERSIST**: `false` (disabled by default)
- **CACHE_FILE**: `~/.weather_app_cache.json`
- **CACHE_TTL**: `600` seconds (10 minutes)

## Cache File Format

The cache is stored in JSON format with the following structure:

```json
{
  "London,GB:metric": {
    "city": "London,GB",
    "units": "metric",
    "status": "Clear",
    "detailed_status": "Clear sky",
    "temperature": 20.5,
    "feels_like": 19.8,
    "humidity": 65,
    "wind_speed": 3.2,
    "wind_direction_deg": 180,
    "precipitation_probability": 10,
    "clouds": 20,
    "visibility_distance": 10000,
    "pressure_hpa": 1013,
    "icon_code": 800
  },
  "New York,US:imperial": {
    "city": "New York,US",
    "units": "imperial",
    "status": "Clouds",
    "detailed_status": "Broken clouds",
    "temperature": 68.0,
    "feels_like": 65.0,
    "humidity": 70,
    "wind_speed": 8.0,
    "wind_direction_deg": 270,
    "precipitation_probability": 30,
    "clouds": 75,
    "visibility_distance": 16000,
    "pressure_hpa": 1012,
    "icon_code": 803
  }
}
```

## Cache Key Format

Cache keys are generated using the format: `{location}:{units}`

Examples:
- `London,GB:metric`
- `New York,US:imperial` 
- `40.7128,-74.0060:metric` (for coordinates)

## Implementation Details

### WeatherService Changes

- Added `_load_cache_from_disk()` method to load cache from JSON file
- Added `_save_cache_to_disk()` method to save cache to JSON file
- Added `__del__()` destructor to automatically save cache on exit
- Added config reference storage for cache persistence settings

### AsyncWeatherService Changes

- Added same cache persistence methods as WeatherService
- Modified `close()` method to save cache when connections are closed
- Added `__del__()` destructor for automatic cache saving

### Config Class Changes

- Added `cache_persist` property to control cache persistence
- Added `cache_file` property to configure cache file path

## Usage Examples

### Enable Cache Persistence

1. Create or edit `.weather.env` file:

```bash
# Enable cache persistence
CACHE_PERSIST=true

# Optional: Custom cache file location
CACHE_FILE=~/.my_weather_cache.json

# Optional: Adjust cache TTL (in seconds)
CACHE_TTL=300  # 5 minutes
```

2. Run the application normally:

```bash
poetry run python -m src.weather_app.main
```

### Manual Cache Management

The cache file can be manually inspected or modified:

```bash
# View cache contents
cat ~/.weather_app_cache.json

# Clear the cache
rm ~/.weather_app_cache.json

# Backup the cache
cp ~/.weather_app_cache.json ~/.weather_app_cache.backup.json
```

## Error Handling

The cache persistence system includes robust error handling:

- **File not found**: Creates directory structure if needed
- **Permission errors**: Logs warnings but continues operation
- **JSON parsing errors**: Logs warnings and uses empty cache
- **Invalid data**: Skips invalid cache entries

## Performance Considerations

- Cache loading happens during service initialization
- Cache saving happens during service destruction/cleanup
- JSON serialization is efficient for the typical cache size (100 items max)
- File operations are non-blocking and handled in background

## Security Considerations

- Cache files are stored in user's home directory
- File permissions follow system defaults
- No sensitive API keys are stored in cache
- Weather data is public information

## Limitations

- Cache size is limited to 100 items (configurable in code)
- TTL expiration is handled by cachetools, not the persistence layer
- Concurrent access to cache file is not supported (single-user application)

## Future Enhancements

Potential improvements:
- Compressed cache storage
- Encryption for cache files
- Cache statistics and monitoring
- Manual cache management commands