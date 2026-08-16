# Bảo mật & Quyền riêng tư — Cải thiện

> **PHẠM VI PERSONAL (2026-08-16):** Vẫn là ràng buộc P0 không được phá vỡ, dù add-on không phát hành công khai. Chỉ mở security task khi thay đổi chạm API key, dữ liệu profile, network, backup hoặc log; khuyến nghị `gpt-5.6-sol` / `high` và review thủ công trước khi dùng collection thật.

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Mục 2.3 Bảo mật & Quyền riêng tư (Điểm: 9.0/10)
> **Trạng thái:** `Hoàn thành` — policy đã được review nội bộ và toàn bộ kiểm tra tự động trong phạm vi S1 đạt.
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

**Trạng thái:** `Hoàn thành — SECURITY.md đã tạo và review nội bộ đạt`

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

- Có threat model document và review nội bộ hoàn thành.
- Không có phát hiện nghiêm trọng trong phạm vi kiểm tra S1.
- Security audit bên ngoài là S2 độc lập, chỉ thực hiện trước phát hành lớn/public hoặc khi có ngân sách.

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

### 2026-08-15 — Security & Privacy / S1 Threat Model

- Trạng thái: `Chờ review nội bộ`
- Phạm vi: `SECURITY.md`, `README.md`, `work_items/SECURITY_PRIVACY.md`
- Thay đổi: Thêm threat model, luồng dữ liệu, biện pháp giảm thiểu, giới hạn, quy trình disclosure và quy tắc maintainer dựa trên cơ chế hiện có.
- Kiểm chứng: Rà soát các boundary credential, logging, HTTP, profile persistence và CI; không thay đổi hành vi runtime.
- Rủi ro còn lại / bước kế tiếp: Xác nhận/bật GitHub private vulnerability reporting trước release public; đây là checklist vận hành, không thay đổi kết quả review code/policy.

### 2026-08-15 — Security & Privacy / S1 internal review

- Trạng thái: `Hoàn thành`
- Reviewer: Project owner (user-provided verification)
- Scope: Credential storage, log redaction, HTTP/TLS, profile persistence, isolated test behavior và secret scan.
- Kiểm chứng: `scripts/test_isolated.ps1 -Python python` — 419 passed ở cả 2 vòng; targeted security suite — 22 passed; `git grep` không có match credential-shaped value (exit code 1/no match là kết quả mong đợi của Git).
- Findings: Không có phát hiện nghiêm trọng trong phạm vi S1.
