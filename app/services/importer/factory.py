from typing import Dict, Type

from app.services.importer.excel_importer import ExcelImporter
from app.services.importer.pdf_importer import PDFImporter
from app.services.importer.protocol import ImporterProtocol


class ImporterFactory:
    _importers: Dict[str, Type[ImporterProtocol]] = {
        "pdf": PDFImporter,
        "xlsx": ExcelImporter,
        "xls": ExcelImporter,
    }

    @classmethod
    def get_importer(cls, filename: str) -> ImporterProtocol:
        ext = filename.split(".")[-1].lower()
        importer_class = cls._importers.get(ext)
        if not importer_class:
            raise ValueError(f"Unsupported file extension: {ext}")
        return importer_class()
