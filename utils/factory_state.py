"""Profile-scoped draft state owned by the factory use case, not its UI."""

from __future__ import annotations

import json
import time

from .logger import get_logger
from .user_data import atomic_write_json, migrate_legacy_json, read_json

logger = get_logger()


class FactoryStateStore:
    def __init__(self, *, legacy_path, path, max_age_seconds=7 * 24 * 3600,
                 max_text_chars=12_000, max_json_chars=24_000, max_items=100,
                 max_flow_bytes=192 * 1024, max_locked_json_chars=1_000_000,
                 max_state_bytes=16 * 1024 * 1024):
        self.legacy_path = legacy_path
        self.path = path
        self.max_age_seconds = max_age_seconds
        self.max_text_chars = max_text_chars
        self.max_json_chars = max_json_chars
        self.max_items = max_items
        self.max_flow_bytes = max_flow_bytes
        self.max_locked_json_chars = max_locked_json_chars
        self.max_state_bytes = max_state_bytes

    def load(self):
        try:
            migrate_legacy_json(self.legacy_path, self.path, lambda value: isinstance(value, dict))
            data = read_json(self.path, {}, lambda value: isinstance(value, dict), max_bytes=self.max_state_bytes)
            clean = self.sanitize(data)
            if data.get("_saved_at", 0) and time.time() - float(data["_saved_at"]) > self.max_age_seconds:
                # Regular drafts expire; explicitly locked JSON is a durable
                # artifact and remains available after a restart.
                return self._locked_json_state(clean)
            return clean
        except Exception as error:
            logger.warning("Could not load factory state: %s", error)
            return {}

    def save(self, state):
        try:
            clean = self.sanitize(state)
            clean["_saved_at"] = time.time()
            atomic_write_json(self.path, clean)
            return clean
        except Exception as error:
            logger.warning("Could not save factory state: %s", error)
            return self.sanitize(state)

    def _bounded_items(self, items, max_bytes):
        if not isinstance(items, list):
            return []
        result, used = [], 0
        for item in items[:self.max_items]:
            if not isinstance(item, dict):
                continue
            try:
                size = len(json.dumps(item, ensure_ascii=False).encode("utf-8"))
            except (TypeError, ValueError):
                continue
            if used + size > max_bytes:
                break
            result.append(item)
            used += size
        return result

    @staticmethod
    def _locked_json_state(state):
        """Keep only explicitly locked flows once normal draft retention ends."""
        kept = {}
        for product, namespaces in state.items():
            if product not in {"language", "knowledge"} or not isinstance(namespaces, dict):
                continue
            product_kept = {}
            for namespace, modes in namespaces.items():
                if not isinstance(modes, dict):
                    continue
                mode_kept = {
                    name: flow for name, flow in modes.items()
                    if isinstance(flow, dict) and flow.get("json_locked")
                }
                if mode_kept:
                    product_kept[namespace] = mode_kept
            if product_kept:
                kept[product] = product_kept
        return kept

    def sanitize(self, state):
        if not isinstance(state, dict):
            return {}
        clean = {}

        def clean_flow(flow):
            if not isinstance(flow, dict):
                return None
            text, json_text, files = flow.get("text", ""), flow.get("json", ""), flow.get("files", [])
            json_locked = bool(flow.get("json_locked", False))
            try:
                card_count = int(flow.get("card_count", 10))
            except (TypeError, ValueError):
                card_count = 10
            return {
                "text": text[:self.max_text_chars] if isinstance(text, str) else "",
                "json": json_text[:(self.max_locked_json_chars if json_locked else self.max_json_chars)] if isinstance(json_text, str) else "",
                "json_locked": json_locked,
                "card_count": max(5, min(20, card_count)),
                "files": [path[:512] for path in files[:5] if isinstance(path, str)],
                "topic_enabled": bool(flow.get("topic_enabled", False)),
                "topic": flow.get("topic", "")[:80] if isinstance(flow.get("topic"), str) else "",
                "raw": self._bounded_items(flow.get("raw", []), self.max_flow_bytes // 2),
                "cards": self._bounded_items(flow.get("cards", []), self.max_flow_bytes // 2),
            }
        # V17 stored {lang: {vocab|grammar: flow}} at the top level.
        # V18 makes the product mode explicit while accepting that shape on
        # read, so old unsent drafts remain available after upgrading.
        language_state = state.get("language", {})
        if not isinstance(language_state, dict):
            language_state = {}
        clean_language = {}
        for lang in ("japanese", "chinese", "korean", "english"):
            lang_state = language_state.get(lang, state.get(lang))
            if not isinstance(lang_state, dict):
                continue
            clean_lang = {}
            for mode in ("vocab", "grammar", "collocation"):
                flow = clean_flow(lang_state.get(mode))
                if flow is None:
                    continue
                clean_lang[mode] = flow
            if clean_lang:
                clean_language[lang] = clean_lang
        if clean_language:
            clean["language"] = clean_language
        # Knowledge is language-independent.  It has one draft flow until the
        # V18-05 workflow owns preview/import state for it.
        knowledge_state = state.get("knowledge", {})
        if isinstance(knowledge_state, dict):
            knowledge_default = knowledge_state.get("default", {})
            flow = clean_flow(knowledge_default.get("knowledge")) if isinstance(knowledge_default, dict) else None
            if flow is not None:
                clean["knowledge"] = {"default": {"knowledge": flow}}
        return clean
