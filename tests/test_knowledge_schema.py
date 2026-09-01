"""V18-02 corpus tests for strict Knowledge prompt/schema boundaries."""

import json
from pathlib import Path

import pytest

from utils import ai_prompt_defaults, prompt_config
from utils.knowledge_schema import KnowledgeSchemaError, parse_knowledge_cards


FIXTURE = Path(__file__).with_name("fixtures") / "knowledge_cards.json"


@pytest.fixture
def corpus():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_knowledge_prompt_and_schema_are_not_language_overrides():
    template = prompt_config.get_knowledge_json_template()
    prompt = prompt_config.get_knowledge_system_prompt()

    assert template == ai_prompt_defaults._KNOWLEDGE_JSON_TEMPLATE
    assert template in prompt
    assert "pronunciation" in prompt.lower()
    assert ai_prompt_defaults.KNOWLEDGE_PROMPT_VERSION == 1
    assert prompt_config.KINDS == ("vocab", "grammar", "collocation")


def test_knowledge_corpus_accepts_valid_basic_and_cloze(corpus):
    cards = parse_knowledge_cards(json.dumps(corpus["valid"]))
    assert [card["type"] for card in cards] == ["basic", "cloze"]
    assert cards[1]["cloze_text"] == corpus["valid"][1]["cloze_text"]


def test_knowledge_corpus_keeps_missing_source_explicitly_empty(corpus):
    card = parse_knowledge_cards(json.dumps(corpus["source_missing"]))[0]
    assert card["source"] == ""
    assert "source" in card


def test_knowledge_corpus_rejects_invalid_cloze_and_ambiguous_shapes(corpus):
    with pytest.raises(KnowledgeSchemaError, match="cloze"):
        parse_knowledge_cards(json.dumps(corpus["invalid"]))
    for response in ('{"cards": []}', '{"type": "basic"}', 'Result: []', '[] trailing'):
        with pytest.raises(KnowledgeSchemaError):
            parse_knowledge_cards(response)


def test_knowledge_rejects_unknown_fields_and_partial_batches(corpus):
    unknown = dict(corpus["valid"][0], audio="not allowed")
    with pytest.raises(KnowledgeSchemaError, match="unknown"):
        parse_knowledge_cards(json.dumps([unknown]))
    with pytest.raises(KnowledgeSchemaError):
        parse_knowledge_cards(json.dumps([corpus["valid"][0], corpus["invalid"][0]]))
