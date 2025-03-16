from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.models import Holiday


def scrape_holidays(year: int, db: Session) -> List[Holiday]:
    """Scrape Argentine holidays from official website and store them in the database."""
    url = f"https://www.argentina.gob.ar/interior/feriados-nacionales-{year}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    holidays = []

    # Usamos un enfoque más seguro que evita confusiones de tipo
    tables = soup.select("table")

    if tables and len(tables) > 0:
        # Procesamos la primera tabla encontrada
        rows = tables[0].select("tr")

        # Saltamos la primera fila (encabezados)
        for row in rows[1:]:
            cols = row.select("td")
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
