from typing import List, Protocol

from app.models.models import Holiday


class HolidayProvider(Protocol):
    """
    Defines the interface for a holiday provider.

    Any class that provides holiday data must implement the methods
    defined in this protocol.
    """

    def get_holidays(self, year: int) -> List[Holiday]:
        """
        Fetches holidays for a given year.

        Args:
            year: The year for which to fetch holidays.

        Returns:
            A list of Holiday model instances.
        """
