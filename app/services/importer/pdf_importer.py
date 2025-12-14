import io
import re
from typing import Any, List, Optional

import pdfplumber

from app.services.importer.protocol import (
    ImporterProtocol,
    ImportResult,
    TimeEntryRecord,
)
from app.utils.validators import validate_date, validate_time_format


class PDFImporter(ImporterProtocol):
    def parse(self, file_content: Any) -> ImportResult:
        records: List[TimeEntryRecord] = []
        errors: List[str] = []

        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        records.extend(self._process_table(table))
        except Exception as e:
            errors.append(f"Error parsing PDF: {str(e)}")

        valid_records = sum(1 for r in records if r.is_valid)
        return ImportResult(
            records=records,
            total_records=len(records),
            valid_records=valid_records,
            errors=errors,
        )

    def _process_table(self, table: List[List[Optional[str]]]) -> List[TimeEntryRecord]:
        records = []
        # Simple heuristic: find header row
        header_map = {}
        data_start_idx = 0

        for idx, row in enumerate(table):
            # Clean row values
            row_clean = [str(c).lower().strip() if c else "" for c in row]
            if "fecha" in row_clean or "date" in row_clean:
                # Map columns
                for col_idx, val in enumerate(row_clean):
                    if "fecha" in val or "date" in val:
                        header_map["date"] = col_idx
                    elif "entrada" in val or "in" in val:
                        header_map["entry"] = col_idx
                    elif "salida" in val or "out" in val:
                        header_map["exit"] = col_idx
                    elif "observ" in val or "note" in val:
                        header_map["obs"] = col_idx
                data_start_idx = idx + 1
                break

        if not header_map:
            return []

        for row in table[data_start_idx:]:
            if not row:
                continue

            # Skip if row doesn't have enough columns or date is missing
            if len(row) <= max(header_map.values()):
                continue

            date_val = row[header_map.get("date", -1)] if "date" in header_map else None
            if not date_val:
                continue

            # Normalize date
            # Assuming YYYY-MM-DD or DD/MM/YYYY
            date_str = self._normalize_date(str(date_val))

            entry_val = (
                row[header_map.get("entry", -1)] if "entry" in header_map else None
            )
            exit_val = row[header_map.get("exit", -1)] if "exit" in header_map else None
            obs_val = row[header_map.get("obs", -1)] if "obs" in header_map else None

            # Normalize times
            entry_str = self._normalize_time(str(entry_val)) if entry_val else None
            exit_str = self._normalize_time(str(exit_val)) if exit_val else None

            # Validation
            is_valid = True
            error_msg = None

            if not validate_date(date_str):
                is_valid = False
                error_msg = f"Invalid date format: {date_val}"
            elif entry_str and not validate_time_format(entry_str):
                is_valid = False
                error_msg = f"Invalid entry time: {entry_val}"
            elif exit_str and not validate_time_format(exit_str):
                is_valid = False
                error_msg = f"Invalid exit time: {exit_val}"

            records.append(
                TimeEntryRecord(
                    date=date_str,
                    entry_time=entry_str,
                    exit_time=exit_str,
                    observation=str(obs_val) if obs_val else None,
                    is_valid=is_valid,
                    error_message=error_msg,
                )
            )

        return records

    def _normalize_date(self, date_str: str) -> str:
        # Simple cleanup
        date_str = date_str.strip()
        # Handle DD/MM/YYYY to YYYY-MM-DD
        if re.match(r"\d{2}/\d{2}/\d{4}", date_str):
            parts = date_str.split("/")
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return date_str

    def _normalize_time(self, time_str: str) -> Optional[str]:
        time_str = time_str.strip()
        # Ensure HH:MM
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            if len(time_str) == 4:  # H:MM
                return f"0{time_str}"
            return time_str
        return None
