"""Regression tests for the isolated AI response parser."""

import ast
from pathlib import Path

import pytest

from utils import ai_extractor
from utils import ai_response_parser as parser


def test_fenced_array_separates_trailing_comment():
    content = '''```json
[
  {"front": "食べる"},
  {"_comment": "parsed"}
]
```'''
    assert parser.parse_ai_json_with_comment(content) == ([{"front": "食べる"}], "parsed")


def test_dict_wrapper_returns_first_list_and_comment():
    content = '{"items":[{"simplified":"学习"}],"_comment":"ok"}'
    assert parser.parse_ai_json_with_comment(content) == ([{"simplified": "学习"}], "ok")


def test_single_dict_is_wrapped_and_comment_removed():
    content = '{"front":"먹다","_comment":"one"}'
    assert parser.parse_ai_json_with_comment(content) == ([{"front": "먹다"}], "one")


def test_embedded_array_is_preserved_and_ambiguous_payloads_are_rejected():
    embedded = 'AI result: [{"front":"行く"}] end.'
    assert parser.parse_ai_json_with_comment(embedded) == ([{"front": "行く"}], "")

    with pytest.raises(RuntimeError):
        parser.parse_ai_json_with_comment('{"front":"a"}{"front":"b"}')


def test_invalid_response_raises_bounded_actionable_error():
    content = "x" * 450
    with pytest.raises(RuntimeError) as exc_info:
        parser.parse_ai_json_with_comment(content)

    message = str(exc_info.value)
    assert "Không parse được JSON" in message
    assert "batch nhỏ hơn" in message
    assert "x" * 400 in message
    assert "x" * 401 not in message


def test_parser_owner_is_pure_and_ai_extractor_reexports_legacy_name():
    source = Path(parser.__file__).read_text(encoding="utf-8")
    imports = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert imports <= {"__future__", "json", "re", "dataclasses", "typing"}
    assert ai_extractor._parse_ai_json_with_comment is parser.parse_ai_json_with_comment
