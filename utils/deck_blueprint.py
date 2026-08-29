"""Pure source-outline and editable deck-blueprint contracts.

This module deliberately has no Anki or Qt imports.  It preserves heading
provenance before AI sees a vocabulary list and validates the proposed deck
tree before any collection mutation is allowed.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Iterable, Mapping, Sequence

from .import_quality import normalize_for_comparison


_MARKDOWN_HEADING_RE = re.compile(
    r"^\s{0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?\s*$"
)
_PLAIN_HEADING_RE = re.compile(r"^\s*H([1-6])\s*[:\-]\s*(.+?)\s*$", re.I)
_HTML_HEADING_RE = re.compile(r"<\s*h[1-6]\b", re.I)
_LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")


class _OutlineHTMLParser(HTMLParser):
    """Convert rich clipboard headings to a small Markdown-like stream."""

    _BLOCK_TAGS = {
        "address", "blockquote", "div", "li", "p", "pre", "section",
        "table", "tr", "ul", "ol", "br",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._heading_level = 0
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self._newline()
            self._heading_level = int(tag[1])
            self._heading_parts = []
        elif tag in self._BLOCK_TAGS:
            self._newline()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._heading_level and tag == f"h{self._heading_level}":
            title = " ".join("".join(self._heading_parts).split())
            if title:
                self._parts.append(f"{'#' * self._heading_level} {title}")
            self._parts.append("\n")
            self._heading_level = 0
            self._heading_parts = []
        elif tag in self._BLOCK_TAGS:
            self._newline()

    def handle_data(self, data):
        if self._heading_level:
            self._heading_parts.append(data)
        else:
            self._parts.append(data)

    def _newline(self):
        if self._parts and not self._parts[-1].endswith("\n"):
            self._parts.append("\n")

    def text(self) -> str:
        return "".join(self._parts)


def html_to_outline_text(html_text: str) -> str:
    """Return text with rich H1-H6 blocks represented as Markdown headings."""
    parser = _OutlineHTMLParser()
    parser.feed(str(html_text or ""))
    parser.close()
    return parser.text()


def _heading_from_line(line: str):
    markdown = _MARKDOWN_HEADING_RE.match(line)
    if markdown:
        return len(markdown.group(1)), markdown.group(2).strip()
    explicit = _PLAIN_HEADING_RE.match(line)
    if explicit:
        return int(explicit.group(1)), explicit.group(2).strip()
    return None


def parse_structured_source(
    text: str,
    html_text: str = "",
    *,
    unsectioned_title: str = "Unsectioned",
) -> list[dict]:
    """Parse H1-H6 source into ordered sections with stable heading paths.

    Rich HTML wins only when it really contains heading tags.  This matters for
    ``QTextEdit.toHtml()``, which always returns an HTML wrapper even when the
    user pasted plain text or Markdown.
    """
    source = (
        html_to_outline_text(html_text)
        if html_text and _HTML_HEADING_RE.search(html_text)
        else str(text or "")
    )
    sections: list[dict] = []
    heading_stack: dict[int, str] = {}
    current = None

    def start_section(level: int, title: str):
        nonlocal current
        title = re.sub(r"\s+", " ", str(title or "")).strip()[:200] or unsectioned_title
        for old_level in tuple(heading_stack):
            if old_level >= level:
                del heading_stack[old_level]
        heading_stack[level] = title
        path = [heading_stack[key] for key in sorted(heading_stack)]
        current = {
            "id": f"section-{len(sections) + 1}",
            "level": level,
            "title": title,
            "path": path,
            "content": "",
            "word_count": 0,
        }
        sections.append(current)

    content_lines: list[str] = []

    def flush_content():
        nonlocal content_lines
        if current is not None:
            cleaned = "\n".join(content_lines).strip()
            current["content"] = cleaned
            current["word_count"] = sum(
                1 for value in cleaned.splitlines() if value.strip()
            )
        content_lines = []

    for raw_line in source.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = _heading_from_line(raw_line)
        if heading:
            flush_content()
            start_section(*heading)
            continue
        if current is None and raw_line.strip():
            start_section(1, unsectioned_title)
        if current is not None:
            content_lines.append(raw_line)
    flush_content()

    return sections


def flatten_section_content(sections: Sequence[Mapping]) -> str:
    """Return source content without heading lines for the batch extractor."""
    return "\n".join(
        str(section.get("content") or "").strip()
        for section in sections
        if str(section.get("content") or "").strip()
    )


def outline_for_prompt(sections: Sequence[Mapping], limit: int = 160) -> list[dict]:
    """Build a bounded, content-free outline safe to include in an AI prompt."""
    outline = []
    for section in sections[: max(1, int(limit))]:
        path = [str(value).strip() for value in section.get("path", ()) if str(value).strip()]
        outline.append({
            "id": str(section.get("id") or ""),
            "level": max(1, min(6, int(section.get("level") or 1))),
            "path": path,
            "item_count": max(0, int(section.get("word_count") or 0)),
        })
    return outline


def _normalized_front(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _front_from_source_line(line: str) -> str:
    value = _LIST_PREFIX_RE.sub("", str(line or "").strip())
    if not value:
        return ""
    for separator in ("\t", "|", ",", "：", ":", " — ", " – ", " - "):
        if separator in value:
            value = value.split(separator, 1)[0].strip()
            break
    return value.strip(" \"'`[]()")


def build_source_context_index(sections: Sequence[Mapping]) -> dict[str, dict]:
    """Map source vocabulary surfaces to the first section that owns them."""
    index: dict[str, dict] = {}
    for section in sections:
        context = {
            "source_section_id": str(section.get("id") or ""),
            "source_heading": str(section.get("title") or ""),
            "source_heading_level": int(section.get("level") or 1),
            "source_path": [
                str(value).strip()
                for value in section.get("path", ())
                if str(value).strip()
            ],
        }
        for line in str(section.get("content") or "").splitlines():
            front = _normalized_front(_front_from_source_line(line))
            if front and front not in index:
                index[front] = context
    return index


def attach_source_context(vocab_list: Iterable[Mapping], sections: Sequence[Mapping]) -> list[dict]:
    """Copy vocabulary rows and attach heading provenance when a surface matches."""
    index = build_source_context_index(sections)
    enriched = []
    for raw_item in vocab_list or ():
        item = dict(raw_item)
        front = item.get("front") or item.get("simplified") or item.get("pattern") or ""
        context = index.get(_normalized_front(front))
        if context:
            item.update(context)
        enriched.append(item)
    return enriched


def sanitize_deck_segment(value, fallback: str = "") -> str:
    """Normalize one Anki deck path segment without creating extra hierarchy."""
    segment = re.sub(r"\s+", " ", str(value or "").replace("::", " ")).strip()
    segment = "".join(char for char in segment if char >= " " and char not in "\r\n")
    return (segment or fallback).strip()[:80]


def normalize_deck_blueprint(
    organization: Mapping,
    vocab_list: Sequence[Mapping],
    *,
    default_parent: str = "AI Deck Blueprint",
    unassigned_name: str = "Unassigned",
) -> dict:
    """Validate an AI proposal and make every known word assignment observable."""
    inventory: dict[str, str] = {}
    for item in vocab_list or ():
        front = item.get("front") or item.get("simplified") or item.get("pattern") or ""
        key = _normalized_front(front)
        if key and key not in inventory:
            inventory[key] = str(front).strip()

    parent_map: dict[str, dict] = {}
    assigned: set[str] = set()
    for raw_parent in organization.get("decks", ()) if isinstance(organization, Mapping) else ():
        if not isinstance(raw_parent, Mapping):
            continue
        parent_name = sanitize_deck_segment(raw_parent.get("parent"), default_parent)
        if not parent_name:
            continue
        parent_key = parent_name.casefold()
        parent = parent_map.setdefault(parent_key, {"parent": parent_name, "sub_decks": []})
        sub_map = {sub["name"].casefold(): sub for sub in parent["sub_decks"]}
        for raw_sub in raw_parent.get("sub_decks", ()):
            if not isinstance(raw_sub, Mapping):
                continue
            sub_name = sanitize_deck_segment(raw_sub.get("name"), "General")
            sub_key = sub_name.casefold()
            sub = sub_map.get(sub_key)
            if sub is None:
                sub = {
                    "name": sub_name,
                    "description": str(raw_sub.get("description") or "").strip(),
                    "word_count": 0,
                    "words": [],
                }
                parent["sub_decks"].append(sub)
                sub_map[sub_key] = sub
            for raw_word in raw_sub.get("words", ()):
                key = _normalized_front(raw_word)
                if key in inventory and key not in assigned:
                    sub["words"].append(inventory[key])
                    assigned.add(key)

    missing = [surface for key, surface in inventory.items() if key not in assigned]
    if missing:
        parent_name = sanitize_deck_segment(default_parent, "AI Deck Blueprint")
        parent = parent_map.setdefault(
            parent_name.casefold(), {"parent": parent_name, "sub_decks": []}
        )
        sub_name = sanitize_deck_segment(unassigned_name, "Unassigned")
        target = next(
            (sub for sub in parent["sub_decks"] if sub["name"].casefold() == sub_name.casefold()),
            None,
        )
        if target is None:
            target = {
                "name": sub_name,
                "description": "",
                "word_count": 0,
                "words": [],
            }
            parent["sub_decks"].append(target)
        target["words"].extend(missing)

    decks = []
    for parent in parent_map.values():
        parent["sub_decks"] = [
            sub for sub in parent["sub_decks"] if sub.get("words") or not inventory
        ]
        for sub in parent["sub_decks"]:
            sub["word_count"] = len(sub.get("words", ()))
        if parent["sub_decks"]:
            decks.append(parent)

    return {
        "suggestion": str(
            organization.get("suggestion") or "" if isinstance(organization, Mapping) else ""
        ).strip(),
        "decks": decks,
        "unassigned_count": len(missing),
    }


def deck_names_from_blueprint(organization: Mapping) -> list[str]:
    """Return unique parent and parent::sub names in stable display order."""
    names: list[str] = []
    seen = set()
    for parent_info in organization.get("decks", ()) if isinstance(organization, Mapping) else ():
        if not isinstance(parent_info, Mapping):
            continue
        parent = sanitize_deck_segment(parent_info.get("parent"))
        if not parent:
            continue
        if parent.casefold() not in seen:
            names.append(parent)
            seen.add(parent.casefold())
        for sub_info in parent_info.get("sub_decks", ()):
            if not isinstance(sub_info, Mapping):
                continue
            sub = sanitize_deck_segment(sub_info.get("name"))
            if not sub:
                continue
            full_name = f"{parent}::{sub}"
            if full_name.casefold() not in seen:
                names.append(full_name)
                seen.add(full_name.casefold())
    return names


def read_blueprint_existing_cards(collection, cfg: Mapping) -> list[dict]:
    """Read canonical duplicate fields for the Blueprint vocabulary note type.

    The query is intentionally global to the note type, not limited to a target
    deck.  Moving the proposed branch must never become a duplicate bypass.
    Missing models are a normal first-run state and produce an empty snapshot.
    """
    models = []
    seen_model_ids = set()
    for model_name in (cfg["model_name"], *cfg.get("old_model_names", ())):
        model = collection.models.by_name(model_name)
        try:
            model_id = int(model["id"])
        except (KeyError, TypeError, ValueError):
            continue
        if model_id not in seen_model_ids:
            models.append(model_id)
            seen_model_ids.add(model_id)
    if not models:
        return []
    front_field = str(cfg.get("front_field") or "")
    meaning_field = str((cfg.get("json_field_map") or {}).get("meaning") or "Meaning")
    cards = []
    seen_note_ids = set()
    for model_id in models:
        for note_id in collection.find_notes(f'"mid:{model_id}"'):
            try:
                normalized_note_id = int(note_id)
                if normalized_note_id in seen_note_ids:
                    continue
                note = collection.get_note(note_id)
                front = str(note[front_field]).strip()
                meaning = str(note[meaning_field]).strip()
            except Exception:
                continue
            if normalize_for_comparison(front):
                cards.append({
                    "front": front, "meaning": meaning, "nid": normalized_note_id,
                })
                seen_note_ids.add(normalized_note_id)
    return cards


def build_blueprint_import_plan(
    organization: Mapping,
    vocab_list: Sequence[Mapping],
    existing_cards: Sequence[Mapping] = (),
    *,
    detect_key: str = "front",
) -> dict:
    """Build a fail-closed, add-only multi-deck import plan.

    A surface assigned more than once, an ambiguous source surface, or an
    existing note with a different meaning is never emitted as an import entry.
    The result is pure data and remains reviewable before any Anki mutation.
    """
    inventory: dict[str, list[dict]] = {}
    for raw_item in vocab_list or ():
        if not isinstance(raw_item, Mapping):
            continue
        item = dict(raw_item)
        front = item.get(detect_key) or item.get("front") or item.get("simplified") or ""
        key = normalize_for_comparison(front)
        if key:
            inventory.setdefault(key, []).append(item)

    existing: dict[str, list[dict]] = {}
    for raw_card in existing_cards or ():
        if not isinstance(raw_card, Mapping):
            continue
        key = normalize_for_comparison(raw_card.get("front"))
        if key:
            existing.setdefault(key, []).append(dict(raw_card))

    groups: list[dict] = []
    group_index: dict[str, dict] = {}
    assigned = set()
    duplicate_count = 0
    conflict_count = 0
    missing_assignment_count = 0
    conflict_examples = []

    for parent_info in organization.get("decks", ()) if isinstance(organization, Mapping) else ():
        if not isinstance(parent_info, Mapping):
            continue
        parent = sanitize_deck_segment(parent_info.get("parent"))
        if not parent:
            continue
        for sub_info in parent_info.get("sub_decks", ()):
            if not isinstance(sub_info, Mapping):
                continue
            sub = sanitize_deck_segment(sub_info.get("name"))
            if not sub:
                continue
            deck_name = f"{parent}::{sub}"
            group = group_index.get(deck_name.casefold())
            if group is None:
                group = {"deck_name": deck_name, "entries": []}
                group_index[deck_name.casefold()] = group
                groups.append(group)

            for raw_word in sub_info.get("words", ()):
                key = normalize_for_comparison(raw_word)
                if not key or key not in inventory:
                    missing_assignment_count += 1
                    continue
                if key in assigned:
                    duplicate_count += 1
                    continue
                assigned.add(key)

                candidates = inventory[key]
                meanings = {
                    normalize_for_comparison(candidate.get("meaning"))
                    for candidate in candidates
                    if normalize_for_comparison(candidate.get("meaning"))
                }
                if len(candidates) != 1 or len(meanings) > 1:
                    conflict_count += 1
                    conflict_examples.append(str(raw_word).strip())
                    continue

                item = candidates[0]
                meaning_key = normalize_for_comparison(item.get("meaning"))
                old_cards = existing.get(key, ())
                if old_cards:
                    old_meanings = {
                        normalize_for_comparison(card.get("meaning"))
                        for card in old_cards
                        if normalize_for_comparison(card.get("meaning"))
                    }
                    if meaning_key and old_meanings and meaning_key not in old_meanings:
                        conflict_count += 1
                        conflict_examples.append(str(raw_word).strip())
                    else:
                        duplicate_count += 1
                    continue

                group["entries"].append({
                    "item": item,
                    "action": "add",
                    "nid": None,
                    "update_fields": [],
                    "audio_enabled": (False, False, False),
                })

    groups = [group for group in groups if group["entries"]]
    unassigned_count = sum(1 for key in inventory if key not in assigned)
    new_count = sum(len(group["entries"]) for group in groups)
    return {
        "groups": groups,
        "new": new_count,
        "duplicates": duplicate_count,
        "conflicts": conflict_count,
        "unassigned": unassigned_count,
        "missing_assignments": missing_assignment_count,
        "skipped": (
            duplicate_count + conflict_count + unassigned_count + missing_assignment_count
        ),
        "conflict_examples": conflict_examples[:10],
    }


def recheck_blueprint_import_plan(
    plan: Mapping,
    existing_cards: Sequence[Mapping],
    *,
    detect_key: str = "front",
) -> dict:
    """Recheck an approved add-only plan against the latest collection state."""
    existing: dict[str, set[str]] = {}
    for card in existing_cards or ():
        if not isinstance(card, Mapping):
            continue
        key = normalize_for_comparison(card.get("front"))
        if key:
            existing.setdefault(key, set()).add(
                normalize_for_comparison(card.get("meaning"))
            )

    groups = []
    late_duplicates = 0
    late_conflicts = 0
    for raw_group in plan.get("groups", ()) if isinstance(plan, Mapping) else ():
        if not isinstance(raw_group, Mapping):
            continue
        entries = []
        for raw_entry in raw_group.get("entries", ()):
            if not isinstance(raw_entry, Mapping) or raw_entry.get("action") != "add":
                continue
            item = raw_entry.get("item") or {}
            front = item.get(detect_key) or item.get("front") or item.get("simplified") or ""
            key = normalize_for_comparison(front)
            if not key:
                continue
            meaning = normalize_for_comparison(item.get("meaning"))
            if key in existing:
                old_meanings = {value for value in existing[key] if value}
                if meaning and old_meanings and meaning not in old_meanings:
                    late_conflicts += 1
                else:
                    late_duplicates += 1
                continue
            entries.append(dict(raw_entry))
            existing[key] = {meaning}
        if entries:
            groups.append({"deck_name": str(raw_group.get("deck_name") or ""), "entries": entries})
    return {
        **dict(plan),
        "groups": groups,
        "new": sum(len(group["entries"]) for group in groups),
        "late_duplicates": late_duplicates,
        "late_conflicts": late_conflicts,
    }


def create_blueprint_decks(collection, organization: Mapping) -> dict:
    """Create only approved deck names and report which names already existed.

    The caller must run this inside an undo-aware Anki collection operation.
    This function never renames, deletes, or moves an existing deck.
    """
    names = deck_names_from_blueprint(organization)
    existing = {str(name) for name in collection.decks.all_names()}
    result = {"created": [], "reused": [], "ids": {}}
    for name in names:
        was_present = name in existing
        deck_id = collection.decks.id(name)
        result["ids"][name] = deck_id
        result["reused" if was_present else "created"].append(name)
        existing.add(name)
    return result
