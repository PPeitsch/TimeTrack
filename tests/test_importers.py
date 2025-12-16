import io
from datetime import datetime, time

import pandas as pd
import pytest

from app.services.importer.excel_importer import ExcelImporter
from app.services.importer.factory import ImporterFactory
from app.services.importer.pdf_importer import PDFImporter


class TestExcelImporter:
    def test_parse_valid_excel(self):
        # Create a sample dataframe
        data = {
            "Fecha": ["2025-01-01", "2025-01-02"],
            "Entrada": ["09:00", "09:30"],
            "Salida": ["18:00", "18:30"],
            "Observación": ["Test 1", "Test 2"],
        }
        df = pd.DataFrame(data)

        # Write to bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 2
        assert result.valid_records == 2
        assert len(result.errors) == 0

        # Check content
        assert result.records[0].date == "2025-01-01"
        assert result.records[0].entry_time == "09:00"
        assert result.records[0].exit_time == "18:00"
        assert result.records[0].observation == "Test 1"

    def test_parse_invalid_excel(self):
        # Missing required columns
        data = {"WrongColumn": ["2025-01-01"]}
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert len(result.errors) > 0  # Should complain about missing Date column

    def test_parse_excel_with_na_date(self):
        """Test that rows with NA date are skipped."""
        data = {
            "Fecha": ["2025-01-01", None, "2025-01-03"],
            "Entrada": ["09:00", "10:00", "09:30"],
            "Salida": ["18:00", "17:00", "18:30"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        # Should only have 2 records (NA date row skipped)
        assert result.total_records == 2

    def test_parse_excel_with_timestamp_dates(self):
        """Test parsing Excel with pandas Timestamp dates."""
        data = {
            "Fecha": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-02")],
            "Entrada": ["09:00", "09:30"],
            "Salida": ["18:00", "18:30"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 2
        assert result.records[0].date == "2025-01-01"

    def test_parse_excel_with_invalid_date_format(self):
        """Test that invalid date format is flagged."""
        data = {
            "Fecha": ["not-a-date"],
            "Entrada": ["09:00"],
            "Salida": ["18:00"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 1
        assert result.valid_records == 0
        assert result.records[0].is_valid is False
        assert "Invalid date format" in result.records[0].error_message

    def test_parse_excel_with_invalid_entry_time(self):
        """Test that invalid entry time format is flagged."""
        data = {
            "Fecha": ["2025-01-01"],
            "Entrada": ["invalid-time"],
            "Salida": ["18:00"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 1
        assert result.valid_records == 0
        assert "Invalid entry time" in result.records[0].error_message

    def test_parse_excel_with_invalid_exit_time(self):
        """Test that invalid exit time format is flagged."""
        data = {
            "Fecha": ["2025-01-01"],
            "Entrada": ["09:00"],
            "Salida": ["not-a-time"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 1
        assert result.valid_records == 0
        assert "Invalid exit time" in result.records[0].error_message

    def test_parse_excel_with_english_headers(self):
        """Test parsing Excel with English column headers."""
        data = {
            "Date": ["2025-01-01"],
            "In": ["09:00"],
            "Out": ["18:00"],
            "Notes": ["Test note"],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 1
        assert result.valid_records == 1
        assert result.records[0].observation == "Test note"

    def test_parse_excel_with_na_observation(self):
        """Test that NA observation becomes None."""
        data = {
            "Fecha": ["2025-01-01"],
            "Entrada": ["09:00"],
            "Salida": ["18:00"],
            "Observación": [None],
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        importer = ExcelImporter()
        result = importer.parse(output.read())

        assert result.total_records == 1
        assert result.records[0].observation is None

    def test_parse_excel_exception_handling(self):
        """Test that parsing errors are caught."""
        importer = ExcelImporter()
        result = importer.parse(b"not valid excel content")

        assert len(result.errors) > 0
        assert "Error parsing Excel" in result.errors[0]

    def test_format_time_with_timestamp(self):
        """Test _format_time with pandas Timestamp."""
        importer = ExcelImporter()
        ts = pd.Timestamp("2025-01-01 09:30:00")
        result = importer._format_time(ts)
        assert result == "09:30"

    def test_format_time_with_na(self):
        """Test _format_time with NA value."""
        importer = ExcelImporter()
        result = importer._format_time(pd.NA)
        assert result is None

    def test_format_time_with_time_object(self):
        """Test _format_time with datetime.time object."""
        importer = ExcelImporter()
        t = time(9, 30)
        result = importer._format_time(t)
        assert result == "09:30"

    def test_format_time_with_string(self):
        """Test _format_time with string."""
        importer = ExcelImporter()
        result = importer._format_time("  09:30  ")
        assert result == "09:30"


class TestImporterFactory:
    def test_get_valid_importer(self):
        assert isinstance(ImporterFactory.get_importer("test.xlsx"), ExcelImporter)
        assert isinstance(ImporterFactory.get_importer("test.pdf"), PDFImporter)

    def test_get_invalid_importer(self):
        with pytest.raises(ValueError):
            ImporterFactory.get_importer("test.txt")

    def test_get_importer_xls(self):
        """Test that .xls extension works."""
        assert isinstance(ImporterFactory.get_importer("test.xls"), ExcelImporter)
