"""Formatting contract for the rich-text Study Coach transcript."""

from __future__ import annotations

import ast
import html
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
_FORMATTERS = {
    "_format_transcript_inline", "_markdown_table_cells",
    "_is_markdown_table_divider", "_format_markdown_table",
    "_format_transcript_markdown",
}


def _formatter():
    source = (ROOT / "ui" / "ai_companion.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = [
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name in _FORMATTERS
    ]
    assert {item.name for item in nodes} == _FORMATTERS
    namespace = {"html": html, "re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "transcript_formatter", "exec"), namespace)
    return namespace["_format_transcript_markdown"]


def test_study_transcript_renders_common_markdown_without_raw_markers():
    render = _formatter()
    rendered = render(
        "# Mục **42**\n\n***\n\n"
        "- **Cấu trúc:** `正在 + V`\n- Dùng trong ngữ cảnh đang diễn ra\n\n"
        "| Mục | Công thức | Ví dụ |\n| --- | --- | --- |\n"
        "| 42 | 正在 + V | 我正在看书呢。 |\n\n"
        "```text\n**literal code**\n```\n\n<script>alert(1)</script>"
    )

    assert "<h3" in rendered and "<b>42</b>" in rendered
    assert "<hr" in rendered and "***" not in rendered
    assert "<ul" in rendered and "正在 + V" in rendered
    assert "<table" not in rendered  # Wide tables become readable cards in a narrow dock.
    assert "<b>Mục:</b>" in rendered and "<b>Ví dụ:</b>" in rendered
    assert "<pre" in rendered and "**literal code**" in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_study_transcript_keeps_two_column_table_large_and_readable():
    render = _formatter()
    rendered = render(
        "| Thành phần | Vai trò |\n| --- | --- |\n"
        "| 正在 | đứng trước động từ |"
    )

    assert "<table" in rendered
    assert "font-size:14px" in rendered
    assert "<th" in rendered and "<td" in rendered
