from flask import Config

from app.services.holiday_providers.argentina_website_provider import (
    ArgentinaWebsiteProvider,
)
from app.services.holiday_providers.base import HolidayProvider

# A mapping of provider names to their corresponding classes.
# This makes it easy to add new providers in the future.
PROVIDER_MAP = {"ARGENTINA_WEBSITE": ArgentinaWebsiteProvider}


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
        return provider_class(base_url=base_url)

    # This part would be extended for other providers
    # For now, we raise an error if the provider is in the map but has no
    # specific initialization logic here.
    raise NotImplementedError(
        f"Initialization logic for provider '{provider_name}' not implemented."
    )
