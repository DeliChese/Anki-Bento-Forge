# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-08-29
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
| P0-04 release artifact | đã kiểm chứng local | Builder allowlist runtime; artifact `18.3.0` có 104 entries/101 Python files/5 worker files, không cache/state local, clean-profile compile và SHA-256/SBOM xanh. Cài GUI trên profile sạch vẫn thuộc owner smoke. |
| P0-05 AI Output Reliability | local implementation xanh | Chat/Card Mode dùng reliability contract hiện hành; còn smoke restart/profile backup và manual large-batch metrics trước khi publish 18.1. |
| P1-07 AI Study Sessions | menu/context smoke pass, card action blocked | Study Coach mở từ menu, nhận đúng `REVIEWER · QA · Mặt câu hỏi · Thẻ chính: 看`, quick actions/library hiện đủ và ngoài Reviewer fail-closed; `Hỏi AI` trên card vắng mặt. Còn fix/restart/concurrency/mục 42 và CI. |
| V18.2 Contextual AI Workspaces | local implementation xanh | Reviewer sở hữu riêng AI Study Sessions/learning loop; Factory tích hợp Forge theo workbench Blueprint responsive `Source | AI/Artifact | Review/Import`, với composer gồm ô nhập + checkbox Tạo thẻ theo Vocab/Grammar phía trên + nút Gửi. Router/bước xử lý không còn lộ ra; không còn standalone surface hoặc banner quy trình đánh số. Model history + rolling summary vẫn tách theo workspace; candidate bám source, do người dùng chọn và deck match chỉ advisory. Còn GUI smoke Reviewer + Factory trên profile backup và CI trước merge/release. |
| V18.3 Language Study Library | guard sắc thái + UI local, chờ re-smoke | Scope mục 42 đúng; prompt/context đặt ý định người học lên trước, cấm suy diễn sắc thái/độ trang trọng giữa biến thể ngữ pháp khi excerpt không đối chiếu và coi history mâu thuẫn là obsolete. Chat dock ưu tiên transcript, toàn bộ chức năng học luôn hiện diện và có chỉ báo AI đang soạn. Isolated `805 passed` ×2. Chưa khép cho tới khi owner re-smoke mục 42 + UI trên thẻ vocabulary/grammar. |
| P1-08 AI Deck Blueprint | local implementation xanh, chờ GUI smoke | Một nút Deck Center trong Forge sở hữu quản lý deck + AI Blueprint; không còn action Blueprint rời ở Tools. Blueprint nhận snapshot nguồn học liệu đã dán/file đã nạp cùng ngôn ngữ hiện tại nên không phải nhập lại. Parser H1–H6/source path/cây editable đã có; import nhiều deck validate + scan trùng toàn note type, chỉ add, final re-check và exact-ID undo. Audio/update note cũ vẫn tắt. Source-transfer gate `97 passed`, full isolated `831 passed`; còn GUI smoke profile backup. |
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | local implementation xanh | Exact curated same-deck warning đã có fixtures bốn ngôn ngữ; chờ smoke profile backup, vẫn chỉ advisory và không tự sửa note/SRS. |
| P2-03 Production Drill | GUI smoke fail | Anki 26.5 không hiện `Tự đặt câu` trên card `看` dù có Usage Pattern/Collocation; local suite vẫn `805 passed` ×2. Cần sửa hook injection rồi re-smoke bốn ngôn ngữ; không note/SRS mutation trong phiên phát hiện. |

## Evidence and boundaries

- Bằng chứng V18.3 hiện tại: transcript profile thật xác nhận manifest đúng mục `42. Thái tiến hành: 在, 正在, 正, 呢`; guard mới cấm biến việc liệt kê dạng thành quy tắc sắc thái tuyệt đối. Renderer có fixture heading/list/code/quote/bảng hẹp/rộng; dock có transcript ưu tiên, các chức năng học luôn hiện diện và typing indicator. Hai isolated suites `805 passed`. Đây là bằng chứng local, không thay thế re-smoke Anki thật đang mở. Chi tiết và điều kiện phát hành hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
