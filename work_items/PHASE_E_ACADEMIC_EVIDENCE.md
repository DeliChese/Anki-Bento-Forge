# Phase E — Bằng chứng học thuật

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Phase E (Không phình to)
> **Trạng thái:** `Có điều kiện` — Anki đã có thống kê; chỉ làm báo cáo Bento riêng khi có câu hỏi người dùng rõ ràng.
> **Mục tiêu:** Dùng **Anki review log có sẵn** — không cần AI, không cần phình to

## Bối cảnh

Chưa có bằng chứng hiệu quả — không có số liệu retention rate, time-to-mastery. Retention analytics KHÔNG cần AI. Anki đã lưu toàn bộ review log (lịch sử Again/Good/Hard/Easy theo từng card). Chỉ cần đọc `revlog` table + `cards` table → tính retention rate. Đây là tính năng nhẹ, không tốn token, không phình to.

## Hạng mục

### E1. Retention Report

**Trạng thái:** `Để sau — retention không tự chứng minh quan hệ nhân quả với Bento Forge`

**Vấn đề:** Không có số liệu retention rate, time-to-mastery — không có bằng chứng hiệu quả học tập.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** `utils/anki_adapter.py`, `utils/anki_ops.py`, `ui/`, `utils/i18n.py`, `tests/`
- **Thay đổi yêu cầu:**
  - Đọc Anki review log → tính retention rate theo kỹ năng (đã có sẵn trong collection)
  - Đọc `revlog` table + `cards` table → tính retention rate
  - Hiển thị báo cáo retention theo deck/kỹ năng
  - Không cần AI, không cần phình to
- **Tiêu chí hoàn tất:**
  - Có test cho retention calculation
  - UI hiển thị báo cáo retention
  - Không thu thập dữ liệu cá nhân — chỉ đọc local collection

### E2. Whitepaper

**Trạng thái:** `Không lên kế hoạch — cần nghiên cứu có consent, phương pháp và dữ liệu đã được duyệt`

**Vấn đề:** Chưa có paper về phương pháp học dựa trên data thực tế.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟢 Thấp
- **Phạm vi dự kiến:** Tài liệu (không phải code)
- **Thay đổi yêu cầu:**
  - Viết paper về phương pháp học dựa trên data thực tế
  - Dùng data từ E1 (retention report) làm bằng chứng
  - Công bố trên nền tảng học thuật
- **Tiêu chí hoàn tất:**
  - Có whitepaper hoàn chỉnh
  - Có data thực tế từ E1 làm bằng chứng
  - Được công bố/công khai

## Bằng chứng cần đạt

- Có số liệu retention rate theo kỹ năng
- Có time-to-mastery data
- Có whitepaper dựa trên data thực tế

## Thứ tự thực hiện bắt buộc

E1 → E2. Mỗi phiên chỉ nhận **một** item.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase E / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
