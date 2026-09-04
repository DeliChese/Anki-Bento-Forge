"""Contract tests for intentional topic-scoped vocabulary variants."""

import pytest

from utils.ai_output_validation import validate_ai_cards
from utils.variant_scope import (
    VARIANT_KEY,
    VariantScopeError,
    note_matches_variant,
    preserves_scoped_variants,
    routing_tags,
    variant_key_for,
)


def _card(front="红", meaning="đỏ", **extra):
    return {"simplified": front, "meaning": meaning, **extra}


def test_topic_scope_is_normalized_and_persisted_as_one_tag():
    card = _card(**{VARIANT_KEY: "  Màu sắc  "})

    assert variant_key_for(card) == "màu sắc"
    assert routing_tags(card) == ("bento-forge::variant::màu-sắc",)
    assert preserves_scoped_variants([card])


def test_unscoped_cards_keep_ordinary_duplicate_protection():
    cards = [_card(), _card()]

    report = validate_ai_cards(cards, lang="chinese", kind="vocab")

    assert len(report.valid_cards) == 1
    assert report.duplicate_count == 1


def test_different_topic_scopes_allow_intentional_same_word_variant():
    cards = [
        _card(**{VARIANT_KEY: "mau-sac"}),
        _card(**{VARIANT_KEY: "an-uong"}),
        _card(**{VARIANT_KEY: "mau-sac"}),
    ]

    report = validate_ai_cards(
        cards, lang="chinese", kind="vocab", preserve_variant_key=True,
    )

    assert len(report.valid_cards) == 2
    assert report.duplicate_count == 1


def test_existing_notes_match_only_their_own_topic_scope():
    class Note:
        tags = ["bento-forge::variant::mau-sac"]

    note = Note()
    assert note_matches_variant(note, "mau-sac")
    assert not note_matches_variant(note, "an-uong")
    assert not note_matches_variant(note, "")


def test_invalid_topic_scope_is_rejected():
    with pytest.raises(VariantScopeError):
        variant_key_for(_card(**{VARIANT_KEY: "x\nng"}))
