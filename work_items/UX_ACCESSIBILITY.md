# UX & Accessibility — Cải thiện

> **PHẠM VI PERSONAL (2026-08-16):** Chỉ audit/sửa màn hình và keyboard flow chủ dự án thật sự dùng; không chạy theo điểm UX/accessibility công khai. Khi mở lỗi UX cụ thể: P2, 🟡 Trung bình, `gpt-5.6-terra` / `medium`, kiểm chứng thủ công trên phiên bản Anki đang dùng.

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Mục 2.4 UX & Accessibility (Điểm: 7.5/10)
> **Trạng thái:** `Có nền tảng` — dialog chính đã có accessible name/tab order; cần audit thủ công trên Anki thật.
> **Mục tiêu:** Nâng UX & Accessibility từ 7.5 lên 8.5+

## Bối cảnh

Hiện tại UX đã khá tốt: i18n EN/VI, keyboard navigation + accessible name, dark/light/midnight themes, glassmorphism theme engine, speed control, interactive games.

## Điểm mạnh hiện tại

- ✅ i18n EN/VI
- ✅ Keyboard navigation + accessible name
- ✅ Dark/light/midnight themes
- ✅ Glassmorphism theme engine
- ✅ Speed control, interactive games

## Hạng mục

### U1. Screen Reader Testing

**Trạng thái:** `Để lên lịch trước release UI kế tiếp — cần kiểm tra NVDA trên Windows/Anki thật`

**Vấn đề:** Chưa có screen reader testing — người dùng khiếm thị có thể gặp khó khăn.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `ui/`, `tests/`
- **Thay đổi yêu cầu:**
  - Test với screen reader (NVDA, VoiceOver, TalkBack)
  - Kiểm tra accessible name cho mọi control
  - Kiểm tra keyboard navigation đầy đủ
  - Sửa các vấn đề phát hiện
- **Tiêu chí hoàn tất:**
  - Mọi control có accessible name
  - Keyboard navigation hoạt động đầy đủ
  - Screen reader đọc đúng nội dung

### U2. Color Contrast Audit

**Trạng thái:** `Để lên lịch trước release UI kế tiếp — audit WCAG thủ công cho ba theme`

**Vấn đề:** Chưa có color contrast audit — người dùng khiếm thị màu có thể gặp khó khăn.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `ui/theme.py`, `mode/css.py`, `tests/`
- **Thay đổi yêu cầu:**
  - Audit color contrast cho cả 3 themes (dark/light/midnight)
  - Đảm bảo contrast ratio ≥ 4.5:1 cho text
  - Đảm bảo contrast ratio ≥ 3:1 cho UI elements
  - Sửa các vấn đề phát hiện
- **Tiêu chí hoàn tất:**
  - Contrast ratio đạt chuẩn WCAG AA
  - Có test cho color contrast
  - Không làm thay đổi visual design đáng kể

### U3. Onboarding Flow

**Trạng thái:** `Để sau — cần phản hồi người dùng mới; ưu tiên checklist/quick-start không ép buộc`

**Vấn đề:** Chưa có onboarding flow cho người mới — người dùng mới có thể bối rối.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `ui/`, `utils/i18n.py`, `tests/`
- **Thay đổi yêu cầu:**
  - Onboarding flow cho người mới
  - Hướng dẫn từng bước: cấu hình AI, chọn ngôn ngữ, đúc thẻ đầu tiên
  - Tooltip/hint cho các tính năng chính
  - Không làm phiền người dùng cũ
- **Tiêu chí hoàn tất:**
  - Có onboarding flow hoàn chỉnh
  - Người dùng mới hoàn thành đúc thẻ đầu tiên trong < 5 phút
  - Có test cho onboarding flow

## Bằng chứng cần đạt

- Screen reader test pass
- Color contrast đạt WCAG AA
- Onboarding flow hoạt động

## Thứ tự thực hiện bắt buộc

U1 → U2 → U3. Mỗi phiên chỉ nhận **một** item.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — UX & Accessibility / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
