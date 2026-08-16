import json
from pathlib import Path

from utils.ai_benchmark import validate_case


ROOT = Path(__file__).resolve().parents[1]


def test_language_quality_cases_are_fixed_valid_20_item_corpora():
    for name, language in (
        ("english_vocab_20_v1.json", "english"),
        ("japanese_vocab_20_v1.json", "japanese"),
        ("chinese_vocab_20_v1.json", "chinese"),
        ("korean_vocab_20_v1.json", "korean"),
    ):
        case = json.loads((ROOT / "benchmarks" / name).read_text(encoding="utf-8"))
        validated = validate_case(case)

        assert validated["language"] == language
        assert len(validated["expected_terms"]) == 20
        assert len(case["source_items"]) == 20
