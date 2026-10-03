import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.holiday_providers.nager_date_provider import NagerDateProvider
from app.services.holiday_service import get_holiday_provider

URL = "http://fake-api.com/{year}/{country}"


def _response(payload):
    mock = MagicMock(spec=requests.Response)
    mock.raise_for_status.return_value = None
    mock.json.return_value = payload
    return mock


def _holiday(date, local_name, name="", is_global=True, types=None):
    return {
        "date": date,
        "localName": local_name,
        "name": name or local_name,
        "global": is_global,
        "types": types or ["Public"],
    }


class TestNagerDateProvider:
    def test_builds_url_with_year_and_country(self):
        provider = NagerDateProvider(api_url=URL, country="es")
        with patch("requests.get", return_value=_response([])) as get:
            provider.get_holidays(2026)
        get.assert_called_once_with("http://fake-api.com/2026/ES", timeout=10)

    def test_parses_nationwide_holidays(self):
        payload = [
            _holiday("2026-01-01", "Año Nuevo", "New Year's Day"),
            _holiday("2026-12-25", "Navidad", "Christmas Day"),
        ]
        provider = NagerDateProvider(api_url=URL, country="ES")
        with patch("requests.get", return_value=_response(payload)):
            holidays = provider.get_holidays(2026)

        assert [h.description for h in holidays] == ["Año Nuevo", "Navidad"]
        assert holidays[0].date.isoformat() == "2026-01-01"
        assert holidays[0].type == "Public"

    def test_skips_regional_holidays(self):
        payload = [
            _holiday("2026-01-01", "Año Nuevo"),
            _holiday("2026-03-19", "San José", is_global=False),
        ]
        provider = NagerDateProvider(api_url=URL, country="ES")
        with patch("requests.get", return_value=_response(payload)):
            holidays = provider.get_holidays(2026)

        assert [h.description for h in holidays] == ["Año Nuevo"]

    def test_merges_holidays_on_the_same_day(self):
        payload = [
            _holiday("2026-04-02", "Malvinas"),
            _holiday("2026-04-02", "Jueves Santo"),
        ]
        provider = NagerDateProvider(api_url=URL, country="AR")
        with patch("requests.get", return_value=_response(payload)):
            holidays = provider.get_holidays(2026)

        assert len(holidays) == 1
        assert holidays[0].description == "Malvinas / Jueves Santo"

    def test_skips_malformed_and_other_years(self):
        payload = [
            _holiday("2026-01-01", "Good"),
            _holiday("", "No date"),
            _holiday("2026-13-01", "Bad date"),
            _holiday("2025-12-31", "Last year"),
        ]
        provider = NagerDateProvider(api_url=URL, country="ES")
        with patch("requests.get", return_value=_response(payload)):
            holidays = provider.get_holidays(2026)

        assert [h.description for h in holidays] == ["Good"]

    def test_network_error_returns_empty_list(self):
        provider = NagerDateProvider(api_url=URL, country="ES")
        with patch("requests.get", side_effect=requests.RequestException("down")):
            assert provider.get_holidays(2026) == []

    def test_unknown_country_returns_empty_list(self):
        response = _response(None)
        response.raise_for_status.side_effect = requests.HTTPError("404")
        provider = NagerDateProvider(api_url=URL, country="XX")
        with patch("requests.get", return_value=response):
            assert provider.get_holidays(2026) == []


class TestNagerDateFactory:
    def test_factory_returns_configured_provider(self):
        config = SimpleNamespace(
            HOLIDAY_PROVIDER="NAGER_DATE", NAGER_DATE_API_URL=URL, HOLIDAY_COUNTRY="de"
        )
        provider = get_holiday_provider(config)  # type: ignore[arg-type]
        assert isinstance(provider, NagerDateProvider)
        assert provider.country == "DE"

    def test_factory_requires_country(self):
        config = SimpleNamespace(
            HOLIDAY_PROVIDER="NAGER_DATE", NAGER_DATE_API_URL=URL, HOLIDAY_COUNTRY=""
        )
        with pytest.raises(ValueError, match="HOLIDAY_COUNTRY"):
            get_holiday_provider(config)  # type: ignore[arg-type]


class TestDefaultProvider:
    @pytest.fixture
    def load_config(self, monkeypatch):
        import app.config.config as config_module

        def load(**env):
            for key in ("HOLIDAY_COUNTRY", "HOLIDAY_PROVIDER"):
                monkeypatch.delenv(key, raising=False)
            for key, value in env.items():
                monkeypatch.setenv(key, value)
            # Keep the developer's .env out of the way.
            with patch("dotenv.load_dotenv"):
                return importlib.reload(config_module).Config

        yield load
        importlib.reload(config_module)

    def test_argentina_by_default(self, load_config):
        config = load_config()
        assert config.HOLIDAY_COUNTRY == "AR"
        assert config.HOLIDAY_PROVIDER == "ARGENTINA_API"

    def test_other_countries_use_nager_date(self, load_config):
        config = load_config(HOLIDAY_COUNTRY="es")
        assert config.HOLIDAY_COUNTRY == "ES"
        assert config.HOLIDAY_PROVIDER == "NAGER_DATE"

    def test_explicit_provider_wins(self, load_config):
        config = load_config(HOLIDAY_COUNTRY="AR", HOLIDAY_PROVIDER="NAGER_DATE")
        assert config.HOLIDAY_PROVIDER == "NAGER_DATE"
