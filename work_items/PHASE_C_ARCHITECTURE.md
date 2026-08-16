# Phase C — Kiến trúc (Giảm nợ kỹ thuật)

> **PHẠM VI PERSONAL (2026-08-16):** `Để sau`. Chỉ tách một lát nhỏ khi nó giải trực tiếp lỗi hoặc ma sát trong workflow cá nhân; không refactor để chuẩn bị cho 12 ngôn ngữ. Mở qua `PERSONAL_ROADMAP.md`, khuyến nghị `gpt-5.6-terra` / `high`; không big-bang rewrite.

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Phase C (TIỀN ĐỀ cho mở rộng ngôn ngữ)
> **Trạng thái:** `Đang làm có kiểm soát` — chỉ tách từng responsibility có regression test; không chạy theo chỉ tiêu số dòng đơn thuần.
> **Mục tiêu:** Giảm chi phí bảo trì, tăng tốc phát triển, CHUẨN BỊ cho 12 ngôn ngữ

## Bối cảnh

Các file lớn hiện tại là điểm tập trung thay đổi lớn:
- `__init__.py` — 2.835 dòng (god object)
- `ai_extractor.py` — 2.461 dòng (god module)
- `i18n.py` — 2.016 dòng (translation dict khổng lồ)
- `templates.py` — 1.315 dòng (HTML template cứng)
- `batch_processor.py` — 1.061 dòng

Nếu không tách trước khi mở rộng 12 ngôn ngữ, file 2.461 dòng sẽ thành 10.000+ dòng không thể bảo trì.

## Hạng mục

### C1. Tách `__init__.py`

**Trạng thái:** `Hoàn thành` (2026-08-15)

**Kết quả:** Package root là compatibility facade 26 dòng; Qt/Anki orchestration thuộc `ui/factory_dialog.py`, còn state/import/model tiếp tục thuộc các use-case/adapter module riêng.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `__init__.py`, `ui/`, `workers/`, `tests/`
- **Thay đổi yêu cầu:**
  - Hoàn thành P1-D: tách orchestration UI thành module riêng
  - Tách lớp điều phối UI, use-case import/model/state và adapter Anki
  - Giữ public import/API tương thích trong một release
- **Tiêu chí hoàn tất:**
  - `__init__.py` giảm xuống < 1.500 dòng
  - Không tăng direct `mw`/`aqt` access ngoài adapter/UI cho phép
  - Public behavior giữ nguyên qua regression test
  - Module mới có owner/ràng buộc dependency rõ ràng

### C2. Tách `ai_extractor.py`

**Trạng thái:** `Hoàn thành` (2026-08-15)

**Kết quả:** `ai_extractor.py` còn 1.489 dòng; HTTP, document extraction, cache, prompt defaults, response parser và import history đều có owner/ràng buộc dependency riêng, với compatibility re-export cho release hiện tại.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🔥 Cao
- **Phạm vi:** `utils/ai_extractor.py`, `utils/ai_http_client.py`, `utils/ai_result_cache.py`, `utils/ai_prompt_defaults.py`, `utils/ai_response_parser.py`, `utils/import_history.py`, `utils/document_extractors.py`, `utils/prompt_config.py`, `tests/`
- **Thay đổi yêu cầu:**
  - Tách prompt/cache/parse thành module riêng
  - Mỗi PR/phiên chỉ tách một responsibility
  - Di chuyển test cùng responsibility
  - Không vừa refactor vừa thay đổi hành vi sản phẩm
- **Tiêu chí hoàn tất:**
  - `ai_extractor.py` giảm xuống < 1.500 dòng
  - Prompt/cache/parse có module riêng với test riêng
  - Public behavior giữ nguyên qua regression test
  - Không "big-bang rewrite" của AI extractor

### C3. Tách `templates.py` → `templates/{lang}.py`

**Trạng thái:** `Hoàn thành` (2026-08-15)

**Vấn đề:** `templates.py` HTML nên tách thành file template riêng (không hardcode trong Python). 15 ngôn ngữ × 5 chế độ × 2 mặt = 150 template — cần tách file riêng.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `mode/templates.py`, `mode/`, `tests/test_card_render.py`
- **Thay đổi yêu cầu:**
  - Mỗi ngôn ngữ 1 file template riêng — TIỀN ĐỀ cho 15 ngôn ngữ
  - Tách HTML template ra khỏi Python code
  - Giữ public API tương thích trong release hiện tại
