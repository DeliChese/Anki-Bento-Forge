from utils.ai_output_repairs import repair_vocabulary_cards


def test_repairs_kiku_question_only_when_translation_claims_ask():
    cards = [{
        "front": "聞く",
        "example_2": "先生に質問を聞きました。",
        "example_2_vn": "Tôi đã hỏi thầy giáo câu hỏi.",
    }]

    repaired = repair_vocabulary_cards(cards, "japanese")

    assert repaired[0]["example_2"] == "先生に質問しました。"
    assert cards[0]["example_2"] == "先生に質問を聞きました。"


def test_keeps_legitimate_question_hearing_and_other_languages_unchanged():
    cards = [{
        "front": "聞く",
        "example": "先生の質問を聞きました。",
        "example_vn": "Tôi đã nghe câu hỏi của thầy giáo.",
    }]

    assert repair_vocabulary_cards(cards, "japanese") == cards
    assert repair_vocabulary_cards(cards, "korean") == cards
