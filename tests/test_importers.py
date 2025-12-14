import io

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


class TestImporterFactory:
    def test_get_valid_importer(self):
        assert isinstance(ImporterFactory.get_importer("test.xlsx"), ExcelImporter)
        assert isinstance(ImporterFactory.get_importer("test.pdf"), PDFImporter)

    def test_get_invalid_importer(self):
        with pytest.raises(ValueError):
            ImporterFactory.get_importer("test.txt")
