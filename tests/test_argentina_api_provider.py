from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models.models import Holiday
from app.services.holiday_providers.argentina_api_provider import ArgentinaApiProvider


class TestArgentinaApiProvider:
    """
    Tests for the ArgentinaApiProvider.
    """

    @pytest.fixture
    def mock_response(self):
        """Creates a mock response object."""
        mock = MagicMock(spec=requests.Response)
        mock.raise_for_status.return_value = None
        return mock

    def test_get_holidays_success(self, mock_response):
        """
        Test successful holiday parsing from API JSON response.
        """
        year = 2025
        mock_response.json.return_value = [
            {"fecha": "2025-01-01", "nombre": "Año Nuevo", "tipo": "inamovible"},
            {
                "fecha": "2025-05-01",
                "nombre": "Día del Trabajador",
                "tipo": "inamovible",
            },
        ]
        provider = ArgentinaApiProvider(api_url="http://fake-api.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(year)
            assert len(holidays) == 2
            assert holidays[0].description == "Año Nuevo"
            assert holidays[0].date.year == 2025

    def test_get_holidays_filter_by_year(self, mock_response):
        """
        Test that holidays from other years are filtered out.
        """
        year = 2025
        mock_response.json.return_value = [
            {"fecha": "2025-01-01", "nombre": "Correct Year", "tipo": "inamovible"},
            {"fecha": "2024-12-31", "nombre": "Wrong Year", "tipo": "inamovible"},
        ]
        provider = ArgentinaApiProvider(api_url="http://fake-api.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(year)
            assert len(holidays) == 1
            assert holidays[0].description == "Correct Year"

    def test_get_holidays_malformed_entry(self, mock_response):
        """
        Test that malformed entries are skipped.
        """
        year = 2025
        mock_response.json.return_value = [
            {"fecha": "2025-01-01", "nombre": "Good", "tipo": "inamovible"},
            {"fecha": "", "nombre": "Bad Date", "tipo": "inamovible"},
            {"fecha": "2025-01-02", "nombre": "", "tipo": "inamovible"},
        ]
        provider = ArgentinaApiProvider(api_url="http://fake-api.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(year)
            assert len(holidays) == 1
            assert holidays[0].description == "Good"

    def test_get_holidays_network_error(self):
        """
        Test that network errors are handled gracefully.
        """
        provider = ArgentinaApiProvider(api_url="http://fake-api.com/{year}")
        with patch(
            "requests.get", side_effect=requests.RequestException("Network Error")
        ):
            holidays = provider.get_holidays(2025)
            assert holidays == []

    def test_get_holidays_json_error(self, mock_response):
        """
        Test that JSON decoding errors are handled gracefully.
        """
        mock_response.json = MagicMock(side_effect=ValueError("Invalid JSON"))
        provider = ArgentinaApiProvider(api_url="http://fake-api.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(2025)
            assert holidays == []
