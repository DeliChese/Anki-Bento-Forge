---
name: project-map
description: Bản đồ toàn bộ dự án AnkiTool — cấu trúc, dependency, data flow, critical paths. Đọc khi bắt đầu bất kỳ task nào chưa rõ phạm vi.
---

# 🗺️ SKILL-01: PROJECT MAP

## KHI NÀO DÙNG
- Mới vào dự án / task lớn chưa biết đụng file nào.
- Cần tìm nhanh nơi chứa 1 chức năng.

## CẤU TRÚC FILE (đầy đủ)

```
> Số dòng file cập nhật theo code hiện tại (V17.1). Số dòng hàm nội bộ nên tự verify bằng `search_files` trước khi dùng.

__init__.py (26)         ← compatibility facade; re-export AnkiSmartFactory/start_smart_factory
ui/factory_dialog.py (2,830) ← AnkiSmartFactory QDialog + Qt/Anki orchestration; entry:2801
audio/engine.py (136)    ← VOICE_OPTIONS, router get_audio_multilang, speed_to_edge_rate
audio/tts.py (263)       ← Edge / gTTS / VoiceVox providers
Language/__init__.py     ← LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO
Language/japanese.py (102) ← LANG_CONFIG, GRAMMAR_CONFIG
Language/chinese.py (110)  ← tương tự
Language/korean.py (104)   ← tương tự (V17 — Hàn)
mode/__init__.py         ← registry exports
mode/css.py (236)        ← css_japanese, css_chinese, css_korean, *_grammar
mode/templates.py (1,149) ← tmpl_*_q/a + COMBO (tmpl_{lang}_combo_q/a), LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES
mode/shared.py (497)     ← _WB_JS_BODY, _HW_JS_BODY, WB_POOLS, _SPEED_CTRL_JS, _LG_JS_BODY, _COMBO_MODE_JS
mode/card_render.py      ← build_qfmt/build_afmt (tự append field tùy chỉnh lên thẻ)
utils/ai_extractor.py (1,489) ← AI extraction/chat orchestration (xem SKILL-02); compatibility facade cho responsibility đã tách
utils/ai_prompt_defaults.py (528) ← schema + prompt defaults VI/EN thuần; không dependency runtime
utils/ai_response_parser.py (64) ← parse AI JSON/comment thuần; dùng chung vocab/grammar/batch
utils/import_history.py (522) ← history storage/query/summary + scan aggregation; Anki context được inject
utils/ai_http_client.py (243) ← HTTP transport AI thuần: TLS/pool/retry/rate-limit/cancel; không phụ thuộc Anki/UI/config
utils/ai_result_cache.py (160) ← AI result cache thuần: key/TTL/persistence/pruning; dependency được inject
utils/ai_workflow.py ← lifecycle worker AI: cancellation/token/signal; stdlib-only, worker/UI callbacks được inject
utils/document_extractors.py (242) ← đọc TXT/CSV/PDF/DOCX/XLSX cục bộ; không phụ thuộc Anki/AI
utils/batch_processor.py (1,061) ← batch (xem SKILL-03)
utils/prompt_config.py   ← prompt/schema/field_map override (utils/ai_prompts.json)
utils/deck_cache.py (258) ← get_existing_vocab_from_deck, invalidate
utils/json_parser.py (78) ← safe_parse_json
utils/logger.py (114)    ← setup_logging, get_logger
utils/i18n.py (1,744)    ← t(), set_language, SUPPORTED_LANGUAGES
utils/ai_config.json     ← 🚨 API key mã hóa — KHÔNG commit
workers/__init__.py      ← re-export 7 threads
workers/import_worker.py ← ImportWorker
workers/ai_workers.py    ← PreviewThread, AiExtractThread, AiChatThread
workers/deck_scan_worker.py ← DeckScanWorker
workers/batch_workers.py ← BatchProcessThread, DeckOrganizerThread
ui/__init__.py           ← re-export dialogs
ui/ai_dialogs.py         ← AiChatDialog
ui/ai_settings.py        ← show_ai_settings_dialog, _test_ai_connection
ui/ai_preview.py         ← show_ai_preview_dialog
ui/batch_dialog.py       ← BatchWordListDialog
ui/verify_dialog.py      ← show_diff_meaning_dialog
ui/history_dialog.py     ← lịch sử AI
ui/prompt_editor.py      ← sửa prompt/schema/field map
ui/theme.py (539)        ← apply_theme, ThemeDialog, snap_maximize
hooks/reviewer.py        ← register_hooks (inject combo mode + LG + speed)
hooks/overview_mode.py   ← register_overview_hooks, patch Overview._table (wrap Onigiri), webview message handler
tests/                   ← 444 tests (36 file) — xem SKILL-10
```

