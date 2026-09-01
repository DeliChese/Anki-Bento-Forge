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

INVENTORY_SCANNER_VERSION = 1
INVENTORY_ROWS_PER_REQUEST = 90
INVENTORY_CHARS_PER_REQUEST = 14_000
INVENTORY_CACHE_TTL = 14 * 24 * 3600
INVENTORY_CACHE_DIR = get_user_data_path(os.path.join("cache", "ai_inventory"))

_DECISIONS = {"keep", "skip", "review"}
_LEVEL_FIELDS = {
    "japanese": "jlptlevel",
    "chinese": "hsk_level",
    "korean": "topik_level",
    "english": "cefr_level",
}

_INVENTORY_SYSTEM_PROMPT = """You are an inventory scanner for a language-card factory.
The input is JSONL. Every object has an immutable source_id plus exact row text and optional context.

GOAL
- Find only target-language headwords, fixed expressions, or grammar patterns that are suitable card candidates.
- Distinguish the main lexical item from row numbers, headers, readings/romanization, translations, examples, notes, labels, frequency/status text, and decorative content.
- Infer a concise broad topic and a proficiency level when reasonably supported. Reuse PREFERRED_TOPIC_LABELS when semantically suitable.
- A row may yield multiple candidate objects. If it yields none, return one skip or review object for that source_id.

DECISIONS
- keep: clearly a card-worthy target item.
- skip: clearly auxiliary/non-target material. State a short reason. If a plausible target candidate exists but you still skip the row, include its exact surface so the user can restore it.
- review: ambiguous layout, uncertain target item, or insufficient evidence. Never silently skip uncertainty.

HARD CONSTRAINTS
1. source_id must exactly match an input source_id.
2. For keep/review candidates, surface must occur verbatim inside that source row. Never invent or normalize the surface.
3. Do not treat serial numbers, column headers, isolated readings, isolated translations, sentences/examples, or notes as headwords.
4. Preserve supplied meaning/reading/level/topic when present; otherwise use an empty string unless topic/level can be classified safely.
5. Return JSON only. No markdown or prose.

OUTPUT
{"rows":[{"source_id":"...","surface":"","reading":"","meaning":"","topic":"","level":"","decision":"keep|skip|review","confidence":0.0,"reason":""}]}
"""


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


def _chunk_rows(rows: Iterable[Mapping]) -> list[list[dict]]:
    chunks = []
    current = []
    current_chars = 0
    for value in rows:
        row = {
            "source_id": str(value.get("source_id") or ""),
            "text": str(value.get("text") or ""),
            "context": str(value.get("context") or ""),
        }
        encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        if current and (
            len(current) >= INVENTORY_ROWS_PER_REQUEST
            or current_chars + len(encoded) > INVENTORY_CHARS_PER_REQUEST
        ):
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(row)
        current_chars += len(encoded)
    if current:
        chunks.append(current)
    return chunks


