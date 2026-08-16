# Personal Roadmap — Bento Forge

> **Quyết định sản phẩm:** 2026-08-16 — Bento Forge được duy trì như add-on cá nhân. Không có mục tiêu cạnh tranh thị trường, mở rộng đại trà hay xây cộng đồng.
> **Mục tiêu:** Giảm thời gian tạo thẻ và tăng chất lượng học cho workflow của chủ dự án, trước hết với Nhật / Trung / Hàn và chỉ các ngôn ngữ chủ dự án thực sự học.
> **Nguồn ưu tiên:** File này là nguồn quyết định cho backlog đang hoạt động. Các Phase A–F giữ lại lịch sử và chuyên môn, nhưng chỉ được thực hiện khi một item bên dưới tham chiếu tới.

## Phạm vi vận hành

### Làm

- Độ tin cậy của các flow dùng hằng tuần: AI extract, preview/chỉnh sửa, import/update, TTS và review template.
- Sao lưu/undo trước các thao tác có thể làm thay đổi collection.
- Benchmark nhỏ để chọn model, prompt và cấu hình rẻ nhưng đủ tốt cho chính người dùng.
- Tinh chỉnh sâu cho **một ngôn ngữ chính** khi nhu cầu cá nhân lặp lại.

### Không làm mặc định

- AnkiWeb, website, Discord, video hướng dẫn, beta công khai, case study hay mục tiêu user base.
- Hỗ trợ mọi phiên bản Anki/nền tảng; chỉ xác minh phiên bản Anki đang sử dụng trước khi nâng cấp.
- Thêm ngôn ngữ, OCR, video mining, ảnh AI, gamification hoặc analytics chỉ để ngang bằng đối thủ.
- Refactor lớn không giải quyết lỗi, thời gian chờ hoặc thao tác lặp lại của chủ dự án.

## Quy tắc chọn task

Một task chỉ được mở khi thỏa ít nhất một điều kiện:

1. Gây lỗi, mất dữ liệu hoặc tốn thời gian trong workflow cá nhân.
2. Được lặp lại ít nhất ba lần trong hai tuần.
3. Có giả thuyết đo được: tiết kiệm thời gian, giảm chi phí AI hoặc nâng chất lượng thẻ.

Nếu không thỏa điều kiện nào, ghi vào backlog `Để sau`, không triển khai.

## Bảng ưu tiên đang hoạt động

`Effort` là reasoning effort khuyến nghị khi giao cho agent, không phải thời lượng. Model chỉ là gợi ý; con người luôn xác nhận thao tác trong Anki thật và nội dung học.

