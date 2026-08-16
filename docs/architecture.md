# Bento Forge Architecture Overview

> Status: active  
> Authority: supporting human overview; skill 01 is canonical for agent implementation  
> Last verified: 2026-08-16  
> Read when: cần định hướng tổng quan, không dùng thay cho skill hoặc source đã xác minh

`__init__.py` là compatibility facade. Điểm vào UI là `ui/factory_dialog.py`, nơi điều phối Language, mode, audio, workers, dialogs và hooks.

| Layer | Ownership |
|---|---|
| `Language/` | Cấu hình ngôn ngữ, field và model metadata. |
| `mode/` | Template, CSS/JS và render thẻ. |
| `audio/` | Router và provider TTS. |
| `utils/` | Domain thuần: AI transport/workflow/cache/prompt/parser/history và các utility. |
| `workers/` | Luồng nền Qt/Anki, gọi domain services. |
| `ui/`, `hooks/` | Tích hợp Anki/Qt, dialog và reviewer/overview hooks. |
| `tests/`, `benchmarks/` | Regression và evidence chất lượng/cost. |

Các bất biến chính: domain module không import `aqt`; UI dùng `t()`; log dùng `get_logger()`; state chia sẻ phải thread-safe; prompt thay đổi phải invalid cache version; thay đổi phát hành phải cập nhật changelog và kiểm chứng.

Để biết dependency, entry point, method và test cụ thể, đọc [skill project map](../.claude/skills/01-project-map/SKILL.md) rồi tìm symbol bằng `rg`.
