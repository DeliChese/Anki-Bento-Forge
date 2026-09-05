"""Profile-local, language-specific topic catalog for focused AI creation."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from .user_data import atomic_write_json, read_json


_SUPPORTED_LANGUAGES = {"japanese", "chinese", "korean", "english"}
_MAX_TOPICS_PER_LANGUAGE = 300
_MAX_TOPIC_LENGTH = 80
_MAX_FILE_BYTES = 128 * 1024


class TopicCatalogError(ValueError):
    """A topic cannot be stored safely in the learner's catalog."""


def normalize_topic(value: object) -> str:
    """Return one display-safe topic label without changing its casing."""
    topic = unicodedata.normalize("NFKC", str(value or ""))
    if re.search(r"[\x00-\x1f]", topic):
        raise TopicCatalogError("invalid_topic")
    topic = " ".join(topic.split())
    if not topic or len(topic) > _MAX_TOPIC_LENGTH:
        raise TopicCatalogError("invalid_topic")
    return topic


def normalize_topics(values: Iterable[object]) -> list[str]:
    """De-duplicate a catalog case-insensitively while retaining user order."""
    result, seen = [], set()
    for value in values:
        topic = normalize_topic(value)
        key = topic.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(topic)
        if len(result) > _MAX_TOPICS_PER_LANGUAGE:
            raise TopicCatalogError("too_many_topics")
    return result


class TopicCatalogStore:
    """Own the bounded on-disk catalog; UI controls never own file I/O."""

    def __init__(self, path: str):
        self.path = path

    def topics_for(self, language: str) -> list[str]:
        language = self._language(language)
        raw = read_json(
            self.path, {}, lambda value: isinstance(value, dict),
            max_bytes=_MAX_FILE_BYTES,
        )
        topics = raw.get("languages", {}).get(language, []) if isinstance(raw, dict) else []
        try:
            return normalize_topics(topics if isinstance(topics, list) else [])
        except TopicCatalogError:
            return []

    def replace_topics(self, language: str, values: Iterable[object]) -> list[str]:
        language = self._language(language)
        topics = normalize_topics(values)
        raw = read_json(
            self.path, {}, lambda value: isinstance(value, dict),
            max_bytes=_MAX_FILE_BYTES,
        )
        languages = dict(raw.get("languages", {})) if isinstance(raw, dict) else {}
        languages[language] = topics
        atomic_write_json(self.path, {"version": 1, "languages": languages})
        return topics

    @staticmethod
    def _language(value: str) -> str:
        language = str(value or "").strip().casefold()
        if language not in _SUPPORTED_LANGUAGES:
            raise TopicCatalogError("unsupported_language")
        return language


__all__ = [
    "TopicCatalogError", "TopicCatalogStore", "normalize_topic", "normalize_topics",
]
