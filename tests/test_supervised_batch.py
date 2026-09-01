from pathlib import Path

from utils import batch_processor
from utils.batch_processor import (
    apply_supervised_metadata,
    build_supervised_inventory,
    filter_supervised_inventory,
    load_supervised_progress,
    recommended_supervised_run_size,
    save_supervised_progress,
    supervised_result_ids,
    supervised_source_id,
)


def test_structured_workshop_source_inherits_topic_and_level():
    source = """
# Ẩm thực
## N5
食べる : ăn
飲む : uống
# Du lịch
## N4
空港 : sân bay
"""

    inventory = build_supervised_inventory(source, "japanese")

    assert [(item["front"], item["topic"], item["level"]) for item in inventory] == [
        ("食べる", "Ẩm thực", "N5"),
        ("飲む", "Ẩm thực", "N5"),
        ("空港", "Du lịch", "N4"),
    ]


def test_declared_table_columns_survive_shuffled_rows():
    source = """word,meaning,level,topic
airport,sân bay,B1,Travel
apple,táo,A1,Food
hotel,khách sạn,A2,Travel
"""

    inventory = build_supervised_inventory(source, "english")
    travel = filter_supervised_inventory(inventory, topic="travel")

    assert [item["front"] for item in travel] == ["airport", "hotel"]
    assert [item["level"] for item in travel] == ["B1", "A2"]


def test_json_array_is_not_mistaken_for_a_bracket_heading():
    inventory = build_supervised_inventory(
        '[{"front":"apple","meaning":"táo","level":"A1","topic":"Food"}]',
        "english",
    )

    assert len(inventory) == 1
    assert inventory[0]["topic"] == "Food"


def test_supervised_filter_excludes_only_completed_ids():
    inventory = build_supervised_inventory(
        "word,meaning,level,topic\na,a,A1,Food\nb,b,A1,Food\nc,c,A2,Food",
        "english",
    )

    remaining = filter_supervised_inventory(
        inventory,
        topic="Food",
        level="A1",
        completed_ids={inventory[0]["id"]},
    )

    assert [item["front"] for item in remaining] == ["b"]


def test_recommended_run_is_reviewable_but_api_batch_remains_small():
    assert recommended_supervised_run_size(1000, "english") == 48
    assert recommended_supervised_run_size(1000, "japanese") == 40
    assert recommended_supervised_run_size(1000, "chinese") == 32
    assert recommended_supervised_run_size(7, "chinese") == 7


def test_source_metadata_wins_and_only_valid_results_complete_items():
    inventory = build_supervised_inventory(
        "word,meaning,level,topic\napple,táo,A1,Food\nairport,sân bay,B1,Travel",
        "english",
    )
    results = [{"front": "apple", "topic": "Objects", "cefr_level": "C1"}]

    merged = apply_supervised_metadata(results, inventory, "english")
    completed = supervised_result_ids(inventory, merged)

    assert merged[0]["topic"] == "Food"
    assert merged[0]["cefr_level"] == "A1"
    assert completed == {inventory[0]["id"]}


def test_progress_persists_only_opaque_source_and_item_ids(tmp_path, monkeypatch):
    progress_path = tmp_path / "supervised_progress.json"
    monkeypatch.setattr(batch_processor, "SUPERVISED_PROGRESS_PATH", str(progress_path))
    source = "# Food\napple : táo : A1"
    source_id = supervised_source_id(source, "english")
    item_id = build_supervised_inventory(source, "english")[0]["id"]

    save_supervised_progress(source_id, {item_id})
    payload = progress_path.read_text(encoding="utf-8")

    assert load_supervised_progress(source_id) == {item_id}
    assert "apple" not in payload
    assert "Food" not in payload


def test_factory_passes_current_workshop_source_to_supervised_dialog():
    root = Path(__file__).resolve().parents[1]
    factory = (root / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    dialog = (root / "ui" / "batch_dialog.py").read_text(encoding="utf-8")

    assert "workshop_text=self.ai_text_input.toPlainText()" in factory
    assert 'workshop_paths=list(getattr(self, "_ai_attached_paths", ()))' in factory
    assert "self.btn_take_workshop" in dialog
    assert "save_supervised_progress(self._source_id" in dialog
