import io
from typing import Any, List, Optional

import pandas as pd

from app.services.importer.protocol import (
    ImporterProtocol,
    ImportResult,
    TimeEntryRecord,
)
from app.utils.validators import validate_date, validate_time_format


class ExcelImporter(ImporterProtocol):
    def parse(self, file_content: Any) -> ImportResult:
        records: List[TimeEntryRecord] = []
        errors: List[str] = []

        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content))

            # Normalize headers
            df.columns = df.columns.astype(str).str.lower().str.strip()

            # Map columns
            col_map = {}
            for col in df.columns:
                if "fecha" in col or "date" in col:
                    col_map["date"] = col
                elif "entrada" in col or "in" in col:
                    col_map["entry"] = col
                elif "salida" in col or "out" in col:
                    col_map["exit"] = col
                elif "observ" in col or "note" in col:
                    col_map["obs"] = col

            if "date" not in col_map:
                errors.append("Could not find 'Fecha' or 'Date' column")
                return ImportResult([], 0, 0, errors)

            for _, row in df.iterrows():
                date_val = row[col_map["date"]]
                if pd.isna(date_val):
                    continue

                # Handle dates
                if isinstance(date_val, pd.Timestamp):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val).strip()

                entry_val = (
                    row.get(col_map.get("entry")) if "entry" in col_map else None
                )
                exit_val = row.get(col_map.get("exit")) if "exit" in col_map else None
                obs_val = row.get(col_map.get("obs")) if "obs" in col_map else None

                entry_str = self._format_time(entry_val)
                exit_str = self._format_time(exit_val)

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
                        observation=str(obs_val) if pd.notna(obs_val) else None,
                        is_valid=is_valid,
                        error_message=error_msg,
                    )
                )

        except Exception as e:
            errors.append(f"Error parsing Excel: {str(e)}")

        valid_records = sum(1 for r in records if r.is_valid)
        return ImportResult(records, len(records), valid_records, errors)

    def _format_time(self, val: Any) -> Optional[str]:
        if pd.isna(val):
            return None

        if isinstance(val, pd.Timestamp):
            return val.strftime("%H:%M")

        # If it's a datetime.time object
        try:
            return val.strftime("%H:%M")
        except AttributeError:
            pass

        s = str(val).strip()
        # Basic fixes
        return s