def _parse_json_object(content: str) -> dict:
    text = str(content or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("inventory scanner returned no JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
        raise ValueError("inventory scanner response must contain a rows array")
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
    source_by_id = {
        str(row.get("source_id") or ""): str(row.get("text") or "")
        for row in source_rows
        if str(row.get("source_id") or "")
    }
    seen_source_ids = set()
    validated = []
    for raw in payload.get("rows", ()):
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
        if decision in {"keep", "review"}:
            if not surface or surface not in source_text:
                decision = "review"
                surface = ""
                reason = "candidate surface is not anchored verbatim in the source row"
            elif not _surface_matches_language(surface, lang):
                decision = "review"
                reason = "candidate does not contain the expected target-language script"
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
            "level": _bounded_text(raw.get("level"), 80),
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


def _cache_key(source: Mapping, lang: str, grammar: bool, instruction: str, cfg: Mapping) -> str:
    payload = "|".join((
        str(INVENTORY_SCANNER_VERSION),
        str(source.get("source_hash") or ""),
        normalize_language(lang),
        "grammar" if grammar else "vocab",
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


def _deduplicate_candidates(rows: Iterable[Mapping], *, grammar: bool) -> list[dict]:
    kind = "grammar" if grammar else "vocab"
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


def _inventory_from_rows(rows: Iterable[Mapping], source_hash: str, lang: str, grammar: bool) -> list[dict]:
    kind = "grammar" if grammar else "vocab"
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
        })
    return inventory


def inventory_from_scan_rows(
    rows: Iterable[Mapping],
    source_hash: str,
    lang: str,
    *,
    grammar: bool = False,
) -> list[dict]:
    """Rebuild actionable inventory after a user changes scan decisions."""
    deduplicated = _deduplicate_candidates(rows, grammar=grammar)
    return _inventory_from_rows(deduplicated, source_hash, lang, grammar)


def scan_inventory_with_ai(
    source: Mapping,
    lang: str,
    *,
    grammar: bool = False,
    custom_instruction: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    runtime_config: Optional[dict] = None,
    force_refresh: bool = False,
) -> dict:
    """Classify a noisy source into supervised keep/skip/review inventory rows."""
    rows = [dict(row) for row in source.get("rows", ()) if str(row.get("source_id") or "")]
    if not rows:
        raise ValueError(t("inventory_ai_empty_source"))
    cfg = dict(runtime_config) if isinstance(runtime_config, dict) else _api.get_api_config()
    if not cfg.get("api_key") and "localhost" not in str(cfg.get("api_base") or ""):
        raise ValueError(t("error_api_key_missing"))
    source_hash = str(source.get("source_hash") or _source_hash(
        rows,
        str(source.get("name") or ""),
        str(source.get("kind") or ""),
    ))
    cache_source = dict(source)
    cache_source["source_hash"] = source_hash
    cache_key = _cache_key(cache_source, lang, grammar, custom_instruction, cfg)
    if not force_refresh:
        cached = _cache_get(cache_key)
        if cached is not None:
            if progress_callback:
                progress_callback(t("inventory_ai_cache_hit", count=len(cached.get("inventory", ()))))
            return cached

    chunks = _chunk_rows(rows)
    all_rows = []
    total_missing = 0
    topic_catalog = []
    total_tokens = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
    }
    for index, chunk in enumerate(chunks, start=1):
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        if progress_callback:
            progress_callback(t("inventory_ai_scanning", current=index, total=len(chunks)))
        preferred = json.dumps(topic_catalog[-60:], ensure_ascii=False)
        user_content = (
            f"TARGET_LANGUAGE={normalize_language(lang)}\n"
            f"TARGET_KIND={'grammar' if grammar else 'vocabulary'}\n"
            f"PREFERRED_TOPIC_LABELS={preferred}\n"
            f"USER_CONSTRAINTS={str(custom_instruction or '').strip()[:2000]}\n\n"
            + "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in chunk)
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
        adapted = adapt_chat_completion_response(json.loads(body), cfg)
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
            if topic and topic.casefold() not in {entry.casefold() for entry in topic_catalog}:
                topic_catalog.append(topic)
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
                total_tokens[key] += float(token_info.get(key, 0) or 0)

    inventory = inventory_from_scan_rows(
        all_rows, source_hash, lang, grammar=grammar,
    )
    result = {
        "schema": INVENTORY_SCANNER_VERSION,
        "source_hash": source_hash,
        "source_name": str(source.get("name") or ""),
        "source_rows": len(rows),
        "rows": all_rows,
        "inventory": inventory,
        "counts": {
            "source_rows": len(rows),
            "keep": sum(1 for row in all_rows if row.get("decision") == "keep"),
            "skip": sum(1 for row in all_rows if row.get("decision") == "skip"),
            "review": sum(1 for row in all_rows if row.get("decision") == "review"),
            "unresolved": total_missing,
        },
        "token_info": total_tokens,
    }
    _cache_set(cache_key, result)
    if progress_callback:
        progress_callback(t("inventory_ai_complete", count=len(inventory)))
    return result


__all__ = [
    "INVENTORY_SCANNER_VERSION",
    "inventory_from_scan_rows",
    "inventory_source_from_file",
    "inventory_source_from_files",
    "inventory_source_from_text",
    "scan_inventory_with_ai",
]
