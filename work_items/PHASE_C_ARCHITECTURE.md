# Phase C — Kiến trúc (Giảm nợ kỹ thuật)

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

**Trạng thái:** `Đang làm` — P1-D còn orchestration UI

**Vấn đề:** `__init__.py` vẫn là "god object" — orchestration UI chưa tách (P1-D còn dang dở).

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

**Trạng thái:** `Đang làm` — document extractors và HTTP/AI client hoàn thành

**Vấn đề:** `ai_extractor.py` vẫn là "god module" — trách nhiệm prompt + cache + API + parse.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/ai_http_client.py`, `utils/document_extractors.py`, `utils/prompt_config.py`, `tests/`
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

**Trạng thái:** `Có điều kiện — thực hiện trước khi mở rộng hơn 3 ngôn ngữ đích`

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

**Trạng thái:** `Có điều kiện — gộp vào C2 hoặc hoàn thành trước khi thêm nhiều ngôn ngữ đích`

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

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase C / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