- **Tiêu chí hoàn tất:**
  - `templates.py` giảm xuống < 500 dòng
  - Mỗi ngôn ngữ có file template riêng
  - Regression test pass cho cả 3 ngôn ngữ hiện tại

### C4. Tách `i18n.py` → `i18n/{lang}.json`

**Trạng thái:** `Để sau — i18n là ngôn ngữ giao diện (VI/EN), không tăng theo từng ngôn ngữ đích`

**Vấn đề:** `i18n.py` translation dict nên tách thành file JSON riêng. 15 ngôn ngữ × ~50 keys = 750 keys — cần tách JSON.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/i18n.py`, `utils/i18n_config.json`, `tests/test_i18n.py`
- **Thay đổi yêu cầu:**
  - Mỗi ngôn ngữ 1 file JSON translation — TIỀN ĐỀ cho 15 ngôn ngữ
  - Tách translation dict ra khỏi Python code
  - Giữ public API tương thích trong release hiện tại
- **Tiêu chí hoàn tất:**
  - `i18n.py` giảm xuống < 500 dòng
  - Mỗi ngôn ngữ có file JSON riêng
  - Regression test pass cho cả 2 ngôn ngữ UI hiện tại (EN/VI)

### C5. Tách `prompts` → `prompts/{lang}.py`

**Trạng thái:** `Hoàn thành` (2026-08-15)

**Vấn đề:** 15 ngôn ngữ × 2 chế độ × 2 ngôn ngữ UI = 60 prompt — cần tách file riêng.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/prompt_config.py`, `tests/test_prompt_config.py`
- **Thay đổi yêu cầu:**
  - Mỗi ngôn ngữ 1 file prompt riêng — TIỀN ĐỀ cho 15 ngôn ngữ
  - Tách prompt ra khỏi `ai_extractor.py`
  - Giữ public API tương thích trong release hiện tại
- **Tiêu chí hoàn tất:**
  - Prompt cho 3 ngôn ngữ hiện tại nằm trong file riêng
  - `ai_extractor.py` không còn chứa prompt text
  - Regression test pass cho cả 3 ngôn ngữ

### C6. Plugin API

**Trạng thái:** `Không lên kế hoạch — chỉ cân nhắc khi đã có maintainer/consumer bên thứ ba cụ thể`

**Vấn đề:** Chưa có public API cho nhà phát triển thứ 3.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟢 Thấp
- **Phạm vi dự kiến:** `__init__.py`, `hooks/`, `utils/`, `tests/`
- **Thay đổi yêu cầu:**
  - Public API cho nhà phát triển thứ 3 (hooks, events, data access)
  - Cho phép cộng đồng tự thêm ngôn ngữ
  - Tài liệu API rõ ràng
- **Tiêu chí hoàn tất:**
  - Có public API documented
  - Có test cho plugin API
  - Không làm thay đổi hành vi core khi không có plugin

## Bằng chứng cần đạt

- `__init__.py` < 1.500 dòng
- `ai_extractor.py` < 1.500 dòng
- `templates.py` < 500 dòng
- `i18n.py` < 500 dòng
- Sẵn sàng cho 15 ngôn ngữ

## Thứ tự thực hiện bắt buộc

C1/C2 theo từng responsibility → C3/C5 khi quyết định mở rộng ngôn ngữ → C4/C6 chỉ khi có nhu cầu thực tế.

