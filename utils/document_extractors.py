"""Local document-to-text extraction without Anki or AI dependencies.

This module owns optional parser discovery and file-format dispatch.  It must
remain safe to import outside Anki: no ``aqt``/``mw`` access, network calls, or
runtime dependency installation belongs here.
"""

import csv
import os
import re
import zipfile
from xml.etree import ElementTree
from typing import Iterable, List, Tuple

from .logger import get_logger


logger = get_logger()

_DOCX_HEADING_STYLE_RE = re.compile(r"^heading\s*([1-6])$", re.IGNORECASE)
_DOCX_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_DOCUMENT_DEPENDENCIES = {
    "docx": "python-docx==1.1.2",
    "openpyxl": "openpyxl==3.1.5",
}


class MissingDocumentDependencyError(RuntimeError):
    """An optional document parser is unavailable in Anki's Python runtime."""

    def __init__(self, module_name: str):
        requirement = _DOCUMENT_DEPENDENCIES[module_name]
        self.module_name = module_name
        self.requirement = requirement
        self.install_command = get_document_install_command(module_name)
        super().__init__(
            f"Missing optional dependency {requirement}. "
            f"Install it manually with: {self.install_command}"
        )


def get_document_install_command(module_name: str) -> str:
    """Return a pinned command for a user-controlled Python environment."""
    requirement = _DOCUMENT_DEPENDENCIES.get(module_name)
    if requirement is None:
        raise ValueError(f"Unknown document dependency: {module_name}")
    return f"python -m pip install {requirement}"


