from flask import current_app

from app.services.holiday_providers.argentina_website_provider import (
    ArgentinaWebsiteProvider,
)
from app.services.holiday_providers.base import HolidayProvider

# A mapping of provider names to their corresponding classes.
# This makes it easy to add new providers in the future.
PROVIDER_MAP = {"ARGENTINA_WEBSITE": ArgentinaWebsiteProvider}


def get_holiday_provider() -> HolidayProvider:
    """
    Factory function that returns an instance of the configured holiday provider.

    Reads the provider name and relevant settings from the Flask app config
    and instantiates the appropriate provider class.

    Raises:
        ValueError: If the configured provider is not found in PROVIDER_MAP.

    Returns:
        An instance of a class that implements the HolidayProvider protocol.
    """
    provider_name = current_app.config.get("HOLIDAY_PROVIDER")
    if not provider_name or provider_name.upper() not in PROVIDER_MAP:
        raise ValueError(f"Invalid or missing HOLIDAY_PROVIDER: '{provider_name}'")

    provider_class = PROVIDER_MAP[provider_name.upper()]

    # Specific initialization logic for each provider
    if provider_name.upper() == "ARGENTINA_WEBSITE":
        base_url = current_app.config.get("HOLIDAYS_BASE_URL")
        if not base_url:
            raise ValueError("HOLIDAYS_BASE_URL is not configured.")
        return provider_class(base_url=base_url)

    # This part would be extended for other providers
    # For now, we raise an error if the provider is in the map but has no
    # specific initialization logic here.
    raise NotImplementedError(
        f"Initialization logic for provider '{provider_name}' not implemented."
    )