### 2026-08-15 — Phase C / C1

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `__init__.py`, `ui/factory_dialog.py`, `tests/test_factory_architecture.py`, factory regression tests và project map.
- Thay đổi: Chuyển `AnkiSmartFactory`, Qt/`mw`, hooks và menu wiring sang owner UI; giữ `AnkiSmartFactory`/`start_smart_factory` tại package root qua compatibility facade. Các use case state/import/model và adapter Anki không đổi owner hoặc hành vi.
- Kiểm chứng: `py_compile` đạt; regression hẹp `45 passed`; harness cô lập chạy hai vòng, mỗi vòng `423 passed`; `git diff --check` đạt. Architecture gate khóa giới hạn `< 1.500` dòng, public re-export và cấm dependency Anki/Qt trực tiếp tại package root.
- Rủi ro còn lại / bước kế tiếp: `ui/factory_dialog.py` vẫn lớn nhưng đã bị cô lập đúng layer; chỉ tách tiếp từng responsibility khi có seam hành vi và regression test cụ thể. Tiếp tục C2 độc lập, không trộn refactor AI vào C1.

### 2026-08-15 — Phase C / C2 — AI result cache

- Trạng thái: lát cắt cache `Đang làm` → `Hoàn thành`; C2 tổng thể giữ `Đang làm`.
- Phạm vi: `utils/ai_result_cache.py`, compatibility wiring trong `utils/ai_extractor.py`, `tests/test_ai_result_cache.py` và tài liệu AI extraction.
- Thay đổi: Chuyển cache key, prompt signature/version dimension, TTL provider 7/14 ngày, migration/pruning, persistence và clear sang owner thuần riêng. Config/provider/prompt được inject; module mới không phụ thuộc Anki, UI hoặc AI workflow. Các tên `_PROMPT_VERSION`, `_ai_cache_*` và `clear_cache` tiếp tục hoạt động qua lớp tương thích.
- Kiểm chứng: `py_compile` đạt; regression AI/prompt/grammar `100 passed`; harness cô lập chạy hai vòng, mỗi vòng `428 passed`; `git diff --check` đạt.
- Rủi ro còn lại / bước kế tiếp: `ai_extractor.py` còn 2.455 dòng; tách prompt defaults ở lát kế tiếp, sau đó parse/history theo từng responsibility có regression riêng.

### 2026-08-15 — Phase C / C2 — prompt defaults

- Trạng thái: lát cắt prompt defaults `Đang làm` → `Hoàn thành`; C2 tổng thể giữ `Đang làm`.
- Phạm vi: `utils/ai_prompt_defaults.py`, `utils/prompt_config.py`, compatibility re-export trong `utils/ai_extractor.py`, `tests/test_ai_prompt_defaults.py` và tài liệu AI extraction.
- Thay đổi: Chuyển nguyên văn 32 symbol schema/prompt mặc định VI/EN cho vocab/grammar sang owner dữ liệu thuần, không có dependency runtime. `prompt_config` phụ thuộc trực tiếp owner mới nên loại circular lazy-import; `ai_extractor` vẫn re-export toàn bộ symbol cũ và API template trong release hiện tại.
- Kiểm chứng: đối chiếu tự động `32/32` symbol với source trước refactor cho `changed=[]`; `py_compile` đạt; regression prompt/grammar/batch `145 passed`; harness cô lập chạy hai vòng, mỗi vòng `432 passed`; `git diff --check` đạt.
- Rủi ro còn lại / bước kế tiếp: `ai_extractor.py` giảm 2.455 → 2.006 dòng, chưa đạt `< 1.500`; tách parse ở lát kế tiếp rồi tách history độc lập.

### 2026-08-15 — Phase C / C2 — AI response parser

- Trạng thái: lát cắt parse `Đang làm` → `Hoàn thành`; C2 tổng thể giữ `Đang làm`.
- Phạm vi: `utils/ai_response_parser.py`, compatibility re-export trong `utils/ai_extractor.py`, direct consumer trong `utils/batch_processor.py`, `tests/test_ai_response_parser.py` và tài liệu AI extraction.
- Thay đổi: Chuyển parse code fence/list/dict/`_comment`/embedded JSON/fallback và lỗi truncation sang owner thuần chỉ phụ thuộc stdlib + `safe_parse_json`. Vocab, grammar và batch dùng cùng implementation; tên `_parse_ai_json_with_comment` tiếp tục được re-export từ `ai_extractor` trong release hiện tại.
- Kiểm chứng: corpus đối chiếu với hàm cũ gồm 7 nhóm đầu vào cho `changed=[]`; `py_compile` đạt; regression parser/batch/grammar `139 passed`; harness cô lập chạy hai vòng, mỗi vòng `438 passed`; `git diff --check` đạt.
- Rủi ro còn lại / bước kế tiếp: `ai_extractor.py` giảm 2.006 → 1.951 dòng, chưa đạt `< 1.500`; tách import history ở lát C2 kế tiếp.

