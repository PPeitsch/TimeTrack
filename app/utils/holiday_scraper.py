from datetime import datetime
from typing import List, Optional, cast

import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import Session

from app.models.models import Holiday


def scrape_holidays(year: int, db: Session) -> List[Holiday]:
    """Scrape Argentine holidays from official website and store them in the database."""
    url = f"https://www.argentina.gob.ar/interior/feriados-nacionales-{year}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    holidays = []
    table_elem = soup.find("table")

    if table_elem is not None:
        # Asegurarnos de que table_elem es un Tag antes de usar find_all
        table = cast(Tag, table_elem)

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                date_str = cols[0].text.strip()
                description = cols[1].text.strip()
                type_ = cols[2].text.strip()

                date = datetime.strptime(f"{date_str}/{year}", "%d/%m/%Y").date()

                holiday = Holiday(date=date, description=description, type=type_)
                holidays.append(holiday)

    db.bulk_save_objects(holidays)
    db.commit()

    return holidays
