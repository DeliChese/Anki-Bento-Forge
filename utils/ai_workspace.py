"""Small, deterministic router for the current Factory AI request."""

from __future__ import annotations

import re


_GRAMMAR_ROUTE_CUES = (
    "grammar", "grammatical", "ngữ pháp", "cấu trúc", "mẫu câu", "pattern",
    "文法", "语法", "語法", "문법", "어미", "助詞", "particle", "conjugation",
)
_VOCAB_ROUTE_CUES = (
    "vocabulary", "vocab", "từ vựng", "từ mới", "word", "words", "collocation",
    "単語", "語彙", "词汇", "詞彙", "生词", "生詞", "어휘", "단어",
)


def route_forge_lane(source_text: str, instruction: str = "", fallback: str = "vocab") -> str:
    """Choose vocab or grammar locally without making an extra AI call."""
    fallback = str(fallback or "vocab").strip().casefold()
    if fallback not in {"vocab", "grammar", "collocation"}:
        fallback = "vocab"
    instruction_text = str(instruction or "").casefold()
    source = str(source_text or "").casefold()

    def score(text: str, cues: tuple[str, ...]) -> int:
        return sum(1 for cue in cues if cue in text)

    instruction_grammar = score(instruction_text, _GRAMMAR_ROUTE_CUES)
    instruction_vocab = score(instruction_text, _VOCAB_ROUTE_CUES)
    if instruction_grammar != instruction_vocab:
        return "grammar" if instruction_grammar > instruction_vocab else "vocab"

    combined = f"{instruction_text}\n{source}"
    grammar_score = score(source, _GRAMMAR_ROUTE_CUES)
    vocab_score = score(source, _VOCAB_ROUTE_CUES)
    if re.search(r"(?:^|\s)[~〜～]|(?:^|\s)[nva]\s*\+|\b(?:tense|clause|syntax)\b", combined):
        grammar_score += 1
    if grammar_score == vocab_score:
        return fallback
    return "grammar" if grammar_score > vocab_score else "vocab"


__all__ = ["route_forge_lane"]
