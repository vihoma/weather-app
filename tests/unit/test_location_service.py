"""Unit tests for location service functionality."""

import pytest
from unittest.mock import Mock, patch
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError
from weather_app.services.location_service import LocationService
from weather_app.exceptions import InvalidLocationError, NetworkError, GeocodingError


class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_format_coordinates_valid(self):
        """Test coordinate format validation with valid coordinates."""
        service = LocationService()
        
        valid_coordinates = [
            "51.5074,-0.1278",
            "-33.8688,151.2093",
            "40.7128,-74.0060",
            "0.0,0.0",
            "90.0,180.0",
            "-90.0,-180.0",
        ]
        
        for coord in valid_coordinates:
            assert service.validate_location_format(coord) is True

    def test_validate_location_format_coordinates_invalid(self):
        """Test coordinate format validation with invalid coordinates."""
        service = LocationService()
        
        invalid_coordinates = [
            "91.0,0.0",  # Latitude too high
            "-91.0,0.0",  # Latitude too low
            "0.0,181.0",  # Longitude too high
            "0.0,-181.0",  # Longitude too low
            "invalid,format",
            "51.5074",  # Missing longitude
            "-0.1278",  # Missing latitude
            "51.5074,-0.1278,extra",  # Too many parts
        ]
        
        for coord in invalid_coordinates:
            assert service.validate_location_format(coord) is False

    def test_validate_location_format_city_country_valid(self):
        """Test city,country format validation with valid inputs."""
        service = LocationService()
        
        valid_locations = [
            "London,GB",
            "New York,US",
            "Paris,FR",
            "Tokyo,JP",
            "Sydney,AU",
        ]
        
        for location in valid_locations:
            assert service.validate_location_format(location) is True

    def test_validate_location_format_city_country_invalid(self):
        """Test city,country format validation with invalid inputs."""
        service = LocationService()
        
        invalid_locations = [
            "London",  # Missing country
            "London,GBR",  # Country code too long
            "London,G",  # Country code too short
            "London,GB,extra",  # Too many parts
            ",GB",  # Missing city
            "London,",  # Missing country
            "  ,GB",  # Empty city
            "London,  ",  # Empty country
        ]
        
        for location in invalid_locations:
            assert service.validate_location_format(location) is False

    def test_normalize_location_valid(self):
        """Test location normalization with valid inputs."""
        service = LocationService()
        
        test_cases = [
            ("London,GB", "London,GB"),
            ("  London,GB  ", "London,GB"),
            ("51.5074,-0.1278", "51.5074,-0.1278"),
            ("  51.5074,-0.1278  ", "51.5074,-0.1278"),
        ]
        
        for input_location, expected_output in test_cases:
            result = service.normalize_location(input_location)
            assert result == expected_output

    def test_normalize_location_empty(self):
        """Test location normalization with empty input."""
        service = LocationService()
        
        with pytest.raises(InvalidLocationError, match="Location cannot be empty"):
            service.normalize_location("")
        
        with pytest.raises(InvalidLocationError, match="Location cannot be empty"):
            service.normalize_location("   ")

    def test_normalize_location_invalid_format(self):
        """Test location normalization with invalid format."""
        service = LocationService()
        
        invalid_locations = [
            "InvalidFormat",
            "London",
            "51.5074",
            "London,GBR",
        ]
        
        for location in invalid_locations:
            with pytest.raises(InvalidLocationError):
                service.normalize_location(location)

    def test_sanitize_location_for_logging(self):
        """Test location sanitization for logging."""
        service = LocationService()
        
        test_cases = [
            ("London,GB", "London,GB"),
            ("", "[empty]"),
            ("  ", "[empty]"),
            ("London\n,GB", "London\\n,GB"),
            ("London\r,GB", "London\\r,GB"),
            ("London\t,GB", "London\\t,GB"),
        ]
        
        for input_location, expected_output in test_cases:
            result = service._sanitize_location_for_logging(input_location)
            print(f"Input: {repr(input_location)}, Expected: {repr(expected_output)}, Got: {repr(result)}")
            assert result == expected_output

    def test_sanitize_location_for_logging_truncation(self):
        """Test location sanitization truncates long strings."""
        service = LocationService()
        
        # Create a very long location string
        long_location = "A" * 150
        result = service._sanitize_location_for_logging(long_location)
        
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_coordinates(self, mock_nominatim):
        """Test geocoding with coordinate input."""
        service = LocationService()
        
        result = service.geocode_location("51.5074,-0.1278")
        
        assert result == (51.5074, -0.1278)
        # Should not call external geocoder for coordinates
        mock_nominatim.return_value.geocode.assert_not_called()

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_city_country_success(self, mock_nominatim):
        """Test successful geocoding with city,country format."""
        service = LocationService()
        
        # Mock successful geocoding
        mock_location = Mock()
        mock_location.latitude = 51.5074
        mock_location.longitude = -0.1278
        mock_nominatim.return_value.geocode.return_value = mock_location
        
        result = service.geocode_location("London,GB")
        
        assert result == (51.5074, -0.1278)
        mock_nominatim.return_value.geocode.assert_called_once_with("London,GB", exactly_one=True)

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_city_country_not_found(self, mock_nominatim):
        """Test geocoding when location is not found."""
        service = LocationService()
        
        # Mock location not found
        mock_nominatim.return_value.geocode.return_value = None
        
        result = service.geocode_location("NonexistentCity,XX")
        
        assert result is None
        mock_nominatim.return_value.geocode.assert_called_once_with("NonexistentCity,XX", exactly_one=True)

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_timeout(self, mock_nominatim):
        """Test geocoding timeout handling."""
        service = LocationService()
        
        # Mock timeout exception
        mock_nominatim.return_value.geocode.side_effect = GeocoderTimedOut("Timeout")
        
        with pytest.raises(NetworkError, match="Geocoding request timed out"):
            service.geocode_location("London,GB")

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_service_unavailable(self, mock_nominatim):
        """Test geocoding service unavailable handling."""
        service = LocationService()
        
        # Mock service unavailable
        mock_nominatim.return_value.geocode.side_effect = GeocoderUnavailable("Service unavailable")
        
        with pytest.raises(NetworkError, match="Geocoding service unavailable"):
            service.geocode_location("London,GB")

    @patch("weather_app.services.location_service.Nominatim")
    def test_geocode_location_unexpected_error(self, mock_nominatim):
        """Test unexpected error handling during geocoding."""
        service = LocationService()
        
        # Mock unexpected error
        mock_nominatim.return_value.geocode.side_effect = Exception("Unexpected error")
        
        with pytest.raises(GeocodingError, match="Unexpected error during geocoding"):
            service.geocode_location("London,GB")

    @patch("weather_app.services.location_service.Nominatim")
    def test_get_location_display_name_success(self, mock_nominatim):
        """Test successful reverse geocoding."""
        service = LocationService()
        
        # Mock successful reverse geocoding
        mock_location = Mock()
        mock_location.address = "London, UK"
        mock_nominatim.return_value.reverse.return_value = mock_location
        
        result = service.get_location_display_name(51.5074, -0.1278)
        
        assert result == "London, UK"
        mock_nominatim.return_value.reverse.assert_called_once_with((51.5074, -0.1278), exactly_one=True)

    @patch("weather_app.services.location_service.Nominatim")
    def test_get_location_display_name_not_found(self, mock_nominatim):
        """Test reverse geocoding when location is not found."""
        service = LocationService()
        
        # Mock location not found
        mock_nominatim.return_value.reverse.return_value = None
        
        result = service.get_location_display_name(0.0, 0.0)
        
        assert result is None

    @patch("weather_app.services.location_service.Nominatim")
    def test_get_location_display_name_timeout(self, mock_nominatim):
        """Test reverse geocoding timeout handling."""
        service = LocationService()
        
        # Mock timeout exception
        mock_nominatim.return_value.reverse.side_effect = GeocoderTimedOut("Timeout")
        
        result = service.get_location_display_name(51.5074, -0.1278)
        
        assert result is None

    @patch("weather_app.services.location_service.Nominatim")
    def test_get_location_display_name_service_unavailable(self, mock_nominatim):
        """Test reverse geocoding service unavailable handling."""
        service = LocationService()
        
        # Mock service unavailable
        mock_nominatim.return_value.reverse.side_effect = GeocoderUnavailable("Service unavailable")
        
        result = service.get_location_display_name(51.5074, -0.1278)
        
        assert result is None

    @patch("weather_app.services.location_service.Nominatim")
    def test_get_location_display_name_unexpected_error(self, mock_nominatim):
        """Test unexpected error handling during reverse geocoding."""
        service = LocationService()
        
        # Mock unexpected error
        mock_nominatim.return_value.reverse.side_effect = Exception("Unexpected error")
        
        with pytest.raises(GeocodingError, match="Unexpected error during reverse geocoding"):
            service.get_location_display_name(51.5074, -0.1278)