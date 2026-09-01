"""AI-first inventory preparation for noisy vocabulary sources.

The scanner preserves source row/cell identity, asks AI only for semantic
classification, and validates every candidate against its exact source row.
It has no Qt or Anki dependency.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import unicodedata
import zipfile
from xml.etree import ElementTree
from typing import Callable, Iterable, Mapping, Optional

from . import ai_extractor as _api
from .ai_reliability import existing_entry_identity
from .ai_response_guard import adapt_chat_completion_response, enable_deepseek_json_output
from .document_extractors import MissingDocumentDependencyError, extract_text_from_file
from .i18n import t
from .language_identity import normalize_language
from .logger import get_logger
from .user_data import atomic_write_json, get_user_data_path, read_json


logger = get_logger()

INVENTORY_SCANNER_VERSION = 5
INVENTORY_ROWS_PER_REQUEST = 90
INVENTORY_CHARS_PER_REQUEST = 14_000
INVENTORY_TURBO_MULTIPLIER = 1.5
INVENTORY_CACHE_TTL = 14 * 24 * 3600
INVENTORY_CACHE_DIR = get_user_data_path(os.path.join("cache", "ai_inventory"))
TOPIC_CATALOG_PATH = get_user_data_path("ai_topic_catalogs.json")
TOPIC_CATALOG_LIMIT = 200

_DECISIONS = {"keep", "skip", "review"}
_LEVEL_FIELDS = {
    "japanese": "jlptlevel",
    "chinese": "hsk_level",
    "korean": "topik_level",
    "english": "cefr_level",
}

_INVENTORY_SYSTEM_PROMPT = """Scan noisy source rows for language-card candidates.
Input is JSONL: {"i":row_index,"v":[exact cell values],"x":optional context}.

GOAL
- Find only target-language headwords, fixed expressions, or grammar patterns that are suitable card candidates.
- Distinguish the main lexical item from row numbers, headers, readings/romanization, translations, examples, notes, labels, frequency/status text, and decorative content.
- Infer a concise broad topic and a proficiency level when reasonably supported. Reuse PREFERRED_TOPIC_LABELS when semantically suitable.
- For collocation, keep only a multiword/fixed expression supported by the source row; mark a contextless or ambiguous fragment as review.
- Treat frequency, register, usage, and "Mức độ / sắc thái" as metadata, never as proficiency. Use only the target language's valid notation: Chinese HSK1–HSK6/HSK7-9, Japanese N5–N1, Korean TOPIK I/II or TOPIK 1–6, English A1–C2.
- A row may yield multiple results. If it yields none, return one skip/review result for that row_index.

DECISIONS
- keep: clearly a card-worthy target item.
- skip: clearly auxiliary/non-target material. State a short reason. If a plausible target candidate exists but you still skip the row, include its exact surface so the user can restore it.
- review: ambiguous layout, uncertain target item, or insufficient evidence. Never silently skip uncertainty.

HARD CONSTRAINTS
1. row_index must exactly match an input i.
2. For keep/review, surface must occur verbatim in an input cell. Never invent or normalize it.
3. Do not treat serial numbers, column headers, isolated readings, isolated translations, sentences/examples, or notes as headwords.
4. Preserve supplied meaning/reading/level/topic when present; otherwise use an empty string unless topic/level can be classified safely.
5. Return JSON only. No markdown or prose.

