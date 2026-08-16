# 📋 Bento Forge — Work Items

> Status: active
> Authority: supporting index; `PERSONAL_ROADMAP.md` is canonical for new work
> Last verified: 2026-08-16
> Read when: cần tìm một work item hoặc tài liệu chuyên môn

> **PHẠM VI HIỆN HÀNH (2026-08-16):** Bento Forge là add-on cá nhân. [PERSONAL_ROADMAP.md](PERSONAL_ROADMAP.md) là nguồn ưu tiên duy nhất cho công việc mới, bao gồm độ ưu tiên, độ khó, model và effort khuyến nghị. Các phase bên dưới được giữ làm lịch sử/chuyên môn; không phải cam kết phát triển công khai.
> **Định hướng:** Ưu tiên workflow cá nhân, an toàn collection, baseline test và benchmark cho ngôn ngữ chủ dự án thực sự học. Không mở rộng đại trà, không xây community và không thêm feature để cạnh tranh.

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
| [PHASE_B_CARD_QUALITY.md](PHASE_B_CARD_QUALITY.md) | B — Chất lượng thẻ | B1 complete; B2 cảnh báo lỗi xác định được, không phát sinh token | 🔥 Đang làm |
| [PHASE_C_ARCHITECTURE.md](PHASE_C_ARCHITECTURE.md) | C — Kiến trúc | C1/C2/C3/C5 hoàn thành; C4/C6 chỉ mở khi có nhu cầu thực tế | ✅ Đủ nền tảng pilot |
| [PHASE_D_LANGUAGE_EXPANSION.md](PHASE_D_LANGUAGE_EXPANSION.md) | D — Mở rộng ngôn ngữ | Một pilot theo nhu cầu đã xác nhận | ⏸ Hoãn |
| [PHASE_E_ACADEMIC_EVIDENCE.md](PHASE_E_ACADEMIC_EVIDENCE.md) | E — Bằng chứng học thuật | Báo cáo riêng chỉ khi có câu hỏi người dùng rõ | 🟡 Có điều kiện |
| [PHASE_F_COMMUNITY.md](PHASE_F_COMMUNITY.md) | F — Cộng đồng | FAQ/troubleshooting trước website/cộng đồng | 🟡 Có điều kiện |
| [QUALITY_TESTING.md](QUALITY_TESTING.md) | Test — Chất lượng test | Targeted test theo boundary mới | 🟡 Có điều kiện |
| [SECURITY_PRIVACY.md](SECURITY_PRIVACY.md) | Bảo mật — Quyền riêng tư | S1 threat model và review nội bộ hoàn thành | ✅ Hoàn thành |
| [UX_ACCESSIBILITY.md](UX_ACCESSIBILITY.md) | UX — Accessibility | Manual audit NVDA/WCAG trước UI release | 🟡 Có nền tảng |
| [P1-04_AWESOMETTS_SAFE_BATCH.md](P1-04_AWESOMETTS_SAFE_BATCH.md) | P1 — TTS cá nhân | Provider AwesomeTTS tùy chọn, audio media lưu local và batch an toàn | 📋 Đã lên kế hoạch |
| [V18_LEARNING_MODES.md](V18_LEARNING_MODES.md) | V18 — Learning Modes | Language và Knowledge cùng lõi import/preview/undo, mode/model riêng | 📋 Milestone kế tiếp |

## Thứ tự triển khai lịch sử

> Phần này được thay thế bởi `PERSONAL_ROADMAP.md`. Chỉ dùng để hiểu bối cảnh các item cũ.

1. Hoàn tất B1/B2 deterministic validation trong preview — đã triển khai và kiểm thử; các kiểm tra semantic vẫn cần corpus/review.
2. C1/C2/C3/C5 đã hoàn thành; chỉ mở C4/C6 khi có nhu cầu thực tế.
3. A: lập benchmark thực tế rồi mới chọn A1/A3/A4/A5.
4. U1/U2 và FAQ: audit thủ công trước release UI kế tiếp.
5. D/E/F: chỉ bắt đầu khi có nhu cầu, scope và người sở hữu rõ ràng.

## Lộ trình 12 tháng lịch sử (đã đóng băng)

> Không thực hiện theo lộ trình này. Đặc biệt, toàn bộ mục tiêu mở rộng ngôn ngữ và community đã chuyển sang backlog đóng băng của `PERSONAL_ROADMAP.md`.

### Tháng 1-2: Nền tảng (Phase A + C) — SỐNG CÒN
- [ ] A1: Model Routing thông minh
- [ ] A2: Semantic Caching
- [ ] A3: Prompt Compression — giảm 30-50% input token
- [ ] A5: Local Model Priority
- [x] C1: Tách `__init__.py` (hoàn thành P1-D)
- [x] C2: Tách `ai_extractor.py`
- [x] C3: Tách `templates.py` → `templates/{lang}.py`
- [ ] C4: Tách `i18n.py` → `i18n/{lang}.json`
- [x] C5: Tách `prompts` → `prompts/{lang}.py`

### Tháng 3-4: Chất lượng thẻ + Ngôn ngữ đầu tiên (Phase B + D1)
- [ ] B1: Quality Scoring — tự đánh giá chất lượng thẻ
- [x] B2: Error Detection — cảnh báo lỗi xác định được; xác minh ngữ pháp/ngữ nghĩa vẫn cần corpus/review
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