| ID | Việc cần làm | Ưu tiên | Độ khó | Model / effort khuyến nghị | Ước lượng | Điều kiện hoàn tất |
| --- | --- | --- | --- | --- | --- | --- |
| P0-01 | Thiết lập baseline xanh: tái chạy isolated suite, sửa mọi lỗi test/compile hiện có và thêm regression test đúng boundary | P0 — làm trước feature | 🟡 Trung bình | `gpt-5.6-terra` / `high` | 2–6 giờ | Hai vòng harness xanh; `py_compile` bao gồm cả `scripts/`; worktree không đổi sau test |
| P0-02 | Xác nhận flow cá nhân trên profile Anki đã backup: extract → preview → import/update → undo → TTS → review | P0 — an toàn dữ liệu | 🟡 Trung bình | Chủ dự án thao tác; `gpt-5.6-terra` / `medium` hỗ trợ checklist/triage | 1–2 giờ mỗi phiên bản Anki | Có checklist ngày chạy, phiên bản Anki và kết quả từng flow; không mất note/media/config |
| P0-03 | Thiết lập “personal contract”: một ngôn ngữ chính, phiên bản Anki đang dùng, 2–3 flow hằng tuần và giới hạn chi phí tháng | P0 — định hướng | 🟢 Dễ | Chủ dự án; `gpt-5.6-luna` / `low` để ghi tài liệu | 20 phút | Ghi tại mục nhật ký bên dưới; mọi task mới liên hệ được với một flow |
| P0-04 | Kiểm chứng artifact phát hành: build phải đóng gói `workers/`, không kèm Python cache và có regression test nội dung gói | P0 — chặn feature/release hỏng | 🟡 Trung bình | `gpt-5.6-terra` / `medium` | 1–3 giờ | Artifact clean-profile có đủ runtime modules, không có `__pycache__`/`.pyc`; test build xanh |
| P1-01 | Chạy benchmark model/prompt cho ngôn ngữ chính; chấm thủ công nghĩa, ví dụ, lỗi cấu trúc, cost và latency | P1 — trước tối ưu AI | 🟠 Khó | `gpt-5.6-sol` / `high` | 4–8 giờ | Ít nhất 3 model × 20 mục; có run JSON; chọn default và ngưỡng chấp nhận theo số liệu |
| P1-02 | Tinh chỉnh prompt/schema/template cho ngôn ngữ chính dựa trên benchmark và thẻ đã học | P1 — khi P1-01 có dữ liệu | 🟠 Khó | `gpt-5.6-sol` / `high` | 3–8 giờ mỗi vòng | So sánh trước/sau trên cùng corpus; không giảm điểm benchmark; prompt version/cache được xử lý đúng |
| P1-03 | Rà soát backup, rollback, duplicate/update và giới hạn batch cho collection cá nhân | P1 — giảm rủi ro | 🟡 Trung bình | `gpt-5.6-terra` / `high` | 2–5 giờ | Có test và thao tác phục hồi đã được thử trên profile bản sao |
| P1-04 | Tích hợp AwesomeTTS tùy chọn theo stored-media và batch an toàn, chấp nhận tốc độ chậm để ổn định | P1 — nâng trải nghiệm TTS | 🟠 Khó | Theo lát cắt trong `P1-04_AWESOMETTS_SAFE_BATCH.md` (`terra`/`sol`) | 8–16 giờ | Đạt checklist provider thiếu/có, media local, retry/cancel/resume và smoke trên profile backup |
| V18-01…06 | Mở rộng Bento Forge thành Learning Modes: Language + Knowledge, V1 có Basic/Cloze/source và giữ an toàn collection cũ | Milestone V18 — phát triển mới | 🔴 Rất khó | Theo từng lát cắt trong `V18_LEARNING_MODES.md` (`terra`/`sol`) | 20–40 giờ | Hai mode cùng hoạt động trong một profile; không migration ngầm; release gate V18 đạt |
| P2-01 | Đơn giản hóa/ẩn các flow không dùng để giảm nhiễu UI và chi phí bảo trì | P2 — chỉ khi gây ma sát | 🟡 Trung bình | `gpt-5.6-terra` / `medium` | 1–4 giờ | Flow còn lại không regression; quyết định được ghi vào nhật ký |
| P2-02 | Bổ sung hoặc nâng một ngôn ngữ khác khi chính chủ dự án dùng đều | P2 — theo nhu cầu | 🟠 Khó | `gpt-5.6-sol` / `high` | 8–20 giờ | Corpus riêng, TTS, template và smoke test cho đúng ngôn ngữ đó |

## Backlog đóng băng

| Nhóm | Trạng thái | Chỉ mở lại khi |
| --- | --- | --- |
| Phase D — mở rộng nhiều ngôn ngữ | Đóng băng | Chủ dự án học ngôn ngữ đó đều và P2-02 được mở |
| Phase E — academic evidence/retention report | Đóng băng | Có câu hỏi học tập cá nhân cụ thể mà Anki Stats không trả lời được |
| Phase F — community/public docs | Đóng băng | Quyết định phát hành công khai trở lại |
| Routing tự động, semantic cache, OCR/video/image AI | Để sau | Có dữ liệu P1-01 hoặc ma sát lặp lại chứng minh lợi ích |
| Big-bang refactor | Không làm | Có lỗi bảo trì cụ thể không thể giải bằng lát cắt nhỏ |

## Trình tự cho sáu phiên làm việc tới

1. V18-01 — contract `learning_mode`, state theo deck và compatibility state Language cũ.
2. V18-02 — schema/prompt/validation Knowledge tối thiểu.
3. V18-03 — note type/template Knowledge riêng, có idempotency test.
4. V18-04 — UI chuyển mode, i18n và state input riêng.
5. V18-05 — nối extract/preview/import/history/undo/batch.
6. V18-06 — regression, smoke profile backup, sau đó mới nâng version V18 và ghi changelog. P1-04 AwesomeTTS giữ ở kế hoạch độc lập.

## Nhật ký personal contract

