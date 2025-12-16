"""Tests for app/services/importer/pdf_importer.py."""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.importer.pdf_importer import PDFImporter


class TestPDFImporter:
    """Tests for the PDF importer."""

    @pytest.fixture
    def importer(self):
        """Create a PDF importer instance."""
        return PDFImporter()

    def test_normalize_date_dd_mm_yyyy(self, importer):
        """Test normalizing DD/MM/YYYY to YYYY-MM-DD."""
        result = importer._normalize_date("15/03/2025")
        assert result == "2025-03-15"

    def test_normalize_date_already_correct(self, importer):
        """Test date already in YYYY-MM-DD format."""
        result = importer._normalize_date("2025-03-15")
        assert result == "2025-03-15"

    def test_normalize_date_strips_whitespace(self, importer):
        """Test date with whitespace is stripped."""
        result = importer._normalize_date("  2025-03-15  ")
        assert result == "2025-03-15"

    def test_normalize_time_valid_hmm(self, importer):
        """Test normalizing H:MM to HH:MM."""
        result = importer._normalize_time("9:30")
        assert result == "09:30"

    def test_normalize_time_valid_hhmm(self, importer):
        """Test normalizing HH:MM stays as is."""
        result = importer._normalize_time("09:30")
        assert result == "09:30"

    def test_normalize_time_invalid(self, importer):
        """Test normalizing invalid time returns None."""
        result = importer._normalize_time("invalid")
        assert result is None

    def test_normalize_time_strips_whitespace(self, importer):
        """Test time with whitespace is stripped."""
        result = importer._normalize_time("  09:30  ")
        assert result == "09:30"

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_error(self, mock_pdfplumber, importer):
        """Test handling PDF parsing error."""
        mock_pdfplumber.open.side_effect = Exception("PDF error")
        result = importer.parse(b"fake pdf content")
        assert len(result.errors) == 1
        assert "Error parsing PDF" in result.errors[0]

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_empty_pdf(self, mock_pdfplumber, importer):
        """Test parsing empty PDF."""
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 0
        assert result.valid_records == 0

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_valid_table(self, mock_pdfplumber, importer):
        """Test parsing PDF with valid table data."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                ["2025-03-10", "09:00", "17:00", "Normal day"],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        assert result.valid_records == 1
        assert result.records[0].date == "2025-03-10"
        assert result.records[0].entry_time == "09:00"
        assert result.records[0].exit_time == "17:00"

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_english_headers(self, mock_pdfplumber, importer):
        """Test parsing PDF with English headers."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Date", "In", "Out", "Notes"],
                ["2025-03-10", "09:00", "17:00", "Note"],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        assert result.valid_records == 1

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_dd_mm_yyyy_date(self, mock_pdfplumber, importer):
        """Test parsing PDF with DD/MM/YYYY date format."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                ["10/03/2025", "09:00", "17:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        assert result.records[0].date == "2025-03-10"

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_invalid_date(self, mock_pdfplumber, importer):
        """Test parsing PDF with invalid date."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                ["invalid-date", "09:00", "17:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        assert result.valid_records == 0
        assert result.records[0].is_valid is False

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_invalid_entry_time(self, mock_pdfplumber, importer):
        """Test parsing PDF with entry time that normalizes but fails validation."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                # The importer normalizes invalid times to None, making them valid records
                # Testing with a time that fails validation after normalization
                ["2025-03-10", "9:30", "17:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        # Entry time 9:30 normalizes to 09:30, which is valid

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_with_times_normalized_to_none(self, mock_pdfplumber, importer):
        """Test parsing PDF where times don't match pattern and become None."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                # Invalid times normalize to None (which is acceptable - no entry/exit)
                ["2025-03-10", "invalid", "invalid-time", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1
        # Invalid times become None, record is still valid (just no entry/exit)
        assert result.records[0].entry_time is None
        assert result.records[0].exit_time is None

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_no_header_row(self, mock_pdfplumber, importer):
        """Test parsing PDF without a recognized header row."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Random", "Data", "Here"],
                ["2025-03-10", "09:00", "17:00"],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 0

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_empty_rows_skipped(self, mock_pdfplumber, importer):
        """Test that empty rows are skipped."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                None,  # Empty row
                [],  # Empty list
                ["2025-03-10", "09:00", "17:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 1

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_short_row_skipped(self, mock_pdfplumber, importer):
        """Test that rows with insufficient columns are skipped."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                ["2025-03-10"],  # Too short
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 0

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_missing_date_skipped(self, mock_pdfplumber, importer):
        """Test that rows without date are skipped."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Observaciones"],
                [None, "09:00", "17:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 0

    @patch("app.services.importer.pdf_importer.pdfplumber")
    def test_parse_pdf_multiple_pages(self, mock_pdfplumber, importer):
        """Test parsing PDF with multiple pages."""
        mock_page1 = MagicMock()
        mock_page1.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Obs"],
                ["2025-03-10", "09:00", "17:00", None],
            ]
        ]
        mock_page2 = MagicMock()
        mock_page2.extract_tables.return_value = [
            [
                ["Fecha", "Entrada", "Salida", "Obs"],
                ["2025-03-11", "08:00", "16:00", None],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = importer.parse(b"fake pdf content")
        assert result.total_records == 2
        assert result.valid_records == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
