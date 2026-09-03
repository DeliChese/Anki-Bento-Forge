"""
Unit tests for file text extraction (đọc tài liệu tham khảo cho AI).

Tests extract_text_from_file cho txt/md/csv + extract_text_from_files nhiều file,
và kiểm tra dependency DOCX/XLSX mà không cần cài thư viện ngoài.
"""

import os
import sys
import types
import zipfile
from pathlib import Path

import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


class TestExtractTextFromFile:
    def test_read_txt(self, tmp_path):
        from utils.ai_extractor import extract_text_from_file
        p = tmp_path / "doc.txt"
        p.write_text("日本語の文法\n第二行", encoding="utf-8")
        text = extract_text_from_file(str(p))
        assert "日本語" in text
        assert "第二行" in text

    def test_read_md(self, tmp_path):
        from utils.ai_extractor import extract_text_from_file
        p = tmp_path / "notes.md"
        p.write_text("# Title\n- item", encoding="utf-8")
        assert "item" in extract_text_from_file(str(p))

    def test_read_csv(self, tmp_path):
        from utils.document_extractors import _extract_csv_text
        p = tmp_path / "list.csv"
        p.write_text("食べる,ăn,N5\n", encoding="utf-8")
        text = _extract_csv_text(str(p))
        assert "食べる" in text
        assert "N5" in text

    def test_missing_file_returns_empty(self, tmp_path):
        from utils.ai_extractor import extract_text_from_file
        assert extract_text_from_file(str(tmp_path / "no_such_file.txt")) == ""

    def test_unknown_ext_fallback(self, tmp_path):
        from utils.ai_extractor import extract_text_from_file
        p = tmp_path / "x.xyz"
        p.write_text("plain text", encoding="utf-8")
        assert "plain text" in extract_text_from_file(str(p))

    def test_docx_missing_dependency_is_actionable_and_never_installs(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "missing.docx"
        path.touch()
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: False)

        with pytest.raises(document_extractors.MissingDocumentDependencyError) as error:
            document_extractors.extract_text_from_file(str(path))

        assert error.value.requirement == "python-docx==1.1.2"
        assert error.value.install_command == "python -m pip install python-docx==1.1.2"

    def test_xlsx_package_fallback_works_without_openpyxl(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "fallback.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "xl/workbook.xml",
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Vocabulary" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            )
            archive.writestr(
                "xl/sharedStrings.xml",
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<si><t>Nhóm</t></si><si><t>Từ</t></si><si><t>Du lịch</t></si><si><t>机场</t></si></sst>',
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
                '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row>'
                '</sheetData></worksheet>',
            )
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: False)
        monkeypatch.setitem(sys.modules, "pandas", None)

        text = document_extractors.extract_text_from_file(str(path))
        assert "### Sheet: Vocabulary" in text
        assert "Du lịch | 机场" in text

    def test_docx_existing_dependency_extracts_text(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "available.docx"
        path.touch()
        document = types.SimpleNamespace(
            paragraphs=[types.SimpleNamespace(text="第一行"), types.SimpleNamespace(text="")]
        )
        fake_docx = types.SimpleNamespace(Document=lambda _: document)
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: True)
        monkeypatch.setitem(sys.modules, "docx", fake_docx)

        assert document_extractors.extract_text_from_file(str(path)) == "第一行"

    def test_docx_heading_styles_are_retained_as_markdown(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "headings.docx"
        path.touch()
        document = types.SimpleNamespace(
            paragraphs=[
                types.SimpleNamespace(text="Grammarbook", style=types.SimpleNamespace(name="Title")),
                types.SimpleNamespace(text="02. 会 và 能", style=types.SimpleNamespace(name="Heading 2")),
                types.SimpleNamespace(text="Nội dung", style=types.SimpleNamespace(name="Normal")),
            ]
        )
        fake_docx = types.SimpleNamespace(Document=lambda _: document)
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: True)
        monkeypatch.setitem(sys.modules, "docx", fake_docx)

        assert document_extractors.extract_text_from_file(str(path)) == (
            "# Grammarbook\n## 02. 会 và 能\nNội dung"
        )

    def test_study_docx_fallback_retains_word_heading_styles(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "grammarbook.docx"
        xml = (
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
            '<w:r><w:t>02. 会 và 能</w:t></w:r></w:p><w:p><w:r><w:t>Nội dung</w:t>'
            '</w:r></w:p></w:body></w:document>'
        )
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: False)

        assert document_extractors.extract_study_text_from_file(str(path)) == (
            "## 02. 会 và 能\nNội dung"
        )

    def test_xlsx_existing_dependency_extracts_cells(self, monkeypatch, tmp_path):
        from utils import document_extractors

        path = tmp_path / "available.xlsx"
        path.touch()
        worksheet = types.SimpleNamespace(
            title="Vocabulary",
            iter_rows=lambda values_only: [("食べる", "ăn", None)],
        )
        workbook = types.SimpleNamespace(worksheets=[worksheet], close=lambda: None)
        fake_openpyxl = types.SimpleNamespace(load_workbook=lambda *args, **kwargs: workbook)
        monkeypatch.setattr(document_extractors, "_document_dependency_available", lambda name: True)
        monkeypatch.setitem(sys.modules, "openpyxl", fake_openpyxl)

        text = document_extractors.extract_text_from_file(str(path))
        assert "### Sheet: Vocabulary" in text
        assert "食べる | ăn" in text

    def test_dependency_checks_have_no_install_side_effects(self):
        from utils import ai_extractor, document_extractors

        assert not hasattr(ai_extractor, "_pip_install")
        assert not hasattr(ai_extractor, "_install_docx")
        assert not hasattr(ai_extractor, "_install_openpyxl")
        assert "import subprocess" not in Path(ai_extractor.__file__).read_text(encoding="utf-8")
        source = Path(document_extractors.__file__).read_text(encoding="utf-8")
        assert "import subprocess" not in source
        assert "import aqt" not in source
        assert "from aqt" not in source
        assert document_extractors.get_document_install_command("docx").endswith("python-docx==1.1.2")
        assert document_extractors.get_document_install_command("openpyxl").endswith("openpyxl==3.1.5")

    def test_ai_extractor_keeps_legacy_public_imports(self):
        from utils import ai_extractor, document_extractors

        assert ai_extractor.extract_text_from_file is document_extractors.extract_text_from_file
        assert ai_extractor.extract_text_from_files is document_extractors.extract_text_from_files
        assert ai_extractor.MissingDocumentDependencyError is document_extractors.MissingDocumentDependencyError


class TestExtractTextFromFiles:
    def test_multi_file(self, tmp_path):
        from utils.ai_extractor import extract_text_from_files
        p1 = tmp_path / "a.txt"
        p2 = tmp_path / "b.txt"
        p1.write_text("AAA", encoding="utf-8")
        p2.write_text("BBB", encoding="utf-8")
        results = extract_text_from_files([str(p1), str(p2)])
        assert len(results) == 2
        assert results[0][0] == "a.txt"
        assert results[1][1] == "BBB"

    def test_bad_files_skipped(self, tmp_path):
        from utils.ai_extractor import extract_text_from_files
        p = tmp_path / "a.txt"
        p.write_text("AAA", encoding="utf-8")
        results = extract_text_from_files([str(p), str(tmp_path / "missing.txt")])
        assert len(results) == 1
