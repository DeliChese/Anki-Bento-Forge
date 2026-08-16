"""Persistent import history and deck-scan aggregation.

Storage, transformations, search, and summaries are owned here. Anki access
is injected lazily through ``scan_context_factory`` so this module has no
direct dependency on aqt, UI, workers, or AI orchestration.
"""

import os
import time

from .logger import get_logger
from .i18n import t
from .user_data import atomic_write_json, get_user_data_path, migrate_legacy_json, read_json


logger = get_logger()
_LEGACY_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════
#  IMPORT HISTORY — Lịch sử nhập JSON/tài liệu
#  Lưu cache từ vựng đã import để AI truy cập mà không cần
#  quét toàn bộ database Anki. Tiết kiệm token.
# ═══════════════════════════════════════════════════════════

_HISTORY_PATH = get_user_data_path("import_history.json")
_LEGACY_HISTORY_PATH = os.path.join(_LEGACY_CONFIG_DIR, "import_history.json")
_HISTORY_VERSION = 1
# Retained as a compatibility constant for callers that used to import it.
# Opening the factory must not use time-based full scans: imports update this
# cache incrementally, and a full scan is now bootstrap/manual only.
_HISTORY_SCAN_TTL = 24 * 3600


def _load_history() -> dict:
    """Đọc file lịch sử import"""
    migrate_legacy_json(_LEGACY_HISTORY_PATH, _HISTORY_PATH, lambda value: isinstance(value, dict))
    data = read_json(_HISTORY_PATH, {}, lambda value: isinstance(value, dict))
    if data.get("version") == _HISTORY_VERSION:
        return data
    return {
        "version": _HISTORY_VERSION,
        "last_full_scan": None,
        "entries": {},       # {lang: {front_lower: {meaning, furigana/pinyin, level, deck, imported_at, source}}}
        "import_sessions": [],  # [{timestamp, count, deck, source, lang}]
    }


def _save_history(data: dict):
    """Ghi file lịch sử import"""
    try:
        atomic_write_json(_HISTORY_PATH, data)
    except Exception as e:
        logger.warning("Lỗi ghi import_history: %s", e)


def load_import_history() -> dict:
    """Load the cached history without touching the Anki collection."""
    return _load_history()


def needs_import_history_scan(data: dict = None) -> bool:
    """Return whether a one-time bootstrap scan has not completed yet.

    Normal imports call :func:`add_to_import_history`, so an existing cache is
    deliberately never invalidated by time.  A caller may still request a
    repair/rebuild explicitly with ``force_rescan=True``.
    """
    data = data if data is not None else _load_history()
    return not bool(data.get("last_full_scan"))


def _report_scan_progress(callback, **progress):
    """Notify an optional observer without letting UI/reporting failures stop a scan."""
    if callback is None:
        return
    try:
        callback(progress)
    except Exception as e:
        logger.warning("Lỗi báo tiến độ import history: %s", e)


def _scan_cancelled(cancel_event) -> bool:
    return bool(cancel_event is not None and cancel_event.is_set())


def clear_import_history():
    """Xóa toàn bộ lịch sử import từ vựng"""
    if os.path.exists(_HISTORY_PATH):
        try:
            os.remove(_HISTORY_PATH)
            return True
        except Exception as e:
            logger.warning("Lỗi xóa import_history: %s", e)
            return False
    return True


