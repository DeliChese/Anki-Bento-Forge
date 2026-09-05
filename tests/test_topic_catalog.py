"""Profile-local topic catalog contracts."""

import pytest

from utils.topic_catalog import TopicCatalogError, TopicCatalogStore, normalize_topics


def test_catalogs_are_independent_per_language_and_persist(tmp_path):
    path = str(tmp_path / "topic_catalog.json")
    store = TopicCatalogStore(path)

    store.replace_topics("chinese", ["Ẩm thực", "Du lịch"])
    store.replace_topics("japanese", ["Ẩm thực"])

    reopened = TopicCatalogStore(path)
    assert reopened.topics_for("chinese") == ["Ẩm thực", "Du lịch"]
    assert reopened.topics_for("japanese") == ["Ẩm thực"]


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
