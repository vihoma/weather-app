"""Location validation and geocoding services."""

import logging
import re
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderServiceError
from ..exceptions import InvalidLocationError, NetworkError

logger = logging.getLogger(__name__)


class LocationService:
    """Handles location validation and geocoding operations."""

    def __init__(self):
        """Initialize the location service with geocoder."""
        self.geolocator = Nominatim(user_agent="weather_app")

    def validate_location_format(self, location: str) -> bool:
        """
        Validate the basic format of a location string.

        Args:
            location: Location string in format "City,CC" or coordinates

        Returns:
            bool: True if format is valid
        """
        # Check for coordinate format (latitude,longitude)
        if self._is_coordinate_format(location):
            return True

        # Check for city,country format
        if self._is_city_country_format(location):
            return True

        return False

    def _is_coordinate_format(self, location: str) -> bool:
        """Check if location is in coordinate format."""
        coord_pattern = r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
        return bool(re.match(coord_pattern, location.strip()))

    def _is_city_country_format(self, location: str) -> bool:
        """Check if location is in city,country format."""
        parts = location.strip().split(",")
        if len(parts) != 2:
            return False

        city, country = parts
        return bool(city.strip() and country.strip() and len(country.strip()) == 2)

    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a location string to coordinates.

        Args:
            location: Location string to geocode

        Returns:
            Optional[Tuple[float, float]]: (latitude, longitude) or None
        """
        try:
            logger.debug("Geocoding location: %s", location)

            if self._is_coordinate_format(location):
                # Already coordinates, just parse them
                lat, lon = map(float, location.split(","))
                return (lat, lon)

            # Geocode city,country format
            location_obj = self.geolocator.geocode(location, exactly_one=True)

            if location_obj:
                logger.debug(
                    "Geocoded %s to coordinates: (%s, %s)",
                    location,
                    location_obj.latitude,
                    location_obj.longitude,
                )
                return (location_obj.latitude, location_obj.longitude)

            logger.warning("Could not geocode location: %s", location)
            return None

        except (GeocoderUnavailable, GeocoderServiceError) as e:
            logger.warning("Geocoding service unavailable: %s", e)
            raise NetworkError(
                "Geocoding service unavailable. Please check your internet connection."
            ) from e
        except Exception as e:
            logger.error("Unexpected error during geocoding: %s", e, exc_info=True)
            return None

    def normalize_location(self, location: str) -> str:
        """
        Normalize location input and validate format.

        Args:
            location: Raw location input

        Returns:
            str: Normalized location string

        Raises:
            InvalidLocationError: If location format is invalid
        """
        location = location.strip()

        if not location:
            raise InvalidLocationError("Location cannot be empty")

        if not self.validate_location_format(location):
            raise InvalidLocationError(
                "Invalid location format. Please use:"
                "\n- 'City,CC' format (e.g., 'London,GB')"
                "\n- Coordinates 'lat,lon' (e.g., '51.5074,-0.1278')"
            )

        return location

    def get_location_display_name(
        self, latitude: float, longitude: float
    ) -> Optional[str]:
        """
        Reverse geocode coordinates to get display name.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Optional[str]: Display name or None
        """
        try:
            location = self.geolocator.reverse((latitude, longitude), exactly_one=True)
            return location.address if location else None
        except (GeocoderUnavailable, GeocoderServiceError):
            logger.warning("Reverse geocoding service unavailable")
            return None
        except Exception as e:
            logger.error("Error in reverse geocoding: %s", e, exc_info=True)
            return None
