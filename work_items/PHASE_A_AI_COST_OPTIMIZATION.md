# Phase A — Tối ưu chi phí AI

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Phase A (Ưu tiên #1 — SỐNG CÒN)
> **Trạng thái:** `Đã rà soát 2026-08-15` — một số cơ chế đã có; chỉ tiếp tục các hạng mục đo được bằng benchmark thực tế.
> **Mục tiêu:** Giảm token/chi phí tối đa cho free tier

## Bối cảnh

Free tier rất hạn chế — tối ưu token/chi phí là ưu tiên #1, không phải thêm tính năng. Hiện tại đúc 100 từ tiêu tốn ~24.5k token. Mục tiêu giảm xuống < 10k token.

## Hạng mục

### A1. Model Routing thông minh

**Trạng thái:** `Để sau — cần bộ mẫu đánh giá và opt-in của người dùng`

**Vấn đề:** Luôn dùng 1 model cấu hình — không tự chọn model rẻ nhất đủ chất lượng.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_providers.py`, `utils/ai_extractor.py`, `ui/ai_settings.py`, `tests/test_ai_providers.py`
- **Thay đổi yêu cầu:**
  - Tự chọn model rẻ nhất đủ chất lượng (gpt-4o-mini cho đơn giản, reasoner cho phức tạp)
  - Phân loại task theo độ phức tạp (vocab đơn giản vs grammar phức tạp)
  - Cho phép người dùng cấu hình routing policy
- **Tiêu chí hoàn tất:**
  - Có test cho routing logic với nhiều kịch bản task
  - Giảm chi phí trung bình 30%+ so với dùng 1 model cố định
  - Không làm giảm chất lượng thẻ (regression test pass)

### A2. Semantic Caching

**Trạng thái:** `Không thực hiện — semantic similarity không bảo đảm cùng bộ thẻ/ngữ cảnh và tăng rủi ro riêng tư`

**Vấn đề:** Cache chỉ exact match — không tận dụng được kết quả tương tự.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/deck_cache.py`, `tests/test_token_optimization.py`
- **Thay đổi yêu cầu:**
  - Cache theo semantic similarity (không chỉ exact match)
  - Tận dụng kết quả tương tự cho văn bản gần giống
  - Giới hạn dung lượng cache hợp lý (không phình to)
- **Tiêu chí hoàn tất:**
  - Có test cho semantic cache hit/miss
  - Giảm số request AI trùng lặp 20%+
  - Cache vẫn tuân thủ giới hạn dung lượng/lifetime hiện có

### A3. Prompt Compression

**Trạng thái:** `Hoàn thành một phần — prompt đã có giới hạn độ dài và test compactness; cần benchmark chất lượng trước khi nén thêm`

**Vấn đề:** System prompt ~500-800 ký tự/ngôn ngữ × 2 (VI/EN) × 2 (vocab/grammar) — có thể nén thêm.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/prompt_config.py`, `tests/test_prompt_config.py`
- **Thay đổi yêu cầu:**
  - Nén system prompt thêm 30-50% — giảm input token
  - Loại bỏ redundancy, giữ nguyên chất lượng hướng dẫn
  - So sánh chất lượng output trước/sau nén
- **Tiêu chí hoàn tất:**
  - Giảm input token 30-50% cho mỗi request
  - Chất lượng thẻ không giảm (so sánh output mẫu)
  - Có test cho prompt nén

### A4. Batch Optimization

**Trạng thái:** `Hoàn thành một phần — batch word-list đã gộp, estimate, cache và cancel/retry; chỉ tối ưu thêm sau benchmark`

**Vấn đề:** Mỗi request gửi 1 chunk — chưa gộp nhiều từ vào 1 request tối ưu.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_extractor.py`, `utils/batch_processor.py`, `tests/test_batch_processor.py`
- **Thay đổi yêu cầu:**
  - Gộp nhiều từ vào 1 request — giảm overhead
  - Tối ưu kích thước batch theo model context window
  - Giữ nguyên khả năng cancel/retry từng phần
- **Tiêu chí hoàn tất:**
  - Giảm số request 30%+ cho batch lớn
  - Không tăng tỷ lệ lỗi/truncated output
  - Có test cho batch optimization

### A5. Local Model Priority

**Trạng thái:** `Hoàn thành một phần — Ollama/LM Studio đã là preset; chỉ còn health-check/gợi ý opt-in`

**Vấn đề:** Ollama/LM Studio có nhưng không được ưu tiên khuyến nghị.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🔥 Cao
- **Phạm vi dự kiến:** `utils/ai_providers.py`, `ui/ai_settings.py`, `utils/i18n.py`, `tests/test_ai_providers.py`
- **Thay đổi yêu cầu:**
  - Ưu tiên khuyến nghị Ollama/LM Studio — 0 chi phí
  - Phát hiện local model đang chạy và hiển thị gợi ý
  - Cảnh báo khi dùng cloud model tốn phí
- **Tiêu chí hoàn tất:**
  - UI hiển thị gợi ý local model khi khả dụng
  - Có test cho detection logic
  - Không làm thay đổi hành vi khi không có local model

### A6. Token Budget UI

**Trạng thái:** `Hoàn thành — có estimate/confirmation trước khi chạy và budget phiên; batch dialog cũng hiển thị estimate`

**Vấn đề:** Chưa hiển thị rõ chi phí ước tính trước khi chạy (chỉ hiển thị sau).

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `ui/ai_settings.py`, `ui/batch_dialog.py`, `utils/ai_session_policy.py`, `utils/i18n.py`, `tests/test_ai_providers.py`
- **Thay đổi yêu cầu:**
  - Hiển thị rõ chi phí ước tính TRƯỚC khi chạy
  - Hiển thị token budget còn lại trong phiên
  - Cảnh báo khi vượt ngân sách
- **Tiêu chí hoàn tất:**
  - UI hiển thị chi phí ước tính trước khi chạy
  - Có test cho budget calculation
  - Không làm thay đổi hành vi AI extraction

### A7. Free Tier Detection

**Trạng thái:** `Để sau — quota không có API chuẩn giữa provider; chỉ làm adapter riêng khi provider hỗ trợ quota headers/API`

**Vấn đề:** Không phát hiện provider free tier, không cảnh báo khi sắp hết quota.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `utils/ai_providers.py`, `ui/ai_settings.py`, `utils/i18n.py`, `tests/test_ai_providers.py`
- **Thay đổi yêu cầu:**
  - Phát hiện provider free tier
  - Cảnh báo khi sắp hết quota
  - Hiển thị thông tin quota còn lại
- **Tiêu chí hoàn tất:**
  - UI hiển thị cảnh báo quota
  - Có test cho free tier detection
  - Không làm thay đổi hành vi khi không có free tier

## Bằng chứng cần đạt

- Có benchmark phiên bản hóa theo loại input, model, cache hit/miss và token/card.
- Chỉ áp dụng thay đổi khi giảm chi phí mà không làm giảm chất lượng trên bộ mẫu đã duyệt.
- Không đặt ngưỡng chung “100 từ < 10k token”: riêng output nhiều field có thể vượt ngưỡng này.

## Thứ tự thực hiện bắt buộc

Benchmark → A3/A4 có bằng chứng → A1 (nếu người dùng bật routing) → A5 health-check → A7 theo provider. A2 không thực hiện.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase A / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