OUTPUT COMPACT JSON ONLY
{"r":[[row_index,"surface","reading","meaning","topic","level","k|s|r",confidence_0_to_100,"short_reason"]]}
"""

_TECHNICAL_ROW_RE = re.compile(r"^(?P<source>.+!R\d+)\t(?P<body>C1=.*)$")
_TECHNICAL_CELL_RE = re.compile(r'C(\d+)=("(?:\\.|[^"\\])*")')


def _card_kind(grammar: bool = False, card_kind: Optional[str] = None) -> str:
    kind = str(card_kind or ("grammar" if grammar else "vocab")).strip().casefold()
    if kind not in {"vocab", "grammar", "collocation"}:
        return "grammar" if grammar else "vocab"
    return kind


def topic_identity(label: object) -> str:
    """Return a conservative identity for labels that are visibly the same topic."""
    text = re.sub(
        r"^\s*(?:\d{1,3}|[ivxlcdm]{1,8})\s*[.)_:\-–—]+\s*",
        "",
        str(label or "").strip(),
        flags=re.IGNORECASE,
    )
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", plain.casefold()).strip()


def _clean_topic_label(label: object) -> str:
    text = re.sub(r"\s+", " ", str(label or "").strip())
    return re.sub(
        r"^\s*(?:\d{1,3}|[ivxlcdm]{1,8})\s*[.)_:\-–—]+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()[:160]


def canonicalize_topics(rows: Iterable[Mapping]) -> tuple[list[dict], list[dict]]:
    """Merge exact label variants, rewrite rows, and build a counted catalog."""
    rewritten = [dict(value) for value in rows]
    canonical = {}
    order = []
    for row in rewritten:
        label = _clean_topic_label(row.get("topic"))
        identity = topic_identity(label)
        if not identity:
            row["topic"] = ""
            continue
        if identity not in canonical:
            canonical[identity] = label
            order.append(identity)
        row["topic"] = canonical[identity]

    counts = {identity: 0 for identity in order}
    for row in rewritten:
        if row.get("decision") not in {"keep", "review"} or not row.get("surface"):
            continue
        identity = topic_identity(row.get("topic"))
        if identity in counts:
            counts[identity] += 1
    catalog = [
        {"id": identity, "name": canonical[identity], "count": counts[identity]}
        for identity in order
        if counts[identity] > 0
    ]
    return rewritten, catalog


def _save_topic_catalog(source_hash: str, lang: str, card_kind: str, catalog: Iterable[Mapping]) -> None:
    """Persist only source checksum and counted topic labels, never source content."""
    if not source_hash:
        return
    payload = read_json(
        TOPIC_CATALOG_PATH,
        {"schema": 1, "catalogs": {}},
        lambda value: isinstance(value, dict) and isinstance(value.get("catalogs"), dict),
    )
    catalogs = dict(payload.get("catalogs", {}))
    key = hashlib.sha256(
        f"{source_hash}|{normalize_language(lang)}|{card_kind}".encode("utf-8")
    ).hexdigest()
    catalogs[key] = {
        "source_hash": source_hash,
        "language": normalize_language(lang),
        "card_kind": card_kind,
        "updated_at": int(time.time()),
        "topics": [
            {
                "id": str(topic.get("id") or ""),
                "name": str(topic.get("name") or "")[:160],
                "count": max(0, int(topic.get("count") or 0)),
            }
            for topic in catalog
            if str(topic.get("name") or "").strip()
        ],
    }
    if len(catalogs) > TOPIC_CATALOG_LIMIT:
        newest = sorted(
            catalogs.items(),
            key=lambda item: int(item[1].get("updated_at", 0)),
            reverse=True,
        )[:TOPIC_CATALOG_LIMIT]
        catalogs = dict(newest)
    atomic_write_json(TOPIC_CATALOG_PATH, {"schema": 1, "catalogs": catalogs})


def topic_catalog_instruction(catalog: Iterable[Mapping]) -> str:
    """Build a compact generation constraint from a prepared topic catalog."""
    labels = [str(topic.get("name") or "").strip() for topic in catalog]
    labels = [label for label in labels if label]
    if not labels:
        return ""
    encoded = json.dumps(labels[:100], ensure_ascii=False, separators=(",", ":"))
    return (
        "Kho tiền sản xuất đã khóa danh mục chủ đề. Chỉ dùng đúng một nhãn trong "
        f"TOPIC_CATALOG={encoded}; không tạo nhãn đồng nghĩa hoặc biến thể dài dòng."
    )


def apply_prepared_inventory(
    results: Iterable[Mapping],
    inventory: Iterable[Mapping],
    catalog: Iterable[Mapping],
    *,
    card_kind: str = "vocab",
) -> list[dict]:
    """Keep only approved candidates and apply their pre-production topic."""
    kind = _card_kind(card_kind=card_kind)
    approved = {
        str(item.get("identity") or ""): str(item.get("topic") or "").strip()
        for item in inventory
        if item.get("decision") == "keep" and item.get("identity") and item.get("topic")
    }
    canonical = {
        str(topic.get("id") or topic_identity(topic.get("name"))): str(topic.get("name") or "")
        for topic in catalog
        if str(topic.get("name") or "").strip()
    }
    prepared = []
    seen = set()
    for value in results:
        row = dict(value)
        identity, _meaning = existing_entry_identity(row, kind)
        if not identity or identity not in approved or identity in seen:
            continue
        row["topic"] = approved[identity] or canonical.get(topic_identity(row.get("topic")), "")
        prepared.append(row)
        seen.add(identity)
    return prepared


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return re.sub(r"\s+", " ", text)


def _trim_row(values: Iterable[object], *, max_columns: int = 64) -> list[str]:
    cells = [_cell_text(value) for value in list(values)[:max_columns]]
    while cells and not cells[-1]:
        cells.pop()
    return cells


def _row_text(cells: Iterable[str]) -> str:
    return " | ".join(
        f"C{index + 1}={json.dumps(str(value), ensure_ascii=False)}"
        for index, value in enumerate(cells)
        if str(value).strip()
    )


def _source_hash(rows: Iterable[Mapping], name: str, kind: str) -> str:
    stable = [
        {
            "source_id": str(row.get("source_id") or ""),
            "text": str(row.get("text") or ""),
            "context": str(row.get("context") or ""),
        }
        for row in rows
    ]
    payload = json.dumps(
        {"version": INVENTORY_SCANNER_VERSION, "name": name, "kind": kind, "rows": stable},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def inventory_source_from_text(text: str, *, name: str = "pasted-source") -> dict:
    """Preserve every non-empty pasted line with a stable local source ID."""
    rows = []
    context = []
    for line_number, raw in enumerate(
        str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"),
        start=1,
    ):
        line = raw.strip()
        if not line:
            continue
        technical = _TECHNICAL_ROW_RE.match(line)
        if technical:
            parsed_cells = {}
            for column, encoded in _TECHNICAL_CELL_RE.findall(technical.group("body")):
                try:
                    parsed_cells[int(column) - 1] = json.loads(encoded)
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
            if parsed_cells:
                max_column = min(63, max(parsed_cells))
                cells = [str(parsed_cells.get(index, "")) for index in range(max_column + 1)]
                source_id = technical.group("source")
                sheet, _, row_label = source_id.rpartition("!R")
                rows.append({
                    "source_id": source_id,
                    "text": _row_text(cells),
                    "context": f"Sheet: {sheet}",
                    "sheet": sheet,
                    "row": int(row_label),
                    "cells": cells,
                })
                continue
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        file_heading = re.match(r"^=+\s*(?:📄\s*)?FILE:\s*(.*?)\s*=+$", line, re.IGNORECASE)
        if heading or file_heading:
            title = (heading or file_heading).group(1).strip()
            if heading:
                level = len(line) - len(line.lstrip("#"))
                context = context[: max(0, level - 1)] + [title]
            else:
                context = [title]
        rows.append({
            "source_id": f"L{line_number:06d}",
            "text": line,
            "context": " > ".join(context),
            "line": line_number,
            "declared_topic": title if heading else "",
        })
    source_hash = _source_hash(rows, name, "text")
    return {"name": str(name or "pasted-source"), "kind": "text", "rows": rows, "source_hash": source_hash}


def _source_from_xlsx(filepath: str) -> dict:
    try:
        import openpyxl
    except ImportError:
        return _source_from_xlsx_package(filepath)

    workbook = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    rows = []
    try:
        for worksheet in workbook.worksheets:
            for row_number, values in enumerate(worksheet.iter_rows(values_only=True), start=1):
                cells = _trim_row(values)
                if not cells or not any(cells):
                    continue
                rows.append({
                    "source_id": f"{worksheet.title}!R{row_number:06d}",
                    "text": _row_text(cells),
                    "context": f"Sheet: {worksheet.title}",
                    "sheet": worksheet.title,
                    "row": row_number,
                    "cells": cells,
                })
    finally:
        workbook.close()
    name = os.path.basename(filepath)
    return {"name": name, "kind": "xlsx", "rows": rows, "source_hash": _source_hash(rows, name, "xlsx")}


_XLSX_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_XLSX_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_XLSX_PACKAGE_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _xlsx_column_index(reference: str) -> int:
    letters = re.match(r"[A-Za-z]+", str(reference or ""))
    if not letters:
        return 0
    value = 0
    for character in letters.group(0).upper():
        value = value * 26 + ord(character) - ord("A") + 1
    return max(0, value - 1)


def _xlsx_cell_value(cell, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(
            node.text or "" for node in cell.iter(f"{_XLSX_MAIN_NS}t")
        )
    value_node = cell.find(f"{_XLSX_MAIN_NS}v")
    value = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return ""
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    return value


def _source_from_xlsx_package(filepath: str) -> dict:
    """Read ordinary XLSX files with the standard library as a safe fallback."""
    rows = []
    try:
        with zipfile.ZipFile(filepath) as archive:
            shared_strings = []
            try:
                shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                for item in shared_root.iter(f"{_XLSX_MAIN_NS}si"):
                    shared_strings.append("".join(
                        node.text or "" for node in item.iter(f"{_XLSX_MAIN_NS}t")
                    ))
            except KeyError:
                pass

            workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            relationships = ElementTree.fromstring(
                archive.read("xl/_rels/workbook.xml.rels")
            )
            targets = {
                relation.attrib.get("Id", ""): relation.attrib.get("Target", "")
                for relation in relationships.iter(f"{_XLSX_PACKAGE_REL_NS}Relationship")
            }
            sheets = workbook.find(f"{_XLSX_MAIN_NS}sheets")
            for sheet in list(sheets) if sheets is not None else ():
                title = sheet.attrib.get("name", "Sheet")
                relation_id = sheet.attrib.get(f"{_XLSX_REL_NS}id", "")
                target = targets.get(relation_id, "")
                if target.startswith("/"):
                    sheet_path = target.lstrip("/")
                elif target.startswith("xl/"):
                    sheet_path = target
                else:
                    sheet_path = f"xl/{target.lstrip('/')}"
                worksheet = ElementTree.fromstring(archive.read(sheet_path))
                for fallback_row, row_node in enumerate(
                    worksheet.iter(f"{_XLSX_MAIN_NS}row"), start=1,
                ):
                    row_number = int(row_node.attrib.get("r") or fallback_row)
                    cells = []
                    for cell in row_node.findall(f"{_XLSX_MAIN_NS}c"):
                        column = _xlsx_column_index(cell.attrib.get("r", ""))
                        if column >= 64:
                            continue
                        if len(cells) <= column:
                            cells.extend([""] * (column + 1 - len(cells)))
                        cells[column] = _cell_text(_xlsx_cell_value(cell, shared_strings))
                    cells = _trim_row(cells)
                    if not cells or not any(cells):
                        continue
                    rows.append({
                        "source_id": f"{title}!R{row_number:06d}",
                        "text": _row_text(cells),
                        "context": f"Sheet: {title}",
                        "sheet": title,
                        "row": row_number,
                        "cells": cells,
                    })
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        raise ValueError(f"Invalid or unsupported XLSX file: {error}") from error
    name = os.path.basename(filepath)
    return {"name": name, "kind": "xlsx", "rows": rows, "source_hash": _source_hash(rows, name, "xlsx")}


def _decode_delimited_file(filepath: str) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
        try:
            with open(filepath, "r", encoding=encoding, newline="") as handle:
                return handle.read()
        except UnicodeDecodeError:
            continue
    return ""


def _source_from_delimited(filepath: str) -> dict:
    text = _decode_delimited_file(filepath)
    if not text:
        return {"name": os.path.basename(filepath), "kind": "csv", "rows": [], "source_hash": ""}
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = "\t" if "\t" in text.partition("\n")[0] else ","
    rows = []
    for row_number, values in enumerate(csv.reader(io.StringIO(text), delimiter=delimiter), start=1):
        cells = _trim_row(values)
        if not cells or not any(cells):
            continue
        rows.append({
            "source_id": f"R{row_number:06d}",
            "text": _row_text(cells),
            "context": os.path.basename(filepath),
            "row": row_number,
            "cells": cells,
        })
    name = os.path.basename(filepath)
    return {"name": name, "kind": "csv", "rows": rows, "source_hash": _source_hash(rows, name, "csv")}


def inventory_source_from_file(filepath: str) -> dict:
    """Read a source for semantic scanning while preserving spreadsheet cells."""
    path = os.path.abspath(str(filepath or ""))
    extension = os.path.splitext(path)[1].lower()
    if extension == ".xlsx":
        return _source_from_xlsx(path)
    if extension in {".csv", ".tsv"}:
        return _source_from_delimited(path)
    if extension == ".xls":
        try:
            import pandas as pd
        except ImportError:
            text = extract_text_from_file(path)
            return inventory_source_from_text(text, name=os.path.basename(path))
        rows = []
        spreadsheet = pd.ExcelFile(path)
        for sheet in spreadsheet.sheet_names:
            frame = spreadsheet.parse(sheet, header=None, dtype=object)
            for offset, values in enumerate(frame.itertuples(index=False, name=None), start=1):
                cells = _trim_row(values)
                if not cells or not any(cells):
                    continue
                rows.append({
                    "source_id": f"{sheet}!R{offset:06d}",
                    "text": _row_text(cells),
                    "context": f"Sheet: {sheet}",
                    "sheet": sheet,
                    "row": offset,
                    "cells": cells,
                })
        name = os.path.basename(path)
        return {"name": name, "kind": "xls", "rows": rows, "source_hash": _source_hash(rows, name, "xls")}
    text = extract_text_from_file(path)
    return inventory_source_from_text(text, name=os.path.basename(path))


def inventory_source_from_files(
    filepaths: Iterable[str],
    *,
    text: str = "",
    name: str = "Forge Workshop",
) -> dict:
    """Combine Workshop text and attachments without losing per-file anchors."""
    sources = []
    if str(text or "").strip():
        sources.append(inventory_source_from_text(text, name=f"{name} text"))
    for filepath in filepaths or ():
        if str(filepath or "").strip():
            sources.append(inventory_source_from_file(str(filepath)))
    rows = []
    for source_number, source in enumerate(sources, start=1):
        source_name = str(source.get("name") or f"Source {source_number}")
        for value in source.get("rows", ()):
            row = dict(value)
            row["source_id"] = f"S{source_number:03d}:{row.get('source_id', '')}"
            context = str(row.get("context") or "").strip()
            row["context"] = f"{source_name} > {context}" if context else source_name
            rows.append(row)
    return {
        "name": name,
        "kind": "workshop",
        "rows": rows,
        "source_hash": _source_hash(rows, name, "workshop"),
    }


_HEADER_ALIASES = {
    "front": frozenset({
        "word", "term", "front", "headword", "vocabulary", "tu", "tu vung",
        "tu tieng trung", "tu tieng nhat", "tu tieng han", "english word",
        "pattern", "grammar", "cau truc", "mau ngu phap",
    }),
    "reading": frozenset({
        "reading", "pronunciation", "romanization", "pinyin", "romaji", "kana",
        "phien am", "cach doc",
    }),
    "meaning": frozenset({
        "meaning", "translation", "definition", "nghia", "nghia tieng viet",
        "nghia tv", "dich", "ban dich",
    }),
    "topic": frozenset({
        "topic", "category", "group", "theme", "chu de", "nhom", "phan nhom",
    }),
    "level": frozenset({
        "level", "proficiency", "jlpt", "jlpt level", "hsk", "hsk level",
        "topik", "topik level", "cefr", "cefr level", "cap do",
        "muc do",
    }),
}


def _header_key(value: object) -> str:
    raw = str(value or "").replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", raw)
    plain = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", plain.casefold()).strip()


def _header_map(cells: Iterable[object]) -> dict[str, int]:
    mapped = {}
    for index, cell in enumerate(cells):
        key = _header_key(cell)
        for role, aliases in _HEADER_ALIASES.items():
            if role not in mapped and key in aliases:
                mapped[role] = index
    if "front" not in mapped or len(mapped) < 2:
        return {}
    return mapped


def _row_file_key(row: Mapping) -> str:
    source_id = str(row.get("source_id") or "")
    combined = re.match(r"^(S\d+):", source_id)
    return combined.group(1) if combined else "source"


def _row_table_key(row: Mapping) -> tuple[str, str]:
    sheet = str(row.get("sheet") or row.get("context") or "table")
    return _row_file_key(row), sheet


def _looks_auxiliary_table(table_key: tuple[str, str], rows: Iterable[Mapping]) -> bool:
    sheet_name = _header_key(table_key[1])
    sheet_markers = (
        "lo trinh", "phan nhom", "nguon", "phuong phap", "method", "summary",
        "stat", "thong ke", "metadata", "readme", "guide", "huong dan",
    )
    if any(marker in sheet_name for marker in sheet_markers):
        return True
    sample = " ".join(
        _header_key(cell)
        for row in list(rows)[:8]
        for cell in row.get("cells", ())
    )
    return any(marker in sample for marker in (
        "so muc", "vai tro", "goi hoc", "cach dung", "ma nguon", "mo ta link",
        "tieu chi giu", "tieu chi giam",
    ))


def _normalized_table_level(value: object) -> str:
    text = _cell_text(value)
    match = re.match(
        r"^(HSK\s*(?:[1-6]|7\s*[-–]\s*9)|N[1-5]|TOPIK\s*(?:I{1,2}|[1-6])|[ABC][12]?)\b",
        text,
        re.IGNORECASE,
    )
    return re.sub(r"\s+", "", match.group(1)).upper() if match else text


def _normalized_language_level(value: object, lang: str) -> str:
    """Accept only a valid proficiency label for the selected language."""
    text = _cell_text(value)
    language = normalize_language(lang)
    patterns = {
        "chinese": r"^(HSK\s*(?:[1-6]|7\s*[-–—]\s*9))\b",
        "japanese": r"^(N[1-5])\b",
        "korean": r"^(TOPIK\s*(?:I{1,2}|[1-6]))\b",
        "english": r"^([ABC][12])\b",
    }
    match = re.match(patterns.get(language, r"$^"), text, re.IGNORECASE)
    if not match:
        return ""
    level = re.sub(r"\s+", "", match.group(1)).upper()
    return re.sub(r"^TOPIK", "TOPIK ", level) if language == "korean" else level


def _structured_spreadsheet_rows(
    rows: Iterable[Mapping],
    lang: str,
) -> tuple[list[dict], list[dict]]:
    """Resolve explicit spreadsheet columns locally and return unresolved rows."""
    source_rows = [dict(row) for row in rows]
    tables = {}
    for row in source_rows:
        if isinstance(row.get("cells"), list):
            tables.setdefault(_row_table_key(row), []).append(row)

    recognized = {}
    structured_files = set()
    for table_key, table_rows in tables.items():
        for offset, row in enumerate(table_rows[:50]):
            mapping = _header_map(row.get("cells", ()))
            if mapping:
                recognized[table_key] = (offset, mapping)
                structured_files.add(table_key[0])
                break

    if not recognized:
        return [], source_rows

    auxiliary_tables = {
        table_key
        for table_key, table_rows in tables.items()
        if table_key not in recognized
        and table_key[0] in structured_files
        and _looks_auxiliary_table(table_key, table_rows)
    }

    local = []
    consumed = set()
    for table_key, (header_offset, mapping) in recognized.items():
        table_rows = tables[table_key]
        header_cells = list(table_rows[header_offset].get("cells", ()))
        header_summary = " | ".join(
            _cell_text(cell) for cell in header_cells if _cell_text(cell)
        )[:600]
        table_context = (
            "Structured columns: " + header_summary
            + ". Frequency/register or Mức độ / sắc thái is not proficiency."
        )
        for offset, row in enumerate(table_rows):
            source_id = str(row.get("source_id") or "")
            consumed.add(source_id)
            cells = list(row.get("cells", ()))
            source_text = " | ".join(str(cell) for cell in cells if str(cell).strip())[:1000]
            if offset <= header_offset:
                local.append({
                    "source_id": source_id, "surface": "", "reading": "", "meaning": "",
                    "topic": "", "level": "", "decision": "skip", "confidence": 1.0,
                    "reason": "spreadsheet header", "source_text": source_text,
                })
                continue

            def cell(role: str) -> str:
                index = mapping.get(role, -1)
                return _cell_text(cells[index]) if 0 <= index < len(cells) else ""

            surface = cell("front")
            if not surface:
                local.append({
                    "source_id": source_id, "surface": "", "reading": "", "meaning": "",
                    "topic": "", "level": "", "decision": "skip", "confidence": 1.0,
                    "reason": "empty headword cell", "source_text": source_text,
                })
                continue
            decision = "keep" if _surface_matches_language(surface, lang) else "review"
            local.append({
                "source_id": source_id,
                "surface": surface,
                "reading": cell("reading"),
                "meaning": cell("meaning"),
                "topic": cell("topic"),
                "level": _normalized_language_level(cell("level"), lang),
                "decision": decision,
                "confidence": 1.0 if decision == "keep" else 0.0,
                "reason": (
                    "recognized spreadsheet columns" if decision == "keep"
                    else "headword cell does not match the target-language script"
                ),
                "source_text": source_text,
                "_ai_context": table_context,
            })

    unresolved = []
    for row in source_rows:
        source_id = str(row.get("source_id") or "")
        if source_id in consumed:
            continue
        if isinstance(row.get("cells"), list) and _row_table_key(row) in auxiliary_tables:
            cells = list(row.get("cells", ()))
            local.append({
                "source_id": source_id, "surface": "", "reading": "", "meaning": "",
                "topic": "", "level": "", "decision": "skip", "confidence": 1.0,
                "reason": "auxiliary spreadsheet sheet",
                "source_text": " | ".join(str(cell) for cell in cells if str(cell).strip())[:1000],
            })
        else:
            unresolved.append(row)
    return local, unresolved


def _compact_input_row(value: Mapping, index: int, previous_context: str) -> tuple[dict, str]:
    cells = value.get("cells")
    if isinstance(cells, list):
        values = [_bounded_text(cell, 500) for cell in cells[:16]]
    else:
        values = [_bounded_text(value.get("text"), 2000)]
    row = {"i": index, "v": values}
    context = _bounded_text(value.get("ai_context") or value.get("context"), 600)
    if context and context != previous_context:
        row["x"] = context
    return row, context or previous_context


def _chunk_rows(rows: Iterable[Mapping], *, turbo: bool = False) -> list[list[dict]]:
    row_limit = int(INVENTORY_ROWS_PER_REQUEST * (INVENTORY_TURBO_MULTIPLIER if turbo else 1))
    char_limit = int(INVENTORY_CHARS_PER_REQUEST * (INVENTORY_TURBO_MULTIPLIER if turbo else 1))
    chunks = []
    current = []
    current_chars = 0
    previous_context = ""
    for value in rows:
        source_row = dict(value)
        compact, next_context = _compact_input_row(
            source_row, len(current), previous_context,
        )
        encoded = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        if current and (
            len(current) >= row_limit or current_chars + len(encoded) > char_limit
        ):
            chunks.append(current)
            current = []
            current_chars = 0
            previous_context = ""
            compact, next_context = _compact_input_row(source_row, 0, previous_context)
            encoded = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        source_row["compact"] = compact
        current.append(source_row)
        current_chars += len(encoded)
        previous_context = next_context
    if current:
        chunks.append(current)
    return chunks


def _repair_compact_inventory_json(text: str) -> str:
    """Repair only harmless formatting slips around the scanner envelope."""
    repaired = str(text or "").lstrip("\ufeff").strip()
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    # Some OpenAI-compatible models emit {r:[...]} despite the JSON-only prompt.
    repaired = re.sub(
        r"([{,]\s*)(r|rows)\s*:",
        r'\1"\2":',
        repaired,
    )
    return repaired


def _decode_inventory_json(text: str) -> object:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as original_error:
        repaired = _repair_compact_inventory_json(text)
        if repaired == text:
            raise original_error
        value = json.loads(repaired)
    return value


def _extract_compact_rows(text: str) -> list | None:
    """Recover the only required scanner field when extra model metadata is malformed."""
    match = re.search(r"(?:\"|')?(?:r|rows)(?:\"|')?\s*:\s*(\[)", text, re.IGNORECASE)
    if not match:
        return None
    start = match.start(1)
    depth = 0
    quote = ""
    escaped = False
    for position in range(start, len(text)):
        char = text[position]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in ('\"', "'"):
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                try:
                    value = _decode_inventory_json(text[start:position + 1])
                except json.JSONDecodeError:
                    return None
                return value if isinstance(value, list) else None
    return None


def _parse_json_object(content: str) -> dict:
    text = str(content or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        value = _decode_inventory_json(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(t("inventory_ai_malformed_json")) from None
        try:
            value = _decode_inventory_json(match.group(0))
        except json.JSONDecodeError:
            value = None
        if value is None:
            rows = _extract_compact_rows(text)
            if rows is None:
                raise ValueError(t("inventory_ai_malformed_json")) from None
            return {"r": rows}
    if not isinstance(value, dict) or not isinstance(value.get("rows", value.get("r")), list):
        raise ValueError(t("inventory_ai_invalid_shape"))
    return value


def _bounded_text(value: object, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())[:limit]


def _surface_matches_language(surface: str, lang: str) -> bool:
    language = normalize_language(lang) if lang else ""
    if language == "chinese":
        return bool(re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", surface))
    if language == "japanese":
        return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", surface))
    if language == "korean":
        return bool(re.search(r"[\u1100-\u11ff\uac00-\ud7af]", surface))
    if language == "english":
        return bool(re.search(r"[A-Za-z]", surface))
    return True


def _validate_chunk_output(
    payload: Mapping,
    source_rows: Iterable[Mapping],
    *,
    lang: str = "",
) -> tuple[list[dict], int]:
    source_rows = list(source_rows)
    source_by_id = {
        str(row.get("source_id") or ""): str(row.get("text") or "")
        for row in source_rows
        if str(row.get("source_id") or "")
    }
    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raw_rows = []
        decision_names = {"k": "keep", "s": "skip", "r": "review"}
        for compact in payload.get("r", ()):
            if not isinstance(compact, list) or len(compact) < 7:
                continue
            try:
                source_index = int(compact[0])
            except (TypeError, ValueError):
                continue
            if not (0 <= source_index < len(source_rows)):
                continue
            confidence = compact[7] if len(compact) > 7 else 0
            try:
                confidence = float(confidence)
                if confidence > 1:
                    confidence /= 100
            except (TypeError, ValueError):
                confidence = 0
            raw_rows.append({
                "source_id": source_rows[source_index].get("source_id", ""),
                "surface": compact[1] if len(compact) > 1 else "",
                "reading": compact[2] if len(compact) > 2 else "",
                "meaning": compact[3] if len(compact) > 3 else "",
                "topic": compact[4] if len(compact) > 4 else "",
                "level": compact[5] if len(compact) > 5 else "",
                "decision": decision_names.get(str(compact[6]).casefold(), compact[6]),
                "confidence": confidence,
                "reason": compact[8] if len(compact) > 8 else "",
            })
    seen_source_ids = set()
    validated = []
    for raw in raw_rows:
        if not isinstance(raw, Mapping):
            continue
        source_id = _bounded_text(raw.get("source_id"), 240)
        if source_id not in source_by_id:
            continue
        decision = _bounded_text(raw.get("decision"), 16).casefold()
        if decision not in _DECISIONS:
            decision = "review"
        surface = _bounded_text(raw.get("surface"), 240)
        source_text = source_by_id[source_id]
        reason = _bounded_text(raw.get("reason"), 300)
        raw_level = _bounded_text(raw.get("level"), 80)
        level = _normalized_language_level(raw_level, lang) if lang else raw_level
        if decision in {"keep", "review"}:
            if not surface or surface not in source_text:
                decision = "review"
                surface = ""
                reason = "candidate surface is not anchored verbatim in the source row"
            elif not _surface_matches_language(surface, lang):
                decision = "review"
                reason = "candidate does not contain the expected target-language script"
            elif raw_level and not level:
                decision = "review"
                reason = "candidate level is not valid for the selected language"
        try:
            confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        validated.append({
            "source_id": source_id,
            "surface": surface,
            "reading": _bounded_text(raw.get("reading"), 240),
            "meaning": _bounded_text(raw.get("meaning"), 500),
            "topic": _bounded_text(raw.get("topic"), 160),
            "level": level,
            "decision": decision,
            "confidence": confidence,
            "reason": reason,
            "source_text": source_text[:1000],
        })
        seen_source_ids.add(source_id)
    missing = 0
    for source_id, source_text in source_by_id.items():
        if source_id in seen_source_ids:
            continue
        missing += 1
        validated.append({
            "source_id": source_id,
            "surface": "",
            "reading": "",
            "meaning": "",
            "topic": "",
            "level": "",
            "decision": "review",
            "confidence": 0.0,
            "reason": "AI returned no decision for this source row",
            "source_text": source_text[:1000],
        })
    return validated, missing


def _cache_path(cache_key: str) -> str:
    return os.path.join(INVENTORY_CACHE_DIR, f"inventory_{cache_key}.json")


def _cache_key(
    source: Mapping,
    lang: str,
    card_kind: str,
    instruction: str,
    cfg: Mapping,
) -> str:
    payload = "|".join((
        str(INVENTORY_SCANNER_VERSION),
        str(source.get("source_hash") or ""),
        normalize_language(lang),
        card_kind,
        str(cfg.get("model") or ""),
        str(instruction or ""),
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(cache_key: str) -> Optional[dict]:
    path = _cache_path(cache_key)
    try:
        if time.time() - os.path.getmtime(path) > INVENTORY_CACHE_TTL:
            return None
    except OSError:
        return None
    return read_json(
        path, None,
        lambda value: isinstance(value, dict) and isinstance(value.get("rows"), list),
    )


def _cache_set(cache_key: str, result: Mapping) -> None:
    os.makedirs(INVENTORY_CACHE_DIR, exist_ok=True)
    atomic_write_json(_cache_path(cache_key), dict(result))


def _deduplicate_candidates(
    rows: Iterable[Mapping],
    *,
    grammar: bool = False,
    card_kind: Optional[str] = None,
) -> list[dict]:
    kind = _card_kind(grammar, card_kind)
    chosen = {}
    passthrough = []
    for value in rows:
        row = dict(value)
        if not row.get("surface") or row.get("decision") == "skip":
            passthrough.append(row)
            continue
        identity, _meaning = existing_entry_identity(
            {"front": row.get("surface"), "pattern": row.get("surface")}, kind,
        )
        if not identity:
            passthrough.append(row)
            continue
        previous = chosen.get(identity)
        rank = (row.get("decision") == "keep", float(row.get("confidence") or 0.0))
        previous_rank = (
            previous.get("decision") == "keep", float(previous.get("confidence") or 0.0)
        ) if previous else (False, -1.0)
        if previous is None or rank > previous_rank:
            chosen[identity] = row
    return list(chosen.values()) + passthrough


def _inventory_from_rows(
    rows: Iterable[Mapping],
    source_hash: str,
    lang: str,
    grammar: bool = False,
    card_kind: Optional[str] = None,
) -> list[dict]:
    kind = _card_kind(grammar, card_kind)
    inventory = []
    for value in rows:
        if value.get("decision") not in {"keep", "review"} or not value.get("surface"):
            continue
        front = str(value.get("surface") or "").strip()
        identity, _meaning = existing_entry_identity(
            {"front": front, "pattern": front}, kind,
        )
        item_id = hashlib.sha256(
            f"{source_hash}|{kind}|{identity}|{value.get('source_id', '')}".encode("utf-8")
        ).hexdigest()[:24]
        inventory.append({
            "id": item_id,
            "identity": identity or front.casefold(),
            "front": front,
            "meaning": str(value.get("meaning") or "").strip(),
            "level": str(value.get("level") or "").strip(),
            "topic": str(value.get("topic") or "").strip(),
            "reading": str(value.get("reading") or "").strip(),
            "decision": str(value.get("decision") or "review"),
            "confidence": float(value.get("confidence") or 0.0),
            "reason": str(value.get("reason") or "").strip(),
            "source_id": str(value.get("source_id") or ""),
            "source_text": str(value.get("source_text") or "")[:1000],
        })
    return inventory


def inventory_from_scan_rows(
    rows: Iterable[Mapping],
    source_hash: str,
    lang: str,
    *,
    grammar: bool = False,
    card_kind: Optional[str] = None,
) -> list[dict]:
    """Rebuild actionable inventory after a user changes scan decisions."""
    kind = _card_kind(grammar, card_kind)
    canonical_rows, _catalog = canonicalize_topics(rows)
    deduplicated = _deduplicate_candidates(canonical_rows, card_kind=kind)
    return _inventory_from_rows(deduplicated, source_hash, lang, card_kind=kind)


def _scan_result(
    source: Mapping,
    source_hash: str,
    source_row_count: int,
    rows: list[dict],
    lang: str,
    card_kind: str,
    token_info: Mapping,
    *,
    unresolved: int = 0,
    mode: str,
    turbo: bool,
) -> dict:
    canonical_rows, topic_catalog = canonicalize_topics(rows)
    for row in canonical_rows:
        if row.get("decision") == "keep" and row.get("surface") and (
            not row.get("topic") or not row.get("level")
        ):
            row["decision"] = "review"
            row["reason"] = "topic or proficiency level was not assigned during pre-production"
    inventory = inventory_from_scan_rows(
        canonical_rows, source_hash, lang, card_kind=card_kind,
    )
    _save_topic_catalog(source_hash, lang, card_kind, topic_catalog)
    return {
        "schema": INVENTORY_SCANNER_VERSION,
        "source_hash": source_hash,
        "source_name": str(source.get("name") or ""),
        "source_rows": source_row_count,
        "card_kind": card_kind,
        "rows": canonical_rows,
        "inventory": inventory,
        "topic_catalog": topic_catalog,
        "counts": {
            "source_rows": source_row_count,
            "keep": sum(1 for row in canonical_rows if row.get("decision") == "keep"),
            "skip": sum(1 for row in canonical_rows if row.get("decision") == "skip"),
            "review": sum(1 for row in canonical_rows if row.get("decision") == "review"),
            "unresolved": unresolved,
        },
        "token_info": dict(token_info),
        "scan_mode": mode,
        "turbo": bool(turbo),
    }


def scan_inventory_with_ai(
    source: Mapping,
    lang: str,
    *,
    grammar: bool = False,
    card_kind: Optional[str] = None,
    custom_instruction: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    runtime_config: Optional[dict] = None,
    force_refresh: bool = False,
    turbo: bool = False,
) -> dict:
    """Classify a noisy source into supervised keep/skip/review inventory rows."""
    kind = _card_kind(grammar, card_kind)
    rows = [dict(row) for row in source.get("rows", ()) if str(row.get("source_id") or "")]
    if not rows:
        raise ValueError(t("inventory_ai_empty_source"))
    source_hash = str(source.get("source_hash") or _source_hash(
        rows,
        str(source.get("name") or ""),
        str(source.get("kind") or ""),
    ))
    local_rows, ai_rows = ([], rows)
    if not str(custom_instruction or "").strip():
        local_rows, ai_rows = _structured_spreadsheet_rows(rows, lang)
        source_by_id = {str(row.get("source_id") or ""): row for row in rows}
        local_by_id = {str(row.get("source_id") or ""): row for row in local_rows}
        needs_enrichment = {
            str(row.get("source_id") or "")
            for row in local_rows
            if row.get("surface") and (
                not _clean_topic_label(row.get("topic")) or not row.get("level")
            )
        }
        if needs_enrichment:
            local_rows = [
                row for row in local_rows
                if str(row.get("source_id") or "") not in needs_enrichment
            ]
            for source_id in needs_enrichment:
                if source_id not in source_by_id:
                    continue
                source_row = dict(source_by_id[source_id])
                source_row["ai_context"] = str(
                    local_by_id.get(source_id, {}).get("_ai_context") or ""
                )
                ai_rows.append(source_row)
    empty_tokens = {
        "prompt_tokens": 0, "completion_tokens": 0,
        "total_tokens": 0, "total_cost": 0.0, "requests": 0,
    }
    if not ai_rows:
        result = _scan_result(
            source, source_hash, len(rows), local_rows, lang, kind,
            empty_tokens, mode="structured_local", turbo=turbo,
        )
        if progress_callback:
            progress_callback(t("inventory_local_complete", count=len(result["inventory"])))
        return result

    cfg = dict(runtime_config) if isinstance(runtime_config, dict) else _api.get_api_config()
    if not cfg.get("api_key") and "localhost" not in str(cfg.get("api_base") or ""):
        raise ValueError(t("error_api_key_missing"))
    cache_source = dict(source)
    cache_source["source_hash"] = source_hash
    cache_key = _cache_key(cache_source, lang, kind, custom_instruction, cfg)
    if not force_refresh:
        cached = _cache_get(cache_key)
        if cached is not None:
            if progress_callback:
                progress_callback(t("inventory_ai_cache_hit", count=len(cached.get("inventory", ()))))
            return cached

    chunks = _chunk_rows(ai_rows, turbo=turbo)
    all_rows = list(local_rows)
    total_missing = 0
    declared_topics = [
        _clean_topic_label(row.get("topic"))
        for row in local_rows
        if _clean_topic_label(row.get("topic"))
    ] + [
        _clean_topic_label(row.get("declared_topic"))
        for row in rows
        if _clean_topic_label(row.get("declared_topic"))
    ]
    topic_catalog = []
    topic_ids = set()
    for label in declared_topics:
        identity = topic_identity(label)
        if identity and identity not in topic_ids:
            topic_catalog.append(label)
            topic_ids.add(identity)
    total_tokens = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "requests": 0,
    }
    for index, chunk in enumerate(chunks, start=1):
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        if progress_callback:
            progress_callback(t("inventory_ai_scanning", current=index, total=len(chunks)))
        preferred = json.dumps(topic_catalog[-60:], ensure_ascii=False)
        user_content = (
            f"TARGET_LANGUAGE={normalize_language(lang)}\n"
            f"TARGET_KIND={kind}\n"
            f"PREFERRED_TOPIC_LABELS={preferred}\n"
            f"USER_CONSTRAINTS={str(custom_instruction or '').strip()[:2000]}\n\n"
            + "\n".join(
                json.dumps(row["compact"], ensure_ascii=False, separators=(",", ":"))
                for row in chunk
            )
        )
        payload = {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": _INVENTORY_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": min(float(cfg.get("temperature", 0.2)), 0.2),
            "max_tokens": min(int(cfg.get("max_tokens", 8192)), 8192),
        }
        _api._apply_reasoning_effort(payload, cfg)
        enable_deepseek_json_output(payload, cfg)
        url = f"{cfg['api_base'].rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {cfg['api_key']}"}
        started_at = time.time()
        started_monotonic = time.monotonic()
        timeout = 600 if "reasoner" in str(cfg.get("model") or "") else 300
        body = _api._http_post_json(
            url, payload, headers, timeout=timeout,
            progress_callback=progress_callback, should_abort=should_abort,
        )
        total_tokens["requests"] += 1
        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(t("inventory_ai_invalid_api_response")) from None
        adapted = adapt_chat_completion_response(response_payload, cfg)
        if adapted.truncated:
            raise RuntimeError(t("error_model_output_truncated"))
        content = adapted.text
        if not content.strip() and adapted.structured_data is not None:
            content = json.dumps(adapted.structured_data, ensure_ascii=False)
        parsed = _parse_json_object(content)
        validated, missing = _validate_chunk_output(parsed, chunk, lang=lang)
        all_rows.extend(validated)
        total_missing += missing
        for value in validated:
            topic = str(value.get("topic") or "").strip()
            identity = topic_identity(topic)
            if identity and identity not in topic_ids:
                topic_catalog.append(topic)
                topic_ids.add(identity)
        usage = adapted.usage
        if usage.get("total_tokens"):
            token_info = _api._calculate_cost(
                cfg["model"], usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0), usage.get("cost"),
            )
            _api._record_token_info(
                token_info, operation="inventory_scan",
                started_at=started_at,
                duration_seconds=time.monotonic() - started_monotonic,
                provider=adapted.provider,
            )
            for key in total_tokens:
                if key == "requests":
                    continue
                total_tokens[key] += float(token_info.get(key, 0) or 0)

    result = _scan_result(
        source,
        source_hash,
        len(rows),
        all_rows,
        lang,
        kind,
        total_tokens,
        unresolved=total_missing,
        mode="hybrid" if local_rows else "ai_compact",
        turbo=turbo,
    )
    _cache_set(cache_key, result)
    if progress_callback:
        progress_callback(t("inventory_ai_complete", count=len(result["inventory"])))
    return result


__all__ = [
    "INVENTORY_SCANNER_VERSION",
    "apply_prepared_inventory",
    "canonicalize_topics",
    "inventory_from_scan_rows",
    "inventory_source_from_file",
    "inventory_source_from_files",
    "inventory_source_from_text",
    "scan_inventory_with_ai",
    "topic_catalog_instruction",
    "topic_identity",
]