def _document_dependency_available(module_name: str) -> bool:
    """Check an optional parser without downloading or changing site-packages."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        requirement = _DOCUMENT_DEPENDENCIES[module_name]
        logger.warning(
            "Thiếu dependency đọc tài liệu %s; cần cài thủ công bằng lệnh: %s",
            requirement,
            get_document_install_command(module_name),
        )
        return False


def extract_text_from_file(filepath: str) -> str:
    """Read text from a supported local document.

    Return ``""`` when the file is absent or an available parser cannot read
    it. Raise :class:`MissingDocumentDependencyError` when DOCX/XLSX support is
    unavailable so the UI can offer an actionable manual-install message.
    """
    if not filepath or not os.path.exists(filepath):
        return ""

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception:
            return ""

    if ext in (".md", ".markdown"):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception:
            pass

    if ext == ".csv":
        return _extract_csv_text(filepath)

    if ext == ".pdf":
        return _extract_pdf_text(filepath)

    if ext == ".docx":
        return _extract_docx_text(filepath)

    if ext == ".doc":
        result = _extract_docx_text(filepath)
        if result:
            return result
        return "⚠️ File .doc (Word cũ) chưa hỗ trợ. Vui lòng lưu lại thành .docx hoặc .txt rồi thử lại."

    if ext in (".xlsx", ".xls"):
        return _extract_sheet_text(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except Exception:
        return ""


def extract_text_from_files(filepaths: Iterable[str]) -> List[Tuple[str, str]]:
    """Read multiple files and return non-empty ``(basename, text)`` pairs."""
    results = []
    for filepath in filepaths or []:
        try:
            text = extract_text_from_file(filepath)
            if text and text.strip():
                results.append((os.path.basename(filepath), text))
        except Exception as error:
            logger.warning("Lỗi đọc file %s: %s", filepath, error)
    return results


def extract_study_text_from_file(filepath: str) -> str:
    """Read a Study Library source, with a local DOCX fallback for headings."""
    if os.path.splitext(str(filepath or ""))[1].lower() != ".docx":
        return extract_text_from_file(filepath)
    try:
        import docx  # noqa: F401
    except ImportError:
        return _extract_docx_package_text(filepath)
    return _extract_docx_text(filepath)


def _extract_csv_text(filepath: str) -> str:
    """Read CSV rows and join non-empty cells with commas."""
    try:
        rows = []
        with open(filepath, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.reader(file):
                cells = [cell.strip() for cell in row if cell and str(cell).strip()]
                if cells:
                    rows.append(", ".join(cells))
        return "\n".join(rows)
    except Exception:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as file:
                return file.read()
        except Exception:
            return ""


def _extract_sheet_text(filepath: str) -> str:
    """Read XLSX/XLS sheets with an already-installed optional parser."""
    openpyxl_available = _document_dependency_available("openpyxl")
    if openpyxl_available:
        try:
            import openpyxl

            workbook = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            parts = []
            for worksheet in workbook.worksheets:
                parts.append(f"### Sheet: {worksheet.title}")
                for row in worksheet.iter_rows(values_only=True):
                    cells = [
                        str(cell).strip()
                        for cell in row
                        if cell is not None and str(cell).strip()
                    ]
                    if cells:
                        parts.append(" | ".join(cells))
            workbook.close()
            if parts:
                return "\n".join(parts)
        except Exception as error:
            logger.warning("openpyxl đọc lỗi %s: %s", filepath, error)

    try:
        import pandas as pd

        parts = []
        spreadsheet = pd.ExcelFile(filepath)
        for sheet in spreadsheet.sheet_names:
            dataframe = spreadsheet.parse(sheet, header=None)
            parts.append(f"### Sheet: {sheet}")
            parts.append(dataframe.to_string(index=False, header=False))
        if parts:
            return "\n".join(parts)
    except ImportError:
        pass
    except Exception as error:
        logger.warning("pandas đọc lỗi %s: %s", filepath, error)

    if not openpyxl_available:
        raise MissingDocumentDependencyError("openpyxl")
    return ""


def _extract_pdf_text(filepath: str) -> str:
    """Read PDF text with the first supported parser already installed."""
    for library in ("pdfplumber", "PyPDF2", "fitz"):
        try:
            if library == "pdfplumber":
                import pdfplumber

                parts = []
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            parts.append(text)
                return "\n".join(parts)
            if library == "PyPDF2":
                from PyPDF2 import PdfReader

                parts = []
                for page in PdfReader(filepath).pages:
                    text = page.extract_text()
                    if text:
                        parts.append(text)
                return "\n".join(parts)
            if library == "fitz":
                import fitz

                document = fitz.open(filepath)
                parts = [page.get_text() for page in document if page.get_text()]
                document.close()
                return "\n".join(parts)
        except ImportError:
            continue
    return ""


def _docx_heading(text: str, style_name: str) -> str:
    """Represent supported Word heading styles as stable Markdown headings."""
    normalized_style = re.sub(r"\s+", "", str(style_name or "")).casefold()
    level_match = _DOCX_HEADING_STYLE_RE.match(normalized_style)
    if normalized_style == "title":
        return f"# {text}"
    if level_match:
        return f"{'#' * int(level_match.group(1))} {text}"
    return text


def _extract_docx_text(filepath: str) -> str:
    """Read DOCX text while retaining Word heading styles as Markdown."""
    if not _document_dependency_available("docx"):
        raise MissingDocumentDependencyError("docx")
    try:
        from docx import Document

        parts = []
        for paragraph in Document(filepath).paragraphs:
            text = str(getattr(paragraph, "text", "") or "").strip()
            if not text:
                continue
            style_name = str(
                getattr(getattr(paragraph, "style", None), "name", "") or ""
            ).strip()
            parts.append(_docx_heading(text, style_name))
        return "\n".join(parts)
    except Exception as error:
        logger.warning("python-docx đọc lỗi %s: %s", filepath, error)
        return ""


def _extract_docx_package_text(filepath: str) -> str:
    """Extract DOCX paragraphs and Word style IDs without optional packages."""
    try:
        with zipfile.ZipFile(filepath) as archive:
            document = archive.read("word/document.xml")
        root = ElementTree.fromstring(document)
        paragraphs = []
        for paragraph in root.iter(f"{_DOCX_NAMESPACE}p"):
            text = "".join(
                node.text or "" for node in paragraph.iter(f"{_DOCX_NAMESPACE}t")
            ).strip()
            if not text:
                continue
            properties = paragraph.find(f"{_DOCX_NAMESPACE}pPr")
            style = properties.find(f"{_DOCX_NAMESPACE}pStyle") if properties is not None else None
            style_name = style.get(f"{_DOCX_NAMESPACE}val", "") if style is not None else ""
            paragraphs.append(_docx_heading(text, style_name))
        return "\n".join(paragraphs)
    except (ElementTree.ParseError, KeyError, OSError, zipfile.BadZipFile) as error:
        logger.warning("DOCX fallback could not read %s: %s", filepath, error)
        return ""


__all__ = [
    "MissingDocumentDependencyError",
    "extract_text_from_file",
    "extract_text_from_files",
    "extract_study_text_from_file",
    "get_document_install_command",
]
