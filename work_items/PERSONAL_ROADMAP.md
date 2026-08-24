Exit code: 0
Wall time: 0.5 seconds
Output:
# Personal Roadmap — Bento Forge

> Status: active
> Authority: canonical backlog and current product decisions
> Last verified: 2026-08-24
> Read when: choosing, scoping or closing work

> **Quyết định sản phẩm:** 2026-08-16 — Bento Forge được duy trì như add-on cá nhân. Không có mục tiêu cạnh tranh thị trường, mở rộng đại trà hay xây cộng đồng.
> **Mục tiêu:** Giảm thời gian tạo thẻ và tăng chất lượng học cho workflow của chủ dự án, tập trung đồng thời vào Nhật / Trung / Hàn / Anh — bốn ngôn ngữ chủ dự án đang học.
> **Nguồn ưu tiên:** File này là nguồn quyết định cho backlog đang hoạt động. Các Phase A–F giữ lại lịch sử và chuyên môn, nhưng chỉ được thực hiện khi một item bên dưới tham chiếu tới.

## Dashboard hiện tại — đọc phần này trước

| Việc | Trạng thái | Điều cần biết ngay |
| --- | --- | --- |
| P0-01 — baseline test | 🟢 Local xanh | Isolated suite gần nhất xanh `791 passed` sau V18.3 Study Library; vòng xanh liền trước `791 passed`. Vẫn cần giữ gate này xanh trước merge/release. |
| P0-02 — smoke profile | ⏳ Chờ chủ dự án | Cần chạy toàn flow trực quan trên profile Anki backup trước merge/release; không chặn việc mở P1-06. |
| P0-05 — AI Output Reliability | 🟡 Local implementation xanh | Batch/Card Mode vocab+grammar dùng chung parser/schema gate; AI config/history dùng profile path động. Chủ dự án báo card output ổn định; còn smoke restart/profile backup và manual large-batch metrics trước khi publish 18.1. |
| P1-07 — AI Study Sessions | 🟡 Local implementation xanh | Companion dock/floating, context an toàn và learning checkpoint cục bộ theo card + study mode; Study Coach không có Card Mode và không sửa SRS. Còn GUI smoke Anki/profile restart và CI. |
| V18.2 — Contextual AI Workspaces | 🟡 Local implementation xanh | Reviewer giữ AI Study Sessions/learning loop; Factory dùng workbench Blueprint responsive `Source | AI/Artifact | Review/Import`, composer thật gồm input + checkbox Tạo thẻ theo Vocab/Grammar + Gửi và fallback xếp Review xuống dưới ở cửa sổ hẹp. Không còn router/bước xử lý lộ ra, standalone Forge dialog hoặc banner quy trình đánh số; model memory vẫn tách theo workspace. Còn GUI smoke Anki/profile restart và CI. |
| V18.3 — Language Study Library | 🟡 Local implementation xanh | Study Pack thuộc profile + ngôn ngữ, dùng lại qua mọi Reviewer session; ingest/index/quota/delete, Scope Manifest bounded, chọn nguồn mơ hồ, link nội bộ opt-in và Card Drill nháp đã có. `178` targeted và hai vòng full isolated `791 passed`; còn CI + GUI smoke Reviewer trên profile backup. |
| P1-05 — Usage Guide V1 | ✅ Đã kiểm chứng | Benchmark model thật đạt `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; smoke collection thật Anki 26.5 xanh đủ bốn ngôn ngữ. |
| P1-06 — Confusion Guard | 🟡 Local implementation xanh | Exact curated same-deck pairs + advisory preview đã có positive/negative fixtures bốn ngôn ngữ; còn smoke trên profile backup trước khi đánh dấu verified. |
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
| P0-03 | Thiết lập “personal contract”: bốn ngôn ngữ đang học, phiên bản Anki đang dùng, 2–3 flow hằng tuần và giới hạn chi phí tháng | P0 — định hướng | 🟢 Dễ | Chủ dự án; `gpt-5.6-luna` / `low` để ghi tài liệu | 20 phút | Ghi trong snapshot/history; mọi task mới liên hệ được với một flow |
| P0-04 | Kiểm chứng artifact phát hành: build phải đóng gói `workers/`, không kèm Python cache và có regression test nội dung gói | P0 — chặn feature/release hỏng | 🟡 Trung bình | `gpt-5.6-terra` / `medium` | 1–3 giờ | Artifact clean-profile có đủ runtime modules, không có `__pycache__`/`.pyc`; test build xanh |
| P0-05 | **AI Output Reliability**: adapter provider-neutral, safe JSON recovery, language/mode validation, completeness reconciliation, partial retry và adaptive Quality V2 batching | P0 — release gate 18.1.0 | 🔴 Rất khó | `gpt-5.6-sol` / `high` | 8–16 giờ | Parser/schema/partial/adaptive tests và full isolated suite xanh; valid partial result không mất; không semantic repair; smoke profile backup + manual large batch được xác nhận |
| P1-01 | Chạy benchmark model/prompt cho ngôn ngữ chính; chấm thủ công nghĩa, ví dụ, lỗi cấu trúc, cost và latency | P1 — trước tối ưu AI | 🟠 Khó | `gpt-5.6-sol` / `high` | 4–8 giờ | Ít nhất 3 model × 20 mục; có run JSON; chọn default và ngưỡng chấp nhận theo số liệu |
| P1-02 | Tinh chỉnh prompt/schema/template cho ngôn ngữ chính dựa trên benchmark và thẻ đã học | P1 — khi P1-01 có dữ liệu | 🟠 Khó | `gpt-5.6-sol` / `high` | 3–8 giờ mỗi vòng | So sánh trước/sau trên cùng corpus; không giảm điểm benchmark; prompt version/cache được xử lý đúng |
| P1-03 | Rà soát backup, rollback, duplicate/update và giới hạn batch cho collection cá nhân | P1 — giảm rủi ro | 🟡 Trung bình | `gpt-5.6-terra` / `high` | 2–5 giờ | Có test và thao tác phục hồi đã được thử trên profile bản sao |
| P1-05 | **Usage Guide V1 — Nhật/Trung/Hàn/Anh**: sinh có chọn lọc `Usage Pattern`, `Usage Note` và tối đa 1 collocation có nghĩa; pattern/register/cảnh báo dùng sai riêng theo từng ngôn ngữ; hiển thị mặt sau, không tạo thêm card mặc định | P1 — đã kiểm chứng, là quality gate | 🔴 Rất khó | `gpt-5.6-sol` / `high` | 12–20 giờ | Corpus review cho cả 4 ngôn ngữ; pattern/usage đúng ≥90%, không sinh nội dung rỗng hoặc lặp ví dụ; migration field/template idempotent; không giảm benchmark/cost vượt ngưỡng đã chốt |
| P1-06 | **Confusion Guard — Nhật/Trung/Hàn/Anh**: trước import, dò candidate dễ lẫn trong cùng deck và chỉ cảnh báo/đề xuất phân biệt có evidence; không tự merge hay tạo thẻ phụ | P1 — local code/fixtures xanh, chờ smoke | 🟠 Khó | `gpt-5.6-sol` / `high` | 8–14 giờ | Fixture mỗi ngôn ngữ có positive/negative pairs; không báo trùng sai hàng loạt; preview cho sửa/bỏ; không đổi dữ liệu hoặc lịch SRS cũ |
| P1-07 | **AI Study Sessions — Dockable Study Coach**: phiên chat cục bộ, context thẻ hiện tại opt-in, quick prompts và checkpoint `understood/needs_practice` theo card + study mode | P1 — local code xanh, chờ smoke | 🔴 Rất khó | `gpt-5.6-sol` / `high` | 12–20 giờ | Checkpoint persistence + prompt exclusion + full suite xanh; micro-quiz không auto-send; không Card Mode/collection scan/SRS mutation; GUI smoke restart/dock/floating/concurrency trên profile backup |
| V18.2 | **Contextual AI Workspaces + Integrated Production Line**: Reviewer sở hữu learning loop; Factory là owner UI duy nhất của source production, candidate manifest, tùy chọn Tạo thẻ theo Vocab/Grammar, artifact và review/import; model memory tách theo workspace | P1 — local code xanh, chờ smoke | 🔴 Rất khó | `gpt-5.6-sol` / `high` | Reviewer checkpoint zero-AI/SRS; manifest bám source và fail-closed; chỉ candidate chọn thủ công đi vào Card Mode; current-deck match chỉ advisory qua QueryOp; history/summary không rò hai chiều; artifact → review/import zero-AI; không standalone Forge dialog; full suite + GUI smoke profile backup |
| V18.3 | **Language Study Library + Semantic Scope + Card Drill**: pack tài liệu thuộc profile + ngôn ngữ, tái dùng qua Reviewer session; prompt linh hoạt → Scope Manifest → catalog/chunk local, link nội bộ chỉ theo opt-in, giải thích/ví dụ theo source và bài tập ngắn nháp từ thẻ hiện tại | P2 — local code xanh, chờ smoke | 🔴 Rất khó | `gpt-5.6-sol` / `high` | Local: format/quota/delete + UX link opt-in, same-language bounded manifest/provenance, Forge/session/cache separation, zero SRS/collection mutation và fixture 4 ngôn ngữ đều xanh. Còn CI + GUI smoke Reviewer trên profile backup trước verification/release. |
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

1. Giữ P0-01 xanh: tái xác nhận baseline trước merge/release và trước feature lớn.
2. Hoàn tất P0-02 trên profile đã backup trước merge/release.
3. Smoke P1-06 Confusion Guard trên profile backup; chỉ đánh dấu verified sau khi xác nhận preview advisory và import không bị chặn/mutate ngoài flow.
4. Hoàn tất P0-04 trước mọi lát cắt AwesomeTTS.
5. Chỉ mở P1-04 AwesomeTTS khi P0-04 xanh và ma sát TTS còn lặp lại.
6. Smoke V18.3 Study Library trong Reviewer trên profile backup; chỉ chuyển verified sau khi attach/toggle/delete/restart/scope ambiguity đều đạt. Knowledge beta vẫn dormant.

## Nhật ký personal contract

| Ngày | Ngôn ngữ chính | Phiên bản Anki | Flow hằng tuần | Ngân sách AI/tháng | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 2026-08-16 | Nhật / Trung / Hàn / Anh | Anki `26.5` | AI extract → preview/import; update/undo; TTS → review | `$10/tháng` (tạm thời) | Tập trung Language; Usage Guide là feature kế tiếp; Knowledge là beta dormant |

## Task records and handoff

- Historical decision and verification records: [history/2026-08.md](history/2026-08.md). They are evidence, not current authority.
- P0-02 remains owner-operated: use [P0-02 smoke checklist](P0-02_ANKI_SMOKE_CHECKLIST.md) on a backed-up Anki profile before release.
- P1-04 is planned only: execute its slices only after P0-04, following [AwesomeTTS safe-batch plan](P1-04_AWESOMETTS_SAFE_BATCH.md).
- P1-06 has a locally tested exact-pair advisory slice; preserve its boundary and run owner smoke before verification.
- Knowledge beta remains dormant; its reactivation procedure is in [V18 learning modes](V18_LEARNING_MODES.md).

For every medium or hard task, create or update a handoff using [the task contract template](../.claude/context/task-contract-template.md).
