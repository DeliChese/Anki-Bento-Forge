"""Tests for profile-scoped, crash-safe persistence."""

import json
from pathlib import Path

import pytest

from utils import user_data


def test_user_data_dir_honors_isolated_override(tmp_path, monkeypatch):
    monkeypatch.setenv("BENTO_FORGE_DATA_DIR", str(tmp_path / "profile-data"))
    target = Path(user_data.get_user_data_path("nested/config.json"))
    assert target.parent == tmp_path / "profile-data" / "nested"
    assert target.parent.is_dir()


def test_user_data_rejects_path_traversal():
    with pytest.raises(ValueError):
        user_data.get_user_data_path("../outside.json")


def test_atomic_write_replaces_valid_document(tmp_path):
    target = tmp_path / "config.json"
    target.write_text('{"old": true}', encoding="utf-8")
    user_data.atomic_write_json(str(target), {"new": "✓"})
    assert json.loads(target.read_text(encoding="utf-8")) == {"new": "✓"}
    assert not list(tmp_path.glob("*.tmp"))


def test_invalid_json_and_schema_use_default(tmp_path):
    target = tmp_path / "corrupt.json"
    target.write_text("not json", encoding="utf-8")
    assert user_data.read_json(str(target), {"safe": True}, lambda v: isinstance(v, dict)) == {"safe": True}
    target.write_text("[]", encoding="utf-8")
    assert user_data.read_json(str(target), {}, lambda v: isinstance(v, dict)) == {}


def test_migration_creates_backup_removes_legacy_and_can_rollback(tmp_path):
    legacy = tmp_path / "addon" / "utils" / "i18n_config.json"
    target = tmp_path / "profile" / "i18n_config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"language": "en"}', encoding="utf-8")

    assert user_data.migrate_legacy_json(str(legacy), str(target), lambda v: v.get("language") in {"vi", "en"})
    assert not legacy.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {"language": "en"}
    assert json.loads((Path(str(target) + ".legacy-backup")).read_text(encoding="utf-8")) == {"language": "en"}

    user_data.atomic_write_json(str(target), {"language": "vi"})
    assert user_data.rollback_migration(str(target))
    assert json.loads(target.read_text(encoding="utf-8")) == {"language": "en"}


def test_cache_pruning_enforces_age_file_and_size_limits(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    for number in range(4):
        item = cache / f"{number}.json"
        item.write_bytes(b"x" * 32)
    old = cache / "old.json"
    old.write_bytes(b"x")
    old.touch()
    # Set an age that is guaranteed to be outside the one-second limit.
    import os
    import time
    os.utime(old, (time.time() - 10, time.time() - 10))

    user_data.prune_cache_dir(str(cache), max_age_seconds=1, max_bytes=64, max_files=2)
    kept = list(cache.iterdir())
    assert not old.exists()
    assert len(kept) <= 2
    assert sum(item.stat().st_size for item in kept) <= 64