def init_import_history(force_rescan: bool = False, scan_context_factory=None,
                        cancel_event=None, progress_callback=None) -> dict:
    """
    Khởi tạo lịch sử import: quét toàn bộ deck Anki để thu thập
    từ vựng hiện có. Chỉ quét nếu:
    - File lịch sử chưa tồn tại
    - Chưa từng bootstrap cache, hoặc ``force_rescan = True``

    ``scan_context_factory`` must be called by an Anki ``QueryOp`` when a
    collection scan is required.  The function itself stays free of Anki/Qt
    dependencies so it can be tested offline.
    - force_rescan = True

    Returns:
        dict lịch sử sau khi khởi tạo
    """
    data = _load_history()
    need_scan = force_rescan or needs_import_history_scan(data)
    if not need_scan:
        return data

    if need_scan:
        try:
            if scan_context_factory is None:
                raise RuntimeError("Anki scan context is unavailable")
            collection, language_configs = scan_context_factory()

            if not data.get("entries"):
                data["entries"] = {}

            total_scanned = 0
            notes_processed = 0
            notes_total = 0
            for lang_key, cfg in language_configs.items():
                if _scan_cancelled(cancel_event):
                    data["_scan_cancelled"] = True
                    return data
                model_name = cfg.get("model_name", "")
                front_field = cfg.get("front_field", "")

                if not model_name or not front_field:
                    continue

                if lang_key not in data["entries"]:
                    data["entries"][lang_key] = {}

                try:
                    note_ids = collection.find_notes(f'"note:{model_name}"')
                    if not note_ids:
                        continue
                    notes_total += len(note_ids)
                    _report_scan_progress(
                        progress_callback,
                        phase="scanning",
                        language=lang_key,
                        processed=notes_processed,
                        total=notes_total,
                        added=total_scanned,
                    )

                    existing_keys = set(data["entries"][lang_key].keys())
                    # Lấy field index từ model (1 lần)
                    model = collection.models.by_name(model_name)
                    if not model:
                        continue
                    field_names = [f["name"] for f in model["flds"]]
                    front_idx = field_names.index(front_field) if front_field in field_names else 0
                    meaning_idx = field_names.index("Meaning") if "Meaning" in field_names else -1
                    furi_idx = field_names.index(cfg.get("furi_label", "")) if cfg.get("furi_label", "") in field_names else -1
                    level_idx = field_names.index(cfg.get("level_field", "")) if cfg.get("level_field", "") in field_names else -1

                    # Batch query: lấy flds trực tiếp từ SQL (tránh N+1 get_note)
                    batch_size = 200
                    for i in range(0, len(note_ids), batch_size):
                        if _scan_cancelled(cancel_event):
                            data["_scan_cancelled"] = True
                            return data
                        batch = note_ids[i:i + batch_size]
                        try:
                            placeholders = ",".join("?" * len(batch))
                            rows = collection.db.all(
                                f"SELECT id, flds FROM notes WHERE id IN ({placeholders})", *batch
                            )
                        except Exception:
                            rows = []
                            for nid in batch:
                                try:
                                    note = collection.get_note(nid)
                                    rows.append((nid, "\x1f".join(str(note[f]) for f in field_names)))
                                except Exception:
                                    continue

                        for nid, flds_raw in rows:
                            if _scan_cancelled(cancel_event):
                                data["_scan_cancelled"] = True
                                return data
                            notes_processed += 1
                            try:
                                fields = flds_raw.split("\x1f")
                                if front_idx >= len(fields):
                                    continue
                                front = fields[front_idx].strip()
                                if not front:
                                    continue

                                front_lower = front.lower()
                                # Nếu đã có trong lịch sử, bỏ qua
                                if front_lower in existing_keys:
                                    continue

                                # Thu thập thông tin
                                entry = {
                                    "front": front,
                                    "front_lower": front_lower,
                                    "meaning": "",
                                    "level": "",
                                    "deck": "",
                                    "imported_at": time.time(),
                                    "source": "deck_scan",
                                }

                                # Lấy meaning
                                if meaning_idx >= 0 and meaning_idx < len(fields):
                                    entry["meaning"] = fields[meaning_idx].strip()

                                # Lấy furigana/pinyin
                                if furi_idx >= 0 and furi_idx < len(fields):
                                    val = fields[furi_idx].strip()
                                    if val:
                                        if lang_key == "japanese":
                                            entry["furigana"] = val
                                        else:
                                            entry["pinyin"] = val

                                # Lấy cấp độ
                                if level_idx >= 0 and level_idx < len(fields):
                                    entry["level"] = fields[level_idx].strip()

                                data["entries"][lang_key][front_lower] = entry
                                total_scanned += 1
                            except Exception:
                                continue
                        _report_scan_progress(
                            progress_callback,
                            phase="scanning",
                            language=lang_key,
                            processed=notes_processed,
                            total=notes_total,
                            added=total_scanned,
                        )
                except Exception as e:
                    logger.warning("Lỗi quét deck %s: %s", lang_key, e)

            if _scan_cancelled(cancel_event):
                data["_scan_cancelled"] = True
                return data

            data["last_full_scan"] = time.time()
            data["_scan_summary"] = {
                "total_words_scanned": total_scanned,
                "languages": list(data["entries"].keys()),
                "word_counts": {k: len(v) for k, v in data["entries"].items()},
            }
            _save_history(data)
            logger.info("Import history initialized: %s words scanned", total_scanned)
        except Exception as e:
            logger.warning("Lỗi init_import_history: %s", e)

    return data


