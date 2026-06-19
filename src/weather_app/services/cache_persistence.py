"""Shared cache persistence logic used by both async and sync weather services.

This module eliminates the duplicate ``_load_cache_from_disk`` /
``_save_cache_to_disk`` methods that previously existed in
``AsyncWeatherService`` and ``WeatherService``.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


def load_cache_from_disk(
    cache_file_path: str,
    cache_dir: str,
    cache_ttl: int,
    in_memory_cache: TTLCache,
    cache_metadata: dict[str, datetime],
    model_validate: Any,
) -> None:
    """Load cache entries from a JSON file into the in-memory TTLCache.

    Args:
        cache_file_path: Path to the on-disk cache JSON file.
        cache_dir: Configured cache directory used for path containment checks.
        cache_ttl: Time-to-live (seconds) for cache entries.
        in_memory_cache: The ``TTLCache`` instance to populate.
        cache_metadata: Dict mapping cache keys to their fetch timestamps.
        model_validate: Callable (e.g. ``WeatherData.model_validate``) used
            to deserialize each entry.
    """
    try:
        cache_path = Path(cache_file_path).expanduser().resolve()
        # Verify the resolved path is within the configured cache directory
        _cache_dir_str = cache_dir
        if isinstance(_cache_dir_str, (str, Path)):
            cache_dir_path = Path(_cache_dir_str).resolve()
            try:
                cache_path.relative_to(cache_dir_path)
            except ValueError:
                logger.warning(
                    "Cache path %s escapes cache directory %s — rejected",
                    cache_path,
                    cache_dir_path,
                )
                return

        if not cache_path.exists():
            logger.debug("Cache file does not exist: %s", cache_path)
            return

        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        now = datetime.now(timezone.utc)
        ttl_delta = timedelta(seconds=cache_ttl)
        loaded = 0
        skipped_expired = 0
        skipped_legacy = 0

        for cache_key, entry in cache_data.items():
            # Detect legacy format (bare dict, no "data" wrapper)
            if not isinstance(entry, dict) or "data" not in entry:
                skipped_legacy += 1
                continue

            # Check fetched_at expiry
            fetched_at: datetime | None = None
            fetched_at_str = entry.get("fetched_at")
            if fetched_at_str:
                try:
                    fetched_at = datetime.fromisoformat(fetched_at_str)
                    if fetched_at.tzinfo is None:
                        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                    if now - fetched_at > ttl_delta:
                        skipped_expired += 1
                        continue
                except (ValueError, TypeError):
                    skipped_legacy += 1
                    continue

            try:
                weather_data = model_validate(entry["data"])
                in_memory_cache[cache_key] = weather_data
                cache_metadata[cache_key] = fetched_at or now
                loaded += 1
            except (TypeError, ValueError, KeyError, AttributeError) as e:
                logger.warning("Skipping corrupt cache entry %s: %s", cache_key, e)

        logger.info(
            "Loaded %d cache items from %s (skipped: %d expired, %d legacy)",
            loaded,
            cache_path,
            skipped_expired,
            skipped_legacy,
        )
    except (json.JSONDecodeError, IOError, PermissionError) as e:
        logger.warning("Failed to load cache from %s: %s", cache_file_path, e)


def save_cache_to_disk(
    cache_file_path: str,
    cache_dir: str,
    cache_ttl: int,
    in_memory_cache: TTLCache,
    cache_metadata: dict[str, datetime],
) -> None:
    """Persist in-memory cache to a JSON file using atomic write.

    Writes to a temporary file first, then atomically replaces the target
    to prevent corrupt files from partial writes.

    Args:
        cache_file_path: Path to the on-disk cache JSON file.
        cache_dir: Configured cache directory used for path containment checks.
        cache_ttl: Time-to-live (seconds) used to skip expired entries.
        in_memory_cache: The ``TTLCache`` to persist.
        cache_metadata: Dict mapping cache keys to their fetch timestamps.
    """
    try:
        cache_path = Path(cache_file_path).expanduser().resolve()
        # Verify the resolved path is within the configured cache directory
        _cache_dir_str = cache_dir
        if isinstance(_cache_dir_str, (str, Path)):
            cache_dir_path = Path(_cache_dir_str).resolve()
            try:
                cache_path.relative_to(cache_dir_path)
            except ValueError:
                logger.warning(
                    "Cache path %s escapes cache directory %s — rejected",
                    cache_path,
                    cache_dir_path,
                )
                return

        cache_path.parent.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        ttl = cache_ttl

        cache_data: dict[str, dict[str, Any]] = {}
        for cache_key, weather_data in in_memory_cache.items():
            fetched_at = cache_metadata.get(cache_key)
            if fetched_at is not None and (now - fetched_at).total_seconds() >= ttl:
                continue
            cache_data[cache_key] = {
                "data": weather_data.model_dump(),
                "fetched_at": (fetched_at or now).isoformat(),
            }

        # Write to temporary file first, then atomically replace
        tmp_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            os.replace(tmp_path, cache_path)
        except (IOError, PermissionError, OSError):
            try:
                tmp_path.unlink(missing_ok=True)
            except (IOError, PermissionError, OSError):
                pass
            raise

        logger.debug("Saved %d cache items to %s", len(cache_data), cache_path)
    except (IOError, PermissionError, OSError) as e:
        logger.warning("Failed to save cache to %s: %s", cache_file_path, e)
