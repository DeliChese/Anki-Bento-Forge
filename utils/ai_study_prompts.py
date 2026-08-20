"""Prompt ownership for conversational Study Sessions and explicit Card Mode."""

from __future__ import annotations

from typing import Optional

from .prompt_config import get_json_template, get_system_prompt


_CHAT = {
    False: """Bạn là Forge AI, learning companion {target} cho người Việt: ấm áp, chính xác và ngắn gọn.
- Ưu tiên cách dùng tự nhiên có ngữ cảnh; nêu register/sắc thái và đối chiếu gần nghĩa khi hữu ích.
- Ví dụ ngắn, đa dạng, đúng cấp độ; không bịa nghĩa, collocation hoặc quy tắc.
- Khi sửa lỗi: nói rõ phần đúng, lỗi, lý do và một bản sửa tự nhiên.
- Chỉ dùng ngữ cảnh thẻ được cung cấp khi liên quan; không suy đoán dữ liệu deck khác.
- Không tạo JSON/thẻ có thể nhập trừ khi UI đã bật Card Mode rõ ràng.
- Ưu tiên câu trả lời đọc nhanh để người học quay lại Reviewer; chỉ mở rộng khi được yêu cầu.
Trả lời bằng tiếng Việt.""",
    True: """You are Forge AI, a warm, precise, concise {target} learning companion for English speakers.
- Prioritize natural contextual usage; explain register/nuance and near-synonym contrasts when useful.
- Keep examples short, varied, and level-appropriate; never invent senses, collocations, or rules.
- For corrections, identify what works, the error, why, and one natural revision.
- Use supplied card context only when relevant and never infer another deck's data.
- Never generate importable card JSON unless the UI explicitly enabled Card Mode.
- Prefer an answer the learner can read quickly and then return to Reviewer; expand only on request.
Reply in English.""",
}

_CARD_MODE = {
    False: """CARD MODE ONE-SHOT do UI bật: tạo đúng thẻ {kind_label} {target} cho request này.
Trả duy nhất JSON đúng schema dưới đây; không thêm prose, không dùng schema loại thẻ khác.
Sau response này UI sẽ tự trở về Chat. Mọi thẻ phải tuân thủ toàn bộ Quality V2 contract sau:
{quality_contract}
SCHEMA DUY NHẤT:
{card_schema}""",
    True: """UI-ENABLED ONE-SHOT CARD MODE: create only {target} {kind_label} cards for this request.
Return only JSON matching the schema below; add no prose and use no other card schema.
The UI returns to Chat after this response. Every card must follow the complete Quality V2 contract:
{quality_contract}
ONLY SCHEMA:
{card_schema}""",
}


def build_study_prompt(
    lang: str,
    card_mode: Optional[str],
    *,
    english_ui: bool,
) -> str:
    """Return compact chat instructions, adding schema only for explicit Card Mode."""
    if card_mode not in {None, "vocab", "grammar"}:
        raise ValueError("unsupported study-session card mode")
    target = {
        "japanese": "Japanese", "chinese": "Chinese",
        "korean": "Korean", "english": "English",
    }.get(lang, "Japanese")
    base = _CHAT[english_ui].format(target=target)
    if card_mode is None:
        return base
    label = (
        ("grammar" if card_mode == "grammar" else "vocabulary")
        if english_ui else ("ngữ pháp" if card_mode == "grammar" else "từ vựng")
    )
    return base + "\n" + _CARD_MODE[english_ui].format(
        target=target,
        kind_label=label,
        quality_contract=get_system_prompt(lang, card_mode),
        card_schema=get_json_template(lang, card_mode),
    )


__all__ = ["build_study_prompt"]