def add_to_import_history(vocab_list: list, lang: str, deck_name: str = "", source: str = "manual",
                          kind: str = "vocab", learning_mode: str = "language"):
    """
    Ghi nhận từ vựng / ngữ pháp mới vào lịch sử sau mỗi lần import.

    Args:
        vocab_list: Danh sách dict item (từ vựng hoặc cấu trúc ngữ pháp)
        lang: "japanese" / "chinese" / "korean" / "english"
        deck_name: Tên deck được import vào
        source: Nguồn gốc ("manual", "ai_extract", "ai_chat", "file_import")
        kind: "vocab" hoặc "grammar" — lưu riêng 2 mục trong lịch sử
    """
    if not vocab_list:
        return

    data = _load_history()
    if not data.get("entries"):
        data["entries"] = {}
    history_key = "knowledge" if learning_mode == "knowledge" else lang
    if history_key not in data["entries"]:
        data["entries"][history_key] = {}

    now = time.time()
    added_count = 0

    for item in vocab_list:
        if not isinstance(item, dict):
            continue

        # Grammar dùng key "pattern" thay cho "front"
        front = (
            item.get("question") or item.get("cloze_text")
            if learning_mode == "knowledge"
            else item.get("front") or item.get("simplified") or item.get("pattern")
        ) or ""
        front = str(front).strip()
        if not front:
            continue

        front_lower = front.lower()

        entry = {
            "front": front,
            "front_lower": front_lower,
            "meaning": str(
                item.get("answer") or item.get("explanation") or ""
                if learning_mode == "knowledge" else item.get("meaning", "")
            ).strip(),
            "level": str(item.get("jlptlevel") or item.get("hsk_level") or "").strip(),
            "deck": deck_name,
            "imported_at": now,
            "source": source,
            "kind": kind,
            "learning_mode": learning_mode,
            # Lưu toàn bộ item gốc để có thể đưa lại vào xưởng và import lại
            "item": item,
        }

        # Furigana / Pinyin
        if learning_mode == "knowledge":
            entry["source_text"] = str(item.get("source", "")).strip()
        elif lang == "japanese":
            entry["furigana"] = str(item.get("furigana", "")).strip()
        else:
            entry["pinyin"] = str(item.get("pinyin", "")).strip()
            entry["traditional"] = str(item.get("traditional", "")).strip()

        # Topic
        entry["topic"] = str(item.get("topic", "")).strip()

        data["entries"][history_key][front_lower] = entry
        added_count += 1

    # Ghi phiên import
    if not data.get("import_sessions"):
        data["import_sessions"] = []
    data["import_sessions"].append({
        "timestamp": now,
        "count": added_count,
        "deck": deck_name,
        "source": source,
        "lang": history_key,
        "learning_mode": learning_mode,
    })
    # Giới hạn 100 phiên gần nhất
    if len(data["import_sessions"]) > 100:
        data["import_sessions"] = data["import_sessions"][-100:]

    _save_history(data)
    logger.info("Import history: +%s items (%s, %s)", added_count, history_key, source)