| Ngày | Ngôn ngữ chính | Phiên bản Anki | Flow hằng tuần | Ngân sách AI/tháng | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 2026-08-16 | Nhật (`japanese`) | Anki `2.1.50` (cần xác nhận trong Help → About) | AI extract → preview/import; update/undo; TTS → review | `$10/tháng` (tạm thời) | Hợp đồng cá nhân khởi đầu; đổi khi có số liệu sử dụng thực tế |

## Mẫu cập nhật task

```md
### YYYY-MM-DD — Personal / <ID>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Để sau`
- Lý do mở task: `<flow bị ảnh hưởng hoặc số lần lặp>`
- Model / effort đã dùng: `<model> / <effort>`
- Phạm vi: `<file hoặc module>`
- Kiểm chứng: `<lệnh, smoke test hoặc số liệu benchmark>`
- Quyết định tiếp theo: `<làm tiếp / đóng băng / rollback>`
```

### 2026-08-16 — Personal / P0-02

- Trạng thái: `Đang làm`
- Lý do mở task: xác nhận an toàn dữ liệu cho flow extract → preview → import/update → undo → TTS → review trên profile Anki đã backup.
- Model / effort đã dùng: `gpt-5.6-terra` / `medium` (hỗ trợ checklist/triage)
- Phạm vi: `work_items/P0-02_ANKI_SMOKE_CHECKLIST.md`
- Kiểm chứng: chưa chạy — cần chủ profile thực hiện trong Anki thật và điền checklist.
- Quyết định tiếp theo: chỉ chuyển `Hoàn thành` sau khi tất cả flow đạt `PASS` và không mất note/media/config.

### 2026-08-16 — Personal / P0-03

- Trạng thái: `Hoàn thành` (hợp đồng khởi đầu; cần xác nhận phiên bản Anki thực tế)
- Lý do mở task: cần giới hạn rõ ngôn ngữ, flow lặp lại và ngân sách trước khi benchmark/tinh chỉnh AI.
- Model / effort đã dùng: `gpt-5.6-luna` / `low` (ghi tài liệu)
- Phạm vi: mục `Nhật ký personal contract` trong file này.
- Kiểm chứng: đối chiếu mặc định `japanese` tại `ui/factory_dialog.py:161` và phạm vi Anki `2.1.50` tại `manifest.json`.
- Quyết định tiếp theo: P0-01; sau đó hoàn tất P0-02 trên profile backup. Nếu chi phí thực tế vượt `$10/tháng`, dừng benchmark mới và cập nhật contract.

### 2026-08-16 — Personal / P1-01

- Trạng thái: `Hoàn thành`.
- Lý do mở task: cần chọn model/prompt mặc định cho flow AI extract → preview/import theo chất lượng, cost và latency đo được; chủ dự án không thao tác benchmark thủ công.
- Model / effort đã dùng: `gpt-5.6-sol` / `high`.
- Phạm vi: `benchmarks/`, `scripts/benchmark_ai_models.py`, `utils/ai_benchmark.py`, `tests/test_ai_benchmark.py`.
- Kiểm chứng: 3 cấu hình × 20 mục tại `benchmarks/runs/`; cả ba đạt coverage/factory-ready/meaning/example `100%`. Flash non-thinking: `$0.001129`, `21.0152s`; Flash thinking: `$0.003266`, `74.2481s`; Pro non-thinking: `$0.003507`, `30.2951s`. `py_compile` xanh; isolated pytest AI liên quan `70 passed` trước benchmark.
- Quyết định tiếp theo: chọn `deepseek-v4-flash` non-thinking làm mặc định cho flow từ vựng Nhật. Ngưỡng chấp nhận: coverage/factory-ready `≥95%`, nghĩa/ví dụ `≥90%`, cost/card `≤$0.000200`, latency/card `≤4.00s`. Chưa mở P1-02 vì prompt hiện tại đạt đủ; chỉ benchmark lại khi thẻ đã học cho thấy lỗi lặp lại.

### 2026-08-16 — Personal / P1-02 (CJK quality round 1)

- Trạng thái: `Hoàn thành` theo yêu cầu mở rộng chủ động sang cả Nhật / Trung / Hàn.
- Lý do mở task: cần tăng độ tin cậy nghĩa, bản dịch ví dụ và cách đọc trước khi đưa thẻ CJK vào review.
- Model / effort đã dùng: `gpt-5.6-sol` / `high`.
- Phạm vi: `utils/prompts/`, `utils/import_quality.py`, `utils/ai_output_repairs.py`, `benchmarks/`.
- Kiểm chứng: corpus cố định 20 mục cho mỗi ngôn ngữ; mỗi run đạt coverage/factory-ready/meaning/example `100%`, chi tiết tại `benchmarks/CJK_QUALITY.md`; regression `89 passed` cho prompt, parser/batch, repair và validator.
- Quyết định tiếp theo: giữ prompt/schema hiện tại; chỉ mở vòng mới khi review thẻ thật xuất hiện lỗi lặp lại hoặc benchmark CJK tụt dưới ngưỡng P1-01.

### 2026-08-16 — Personal / P1-03 (English quality round 1)

- Trạng thái: `Hoàn thành` theo yêu cầu mở rộng sang tiếng Anh của chủ dự án.
- Lý do mở task: tiếng Anh có prompt nhưng chưa có corpus chất lượng và review output thật tương đương CJK.
- Model / effort đã dùng: `gpt-5.6-sol` / `high`.
- Phạm vi: `utils/prompts/english.py`, `utils/batch_processor.py`, `utils/import_quality.py`, `benchmarks/`.
- Kiểm chứng: corpus cố định 20 mục có nghĩa đích; run `deepseek-v4-flash` non-thinking đạt coverage/factory-ready/meaning/example `100%`, `$0.000048/card`, `0.77s/card`, chi tiết tại `benchmarks/ENGLISH_QUALITY.md`; regression `123 passed` cho prompt, cache, batch, benchmark và validator.
- Quyết định tiếp theo: giữ V4 Flash non-thinking và quality gate tiếng Anh; chỉ mở vòng mới nếu review thẻ thật phát hiện lỗi nghĩa/ví dụ lặp lại hoặc benchmark tụt dưới ngưỡng P1-01.

### 2026-08-16 — Personal / P1-04 (AwesomeTTS safe batch plan)

- Trạng thái: `Đã lên kế hoạch`; chưa sửa mã nguồn và chưa tuyên bố hỗ trợ runtime.
- Lý do mở task: chủ dự án chấp nhận đánh đổi tốc độ lấy giọng/preset quen thuộc và cần tạo audio hàng loạt mà không gây giới hạn dịch vụ hoặc làm hỏng media.
- Model / effort đã dùng: `gpt-5.6-luna` / `low` cho tài liệu; model triển khai được phân lát trong `P1-04_AWESOMETTS_SAFE_BATCH.md`.
- Phạm vi: quyết định stored-media, adapter optional, policy concurrency/retry/cooldown, resume và UI; không thêm provider cloud/API key mới.
- Kiểm chứng: đối chiếu AwesomeTTS cài cục bộ có router callback và Bento hiện dùng worker audio; chưa chạy test vì chưa có thay đổi mã.
- Quyết định tiếp theo: mở đúng P0-04 trước; sau đó thực hiện lần lượt P1-04-A đến P1-04-E, một lát cắt mỗi phiên.

### 2026-08-16 — Personal / V18 Learning Modes

- Trạng thái: `Đã lên kế hoạch`; đây là hướng phát triển mới sau khi chủ dự án xác nhận các P0/P1 trước đã hoàn thành.
- Lý do mở task: Bento Forge phục vụ cả học ngoại ngữ lẫn kiến thức chuyên ngành, nhưng cần tách contract/model để không làm hỏng collection Language hiện hữu.
- Model / effort: `gpt-5.6-terra` / `high` cho contract/UI/release; `gpt-5.6-sol` / `high` cho schema, model lifecycle và workflow đa boundary. Chi tiết ở `V18_LEARNING_MODES.md`.
- Phạm vi: `language` giữ vocab/grammar; `knowledge` V1 hỗ trợ Basic, Cloze, Explanation, Source và Tags; AwesomeTTS không thuộc scope V18 mặc định.
- Kiểm chứng kế hoạch: đã map state `vocab/grammar`, config note type, UI selector, extract/preview/import/history và release boundary vào skill `13-learning-modes`.
- Quyết định tiếp theo: chỉ mở V18-01. Metadata version vẫn giữ nguyên cho đến V18-06 có test/smoke và release record.
