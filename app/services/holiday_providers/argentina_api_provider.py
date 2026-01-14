from datetime import datetime
from typing import List

import requests

from app.models.models import Holiday


class ArgentinaApiProvider:
    """
    Holiday provider that fetches holidays from the ArgentinaDatos API.
    """

    def __init__(self, api_url: str):
        self.url_template = api_url

    def get_holidays(self, year: int) -> List[Holiday]:
        """
        Fetches holidays for a given year from the API and returns them as Holiday objects.
        """
        url = self.url_template.format(year=year)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching holiday data from API for year {year}: {e}")
            return []
        except ValueError as e:
            print(f"Error decoding JSON from API for year {year}: {e}")
            return []

        holidays: List[Holiday] = []
        for entry in data:
            try:
                date_str = entry.get("fecha")
                description = entry.get("nombre")
                type_raw = entry.get("tipo")

                if not date_str or not description:
                    continue

                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Filter by year just in case
                if parsed_date.year != year:
                    continue

                type_map = {
                    "inamovible": "Inamovible",
                    "trasladable": "Trasladable",
                    "puente": "Fines Turísticos",
                    "nolaborable": "No Laborable",
                }
                type_ = type_map.get(type_raw, "Otro")

                holiday = Holiday(date=parsed_date, description=description, type=type_)
                holidays.append(holiday)

            except (ValueError, AttributeError) as e:
                print(f"Error parsing holiday entry: {entry}. Error: {e}")
                continue

        return holidays
