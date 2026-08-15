# Phase B — Chất lượng thẻ

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Phase B (Core competency)
> **Trạng thái:** `Đang làm` — B1 và phần structural của B2 đã hoàn thành; không dùng AI để “chấm AI”.
> **Mục tiêu:** Thẻ tạo ra phải là tốt nhất thị trường

## Bối cảnh

Đây là core competency của Bento Forge — đúc thẻ tự động chất lượng cao với AI. Thẻ tạo ra phải tốt nhất thị trường: Quality Scoring + Error Detection + Level Validation.

## Hạng mục

### B1. Quality Scoring

**Trạng thái:** `Hoàn thành (phạm vi structural) — preview hiển thị điểm completeness 0-100 cho Front/Pattern, Meaning, Example`

**Vấn đề:** Không tự đánh giá chất lượng thẻ (điểm 0-100) trước khi xuất.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/import_quality.py`, `ui/ai_preview.py`, `utils/i18n.py`, `tests/test_import_quality.py`
- **Thay đổi yêu cầu:**
  - Tự đánh giá chất lượng thẻ (điểm 0-100) trước khi xuất
  - Đánh giá dựa trên: độ đầy đủ field, chất lượng ví dụ, độ chính xác nghĩa, cấp độ phù hợp
  - Hiển thị điểm chất lượng trong preview trước khi import
  - Cảnh báo khi thẻ dưới ngưỡng chất lượng
- **Tiêu chí hoàn tất:**
  - Có test cho scoring logic với nhiều kịch bản thẻ
  - UI hiển thị điểm chất lượng trước khi import
  - Không làm thay đổi hành vi import khi không có scoring

### B2. Error Detection

**Trạng thái:** `Hoàn thành (phạm vi deterministic) — cảnh báo lỗi quan sát được, không chặn import; xác minh ngữ pháp/ngữ nghĩa cần nguồn dữ liệu hoặc đánh giá thủ công`

**Vấn đề:** Không phát hiện lỗi ngữ pháp/ngữ nghĩa trong thẻ AI tạo.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/import_quality.py`, `ui/ai_preview.py`, `utils/i18n.py`, `tests/test_import_quality.py`
- **Thay đổi yêu cầu:**
  - Phát hiện lỗi ngữ pháp/ngữ nghĩa trong thẻ AI tạo
  - Kiểm tra: ví dụ có đúng ngữ pháp, nghĩa có khớp từ, field có đầy đủ
  - Cảnh báo khi phát hiện lỗi tiềm ẩn
  - Cho phép người dùng sửa trước khi import
- **Tiêu chí hoàn tất:**
  - Có test cho error detection với thẻ lỗi/đúng
  - UI hiển thị cảnh báo lỗi tiềm ẩn
  - Không chặn import khi chỉ có cảnh báo (người dùng quyết định)

### B3. Level Validation

**Trạng thái:** `Để sau — chỉ làm khi chọn được dataset chuẩn có giấy phép cho từng ngôn ngữ`

**Vấn đề:** Không kiểm tra từ có đúng cấp độ JLPT/HSK/TOPIK hay không.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `Language/`, `utils/import_quality.py`, `utils/i18n.py`, `tests/test_import_quality.py`
- **Thay đổi yêu cầu:**
  - Kiểm tra từ có đúng cấp độ JLPT/HSK/TOPIK hay không
  - So sánh cấp độ AI gán với cấp độ chuẩn (nếu có dữ liệu)
  - Cảnh báo khi cấp độ không khớp
  - Cho phép người dùng điều chỉnh cấp độ
- **Tiêu chí hoàn tất:**
  - Có test cho level validation với nhiều ngôn ngữ
  - UI hiển thị cảnh báo cấp độ không khớp
  - Không chặn import khi chỉ có cảnh báo

### B4. Context-aware Examples

**Trạng thái:** `Để sau — prompt hiện đã yêu cầu ví dụ theo ngữ cảnh; cần phản hồi người dùng/bộ mẫu trước khi thay đổi`

