"""Parse AI JSON responses independently of providers and workflows."""

import json
import re

from .json_parser import safe_parse_json


def parse_ai_json_with_comment(content: str, error_formatter=None) -> tuple:
    """Parse an AI JSON response and separate its optional ``_comment``."""
    comment = ""
    content = content.strip()

    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)
        if isinstance(data, list):
            if data and isinstance(data[-1], dict) and "_comment" in data[-1] and len(data[-1]) == 1:
                comment = data[-1]["_comment"]
                data = data[:-1]
            return data, comment
        if isinstance(data, dict):
            if "_comment" in data:
                comment = data.pop("_comment")
            for value in data.values():
                if isinstance(value, list):
                    return value, comment
            return [data], comment
    except json.JSONDecodeError:
        pass

    array_match = re.search(r"\[.*\]", content, re.DOTALL)
    if array_match:
        try:
            data = json.loads(array_match.group(0))
            if isinstance(data, list):
                if data and isinstance(data[-1], dict) and "_comment" in data[-1] and len(data[-1]) == 1:
                    comment = data[-1]["_comment"]
                    data = data[:-1]
                return data, comment
        except json.JSONDecodeError:
            pass

    results = safe_parse_json(content)
    if results:
        return results, comment

    preview = content[:400]
    if error_formatter is not None:
        raise RuntimeError(error_formatter(preview))
    raise RuntimeError(
        "⚠️ Không parse được JSON — thường do KẾT QUẢ BỊ CẮT vì vượt giới hạn "
        "token output (DeepSeek ~8192/response).\n"
        "💡 Cách khắc phục: Vào Cài Đặt AI → giảm 'Độ dài xử lý mỗi lần gọi' "
        "xuống 8k-12k, rồi thử lại. Văn bản dài vẫn được xử lý hết (tự chia đoạn).\n"
        f"Nội dung nhận được:\n{preview}"
    )


__all__ = ["parse_ai_json_with_comment"]
