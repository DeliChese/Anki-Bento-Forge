"""Profile-local topic catalog contracts."""

import ast
from pathlib import Path

import pytest

from utils.topic_catalog import TopicCatalogError, TopicCatalogStore, normalize_topics


def test_catalog_dialog_imports_the_selection_normalizer():
    source = Path("ui/topic_catalog_dialog.py").read_text(encoding="utf-8")
    imported_names = {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module == "utils.topic_catalog"
        for alias in node.names
    }

    assert "normalize_topics" in imported_names


def test_catalog_is_shared_across_languages_and_persists(tmp_path):
    path = str(tmp_path / "topic_catalog.json")
    store = TopicCatalogStore(path)

    store.replace_topics("chinese", ["Ẩm thực", "Du lịch"])

    reopened = TopicCatalogStore(path)
    assert reopened.topics_for("chinese") == ["Ẩm thực", "Du lịch"]
    assert reopened.topics_for("japanese") == ["Ẩm thực", "Du lịch"]


def test_catalog_merges_legacy_language_specific_topics_without_data_loss(tmp_path):
    path = tmp_path / "topic_catalog.json"
    path.write_text(
        '{"version": 1, "languages": {"japanese": ["Ẩm thực"], '
        '"chinese": ["Du lịch", "ẩm thực"]}}',
        encoding="utf-8",
    )

    store = TopicCatalogStore(str(path))

    assert store.topics_for("korean") == ["Ẩm thực", "Du lịch"]


def test_catalog_deduplicates_case_insensitively_without_losing_order():
    assert normalize_topics(["  Màu sắc ", "mÀU SẮC", "Ăn uống"]) == [
        "Màu sắc", "Ăn uống",
    ]


def test_catalog_rejects_invalid_topic_or_language(tmp_path):
    store = TopicCatalogStore(str(tmp_path / "topic_catalog.json"))
    with pytest.raises(TopicCatalogError):
        store.replace_topics("chinese", ["x\nng"])
    with pytest.raises(TopicCatalogError):
        store.topics_for("thai")
