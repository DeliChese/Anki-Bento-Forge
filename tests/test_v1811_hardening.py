import copy

import pytest

from utils import ai_extractor
from utils.ai_card_artifacts import create_card_artifact, artifact_to_factory_payload
from utils.ai_context_manager import minimal_card_context
from utils.ai_output_validation import AI_OUTPUT_SCHEMA_VERSION, validate_ai_cards
from utils.ai_reliability import is_exact_existing_card
from utils.ai_session_store import StudySessionStore
from utils.ai_study_prompts import build_study_prompt
from utils.ai_text_recovery import IncompleteExtractionError
from utils.grammar_ai import _parse_grammar_json_strict
from utils.language_identity import normalize_language
from utils.prompt_config import validate_json_template


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("japanese", "japanese"), ("Japanese", "japanese"),
        ("ja", "japanese"), ("JA", "japanese"),
        ("chinese", "chinese"), ("zh", "chinese"), ("ZH", "chinese"),
        ("korean", "korean"), ("ko", "korean"), ("KO", "korean"),
        ("english", "english"), ("English", "english"),
        ("en", "english"), ("EN", "english"),
    ],
)
def test_language_aliases_are_canonical(value, expected):
    assert normalize_language(value) == expected
    assert expected.title() in build_study_prompt(value, None, english_ui=True)


@pytest.mark.parametrize("value", ["", "   ", None, "german", "unknown"])
def test_invalid_language_never_becomes_japanese(tmp_path, value):
    with pytest.raises(ValueError):
        normalize_language(value)
    with pytest.raises(ValueError):
        build_study_prompt(value, None, english_ui=True)
    with pytest.raises(ValueError):
        StudySessionStore(str(tmp_path / "sessions.json")).create_session(language=value)


def _card(lang, kind="vocab", *, identity=None, example=None):
    values = {
        "japanese": (
            "聞く", "彼の話を聞きます。", "先生の話を聞きました。",
            "音楽を聞きません。", "何を聞きますか。",
        ),
        "chinese": (
            "学习", "我每天学习中文。", "她在学校学习汉语。",
            "我今天不学习。", "你想学习中文吗？",
        ),
        "korean": (
            "배우다", "저는 매일 한국어를 배워요.", "학교에서 한국어를 배웠어요.",
            "오늘은 한국어를 배우지 않아요.", "무엇을 배우고 싶어요?",
        ),
        "english": (
            "learn", "I learn something every day.", "She learned the rule yesterday.",
            "We do not learn by waiting.", "Can you learn this quickly?",
        ),
    }
    front, sentence, example_2, example_3, example_4 = values[lang]
    if kind == "grammar":
        return {
            "pattern": identity or front, "meaning": "meaning", "usage": "usage",
            "example": example or sentence,
        }
    return {
        "front": identity or front, "meaning": "meaning", "example": example or sentence,
        "example_2": example_2, "example_3": example_3, "example_4": example_4,
    }


@pytest.mark.parametrize(
    ("lang", "wrong", "category"),
    [
        ("english", "これは日本語です。", "content_language_mismatch"),
        ("chinese", "これは例です。", "content_language_mismatch"),
        ("korean", "这是一个中文句子。", "content_language_mismatch"),
        ("japanese", "이것은 한국어예요.", "content_language_mismatch"),
    ],
)
def test_high_confidence_identity_script_mismatches_fail_closed(lang, wrong, category):
    report = validate_ai_cards([_card(lang, identity=wrong)], lang=lang, kind="vocab")
    assert report.invalid[0].category == category


@pytest.mark.parametrize(
    ("lang", "wrong"),
    [
        ("english", "한국어 문장입니다."),
        ("chinese", "これは例です。"),
        ("korean", "这是一个中文句子。"),
        ("japanese", "한국어 문장입니다."),
    ],
)
@pytest.mark.parametrize("kind", ["vocab", "grammar"])
def test_wrong_script_examples_are_rejected_for_both_card_kinds(lang, wrong, kind):
    report = validate_ai_cards([_card(lang, kind, example=wrong)], lang=lang, kind=kind)
    assert report.invalid[0].category == "example_language_mismatch"


def test_english_grammar_notation_and_japanese_kanji_only_remain_valid():
    grammar = {
        "pattern": "S + used to + V", "meaning": "past habit", "usage": "S + used to + V",
        "example": "I used to walk to school.",
    }
    assert validate_ai_cards([grammar], lang="english", kind="grammar").valid_cards
    assert validate_ai_cards([_card("japanese")], lang="japanese", kind="vocab").valid_cards


def test_artifact_is_immutable_current_schema_and_rejects_stale_or_future():
    source = _card("english")
    original = copy.deepcopy(source)
    artifact = create_card_artifact(
        session_id="session-a", language="EN", kind="vocab",
        cards=[source], source_message_id="msg-a",
    )
    assert source == original
    assert artifact["language"] == "english"
    assert artifact_to_factory_payload(artifact) == ("english", "vocab", [original])
    for schema in (AI_OUTPUT_SCHEMA_VERSION - 1, AI_OUTPUT_SCHEMA_VERSION + 1):
        stale = dict(artifact, schema_version=schema)
        with pytest.raises(ValueError, match="unsupported"):
            artifact_to_factory_payload(stale)


