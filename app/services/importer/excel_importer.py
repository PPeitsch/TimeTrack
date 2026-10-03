import io
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from openpyxl import load_workbook  # type: ignore

from app.services.importer.columns import column_kind
from app.services.importer.protocol import (
    ImporterProtocol,
    ImportResult,
    TimeEntryRecord,
)
from app.utils.validators import validate_date, validate_time_format


class ExcelImporter(ImporterProtocol):
    """Reads .xlsx files: the first row holds the headers, one day per row."""

    def parse(self, file_content: Any) -> ImportResult:
        records: List[TimeEntryRecord] = []
        errors: List[str] = []

        try:
            workbook = load_workbook(
                io.BytesIO(file_content), read_only=True, data_only=True
            )
            rows = workbook.active.iter_rows(values_only=True)
            headers = next(rows, ())

            # Map each kind of column to its index (first match wins).
            col_map: Dict[str, int] = {}
            for idx, header in enumerate(headers):
                kind = column_kind(str(header)) if header is not None else None
                if kind and kind not in col_map:
                    col_map[kind] = idx

            if "date" not in col_map:
                errors.append("Could not find 'Fecha' or 'Date' column")
                return ImportResult([], 0, 0, errors)

            for row in rows:
                date_val = _cell(row, col_map.get("date"))
                if _is_empty(date_val):
                    continue

                if isinstance(date_val, (datetime, date)):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val).strip()

                entry_str = self._format_time(_cell(row, col_map.get("entry")))
                exit_str = self._format_time(_cell(row, col_map.get("exit")))
                obs_val = _cell(row, col_map.get("obs"))

                # Logic for validating
                is_valid = True
                error_msg = None

                if not validate_date(date_str):
                    is_valid = False
                    error_msg = f"Invalid date format: {date_str}"
                elif entry_str and not validate_time_format(entry_str):
                    is_valid = False
                    error_msg = f"Invalid entry time: {entry_str}"
                elif exit_str and not validate_time_format(exit_str):
                    is_valid = False
                    error_msg = f"Invalid exit time: {exit_str}"

                records.append(
                    TimeEntryRecord(
                        date=date_str,
                        entry_time=entry_str,
                        exit_time=exit_str,
                        observation=None if _is_empty(obs_val) else str(obs_val),
                        is_valid=is_valid,
                        error_message=error_msg,
                    )
                )

            workbook.close()

        except Exception as e:
            errors.append(f"Error parsing Excel: {str(e)}")

        valid_records = sum(1 for r in records if r.is_valid)
        return ImportResult(records, len(records), valid_records, errors)

    def _format_time(self, val: Any) -> Optional[str]:
        if _is_empty(val):
            return None

        if isinstance(val, (datetime, time)):
            return val.strftime("%H:%M")

        return str(val).strip()


def _cell(row: tuple, idx: Optional[int]) -> Any:
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _is_empty(val: Any) -> bool:
    return val is None or (isinstance(val, str) and not val.strip())
