# Chất lượng Test — Cải thiện

> **ƯU TIÊN THAY THẾ (2026-08-16):** P0 personal reliability — đưa baseline test/compile về xanh trước khi theo đuổi property, mutation hay UI automation testing. Khuyến nghị `gpt-5.6-terra` / `high`.

## T0. Baseline xanh cho personal workflow

**Trạng thái:** `Làm trước T1–T3`.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** P0
- **Model / effort:** `gpt-5.6-terra` / `high`
- **Phạm vi:** `scripts/test_isolated.ps1`, test mock/fixture, script Python, CI compile gate và test của flow bị lỗi.
- **Tiêu chí hoàn tất:** isolated harness chạy hai vòng xanh; mọi script Python tracked được compile; lỗi có regression test; không dùng test count/coverage làm KPI.

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Mục 2.2 Chất lượng Test (Điểm: 8.0/10)
> **Trạng thái:** `Có điều kiện` — CI, isolated harness và 30 file test đã tồn tại; chỉ mở rộng test khi có boundary phù hợp.
> **Mục tiêu:** Nâng chất lượng test từ 8.0 lên 9.0+

## Bối cảnh

Hiện tại có ~400 tests, 30 files — coverage rộng. Isolated harness (`scripts/test_isolated.ps1`) — chạy 2 vòng, worktree check. Profile-scoped temp paths (`conftest.py`). CI Python 3.9/3.11. Smoke harness mock Anki public API.

## Điểm mạnh hiện tại

- ✅ ~400 tests, 30 files — coverage rộng
- ✅ Isolated harness (`scripts/test_isolated.ps1`) — chạy 2 vòng, worktree check
- ✅ Profile-scoped temp paths (`conftest.py`)
- ✅ CI Python 3.9/3.11
- ✅ Smoke harness mock Anki public API

## Hạng mục

### T1. Property-based Testing (Hypothesis)

**Trạng thái:** `Để sau — áp dụng chọn lọc cho utility thuần Python (parser/chunk/cache), không đặt số file tùy ý`

**Vấn đề:** Chưa có property-based testing (Hypothesis) — test chỉ dùng ví dụ cụ thể, không khám phá edge cases tự động.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `tests/`, `requirements-dev.txt`
- **Thay đổi yêu cầu:**
  - Thêm Hypothesis vào `requirements-dev.txt`
  - Viết property-based test cho các hàm quan trọng:
    - `json_parser.py` — parse JSON với input ngẫu nhiên
    - `ai_extractor.py` — chunking với văn bản ngẫu nhiên
    - `srs_policy.py` — scheduling với input ngẫu nhiên
    - `i18n.py` — translation với key ngẫu nhiên
  - Property: output phải thỏa mãn invariant (không crash, không mất data)
- **Tiêu chí hoàn tất:**
  - Có ít nhất 5 property-based test files
  - Tất cả property test pass trong isolated harness
  - Không làm tăng đáng kể thời gian test

### T2. Mutation Testing

**Trạng thái:** `Để sau — chạy targeted/offline trong lúc refactor; không lấy mutation score làm KPI phát hành`

**Vấn đề:** Chưa có mutation testing (kiểm tra chất lượng test thật sự) — không biết test có bắt được lỗi hay không.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `tests/`, `scripts/`, `requirements-dev.txt`
- **Thay đổi yêu cầu:**
  - Thêm mutation testing tool (mutmut hoặc tương đương)
  - Chạy mutation test trên các module quan trọng
  - Xác định mutation score hiện tại
  - Cải thiện test để tăng mutation score
- **Tiêu chí hoàn tất:**
  - Mutation score ≥ 80% cho các module quan trọng
  - Có script chạy mutation test
  - Kết quả được ghi vào tài liệu

### T3. UI Automation Testing (QtTest)

**Trạng thái:** `Để sau — ưu tiên smoke/manual test trên Anki thật; QtTest chỉ thêm khi UI boundary đã ổn định`

**Vấn đề:** Chưa có test cho UI automation (QtTest) — UI có thể bị lỗi mà test không phát hiện.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `ui/`, `tests/`, `requirements-dev.txt`
- **Thay đổi yêu cầu:**
  - Thêm QtTest framework
  - Viết UI test cho các dialog chính:
    - `ai_settings.py` — cấu hình AI
    - `batch_dialog.py` — batch processing
    - `prompt_editor.py` — prompt editor
    - `deck_manager_dialog.py` — deck manager
  - Test keyboard navigation, accessible name
- **Tiêu chí hoàn tất:**
  - Có ít nhất 5 UI test files
  - Tất cả UI test pass trong isolated harness
  - Keyboard navigation được test

## Bằng chứng cần đạt

- Mutation score ≥ 80% cho các module quan trọng
- Property-based test phát hiện ít nhất 1 bug mới
- UI test phát hiện ít nhất 1 bug UI mới

## Thứ tự thực hiện bắt buộc

T1 → T2 → T3. Mỗi phiên chỉ nhận **một** item.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Quality Testing / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
