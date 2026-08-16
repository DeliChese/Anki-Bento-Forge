# Personal Roadmap — Bento Forge

> **Quyết định sản phẩm:** 2026-08-16 — Bento Forge được duy trì như add-on cá nhân. Không có mục tiêu cạnh tranh thị trường, mở rộng đại trà hay xây cộng đồng.
> **Mục tiêu:** Giảm thời gian tạo thẻ và tăng chất lượng học cho workflow của chủ dự án, tập trung đồng thời vào Nhật / Trung / Hàn / Anh — bốn ngôn ngữ chủ dự án đang học.
> **Nguồn ưu tiên:** File này là nguồn quyết định cho backlog đang hoạt động. Các Phase A–F giữ lại lịch sử và chuyên môn, nhưng chỉ được thực hiện khi một item bên dưới tham chiếu tới.

## Dashboard hiện tại — đọc phần này trước

| Việc | Trạng thái | Điều cần biết ngay |
| --- | --- | --- |
| P0-01 — baseline test | 🟢 Local xanh | Compile toàn bộ Python tracked và hai vòng isolated suite đều xanh `547 passed`; vẫn cần giữ gate này xanh trước merge/release. |
| P0-02 — smoke profile | ⏳ Chờ chủ dự án | Cần chạy toàn flow trực quan trên profile Anki backup trước merge/release; không chặn việc mở P1-06. |
| P1-05 — Usage Guide V1 | ✅ Đã kiểm chứng | Benchmark model thật đạt `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; smoke collection thật Anki 26.5 xanh đủ bốn ngôn ngữ. |
| P1-06 — Confusion Guard | 🟢 Đủ điều kiện mở | P1-05 đã đạt benchmark; review/prompt tuning đã ghi nhận các boundary dễ lẫn ở cả bốn ngôn ngữ. Chưa bắt đầu triển khai P1-06. |
| Knowledge beta | 🧊 Dormant | Ẩn UI, không nằm trong release plan. |

**Cách đọc trạng thái:** `🔴` cần xử lý · `🟢` local gate xanh/đủ điều kiện mở · `🟡` đang làm/chờ kiểm chứng · `✅` đã kiểm chứng · `⏳` cần thao tác của chủ dự án · `⚪` chưa mở · `🧊` đóng băng.

**Quy tắc khi AI làm trước thứ tự:** được phép. Không đánh dấu hoàn thành theo lời bàn giao đơn lẻ; chỉ chuyển P1-05 sang `✓ Đã kiểm chứng` khi có diff rõ ràng, test liên quan và benchmark bốn ngôn ngữ. P0-01/P0-02 là gate trước merge/release, không bắt buộc ngăn AI chuẩn bị P1-05.

## Phạm vi vận hành

### Làm

- Độ tin cậy của các flow dùng hằng tuần: AI extract, preview/chỉnh sửa, import/update, TTS và review template.
- Sao lưu/undo trước các thao tác có thể làm thay đổi collection.
- Benchmark nhỏ để chọn model, prompt và cấu hình rẻ nhưng đủ tốt cho chính người dùng.
- Tinh chỉnh Usage Guide chung cho cả bốn ngôn ngữ, nhưng rubric, cấu trúc và corpus vẫn phải đặc thù từng ngôn ngữ.

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
| P0-03 | Thiết lập “personal contract”: bốn ngôn ngữ đang học, phiên bản Anki đang dùng, 2–3 flow hằng tuần và giới hạn chi phí tháng | P0 — định hướng | 🟢 Dễ | Chủ dự án; `gpt-5.6-luna` / `low` để ghi tài liệu | 20 phút | Ghi tại mục nhật ký bên dưới; mọi task mới liên hệ được với một flow |
| P0-04 | Kiểm chứng artifact phát hành: build phải đóng gói `workers/`, không kèm Python cache và có regression test nội dung gói | P0 — chặn feature/release hỏng | 🟡 Trung bình | `gpt-5.6-terra` / `medium` | 1–3 giờ | Artifact clean-profile có đủ runtime modules, không có `__pycache__`/`.pyc`; test build xanh |
| P1-01 | Chạy benchmark model/prompt cho ngôn ngữ chính; chấm thủ công nghĩa, ví dụ, lỗi cấu trúc, cost và latency | P1 — trước tối ưu AI | 🟠 Khó | `gpt-5.6-sol` / `high` | 4–8 giờ | Ít nhất 3 model × 20 mục; có run JSON; chọn default và ngưỡng chấp nhận theo số liệu |
| P1-02 | Tinh chỉnh prompt/schema/template cho ngôn ngữ chính dựa trên benchmark và thẻ đã học | P1 — khi P1-01 có dữ liệu | 🟠 Khó | `gpt-5.6-sol` / `high` | 3–8 giờ mỗi vòng | So sánh trước/sau trên cùng corpus; không giảm điểm benchmark; prompt version/cache được xử lý đúng |
| P1-03 | Rà soát backup, rollback, duplicate/update và giới hạn batch cho collection cá nhân | P1 — giảm rủi ro | 🟡 Trung bình | `gpt-5.6-terra` / `high` | 2–5 giờ | Có test và thao tác phục hồi đã được thử trên profile bản sao |
| P1-05 | **Usage Guide V1 — Nhật/Trung/Hàn/Anh**: sinh có chọn lọc `Usage Pattern`, `Usage Note` và tối đa 1 collocation có nghĩa; pattern/register/cảnh báo dùng sai riêng theo từng ngôn ngữ; hiển thị mặt sau, không tạo thêm card mặc định | P1 — tính năng học kế tiếp | 🔴 Rất khó | `gpt-5.6-sol` / `high` | 12–20 giờ | Corpus review cho cả 4 ngôn ngữ; pattern/usage đúng ≥90%, không sinh nội dung rỗng hoặc lặp ví dụ; migration field/template idempotent; không giảm benchmark/cost vượt ngưỡng đã chốt |
| P1-06 | **Confusion Guard — Nhật/Trung/Hàn/Anh**: trước import, dò candidate dễ lẫn trong cùng deck và chỉ cảnh báo/đề xuất phân biệt có evidence; không tự merge hay tạo thẻ phụ | P1 — sau Usage Guide | 🟠 Khó | `gpt-5.6-sol` / `high` | 8–14 giờ | Fixture mỗi ngôn ngữ có positive/negative pairs; không báo trùng sai hàng loạt; preview cho sửa/bỏ; không đổi dữ liệu hoặc lịch SRS cũ |
| P1-04 | Tích hợp AwesomeTTS tùy chọn theo stored-media và batch an toàn, chấp nhận tốc độ chậm để ổn định | P1 — nâng trải nghiệm TTS | 🟠 Khó | Theo lát cắt trong `P1-04_AWESOMETTS_SAFE_BATCH.md` (`terra`/`sol`) | 8–16 giờ | Đạt checklist provider thiếu/có, media local, retry/cancel/resume và smoke trên profile backup |
| Knowledge beta | Giữ code/schema/model Knowledge riêng tư nhưng tắt UI; không phát hành V18 và không mở feature mới | Đóng băng | — | — | — | Chỉ mở lại khi chủ dự án yêu cầu, rồi khôi phục smoke/CI riêng |
| P2-01 | Đơn giản hóa/ẩn các flow không dùng để giảm nhiễu UI và chi phí bảo trì | P2 — chỉ khi gây ma sát | 🟡 Trung bình | `gpt-5.6-terra` / `medium` | 1–4 giờ | Flow còn lại không regression; quyết định được ghi vào nhật ký |
| P2-02 | Bổ sung hoặc nâng một ngôn ngữ khác khi chính chủ dự án dùng đều | P2 — theo nhu cầu | 🟠 Khó | `gpt-5.6-sol` / `high` | 8–20 giờ | Corpus riêng, TTS, template và smoke test cho đúng ngôn ngữ đó |
| P2-03 | **Production Prompt — Nhật/Trung/Hàn/Anh**: nút luyện sản sinh tùy chọn trong reviewer, dùng Usage Pattern/Collocation của thẻ để gợi ý người học tự đặt câu; không chấm AI hoặc tạo card/lịch mới ở V1 | P2 — sau khi Usage Guide được dùng thực tế | 🟠 Khó | `gpt-5.6-terra` / `high` | 6–10 giờ | Hoạt động độc lập trên template 4 ngôn ngữ; graceful fallback Anki cũ; không làm lộ đáp án trước khi người học chọn xem |
| P2-04 | **Review Health — read-only**: báo cáo thẻ khó/leech, nhóm lỗi và đề xuất hành động (sửa Usage Guide, suspend, học lại); tuyệt đối không tự đổi lịch SRS | P2 — khi review lặp lại cho thấy vấn đề | 🟡 Trung bình | `gpt-5.6-terra` / `high` | 5–9 giờ | Đọc collection qua Anki operation an toàn; số liệu đối chiếu được Anki Browser; không mutation nếu không có xác nhận rõ ràng |

## Backlog đóng băng

| Nhóm | Trạng thái | Chỉ mở lại khi |
| --- | --- | --- |
| Phase D — mở rộng nhiều ngôn ngữ | Đóng băng | Chủ dự án học ngôn ngữ đó đều và P2-02 được mở |
| Phase E — academic evidence/retention report | Đóng băng | Có câu hỏi học tập cá nhân cụ thể mà Anki Stats không trả lời được |
| Phase F — community/public docs | Đóng băng | Quyết định phát hành công khai trở lại |
| Routing tự động, semantic cache, OCR/video/image AI | Để sau | Có dữ liệu P1-01 hoặc ma sát lặp lại chứng minh lợi ích |
| Big-bang refactor | Không làm | Có lỗi bảo trì cụ thể không thể giải bằng lát cắt nhỏ |

## Trình tự cho sáu phiên làm việc tới

1. Hoàn tất P0-01: xử lý baseline test xanh trước feature mới.
2. Hoàn tất P0-02 trên profile đã backup.
3. Chốt contract và corpus cho P1-05 Usage Guide của cả bốn ngôn ngữ.
4. Triển khai P1-05 theo lát cắt schema/prompt → preview/model/template → benchmark/regression.
5. Chỉ mở P1-06 Confusion Guard nếu Usage Guide đạt rubric và nhu cầu phân biệt từ lặp lại.
6. Chọn P1-04 AwesomeTTS hoặc P2-03 Production Prompt theo ma sát thực tế khi học; Knowledge beta vẫn dormant.

## Nhật ký personal contract

| Ngày | Ngôn ngữ chính | Phiên bản Anki | Flow hằng tuần | Ngân sách AI/tháng | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 2026-08-16 | Nhật / Trung / Hàn / Anh | Anki `26.5` | AI extract → preview/import; update/undo; TTS → review | `$10/tháng` (tạm thời) | Tập trung Language; Usage Guide là feature kế tiếp; Knowledge là beta dormant |

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
- Kiểm chứng: đối chiếu mặc định `japanese` tại `ui/factory_dialog.py:161` và phạm vi Anki `2.1.50` đến `26.5` tại `manifest.json`.
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

### 2026-08-16 — Personal / P1-05 (Usage Guide V1)

- Trạng thái: `Đã kiểm chứng`; đủ điều kiện mở P1-06. Smoke trực quan toàn profile vẫn được theo dõi riêng ở P0-02 trước merge/release.
- Lý do mở task: chủ dự án cần biết cách dùng, cấu trúc, sắc thái và collocation của từ thay vì chỉ nhớ nghĩa; phạm vi được quyết định là Nhật / Trung / Hàn / Anh cùng lúc.
- Model / effort: `gpt-5.6-sol` / `high` cho contract đa ngôn ngữ, prompt/schema/template và benchmark; `gpt-5.6-terra` / `high` cho wiring UI/Anki khi cần.
- Phạm vi: `Usage Pattern`, `Usage Note` và tối đa một collocation có nghĩa; V1 chỉ hiển thị mặt sau, không tạo thêm card hoặc lịch SRS.
- Kiểm chứng: benchmark DeepSeek thật trên 20 mục (5/ngôn ngữ) đạt `19/20` (`95%`), coverage/factory-ready `20/20`, `$0.002035` và `1.69 giây/card`; kết quả chấm có máy kiểm tại `benchmarks/usage_guide_review_v1.json`. Compile toàn bộ Python tracked và hai vòng isolated suite đều xanh `547 passed`. Regression phủ schema/field map, preview, output rỗng/lặp, tối đa một collocation có nghĩa, mặt sau-only và migration idempotent. Smoke collection thật bằng runtime Anki 26.5 xác nhận migration/import/update/native undo/rollback, giữ một card mặc định và không mở profile cá nhân.
- Quyết định tiếp theo: cho phép mở P1-06. P0-02 tiếp tục giữ checklist smoke GUI trên profile backup như gate phát hành chung, không chặn task kế tiếp.

### 2026-08-16 — Personal / P1-06 (Confusion Guard)

- Trạng thái: `Đủ điều kiện mở`, chưa bắt đầu triển khai.
- Model / effort: `gpt-5.6-sol` / `high`.
- Phạm vi: cảnh báo candidate trong cùng deck và giải thích phân biệt có thể sửa trong preview; không auto-merge, sửa note hay đổi SRS.
- Bằng chứng mở task: benchmark/tuning P1-05 đã lặp lại các boundary cần phân biệt như Nhật `聞く/質問する` và `気になる/気にする`, Trung `了解/认识`, Hàn `묻다/질문하다`, Anh `say/tell`; một note Hàn bị loại vì khái quát quá rộng, củng cố yêu cầu P1-06 chỉ advisory.
- Kiểm chứng khi triển khai: fixture positive/negative cho cả bốn ngôn ngữ, benchmark false-positive và smoke import/update/undo.

### 2026-08-16 — Personal / Knowledge beta

- Trạng thái: `Dormant`; code V18 được giữ riêng nhưng selector/UI tắt, không phát hành chính thức.
- Lý do mở task: Bento Forge phục vụ cả học ngoại ngữ lẫn kiến thức chuyên ngành, nhưng cần tách contract/model để không làm hỏng collection Language hiện hữu.
- Model / effort: `gpt-5.6-terra` / `high` cho contract/UI/release; `gpt-5.6-sol` / `high` cho schema, model lifecycle và workflow đa boundary. Chi tiết ở `V18_LEARNING_MODES.md`.
- Phạm vi: `language` giữ vocab/grammar; `knowledge` V1 hỗ trợ Basic, Cloze, Explanation, Source và Tags; AwesomeTTS không thuộc scope V18 mặc định.
- Kiểm chứng: isolated harness sau sửa hành động gửi Knowledge hai vòng `532 passed` mỗi vòng; Anki 26.5/Python 3.13.5 đã đạt packaged manifest, entry/UI/public-hook import và collection thật Basic/Cloze add/update/card generation/rollback; artifact SHA-256 `8e2d0fc60e725a2ffa728c9f9a35199aa833c8f277aef2cd7a21c7f915a65ea0`.
- Quyết định tiếp theo: tập trung Language. Chỉ khi chủ dự án yêu cầu mở beta mới chạy lại `V18_SMOKE_PROFILE.md`, CI và endpoint legacy; không bump `18.0.0` trong trạng thái này.