def get_import_history(lang: str = None, limit: int = 2000) -> dict:
    """
    Lấy lịch sử từ vựng đã import để cung cấp cho AI.

    Args:
        lang: Lọc theo ngôn ngữ (None = tất cả)
        limit: Giới hạn số từ trả về (để tiết kiệm token)

    Returns:
        dict với keys: total_count, words (list), sessions, summary
    """
    data = _load_history()
    entries = data.get("entries", {})

    result = {
        "total_count": 0,
        "words": [],
        "sessions": data.get("import_sessions", [])[-20:],  # 20 phiên gần nhất
        "summary": {},
    }

    # Tổng hợp
    for l, words in entries.items():
        if lang and l != lang:
            continue
        result["summary"][l] = {
            "count": len(words),
            "levels": {},
            "topics": {},
        }
        result["total_count"] += len(words)

        # Thống kê cấp độ & chủ đề
        for w in words.values():
            lvl = w.get("level", "")
            if lvl:
                result["summary"][l]["levels"][lvl] = result["summary"][l]["levels"].get(lvl, 0) + 1
            topic = w.get("topic", "")
            if topic:
                result["summary"][l]["topics"][topic] = result["summary"][l]["topics"].get(topic, 0) + 1

    # Lấy danh sách từ (có giới hạn)
    all_words = []
    for l, words in entries.items():
        if lang and l != lang:
            continue
        for w in words.values():
            all_words.append({
                "front": w.get("front", ""),
                "meaning": w.get("meaning", ""),
                "level": w.get("level", ""),
                "deck": w.get("deck", ""),
                "lang": l,
                "imported_at": w.get("imported_at", 0),
            })

    # Sắp xếp theo thời gian import (mới nhất trước)
    all_words.sort(key=lambda x: x.get("imported_at", 0), reverse=True)
    result["words"] = all_words[:limit]

    return result


def get_import_history_items(lang: str = None, limit: int = 5000, kind: str = None) -> list:
    """
    Lấy từ vựng / ngữ pháp trong lịch sử import dưới dạng item dict tương thích
    với xưởng (để đưa lại vào xưởng và import lại). Mới nhất trước.

    Args:
        lang: Lọc theo ngôn ngữ (None = tất cả)
        limit: Giới hạn số mục trả về
        kind: Lọc theo loại ("vocab" / "grammar"; None = tất cả)

    Returns:
        List [(lang, item_dict), ...] — ưu tiên item gốc đã lưu trong lịch sử;
        nếu entry cũ chưa có item thì dựng lại từ các field đã lưu.
    """
    data = _load_history()
    entries = data.get("entries", {})
    result = []
    for l, words in entries.items():
        if lang and l != lang:
            continue
        for w in words.values():
            if kind and w.get("kind", "vocab") != kind:
                continue
            item = w.get("item")
            if not isinstance(item, dict):
                item = {
                    "front": w.get("front", ""),
                    "meaning": w.get("meaning", ""),
                    "topic": w.get("topic", ""),
                }
                level = w.get("level", "")
                if level:
                    if l == "japanese":
                        item["jlptlevel"] = level
                    else:
                        item["hsk_level"] = level
                if w.get("furigana"):
                    item["furigana"] = w["furigana"]
                if w.get("pinyin"):
                    item["pinyin"] = w["pinyin"]
                if w.get("traditional"):
                    item["traditional"] = w["traditional"]
            else:
                item = dict(item)  # tránh mutate dữ liệu gốc trong file
                if not item.get("front") and w.get("learning_mode") != "knowledge":
                    item["front"] = w.get("front", "")
            is_knowledge = w.get("learning_mode") == "knowledge"
            if not is_knowledge:
                item.setdefault("kind", w.get("kind", "vocab"))
            if not item.get("front") and not is_knowledge:
                continue
            result.append((l, w.get("imported_at", 0), item))
    result.sort(key=lambda x: x[1], reverse=True)
    return [(l, it) for l, _, it in result[:limit]]


