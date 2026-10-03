from datetime import date, datetime
from typing import Dict, List, Tuple

import requests

from app.models.models import Holiday


class NagerDateProvider:
    """
    Holiday provider backed by the Nager.Date API (https://date.nager.at),
    which covers more than 100 countries.

    Only nationwide holidays are kept: regional ones (``global: false``) do not
    apply to everyone in the country.
    """

    def __init__(self, api_url: str, country: str):
        self.url_template = api_url
        self.country = country.upper()

    def get_holidays(self, year: int) -> List[Holiday]:
        """
        Fetches the public holidays of the configured country for a given year.
        """
        url = self.url_template.format(year=year, country=self.country)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching holiday data from Nager.Date for year {year}: {e}")
            return []
        except ValueError as e:
            print(f"Error decoding JSON from Nager.Date for year {year}: {e}")
            return []

        # date -> (names, type); two holidays on the same day share one row.
        by_date: Dict[date, Tuple[List[str], str]] = {}
        for entry in data:
            try:
                if not entry.get("global", True):
                    continue

                date_str = entry.get("date")
                description = entry.get("localName") or entry.get("name")
                if not date_str or not description:
                    continue

                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if parsed_date.year != year:
                    continue

                types = entry.get("types") or ["Public"]
                names, _ = by_date.setdefault(parsed_date, ([], types[0]))
                names.append(description)

            except (ValueError, AttributeError, TypeError) as e:
                print(f"Error parsing holiday entry: {entry}. Error: {e}")
                continue

        return [
            Holiday(date=day, description=" / ".join(names), type=type_)
            for day, (names, type_) in by_date.items()
        ]
