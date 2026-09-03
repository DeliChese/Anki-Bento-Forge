# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-09-02
> Read when: every agent session, immediately after `AGENTS.md`

## Operating contract

- Bento Forge là add-on cá nhân, ưu tiên bốn ngôn ngữ Nhật/Trung/Hàn/Anh và các flow: AI extract → preview/import, update/undo, TTS → review.
- Không tự mở rộng public/community, ngôn ngữ mới, OCR/video/image AI, analytics hay big-bang refactor.
- Knowledge beta đang dormant: UI tắt, không phát hành V18 nếu không có yêu cầu rõ ràng từ chủ dự án.

## Active state

| Item | Status | Next action |
|---|---|---|
| P0-01 baseline | local gate xanh | Giữ compile tracked Python và hai vòng isolated suite xanh trước merge/release. |
| P0-02 smoke profile | partial smoke, blocked | Anki 26.5/profile `ChinD` backup: Factory, combo/Usage Guide, Study Coach context và role split pass; Reviewer không inject `Hỏi AI`/`Tự đặt câu` trên card `看`. Không rating/mutation; sửa hook trước khi tiếp tục. |
| P0-04 release artifact | cần dựng lại | Runtime Batch/Inventory/Blueprint đã bị gỡ nên artifact cũ không còn đại diện current tree; cần rebuild trước release. |
| P0-05 AI Output Reliability | local implementation xanh | Luồng nhỏ dùng một request trực tiếp, validate → Preview → Import; còn smoke restart/profile backup trước publish. |
| P1-07 AI Study Sessions | menu/context smoke pass, card action blocked | Study Coach mở từ menu, nhận đúng `REVIEWER · QA · Mặt câu hỏi · Thẻ chính: 看`, quick actions/library hiện đủ và ngoài Reviewer fail-closed; `Hỏi AI` trên card vắng mặt. Còn fix/restart/concurrency/mục 42 và CI. |
| V18.2 Contextual AI Workspaces | Factory đã thu gọn | Reviewer vẫn sở hữu Study Coach; Factory không còn nhúng Forge chat/artifact station. Production chỉ còn nguồn nhỏ + yêu cầu tùy chọn + một nút tạo tối đa 5 thẻ → Preview → Import. |
| V18.3 Language Study Library | guard sắc thái + UI local, chờ re-smoke | Scope mục 42 đúng; prompt/context đặt ý định người học lên trước, cấm suy diễn sắc thái/độ trang trọng giữa biến thể ngữ pháp khi excerpt không đối chiếu và coi history mâu thuẫn là obsolete. Chat dock ưu tiên transcript, toàn bộ chức năng học luôn hiện diện và có chỉ báo AI đang soạn. Isolated `805 passed` ×2. Chưa khép cho tới khi owner re-smoke mục 42 + UI trên thẻ vocabulary/grammar. |
| Language Collocation subtype | local implementation xanh, chờ GUI smoke | Nhật/Trung/Hàn/Anh có lựa chọn Collocation/Thành ngữ chủ động, prompt/schema/candidate/artifact/history và Note Type riêng; hai hướng Nhận diện/Sản xuất, không migrate note/SRS vocab hoặc grammar. Batch danh sách thiếu ngữ cảnh bị chặn. Isolated `838 passed` ×2; còn smoke chọn mode → AI Preview → import → review trên profile backup. |
| Supervised AI Inventory | retired 2026-09-01 | Đã xóa scanner, topic-first gate, checkpoint và UI sản xuất quy mô lớn. XLSX fallback chuẩn vẫn được giữ cho thao tác mở file nhỏ. |
| P1-08 AI Deck Blueprint | retired 2026-09-01 | Đã xóa AI Blueprint/import nhiều deck; Deck Manager cơ bản tạo/đổi tên/xóa deck vẫn giữ nguyên. |
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | local implementation xanh | Exact curated same-deck warning đã có fixtures bốn ngôn ngữ; chờ smoke profile backup, vẫn chỉ advisory và không tự sửa note/SRS. |
| P2-03 Production Drill | GUI smoke fail | Anki 26.5 không hiện `Tự đặt câu` trên card `看` dù có Usage Pattern/Collocation; local suite vẫn `805 passed` ×2. Cần sửa hook injection rồi re-smoke bốn ngôn ngữ; không note/SRS mutation trong phiên phát hiện. |

## Evidence and boundaries

- Factory production hiện là một lượt trực tiếp, tối đa 4.000 ký tự nguồn và 5 thẻ; không gọi Inventory Scanner, không chunk/batch và luôn đi qua AI Preview trước JSON/import. Dữ liệu thẻ/SRS hiện hữu không bị migration hay mutation bởi thay đổi này. Full isolated suite sau khi gỡ feature: `730 passed, 28 skipped` (toàn bộ skip là regression cũ của Batch đã retired).

- Bằng chứng V18.3 hiện tại: transcript profile thật xác nhận manifest đúng mục `42. Thái tiến hành: 在, 正在, 正, 呢`; guard mới cấm biến việc liệt kê dạng thành quy tắc sắc thái tuyệt đối. Renderer có fixture heading/list/code/quote/bảng hẹp/rộng; dock có transcript ưu tiên, các chức năng học luôn hiện diện và typing indicator. Hai isolated suites `805 passed`. Đây là bằng chứng local, không thay thế re-smoke Anki thật đang mở. Chi tiết và điều kiện phát hành hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