def search_import_history(query: str, lang: str = None, limit: int = 50) -> list:
    """
    Tìm kiếm trong lịch sử import.

    Args:
        query: Từ khóa tìm kiếm
        lang: Lọc theo ngôn ngữ
        limit: Giới hạn kết quả

    Returns:
        List các từ khớp
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    data = _load_history()
    entries = data.get("entries", {})
    results = []

    for l, words in entries.items():
        if lang and l != lang:
            continue
        for w in words.values():
            front = w.get("front", "").lower()
            meaning = w.get("meaning", "").lower()
            furi = w.get("furigana", "").lower()
            pinyin = w.get("pinyin", "").lower()

            if (query_lower in front or query_lower in meaning
                    or query_lower in furi or query_lower in pinyin):
                results.append({
                    "front": w.get("front", ""),
                    "meaning": w.get("meaning", ""),
                    "level": w.get("level", ""),
                    "deck": w.get("deck", ""),
                    "lang": l,
                })

        if len(results) >= limit:
            break

    return results[:limit]


def get_history_summary_text(lang: str = None, max_words_for_ai: int = 50) -> str:
    """
    Tạo text tóm tắt lịch sử để gửi cho AI (tiết kiệm token).
    Tách biệt rõ ràng Japanese và Chinese.

    Args:
        lang: Ngôn ngữ cần tóm tắt (None = cả hai)
        max_words_for_ai: Số từ tối đa gửi cho AI

    Returns:
        Text mô tả lịch sử
    """
    if lang:
        # Chỉ lấy 1 ngôn ngữ
        history = get_import_history(lang=lang, limit=max_words_for_ai)
        return _build_single_lang_summary(history, lang)
    else:
        # Lấy cả hai, tách biệt rõ ràng
        parts = []
        parts.append(t("history_ai_overview"))
        parts.append("═" * 50)

        languages = ["japanese", "chinese", "korean", "english"]
        for l in languages:
            h = get_import_history(lang=l, limit=max_words_for_ai // len(languages))
            summary_text = _build_single_lang_summary(h, l)
            if summary_text:
                parts.append(summary_text)
                parts.append("")  # blank line between languages

        return "\n".join(parts)


def _build_single_lang_summary(history: dict, lang: str) -> str:
    """Xây dựng text tóm tắt cho MỘT ngôn ngữ"""
    parts = []

    language_key = {
        "japanese": "history_ai_lang_japanese",
        "chinese": "history_ai_lang_chinese",
        "korean": "history_ai_lang_korean",
        "english": "history_ai_lang_english",
    }.get(lang, "history_ai_lang_japanese")
    parts.append(t(language_key))

    summary = history.get("summary", {}).get(lang, {})
    parts.append("   " + t("history_ai_total", count=summary.get("count", 0)))

    if summary.get("levels"):
        levels_str = ", ".join(f"{k}:{v}" for k, v in sorted(summary["levels"].items()))
        parts.append("   " + t("history_ai_levels", levels=levels_str))

    if summary.get("topics"):
        top_topics = sorted(summary["topics"].items(), key=lambda x: -x[1])[:5]
        topics_str = ", ".join(f"{k}({v})" for k, v in top_topics)
        parts.append("   " + t("history_ai_topics", topics=topics_str))

    # Từ gần đây
    words = history.get("words", [])
    if words:
        parts.append("   " + t("history_ai_recent", count=min(len(words), 30)))
        for w in words[:30]:
            lvl = f" [{w.get('level', '')}]" if w.get("level") else ""
            parts.append(f"      • {w['front']} = {w['meaning']}{lvl}")

    return "\n".join(parts)

__all__ = [
    "init_import_history",
    "add_to_import_history",
    "get_import_history",
    "get_import_history_items",
    "search_import_history",
    "get_history_summary_text",
    "clear_import_history",
    "load_import_history",
    "needs_import_history_scan",
]
