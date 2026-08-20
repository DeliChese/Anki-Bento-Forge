"""Tests for the privacy-safe persistent AI usage history."""

import json

from utils import ai_usage_history as history


def test_usage_history_persists_only_usage_metadata_and_summarizes(tmp_path, monkeypatch):
    path = tmp_path / "ai_usage_history.json"
    monkeypatch.setattr(history, "_PATH", str(path))

    history.record_usage(
        {
            "model": "deepseek-chat",
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "total_tokens": 200,
            "input_cost": 0.0000168,
            "output_cost": 0.0000224,
            "total_cost": 0.0000392,
            "prompt": "must never be written",
            "api_key": "must never be written",
        },
        operation="vocab_extraction",
        started_at=1_700_000_000,
        duration_seconds=1.25,
    )

    entries = history.get_usage_entries()
    assert len(entries) == 1
    assert entries[0]["operation"] == "vocab_extraction"
    assert entries[0]["duration_seconds"] == 1.25
    assert "prompt" not in entries[0] and "api_key" not in entries[0]
    assert history.summarize_usage(entries) == {
        "calls": 1,
        "prompt_tokens": 120,
        "completion_tokens": 80,
        "total_tokens": 200,
        "total_cost": 0.0000392,
    }
    serialized = json.dumps(json.loads(path.read_text(encoding="utf-8")))
    assert "must never be written" not in serialized


def test_usage_history_can_be_cleared(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_PATH", str(tmp_path / "ai_usage_history.json"))
    history.record_usage({"model": "model", "total_tokens": 1}, operation="ai_chat")
    history.clear_usage_history()
    assert history.get_usage_entries() == []


def test_usage_history_resolves_profile_path_lazily(tmp_path, monkeypatch):
    active = {"root": tmp_path / "profile-a"}
    monkeypatch.setattr(history, "_PATH", None)
    monkeypatch.setattr(
        history, "get_user_data_path",
        lambda name: str(active["root"] / name),
    )

    history.record_usage(
        {"model": "stable-model", "total_tokens": 7}, operation="ai_chat",
    )
    active["root"] = tmp_path / "profile-b"
    assert history.get_usage_entries() == []
    active["root"] = tmp_path / "profile-a"
    assert history.get_usage_entries()[0]["model"] == "stable-model"
