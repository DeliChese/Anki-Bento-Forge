"""Pure workspace policy for Reviewer tutor vs Forge production assistant.

V18.2 keeps one AI/session backend while giving each surface an explicit job.
This module is intentionally Qt-free so workspace semantics are easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional


WORKSPACE_REVIEWER = "reviewer"
WORKSPACE_FORGE = "forge"
SUPPORTED_WORKSPACES = frozenset({WORKSPACE_REVIEWER, WORKSPACE_FORGE})

_LANGUAGE_LABELS = {
    "japanese": "Japanese",
    "chinese": "Chinese",
    "korean": "Korean",
    "english": "English",
}
_MODE_LABELS = {
    "vocab": {"vi": "Từ vựng", "en": "Vocabulary"},
    "grammar": {"vi": "Ngữ pháp", "en": "Grammar"},
    "chat": {"vi": "Trao đổi", "en": "Chat"},
}


@dataclass(frozen=True)
class WorkspaceAction:
    key: str
    label_vi: str
    label_en: str
    prompt_vi: str
    prompt_en: str

    def label(self, ui_lang: str) -> str:
        return self.label_en if ui_lang == "en" else self.label_vi

    def prompt(self, ui_lang: str) -> str:
        return self.prompt_en if ui_lang == "en" else self.prompt_vi


@dataclass(frozen=True)
class AiWorkspacePolicy:
    workspace: str
    title_vi: str
    title_en: str
    subtitle_vi: str
    subtitle_en: str
    context_kind: str
    actions: tuple[WorkspaceAction, ...]

    def title(self, ui_lang: str) -> str:
        return self.title_en if ui_lang == "en" else self.title_vi

    def subtitle(self, ui_lang: str) -> str:
        return self.subtitle_en if ui_lang == "en" else self.subtitle_vi


_REVIEWER_ACTIONS = (
    WorkspaceAction(
        "explain", "Giải thích", "Explain",
        "Giải thích ngắn gọn điểm học chính của thẻ hiện tại. Nếu đang ở mặt câu hỏi, không tiết lộ đáp án trừ khi tôi yêu cầu.",
        "Briefly explain the main learning point of the current card. On the question side, do not reveal the answer unless I ask.",
    ),
    WorkspaceAction(
        "hint", "Gợi ý", "Hint",
        "Cho tôi 1–2 gợi ý gián tiếp để tự nhớ đáp án của thẻ hiện tại, không nói thẳng đáp án.",
        "Give me 1–2 indirect cues to retrieve the current card answer without stating it directly.",
    ),
    WorkspaceAction(
        "contrast", "Phân biệt", "Contrast",
        "Phân biệt mục đang học với một mục dễ nhầm, tập trung vào dấu hiệu giúp chọn đúng khi ôn tập.",
        "Contrast the current learning item with a commonly confused one, focusing on cues that help retrieval.",
    ),
    WorkspaceAction(
        "usage", "Cách dùng", "Usage",
        "Giải thích cách dùng thực tế của mục đang học và nêu một lỗi người học thường mắc.",
        "Explain practical usage of the current learning item and one common learner mistake.",
    ),
    WorkspaceAction(
        "example", "Ví dụ khác", "New example",
        "Cho một ví dụ mới tự nhiên cho mục đang học, khác với ví dụ trên thẻ, rồi giải thích ngắn vì sao ví dụ đó phù hợp.",
        "Give one natural new example for the current learning item, different from the card example, then briefly explain why it fits.",
    ),
    WorkspaceAction(
        "check", "Kiểm tra tôi", "Quiz me",
        "Đặt một câu hỏi ngắn để kiểm tra xem tôi thực sự hiểu mục đang học hay chỉ nhớ mặt chữ. Chưa đưa đáp án.",
        "Ask one short question that checks whether I understand the current item rather than merely recognize it. Do not give the answer yet.",
    ),
)

_FORGE_ACTIONS = (
    WorkspaceAction(
        "analyze_source", "Phân tích nguồn", "Analyze source",
        "Phân tích nguồn tôi đã dán: xác định những điểm đáng học nhất, nhóm chúng theo từ vựng/ngữ pháp và giải thích ngắn tiêu chí chọn.",
        "Analyze the source I pasted: identify the highest-value learning items, group them into vocabulary/grammar, and briefly explain the selection criteria.",
    ),
    WorkspaceAction(
        "build_vocab", "Tạo từ vựng", "Build vocabulary",
        "Từ nguồn tôi đã dán, tạo các candidate từ vựng có giá trị học tập cao. Ưu tiên nghĩa đúng trong ngữ cảnh và ví dụ bám sát cách dùng trong nguồn.",
        "From the source I pasted, build high-value vocabulary candidates. Prioritize the contextual sense and examples grounded in how the source uses each item.",
    ),
    WorkspaceAction(
        "build_grammar", "Tạo ngữ pháp", "Build grammar",
        "Từ nguồn tôi đã dán, tìm các mẫu ngữ pháp đáng học và tạo candidate với chức năng, cách dùng và ví dụ rõ ràng.",
        "From the source I pasted, identify useful grammar patterns and build candidates with clear function, usage, and examples.",
    ),
    WorkspaceAction(
        "contrast_candidates", "So sánh mục dễ nhầm", "Contrast candidates",
        "Tìm các candidate trong nguồn có nguy cơ bị nhầm với nhau hoặc với mục gần nghĩa, rồi nêu ràng buộc/cách phân biệt ngắn gọn.",
        "Find candidates in the source that are easy to confuse with each other or near-synonyms, then give concise constraints that distinguish them.",
    ),
    WorkspaceAction(
        "improve_examples", "Làm giàu ví dụ", "Improve examples",
        "Đánh giá các ví dụ/candidate trong nguồn hiện tại và đề xuất ví dụ tự nhiên hơn khi cần. Không tự bịa thông tin ngoài ngữ cảnh nếu không cần thiết.",
        "Review the examples/candidates in the current source and suggest more natural examples where useful. Avoid inventing unnecessary context.",
    ),
    WorkspaceAction(
        "quality_check", "Kiểm tra nguyên liệu", "Quality check",
        "Kiểm tra nguyên liệu học hiện tại trước khi tạo artifact: chỉ ra mục mơ hồ, nghĩa chưa đủ ràng buộc, ví dụ lệch mục tiêu hoặc candidate chưa đáng đưa vào Xưởng.",
        "Check the current learning material before creating an artifact: flag ambiguity, under-specified senses, off-target examples, or candidates not worth sending to the Factory.",
    ),
)

_POLICIES = {
    WORKSPACE_REVIEWER: AiWorkspacePolicy(
        workspace=WORKSPACE_REVIEWER,
        title_vi="🚉 Trợ giảng toa học",
        title_en="🚉 Study Coach",
        subtitle_vi="Hiểu thẻ đang học · gợi ý vừa đủ · không làm lộ đáp án",
        subtitle_en="Understand the current card · useful cues · no answer leakage",
        context_kind="current_card",
        actions=_REVIEWER_ACTIONS,
    ),
    WORKSPACE_FORGE: AiWorkspacePolicy(
        workspace=WORKSPACE_FORGE,
        title_vi="🚉 Forge AI Workshop",
        title_en="🚉 Forge AI Workshop",
        subtitle_vi="Phân tích nguồn · tạo candidate · đóng gói artifact · chuyển sang Xưởng",
        subtitle_en="Analyze source · build candidates · package artifacts · send to Factory",
        context_kind="source_workspace",
        actions=_FORGE_ACTIONS,
    ),
}


def get_workspace_policy(workspace: str) -> AiWorkspacePolicy:
    key = str(workspace or "").strip().casefold()
    try:
        return _POLICIES[key]
    except KeyError as exc:
        raise ValueError("unsupported AI workspace") from exc


def reviewer_context_line(snapshot: Optional[Mapping], *, ui_lang: str = "vi") -> str:
    """Describe exactly what Reviewer AI is allowed to know at a glance."""
    snapshot = snapshot if isinstance(snapshot, Mapping) else {}
    language = _LANGUAGE_LABELS.get(str(snapshot.get("language") or ""), "—")
    side = str(snapshot.get("side") or "question").strip().casefold()
    mode = str(snapshot.get("study_mode") or "qa").strip().casefold() or "qa"
    has_card = bool(str(snapshot.get("card_id") or "").strip())
    if ui_lang == "en":
        side_label = "Answer side" if side == "answer" else "Question side"
        state = "Current card attached" if has_card else "No current card"
        return f"REVIEWER · {language} · {mode.upper()} · {side_label} · {state}"
    side_label = "Mặt đáp án" if side == "answer" else "Mặt câu hỏi"
    state = "Đã gắn thẻ hiện tại" if has_card else "Không có thẻ hiện tại"
    return f"REVIEWER · {language} · {mode.upper()} · {side_label} · {state}"


def forge_context_line(
    language: str,
    *,
    card_mode: Optional[str] = None,
    source_chars: int = 0,
    ui_lang: str = "vi",
) -> str:
    """Make Forge's non-card context explicit instead of pretending to be Reviewer."""
    language_label = _LANGUAGE_LABELS.get(str(language or ""), "—")
    mode = str(card_mode or "chat").strip().casefold()
    mode_label = _MODE_LABELS.get(mode, _MODE_LABELS["chat"])["en" if ui_lang == "en" else "vi"]
    chars = max(0, int(source_chars or 0))
    if ui_lang == "en":
        source = f"{chars:,} source chars" if chars else "No source loaded"
        return f"FORGE · {language_label} · {mode_label} · {source} · No current card"
    source = f"{chars:,} ký tự nguồn" if chars else "Chưa nạp nguồn"
    return f"FORGE · {language_label} · {mode_label} · {source} · Không có current card"


__all__ = [
    "AiWorkspacePolicy", "WorkspaceAction", "SUPPORTED_WORKSPACES",
    "WORKSPACE_FORGE", "WORKSPACE_REVIEWER", "forge_context_line",
    "get_workspace_policy", "reviewer_context_line",
]
