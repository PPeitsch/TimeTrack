import json
import re
from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4.element import Tag

from app.config.config import Config
from app.models.models import Holiday
from app.services.holiday_providers.argentina_api_provider import (
    ArgentinaApiProvider,
)
from app.services.holiday_providers.argentina_website_provider import (
    ArgentinaWebsiteProvider,
)
from app.services.holiday_service import PROVIDER_MAP, get_holiday_provider


class TestArgentinaWebsiteProvider:
    """
    Tests for the ArgentinaWebsiteProvider.
    """

    @pytest.fixture
    def mock_response(self):
        """Creates a mock response object for requests.get."""
        mock = MagicMock(spec=requests.Response)
        mock.raise_for_status.return_value = None
        return mock

    def test_get_holidays_success(self, mock_response):
        """
        Test successful holiday parsing from mock HTML content.
        """
        year = 2025
        mock_response.text = f"""
        <html><script>
            const holidays{year} = {{
                es: [
                    {{"date": "01/01/2025", "label": "Año Nuevo", "type": "inamovible"}},
                    {{"date": "01/05/2025", "label": "Día del Trabajador", "type": "inamovible"}}
                ],
            }};
        </script></html>
        """
        provider = ArgentinaWebsiteProvider(base_url="http://fake-url.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(year)
            assert len(holidays) == 2
            assert holidays[0].description == "Año Nuevo"

    def test_get_holidays_with_malformed_entry(self, mock_response):
        """
        Test that a single malformed holiday entry is skipped.
        """
        year = 2025
        mock_response.text = f"""
        <html><script>
            const holidays{year} = {{
                es: [
                    {{"date": "01/01/2025", "label": "Año Nuevo", "type": "inamovible"}},
                    {{"date": "invalid-date", "label": "Invalid", "type": "invalido"}}
                ],
            }};
        </script></html>
        """
        provider = ArgentinaWebsiteProvider(base_url="http://fake-url.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(year)
            assert len(holidays) == 1
            assert holidays[0].description == "Año Nuevo"

    def test_get_holidays_network_error(self):
        """
        Test that network errors are handled gracefully.
        """
        provider = ArgentinaWebsiteProvider(base_url="http://fake-url.com/{year}")
        with patch(
            "requests.get", side_effect=requests.RequestException("Network Error")
        ):
            holidays = provider.get_holidays(2025)
            assert holidays == []

    def test_get_holidays_no_script_found(self, mock_response):
        """
        Test behavior when the specific holiday script tag is not found.
        """
        mock_response.text = "<html><body>No data here</body></html>"
        provider = ArgentinaWebsiteProvider(base_url="http://fake-url.com/{year}")
        with patch("requests.get", return_value=mock_response):
            holidays = provider.get_holidays(2025)
            assert holidays == []

    def test_parse_holidays_from_script_handles_trailing_comma(self):
        """
        Test that JSON with a trailing comma is handled correctly.
        """
        script_content = """
        es: [{"date": "01/01/2025", "label": "Año Nuevo", "type": "inamovible"},],
        """
        provider = ArgentinaWebsiteProvider(base_url="")

        holidays = provider._parse_holidays_from_script(script_content)
        assert len(holidays) == 1
        assert holidays[0]["label"] == "Año Nuevo"

    def test_parse_holidays_from_script_raises_decode_error(self):
        """
        Test the except block for JSONDecodeError.
        """
        script_content = 'es: [{"date": "01/01/2025", "label": "Broken "JSON" here"}],'
        provider = ArgentinaWebsiteProvider(base_url="")

        holidays = provider._parse_holidays_from_script(script_content)
        assert holidays == []

    def test_parse_holidays_from_script_no_match(self):
        """
        Test the 'if not match' path in _parse_holidays_from_script.
        """
        # This content lacks the 'es:' key, so the regex will not match.
        script_content = "const holidays2025 = { en: [] };"
        provider = ArgentinaWebsiteProvider(base_url="")
        holidays = provider._parse_holidays_from_script(script_content)
        assert holidays == []


class TestHolidayService:
    """
    Tests for the holiday provider factory service.
    """

    class MockConfig(Config):
        HOLIDAY_PROVIDER = "ARGENTINA_WEBSITE"
        HOLIDAYS_BASE_URL = "http://fake-url.com/{year}"
        HOLIDAY_API_URL = "http://fake-api.com/{year}"

    def test_get_holiday_provider_success(self):
        """
        Test that the factory returns the correct provider instance.
        """
        provider = get_holiday_provider(TestHolidayService.MockConfig)
        assert isinstance(provider, ArgentinaWebsiteProvider)

    def test_get_holiday_provider_invalid_provider(self):
        """
        Test that a ValueError is raised for an unknown provider.
        """

        class InvalidConfig(TestHolidayService.MockConfig):
            HOLIDAY_PROVIDER = "INVALID_PROVIDER"

        with pytest.raises(ValueError, match="Invalid or missing HOLIDAY_PROVIDER"):
            get_holiday_provider(InvalidConfig)

    def test_get_holiday_provider_no_provider_configured(self):
        """
        Test that a ValueError is raised if HOLIDAY_PROVIDER is not set.
        """

        class NoProviderConfig(TestHolidayService.MockConfig):
            HOLIDAY_PROVIDER = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="Invalid or missing HOLIDAY_PROVIDER"):
            get_holiday_provider(NoProviderConfig)

    def test_get_holiday_provider_missing_url(self):
        """
        Test that a ValueError is raised if the URL is missing for the provider.
        """

        class MissingUrlConfig(TestHolidayService.MockConfig):
            HOLIDAYS_BASE_URL = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="HOLIDAYS_BASE_URL is not configured"):
            get_holiday_provider(MissingUrlConfig)

    def test_get_holiday_provider_api_success(self):
        """
        Test that the factory returns the correct API provider instance.
        """

        class ApiConfig(TestHolidayService.MockConfig):
            HOLIDAY_PROVIDER = "ARGENTINA_API"

        provider = get_holiday_provider(ApiConfig)
        assert isinstance(provider, ArgentinaApiProvider)

    def test_get_holiday_provider_api_missing_url(self):
        """
        Test that a ValueError is raised if the API URL is missing.
        """

        class MissingApiUrlConfig(TestHolidayService.MockConfig):
            HOLIDAY_PROVIDER = "ARGENTINA_API"
            HOLIDAY_API_URL = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="HOLIDAY_API_URL is not configured"):
            get_holiday_provider(MissingApiUrlConfig)

    def test_get_holiday_provider_not_implemented(self):
        """
        Test that a NotImplementedError is raised for a provider without init logic.
        """

        class NewDummyProvider:
            pass

        original_map = PROVIDER_MAP.copy()
        PROVIDER_MAP["NEW_DUMMY_PROVIDER"] = NewDummyProvider  # type: ignore[assignment]

        class DummyProviderConfig(TestHolidayService.MockConfig):
            HOLIDAY_PROVIDER = "NEW_DUMMY_PROVIDER"

        with pytest.raises(NotImplementedError):
            get_holiday_provider(DummyProviderConfig)

        PROVIDER_MAP.clear()
        PROVIDER_MAP.update(original_map)
