import re
from datetime import datetime
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from app.models.models import Holiday


class ArgentinaWebsiteProvider:
    """
    Holiday provider that scrapes holidays from the official Argentine government website.
    This provider parses an embedded JSON object from a <script> tag.
    """

    def __init__(self, base_url: str):
        self.url_template = base_url

    def _parse_holidays_from_script(self, script_content: str) -> List[Dict[str, Any]]:
        """
        Extracts Spanish holiday data from a string containing a JavaScript object.
        """
        # This regex now specifically looks for the 'es: [...]' array.
        object_pattern = re.compile(r"es:\s*(\[.*?\]),", re.DOTALL)
        match = object_pattern.search(script_content)

        if not match:
            return []

        # group(1) contains the list content, e.g., '[{"date": ...}]'
        json_list_text = match.group(1)

        try:
            # Replace single quotes with double quotes for valid JSON
            # and remove trailing commas before brackets/braces
            valid_json_text = json_list_text.replace("'", '"')
            valid_json_text = re.sub(r",\s*([\]}])", r"\1", valid_json_text)
            return __import__("json").loads(valid_json_text)
        except __import__("json").JSONDecodeError as e:
            print(f"Failed to decode JSON from script: {e}")
            return []

    def get_holidays(self, year: int) -> List[Holiday]:
        """
        Scrapes Argentine holidays for a given year and returns them as Holiday objects.
        """
        url = self.url_template.format(year=year)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching holiday data for year {year}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        holidays_list = []
        script_tag = soup.find(
            "script", string=re.compile(rf"const holidays{year}\s*=")
        )

        if script_tag and script_tag.string:
            holidays_list = self._parse_holidays_from_script(script_tag.string)

        if not holidays_list:
            return []

        holidays: List[Holiday] = []
        for holiday_info in holidays_list:
            try:
                date_str = holiday_info["date"]
                description = holiday_info["label"]
                type_map = {
                    "inamovible": "Inamovible",
                    "trasladable": "Trasladable",
                    "turistico": "Fines Turísticos",
                    "no_laborable": "No Laborable",
                }
                type_ = type_map.get(holiday_info["type"], "Otro")

                parsed_date = datetime.strptime(date_str, "%d/%m/%Y").date()

                if parsed_date.year == year:
                    holiday = Holiday(
                        date=parsed_date, description=description, type=type_
                    )
                    holidays.append(holiday)
            except (ValueError, KeyError, TypeError) as e:
                print(f"Could not parse holiday entry: {holiday_info}. Error: {e}")
                continue

        return holidays
