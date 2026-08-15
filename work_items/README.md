# 📋 Bento Forge — Work Items

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Đánh giá học thuật V17.1.0
> **Ngày tạo:** 2026-08-15
> **Mục đích:** Chuyển các điểm cần cải thiện từ đánh giá học thuật sang các file công việc để tiến hành triển khai
> **Rà soát code:** 2026-08-15 — trạng thái trong từng file là nguồn quyết định hiện hành; `ACADEMIC_ASSESSMENT.md` vẫn được giữ như đánh giá lịch sử.

## Tổng quan

Các file công việc được tạo từ `ACADEMIC_ASSESSMENT.md`, chia theo Phase và trục đánh giá. Mỗi file có cấu trúc chuẩn: bối cảnh, hạng mục, tiêu chí hoàn tất, thứ tự thực hiện, mẫu cập nhật.

## Danh sách file công việc

| File | Phase | Mục tiêu | Ưu tiên |
|------|-------|----------|---------|
| [PHASE_A_AI_COST_OPTIMIZATION.md](PHASE_A_AI_COST_OPTIMIZATION.md) | A — Chi phí AI | Benchmark trước; A3/A4/A5 đã có một phần, A6 đã hoàn thành | 🟡 Theo bằng chứng |
| [PHASE_B_CARD_QUALITY.md](PHASE_B_CARD_QUALITY.md) | B — Chất lượng thẻ | B1 structural complete; B2 cảnh báo thiếu trường, không phát sinh token | 🔥 Đang làm |
| [PHASE_C_ARCHITECTURE.md](PHASE_C_ARCHITECTURE.md) | C — Kiến trúc | Tiếp tục tách responsibility có regression test | 🟡 Đang làm |
| [PHASE_D_LANGUAGE_EXPANSION.md](PHASE_D_LANGUAGE_EXPANSION.md) | D — Mở rộng ngôn ngữ | Một pilot theo nhu cầu đã xác nhận | ⏸ Hoãn |
| [PHASE_E_ACADEMIC_EVIDENCE.md](PHASE_E_ACADEMIC_EVIDENCE.md) | E — Bằng chứng học thuật | Báo cáo riêng chỉ khi có câu hỏi người dùng rõ | 🟡 Có điều kiện |
| [PHASE_F_COMMUNITY.md](PHASE_F_COMMUNITY.md) | F — Cộng đồng | FAQ/troubleshooting trước website/cộng đồng | 🟡 Có điều kiện |
| [QUALITY_TESTING.md](QUALITY_TESTING.md) | Test — Chất lượng test | Targeted test theo boundary mới | 🟡 Có điều kiện |
| [SECURITY_PRIVACY.md](SECURITY_PRIVACY.md) | Bảo mật — Quyền riêng tư | Threat model công khai | 🔥 Đang làm |
| [UX_ACCESSIBILITY.md](UX_ACCESSIBILITY.md) | UX — Accessibility | Manual audit NVDA/WCAG trước UI release | 🟡 Có nền tảng |

## Thứ tự triển khai hiện hành

1. Hoàn tất B1/B2 structural validation trong preview — đã triển khai và kiểm thử; các kiểm tra semantic vẫn cần corpus/review.
2. S1: threat model/`SECURITY.md` và review nội bộ.
3. C1/C2: tiếp tục refactor từng responsibility khi có regression test.
4. A: lập benchmark thực tế rồi mới chọn A1/A3/A4/A5.
5. U1/U2 và FAQ: audit thủ công trước release UI kế tiếp.
6. D/E/F: chỉ bắt đầu khi có nhu cầu, scope và người sở hữu rõ ràng.

## Lộ trình 12 tháng lịch sử (từ ACADEMIC_ASSESSMENT.md)

### Tháng 1-2: Nền tảng (Phase A + C) — SỐNG CÒN
- [ ] A1: Model Routing thông minh
- [ ] A2: Semantic Caching
- [ ] A3: Prompt Compression — giảm 30-50% input token
- [ ] A5: Local Model Priority
- [ ] C1: Tách `__init__.py` (hoàn thành P1-D)
- [ ] C2: Tách `ai_extractor.py`
- [ ] C3: Tách `templates.py` → `templates/{lang}.py`
- [ ] C4: Tách `i18n.py` → `i18n/{lang}.json`
- [ ] C5: Tách `prompts` → `prompts/{lang}.py`

### Tháng 3-4: Chất lượng thẻ + Ngôn ngữ đầu tiên (Phase B + D1)
- [ ] B1: Quality Scoring — tự đánh giá chất lượng thẻ
- [ ] B2: Error Detection — phát hiện lỗi ngữ pháp/ngữ nghĩa
- [ ] B3: Level Validation — kiểm tra cấp độ JLPT/HSK/TOPIK
- [ ] D1: Thêm Tiếng Việt + Tiếng Anh

### Tháng 5-6: Mở rộng ngôn ngữ (Phase D2)
- [ ] D2: Thêm Tây Ban Nha + Pháp + Đức

### Tháng 7-9: Mở rộng ngôn ngữ (Phase D3)
- [ ] D3: Thêm Ý + Bồ Đào Nha + Indonesia

### Tháng 10-12: Mở rộng ngôn ngữ đặc biệt (Phase D4)
- [ ] D4: Thêm Thái + Nga + Ả Rập + Hindi
- [ ] E1: Retention Report — dùng Anki review log có sẵn
- [ ] F1: User Documentation Site

## Nguyên tắc chiến lược

| Nguyên tắc | Mô tả |
|------------|-------|
| **🎯 Core competency** | Bento Forge = **đúc thẻ tự động chất lượng cao** với AI. Mọi tính năng phải phục vụ mục tiêu này. |
| **💰 Tối ưu chi phí AI** | Free tier rất hạn chế — tối ưu token/chi phí là ưu tiên #1, không phải thêm tính năng. |
| **🔌 Không phình to** | Game/analytics/gamification KHÔNG nhét vào core. Nếu làm thì là plugin riêng biệt. |
| **📊 Tận dụng Anki data** | Retention analytics dùng **review log có sẵn của Anki** — không cần AI, không cần phình to. |
| **🌍 Mở rộng ngôn ngữ có chiến lược** | Mở rộng dần theo độ khó, không mở rộng ồ ạt 12 ngôn ngữ cùng lúc. |
| **🤝 Cộng tác ecosystem** | Khuyến khích người dùng dùng add-on khác cho game/analytics — Bento Forge tập trung đúc thẻ. |

## KHÔNG làm

- Game mới, gamification, adaptive learning, AI tutor mở rộng — những thứ này không phải core competency và tốn token khổng lồ.
- Người dùng có thể cài add-on khác cho game/analytics.

## Quy tắc sử dụng

1. Mỗi phiên làm việc chỉ nhận **một** item từ **một** file.
2. Trước khi sửa: chuyển đúng hạng mục sang `Đang làm`, ghi ngày và phạm vi thay đổi.
3. Sau khi sửa: ghi kết quả, test đã chạy, rủi ro còn lại và chuyển sang `Hoàn thành` chỉ khi đạt tiêu chí hoàn tất.
4. Không ghi API key, nội dung học, đường dẫn cá nhân, hay log chứa dữ liệu riêng tư.
5. Nếu ưu tiên thay đổi, giữ lại quyết định cũ ngắn gọn trong **Nhật ký thay đổi** thay vì xóa mất bối cảnh.