### 2026-08-15 — Phase C / C2 — import history và hoàn tất

- Trạng thái: lát cắt import history `Đang làm` → `Hoàn thành`; C2 tổng thể `Đang làm` → `Hoàn thành`.
- Phạm vi: `utils/import_history.py`, compatibility/injection boundary trong `utils/ai_extractor.py`, direct consumers trong `utils/`, `ui/`, `tests/test_import_history.py`, `tests/test_history_items.py` và project map.
- Thay đổi: Chuyển storage/migration, TTL, deck-scan aggregation, add/query/reconstruction/search/summary/clear sang owner riêng. Owner không import Anki/UI/AI orchestration; collection và language config được inject lazy từ compatibility wrapper chỉ khi TTL yêu cầu scan. Các API history công khai tiếp tục được re-export trong release hiện tại.
- Kiểm chứng: `py_compile` đạt; regression history/AI `134 passed`; harness cô lập chạy hai vòng, mỗi vòng `444 passed`; `git diff --check` đạt.
- Kết quả: `ai_extractor.py` giảm 1.951 → 1.489 dòng và đạt tiêu chí `< 1.500`; prompt/cache/parse/history có test và owner rõ ràng. C2 hoàn thành, không thay đổi version hoặc hành vi sản phẩm.

### 2026-08-15 — Phase C / C3 — language-scoped card templates

- Trạng thái: `Có điều kiện` → `Hoàn thành`.
- Phạm vi: `mode/templates/`, compatibility import `mode.templates`, `tests/test_template_architecture.py`.
- Thay đổi: Tách markup Mustache/HTML theo owner `japanese.py`, `chinese.py` và `korean.py`; các helper thật sự dùng chung ở `common.py`. `mode.templates` trở thành package facade nhỏ, giữ nguyên các hàm `tmpl_*`, `LANG_TEMPLATES` và `LANG_GRAMMAR_TEMPLATES` cho consumer hiện tại. Xóa god module `mode/templates.py`.
- Kiểm chứng: kiểm tra SHA-256 cho toàn bộ 46 template trước/sau tách cho kết quả trùng khớp; architecture gate khóa package facade `< 500` dòng, ownership của 3 ngôn ngữ và registry vocab/grammar/SRS.
- Rủi ro còn lại / bước kế tiếp: CSS/JS shared tiếp tục ở owner `mode/css.py` và `mode/shared.py`; khi thêm ngôn ngữ mới chỉ cần thêm module ngôn ngữ và đăng ký registry, không ghép lại markup vào facade.

### 2026-08-15 — Phase C / C5 — language-scoped AI prompts

- Trạng thái: `Có điều kiện` → `Hoàn thành`.
- Phạm vi: `utils/prompts/`, compatibility facade `utils/ai_prompt_defaults.py`, `tests/test_ai_prompt_defaults.py`.
- Thay đổi: Chuyển nguyên vẹn prompt và JSON schema vocab/grammar, cho cả UI VI/EN, sang owner `japanese.py`, `chinese.py` và `korean.py`. Package registry hợp nhất các owner; `ai_prompt_defaults`, `prompt_config` và compatibility re-export từ `ai_extractor` giữ nguyên API/symbol identity.
- Kiểm chứng: SHA-256 của toàn bộ 32 public prompt/default symbols trùng khớp trước/sau refactor; architecture gate kiểm tra facade nhỏ, các module ngôn ngữ không có runtime dependency, registry và re-export tương thích.
- Rủi ro còn lại / bước kế tiếp: Tăng prompt mặc định phải bump `_PROMPT_VERSION` trong `ai_extractor.py`; override người dùng qua `ai_prompts.json` vẫn tự invalid cache theo signature. C4 chưa cần làm nếu chỉ có hai UI locale; ưu tiên hướng mở rộng ngôn ngữ đích hoặc card-quality theo roadmap sản phẩm.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase C / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