**Vấn đề:** Ví dụ phụ thuộc hoàn toàn vào prompt — chưa có validation tự động.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/prompt_config.py`, `tests/test_prompt_config.py`
- **Thay đổi yêu cầu:**
  - Ví dụ phù hợp ngữ cảnh, không generic
  - Validation tự động: ví dụ có chứa từ mục tiêu, đúng cấp độ, tự nhiên
  - Cải thiện prompt để ví dụ bám ngữ cảnh thực
- **Tiêu chí hoàn tất:**
  - Có test cho context-aware example validation
  - Tỷ lệ ví dụ generic giảm 50%+
  - Chất lượng thẻ không giảm (regression test pass)

### B5. Multi-sense Disambiguation

**Trạng thái:** `Để sau — grammar prompt đã hỗ trợ nghĩa/pattern riêng; vocab cần nghiên cứu schema và tác động token`

**Vấn đề:** Không phân biệt rõ các nghĩa khác nhau của từ đa nghĩa.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/prompt_config.py`, `Language/`, `tests/test_prompt_config.py`
- **Thay đổi yêu cầu:**
  - Phân biệt rõ các nghĩa khác nhau của từ đa nghĩa
  - Tạo entry riêng cho mỗi nghĩa khi cần
  - Ví dụ phải làm rõ nghĩa đang dùng
- **Tiêu chí hoàn tất:**
  - Có test cho multi-sense disambiguation
  - Từ đa nghĩa được xử lý đúng (entry riêng hoặc nghĩa rõ ràng)
  - Không làm tăng đáng kể số request AI

### B6. Collocation/Usage Notes

**Trạng thái:** `Có điều kiện — field map tùy chỉnh đã hỗ trợ; chỉ thêm mặc định khi có nhu cầu đã xác nhận`

**Vấn đề:** Không thêm ghi chú cách dùng, collocation, register.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/prompt_config.py`, `mode/templates.py`, `tests/test_prompt_config.py`
- **Thay đổi yêu cầu:**
  - Thêm ghi chú cách dùng, collocation, register
  - Hiển thị ghi chú trên thẻ (field mới hoặc trong ví dụ)
  - Cải thiện prompt để tạo ghi chú hữu ích
- **Tiêu chí hoàn tất:**
  - Có test cho collocation/usage notes
  - Thẻ có ghi chú cách dùng khi cần
  - Không làm tăng đáng kể output token

## Bằng chứng cần đạt

- Thẻ tạo ra có điểm chất lượng trung bình 80/100+
- Tỷ lệ lỗi ngữ pháp/ngữ nghĩa giảm 50%+
- Cấp độ JLPT/HSK/TOPIK chính xác 90%+

## Thứ tự thực hiện bắt buộc

B1/B2 structural validation → đánh giá mẫu thủ công → B3 (nếu có dataset) → B4/B5/B6 theo phản hồi người dùng.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase B / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`

### 2026-08-15 — Phase B / B1-B2 structural validation

- Trạng thái: `Hoàn thành` (B1 structural) / `Hoàn thành một phần` (B2 structural)
- Phạm vi: `utils/import_quality.py`, `ui/ai_preview.py`, `utils/i18n.py`, `tests/test_import_quality.py`
- Thay đổi: Chấm completeness 0-100 theo Front/Pattern, Meaning, Example; preview cảnh báo thẻ thiếu trường và vẫn cho phép sửa/import.
- Kiểm chứng: `scripts/test_isolated.ps1 -Python python` — 419 passed, chạy 2 vòng.
- Rủi ro còn lại / bước kế tiếp: Không đánh giá độ đúng nghĩa, ngữ pháp, độ tự nhiên hay cấp độ; chỉ tiếp tục khi có corpus/dataset hoặc quy trình review phù hợp.

### 2026-08-15 — Phase B / B2 deterministic error detection

- Trạng thái: `Hoàn thành` trong phạm vi có thể xác minh bằng quy tắc, không dùng AI để “chấm AI”.
- Phạm vi: `utils/import_quality.py`, `ui/ai_preview.py`, `utils/i18n.py`, `tests/test_import_quality.py`
- Thay đổi: Phát hiện placeholder, nghĩa lặp mặt thẻ, ví dụ sai hệ chữ, từ Trung không có trong ví dụ, mẫu ngữ pháp nguyên văn không có trong ví dụ, và ví dụ chỉ lặp target; hiển thị chi tiết bằng tooltip ở hàng preview.
- Kiểm chứng: `python -m pytest --rootdir=tests -p no:cacheprovider -q tests/test_import_quality.py`.
- Rủi ro còn lại / bước kế tiếp: Không thể xác nhận độ đúng của dịch nghĩa, ngữ pháp, tính tự nhiên hay cấp độ nếu không có corpus/dataset được cấp phép hoặc quy trình review thủ công.
