from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup

from app.models.models import Holiday


class ArgentinaWebsiteProvider:
    """
    Holiday provider that scrapes holidays from the official Argentine government website.
    """

    def __init__(self, base_url: str):
        self.url_template = base_url

    def get_holidays(self, year: int) -> List[Holiday]:
        """
        Scrapes Argentine holidays for a given year and returns them as Holiday objects.
        """
        url = self.url_template.format(year=year)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching holiday data for year {year}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        holidays: List[Holiday] = []
        tables = soup.select("table")

        if not tables:
            return []

        rows = tables[0].select("tr")
        # Skip the header row (index 0)
        for row in rows[1:]:
            cols = row.select("td")
            if len(cols) >= 3:
                try:
                    date_str = cols[0].text.strip()
                    description = cols[1].text.strip()
                    type_ = cols[2].text.strip()

                    # The date on the website is in "DD/MM" format
                    parsed_date = datetime.strptime(
                        f"{date_str}/{year}", "%d/%m/%Y"
                    ).date()

                    holiday = Holiday(
                        date=parsed_date, description=description, type=type_
                    )
                    holidays.append(holiday)
                except (ValueError, IndexError) as e:
                    # Log error for a specific row but continue processing others
                    print(f"Could not parse row for year {year}: {cols}. Error: {e}")
                    continue
        return holidays