def test_artifact_never_semantically_rewrites_kiku_example():
    card = {
        "front": "聞く", "meaning": "ask", "example": "質問を聞く",
        "example_vn": "ask a question", "example_2": "先生に聞きました。",
        "example_3": "友達に聞きませんでした。", "example_4": "誰に聞きますか。",
    }
    artifact = create_card_artifact(
        session_id="session-a", language="japanese", kind="vocab",
        cards=[card], source_message_id="msg-a",
    )
    assert artifact["cards"][0]["front"] == "聞く"
    assert artifact["cards"][0]["example"] == "質問を聞く"


def test_artifact_store_requires_live_source_message(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    artifact = create_card_artifact(
        session_id=session["id"], language="english", kind="vocab",
        cards=[_card("english")], source_message_id="deleted-message",
    )
    with pytest.raises(ValueError, match="source message"):
        store.add_artifact(session["id"], artifact)


@pytest.mark.parametrize("lang", ["japanese", "chinese", "korean", "english"])
@pytest.mark.parametrize(
    ("mode", "present", "absent"),
    [
        ("qa", {"front"}, {"meaning"}),
        ("vn", {"meaning"}, {"front", "pinyin", "romanization", "furigana"}),
        ("wb", {"meaning"}, {"front", "pinyin", "romanization", "furigana"}),
        ("pron", {"front", "meaning"}, {"pinyin", "romanization", "furigana"}),
        ("lg", {"meaning", "pinyin", "romanization", "furigana"}, {"front"}),
    ],
)
def test_reviewer_question_context_is_mode_aware(lang, mode, present, absent):
    snapshot = {
        "language": lang, "side": "question", "study_mode": mode,
        "front": "TARGET", "meaning": "MEANING", "pinyin": "PINYIN",
        "romanization": "ROMANIZATION", "furigana": "FURIGANA",
    }
    context = minimal_card_context(snapshot, include_answer=False)
    assert present <= set(context)
    assert not absent.intersection(context)
    assert set(snapshot) <= set(minimal_card_context(snapshot, include_answer=True))


def test_same_surface_distinct_sense_survives_existing_deck_filter():
    existing = [{"front": "light", "meaning": "illumination"}]
    assert is_exact_existing_card(
        {"front": "light", "meaning": "illumination"}, existing, kind="vocab",
    )
    assert not is_exact_existing_card(
        {"front": "light", "meaning": "not heavy"}, existing, kind="vocab",
    )
    grammar = [{"pattern": "-ing", "meaning": "gerund"}]
    assert not is_exact_existing_card(
        {"pattern": "-ing", "meaning": "progressive aspect"}, grammar, kind="grammar",
    )


def test_custom_template_core_contract_is_enforced_but_extra_fields_survive():
    assert not validate_json_template('{"meaning":"M"}', "english", "vocab")[0]
    assert not validate_json_template(
        '{"front":"F","meaning":"M"}', "english", "grammar",
    )[0]
    assert not validate_json_template(
        '{"front":"F","meaning":"M","hsk_level":"HSK1"}', "english", "vocab",
    )[0]
    ok, _error, fields = validate_json_template(
        '{"front":"F","meaning":"M","cefr_level":"B1","custom":"X"}',
        "english", "vocab",
    )
    assert ok and "custom" in fields


def test_grammar_practice_parser_rejects_prose_ambiguity_and_truncation():
    assert _parse_grammar_json_strict('{"sentence":"A","translation":"B"}')["error"] is None
    assert _parse_grammar_json_strict(
        '{"sentence":"A","translation":"B"} {"sentence":"C"}'
    )["error"] == "ambiguous_json_payloads"
    assert _parse_grammar_json_strict('{"sentence":"cut"')["error"] == "malformed_json"
    assert _parse_grammar_json_strict(
        'prefix {"sentence":"A","translation":"B"}'
    )["error"] == "malformed_json"


def test_long_text_partial_recovery_cannot_return_ordinary_success(monkeypatch):
    monkeypatch.setattr(ai_extractor, "ensure_ai_session_budget", lambda _text: {})
    monkeypatch.setattr(ai_extractor, "get_api_config", lambda: {"chunk_size": 4})
    calls = iter([([_card("english")], 0), ([], 1)])
    monkeypatch.setattr(ai_extractor, "_recover_text_chunk", lambda *args, **kwargs: next(calls))
    with pytest.raises(IncompleteExtractionError) as exc_info:
        ai_extractor.extract_vocabulary_long_text("abcdefgh", "english")
    assert exc_info.value.unresolved_count == 1
    assert len(exc_info.value.cards) == 1
