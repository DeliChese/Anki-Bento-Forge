# Bảo mật & Quyền riêng tư — Cải thiện

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Mục 2.3 Bảo mật & Quyền riêng tư (Điểm: 9.0/10)
> **Trạng thái:** `Đang làm` — code hiện đã có keyring, redaction, profile-scoped data và CI audit; còn thiếu threat model công khai.
> **Mục tiêu:** Nâng bảo mật từ 9.0 lên 9.5+

## Bối cảnh

Hiện tại bảo mật đã rất tốt: API key → OS credential store (keyring), log redaction (Authorization, api_key, sk-/rk-/pk- patterns), không telemetry — chỉ aggregate usage cục bộ, profile-scoped data (không ghi vào addon dir), atomic write + validation + migration backup.

## Điểm mạnh hiện tại

- ✅ API key → OS credential store (keyring)
- ✅ Log redaction (Authorization, api_key, sk-/rk-/pk- patterns)
- ✅ Không telemetry — chỉ aggregate usage cục bộ
- ✅ Profile-scoped data (không ghi vào addon dir)
- ✅ Atomic write + validation + migration backup

## Hạng mục

### S1. Threat Model Document

**Trạng thái:** `Đang làm — tạo SECURITY.md và review nội bộ trước`

**Vấn đề:** Chưa có threat model document — không có phân tích rủi ro bảo mật có hệ thống.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟡 Trung bình
- **Phạm vi dự kiến:** Tài liệu (SECURITY.md)
- **Thay đổi yêu cầu:**
  - Viết threat model document
  - Phân tích các mối đe dọa tiềm ẩn:
    - API key bị đánh cắp
    - Dữ liệu học bị lộ
    - Prompt injection
    - Supply chain attack
  - Đánh giá rủi ro và biện pháp giảm thiểu
- **Tiêu chí hoàn tất:**
  - Có SECURITY.md hoàn chỉnh
  - Mọi mối đe dọa có biện pháp giảm thiểu
  - Được review bởi ít nhất 1 người

### S2. Security Audit bên ngoài

**Trạng thái:** `Để sau — chỉ thực hiện trước phát hành lớn/public hoặc khi có ngân sách và phạm vi audit rõ ràng`

**Vấn đề:** Chưa có security audit bên ngoài — chưa có đánh giá độc lập về bảo mật.

- **Độ khó:** 🟠 Khó
- **Ưu tiên:** 🟢 Thấp
- **Phạm vi dự kiến:** Toàn bộ codebase
- **Thay đổi yêu cầu:**
  - Thuê/đề nghị security audit bên ngoài
  - Audit toàn bộ codebase
  - Xử lý các phát hiện từ audit
- **Tiêu chí hoàn tất:**
  - Có báo cáo audit hoàn chỉnh
  - Mọi phát hiện nghiêm trọng được xử lý
  - Kết quả được ghi vào tài liệu

## Bằng chứng cần đạt

- Có threat model document
- Có security audit bên ngoài
- Không có lỗ hổng nghiêm trọng chưa xử lý

## Thứ tự thực hiện bắt buộc

S1 → S2. Mỗi phiên chỉ nhận **một** item.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Security & Privacy / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