## DEPENDENCY GRAPH (imports chính)

```
__init__.py → ui.factory_dialog (compatibility facade only)
ui.factory_dialog → Language, mode, audio.engine, utils(safe_parse_json,logger,ai_extractor)
                  → workers (7 thread), ui (dialogs), ui.theme, hooks.reviewer
ai_extractor → utils.logger, utils.ai_http_client, utils.document_extractors, utils.json_parser(ko trực tiếp—dùng batch), deck_cache(qua utils)
ai_prompt_defaults → pure data; prompt_config phụ thuộc trực tiếp, ai_extractor re-export compatibility
ai_response_parser → utils.json_parser; ai_extractor re-export compatibility, batch import owner trực tiếp
import_history → utils.user_data + logger; không import aqt/Language, scan context do ai_extractor inject lazy
ai_http_client → Python stdlib; không phụ thuộc aqt/mw/config/prompt/parser
ai_result_cache → utils.user_data; không phụ thuộc aqt/mw/AI workflow/prompt config
ai_workflow → Python stdlib; Factory inject `AiExtractThread`/`AiChatThread` và UI callbacks
document_extractors → utils.logger + parser tùy chọn đã cài; không phụ thuộc aqt/mw/AI/network
batch_processor → ai_extractor (get_api_config, prompts, _parse_ai_json_with_comment, _apply_reasoning_effort)
workers/* → aqt.qt, utils.ai_extractor / batch_processor / deck_cache
hooks/reviewer → audio.engine (detect_lang_from_model), mode (_SPEED_CTRL_JS, _LG_JS_BODY)
ui/* → aqt.qt, utils (batch_processor, ai_extractor, i18n)
```

**Lưu ý vòng lặp**: `utils/__init__.py` import từ `ai_extractor`; `ai_extractor` KHÔNG import lại `utils/__init__` (chỉ import `.logger`). Giữ nguyên để tránh circular import.

## DATA FLOW

```
[A] Import JSON thủ công:
    json_input → ui/factory_dialog.py::_analyze_content:1463 → safe_parse_json
    → _verify_batch_impl:1484 (query Anki, phân loại add/update/dup/dup_diff)
    → _process_import:1897 → ImportWorker (thread) → get_audio_multilang → add_to_import_history

[B] AI Extract:
    ui/factory_dialog.py::_ai_extract:2284 → DeckScanWorker (lấy existing words, cache 30p)
    → _start_ai_extract:2364 → AiExtractThread → extract_vocabulary_long_text
    → _show_ai_preview:2719 → ui/ai_preview → _finalize_ai_vocab:2733

[C] Batch:
    ui/factory_dialog.py::_ai_batch_process:2432 → ui/batch_dialog (BatchWordListDialog)
    → BatchProcessThread → process_large_word_list → AI per batch
    → DeckOrganizerThread → organize_decks_with_ai → create_decks_from_organization

[D] Chat:
    ui/factory_dialog.py::_ai_chat:2492 → AiChatThread → chat_with_ai (query_anki_context)
    → _show_ai_chat_dialog:2680 → AiChatDialog
```

## CRITICAL PATHS (cấm phá vỡ)

| Path | Lý do |
|------|-------|
| `get_audio_multilang` → `_install_edge_tts` | Audio = tính năng chính |
| `safe_parse_json` | Mọi input JSON đi qua |
| `get_api_config` encryption round-trip | API key mã hóa; break = mất key |
| `get_or_create_model` (`ui/factory_dialog.py:2115`) | Sai = hỏng Note Type/template |
| `register_hooks` (`hooks/reviewer.py:45`) | Speed control + Letter Gap khi review |
| `_PROMPT_VERSION` bump | Quên bump = cache cũ sai |

## TOKEN BUDGET (đọc tối thiểu)

| Việc | Đọc skill + source |
|------|--------------------|
| Sửa audio | SKILL-04 + `audio/engine.py` (~1k token) |
| Sửa prompt AI | SKILL-02 + `ai_prompt_defaults.py` + `prompt_config.py` |
| Sửa template thẻ | SKILL-08 + `mode/templates.py` 1 hàm (~0.8k) |
| Sửa UI dialog | SKILL-06 + file ui/ tương ứng |
| Thêm ngôn ngữ mới | SKILL-07 + SKILL-08 + SKILL-04 (3 skill, ~3.5k) |
| Sửa worker | SKILL-05 + 1 file workers/ |
