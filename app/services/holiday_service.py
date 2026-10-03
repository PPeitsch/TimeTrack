from flask import Config

from app.services.holiday_providers.argentina_api_provider import ArgentinaApiProvider
from app.services.holiday_providers.argentina_website_provider import (
    ArgentinaWebsiteProvider,
)
from app.services.holiday_providers.base import HolidayProvider
from app.services.holiday_providers.nager_date_provider import NagerDateProvider

# A mapping of provider names to their corresponding classes.
# This makes it easy to add new providers in the future.
PROVIDER_MAP = {
    "ARGENTINA_WEBSITE": ArgentinaWebsiteProvider,
    "ARGENTINA_API": ArgentinaApiProvider,
    "NAGER_DATE": NagerDateProvider,
}


def get_holiday_provider(config: Config) -> HolidayProvider:
    """
    Factory function that returns an instance of the configured holiday provider.

    Reads the provider name and settings from the provided config object.
    """
    provider_name = getattr(config, "HOLIDAY_PROVIDER", None)
    if not provider_name or provider_name.upper() not in PROVIDER_MAP:
        raise ValueError(f"Invalid or missing HOLIDAY_PROVIDER: '{provider_name}'")

    provider_class = PROVIDER_MAP[provider_name.upper()]

    # Specific initialization logic for each provider
    if provider_name.upper() == "ARGENTINA_WEBSITE":
        base_url = getattr(config, "HOLIDAYS_BASE_URL", None)
        if not base_url:
            raise ValueError("HOLIDAYS_BASE_URL is not configured.")
        return ArgentinaWebsiteProvider(base_url=base_url)

    if provider_name.upper() == "ARGENTINA_API":
        api_url = getattr(config, "HOLIDAY_API_URL", None)
        if not api_url:
            raise ValueError("HOLIDAY_API_URL is not configured.")
        return ArgentinaApiProvider(api_url=api_url)

    if provider_name.upper() == "NAGER_DATE":
        api_url = getattr(config, "NAGER_DATE_API_URL", None)
        country = getattr(config, "HOLIDAY_COUNTRY", None)
        if not api_url:
            raise ValueError("NAGER_DATE_API_URL is not configured.")
        if not country:
            raise ValueError("HOLIDAY_COUNTRY is not configured.")
        return NagerDateProvider(api_url=api_url, country=country)

    # This part would be extended for other providers
    # For now, we raise an error if the provider is in the map but has no
    # specific initialization logic here.
    raise NotImplementedError(
        f"Initialization logic for provider '{provider_name}' not implemented."
    )
