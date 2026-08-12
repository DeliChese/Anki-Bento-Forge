"""
═══════════════════════════════════════════════════════════════
 grammar_ai.py — AI sinh câu luyện tập & ví dụ cho THẺ NGỮ PHÁP
 ===============================================================

 Mục đích (theo yêu cầu cải tiến luồng học ngữ pháp):
   1) Sinh tự động câu ví dụ áp dụng cấu trúc ngữ pháp để người học
      LUYỆN DỊCH (không gõ lại lý thuyết / giải thích mặt sau).
   2) Khi "đúc thẻ" ngữ pháp bằng Bento Forge → dùng câu do AI sinh
      để điền vào Example / Example2 THAY CHO ví dụ cứng mặc định.

 Điểm cốt lõi: AI trả JSON {"sentence", "translation"}; phía card
 hiển thị dạng "streaming" (hiện dần) rồi tự chấm điểm bản dịch.

 Tái sử dụng hạ tầng AI của Forge (utils/ai_extractor.chat_with_ai).
═══════════════════════════════════════════════════════════════
"""

import json
import re

from utils.logger import get_logger

logger = get_logger()

# Tên ngôn ngữ đích dùng trong prompt
_LANG_EN = {
    "japanese": "Japanese",
    "chinese": "Chinese",
    "korean": "Korean",
}


def _lang_en(lang: str) -> str:
    return _LANG_EN.get(lang, "Japanese")


def _parse_grammar_json(reply: str) -> dict:
    """Parse JSON lỏng lẻo từ AI (chịu ```json```, khoảng trắng thừa, text xung quanh)."""
    if not reply:
        return {"sentence": "", "translation": "", "error": "AI trả về rỗng."}
    text = reply.strip()
    # Bóc khối ```json ... ``` nếu có
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return {"sentence": "", "translation": "", "error": "AI không trả đúng JSON."}
        try:
            data = json.loads(m.group(0))
        except Exception:
            return {"sentence": "", "translation": "", "error": "AI không trả đúng JSON."}
    if not isinstance(data, dict):
        return {"sentence": "", "translation": "", "error": "AI không trả đúng JSON."}
    return {
        "sentence": str(data.get("sentence") or "").strip(),
        "translation": str(data.get("translation") or "").strip(),
        "error": None,
    }


def generate_grammar_sentence(pattern: str, meaning: str, lang: str = "japanese") -> dict:
    """
    Gọi AI sinh 1 câu ví dụ áp dụng cấu trúc ngữ pháp + bản dịch tiếng Việt.

    Returns:
        {"sentence": str, "translation": str, "error": None|str}
    """
    target = _lang_en(lang)
    prompt = (
        f'Cấu trúc ngữ pháp tiếng {target}: "{pattern}" (nghĩa: {meaning}).\n'
        "Tạo ĐÚNG 1 câu ngắn (≤15 từ) dùng cấu trúc này + bản dịch tiếng Việt.\n"
        'Chỉ trả JSON: {"sentence":"...","translation":"..."}'
    )
    try:
        from utils.ai_extractor import chat_with_ai
        # quick=True → bỏ qua truy vấn context Anki → phản hồi nhanh hơn
        res = chat_with_ai(prompt, lang=lang, quick=True)
        if res.get("error"):
            return {"sentence": "", "translation": "", "error": res["error"]}
        return _parse_grammar_json(res.get("reply") or "")
    except Exception as e:  # noqa: BLE001
        logger.warning("grammar_ai: lỗi sinh câu: %s", e)
        return {"sentence": "", "translation": "", "error": str(e)}


def generate_grammar_examples(pattern: str, meaning: str, lang: str = "japanese",
                              count: int = 2) -> list:
    """
    Sinh `count` câu ví dụ AI cho cấu trúc ngữ pháp (để điền Example/Example2 khi đúc thẻ).

    Returns:
        list[dict] mỗi phần tử {"sentence", "translation"} (rỗng nếu lỗi).
    """
    target = _lang_en(lang)
    prompt = (
        f'Cấu trúc ngữ pháp tiếng {target}: "{pattern}" (nghĩa: {meaning}).\n'
        f"Tạo {count} câu ngắn (≤15 từ) dùng cấu trúc này, khác ngữ cảnh, + bản dịch tiếng Việt.\n"
        'Chỉ trả JSON array: [{"sentence":"...","translation":"..."}, ...]'
    )
    try:
        from utils.ai_extractor import chat_with_ai
        # quick=True → bỏ qua truy vấn context Anki → phản hồi nhanh hơn
        res = chat_with_ai(prompt, lang=lang, quick=True)
        if res.get("error"):
            return []
        reply = (res.get("reply") or "").strip()
        if reply.startswith("```"):
            reply = reply.strip("`").strip()
            if reply.lower().startswith("json"):
                reply = reply[4:].strip()
        try:
            data = json.loads(reply)
        except Exception:
            m = re.search(r"\[.*\]", reply, re.S)
            data = json.loads(m.group(0)) if m else []
        if not isinstance(data, list):
            return []
        out = []
        for it in data:
            if isinstance(it, dict) and it.get("sentence"):
                out.append({
                    "sentence": str(it["sentence"]).strip(),
                    "translation": str(it.get("translation") or "").strip(),
                })
        return out
    except Exception as e:  # noqa: BLE001
        logger.warning("grammar_ai: lỗi sinh ví dụ: %s", e)
        return []


def ensure_grammar_examples(item: dict, lang: str = "japanese") -> bool:
    """
    Điền ví dụ AI cho 1 thẻ ngữ pháp NẾU chưa có — thay thế ví dụ cứng/mặc định
    bằng câu do AI sinh khi tiến hành đúc thẻ bằng Bento Forge.

    Keys JSON khớp với json_field_map ngữ pháp:
        example → Example, example_vn → Example in Vietnamese,
        example_2 → Example2, example_2_vn → Example2 in Vietnamese.

    Returns:
        True nếu đã điền; False nếu không (thiếu pattern / đã có ví dụ / lỗi AI).
    """
    if not isinstance(item, dict):
        return False
    if item.get("example") or item.get("example_2"):
        return False  # đã có ví dụ → giữ nguyên (không đè dữ liệu người dùng)
    pattern = str(item.get("pattern") or item.get("front") or "").strip()
    meaning = str(item.get("meaning") or "").strip()
    if not pattern:
        return False
    exs = generate_grammar_examples(pattern, meaning, lang, count=2)
    if not exs:
        return False
    if not item.get("example") and exs:
        item["example"] = exs[0]["sentence"]
        if exs[0]["translation"]:
            item.setdefault("example_vn", exs[0]["translation"])
    if not item.get("example_2") and len(exs) > 1:
        item["example_2"] = exs[1]["sentence"]
        if exs[1]["translation"]:
            item.setdefault("example_2_vn", exs[1]["translation"])
    return True
