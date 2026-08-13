"""Contract tests for Phase 4 boundaries and privacy guarantees."""

import json
from pathlib import Path

from utils.ai_session_policy import AiSessionPolicy
from utils.anki_adapter import AnkiCollectionAdapter
from utils.factory_state import FactoryStateStore
from utils.import_quality import find_near_duplicate, normalize_for_comparison
from utils.import_report import build_import_report, write_import_report


def test_ai_session_policy_estimates_and_enforces_aggregate_budget():
    policy = AiSessionPolicy(max_input_chars=20_000, max_tokens=10_000, max_cost_usd=0.10)
    estimate = policy.estimate(text_chars=8_000, model="deepseek-chat", max_output_tokens=2_000, chunk_size=4_000)

    assert estimate.calls == 2
    assert estimate.total_tokens > 0
    assert policy.check(estimate) is None

    policy.record({"total_tokens": 9_500, "total_cost": 0.09})
    assert policy.check(estimate) == "remaining session token budget is too small"
    assert policy.snapshot()["calls"] == 1


def test_quality_check_normalizes_but_never_merges_a_card():
    assert normalize_for_comparison("  Café—Test ") == "cafétest"
    match = find_near_duplicate("vocabulary", ["vocabularly", "grammar"])
    assert match[0] == "vocabularly"
    assert match[1] >= 0.88
    assert find_near_duplicate("a", ["b"]) is None


def test_import_report_excludes_learning_content_and_is_profile_scoped(tmp_path, monkeypatch):
    monkeypatch.setenv("BENTO_FORGE_DATA_DIR", str(tmp_path))
    report = {
        "added": 2, "updated": 1, "audio_gen": 3, "audio_failed": 0,
        "errors": 1, "errors_detail": ["secret card meaning"],
    }
    safe = build_import_report(report, {"new": 2, "updates": 1})
    serialized = json.dumps(safe)
    assert "secret card meaning" not in serialized
    assert safe["result"]["added"] == 2

    path = Path(write_import_report(report, {"new": 2, "updates": 1}))
    assert path.parent == tmp_path / "reports"
    assert json.loads(path.read_text(encoding="utf-8"))["selection"] == {"new": 2, "updates": 1}


def test_factory_state_store_is_bounded_and_migrates_out_of_source(tmp_path):
    legacy = tmp_path / "addon" / "factory_state.json"
    target = tmp_path / "profile" / "factory_state.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"japanese": {"vocab": {"text": "x" * 20}}}), encoding="utf-8")
    store = FactoryStateStore(legacy_path=str(legacy), path=str(target), max_text_chars=5)

    state = store.load()
    assert state["japanese"]["vocab"]["text"] == "xxxxx"
    assert target.exists() and not legacy.exists()


def test_anki_collection_adapter_hides_collection_lookup_details():
    class Models:
        def by_name(self, name):
            return {"id": 7} if name == "model" else None

    class Collection:
        models = Models()

        def find_notes(self, query):
            assert query == '"mid:7"'
            return [1, 2]

        def get_note(self, note_id):
            return {"id": note_id}

    adapter = AnkiCollectionAdapter(Collection())
    assert adapter.model_id_by_name("model") == 7
    assert adapter.notes_for_model(7) == [{"id": 1}, {"id": 2}]
