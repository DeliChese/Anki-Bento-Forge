# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-08-24
> Read when: every agent session, immediately after `AGENTS.md`

## Operating contract

- Bento Forge là add-on cá nhân, ưu tiên bốn ngôn ngữ Nhật/Trung/Hàn/Anh và các flow: AI extract → preview/import, update/undo, TTS → review.
- Không tự mở rộng public/community, ngôn ngữ mới, OCR/video/image AI, analytics hay big-bang refactor.
- Knowledge beta đang dormant: UI tắt, không phát hành V18 nếu không có yêu cầu rõ ràng từ chủ dự án.

## Active state

| Item | Status | Next action |
|---|---|---|
| P0-01 baseline | local gate xanh | Giữ compile tracked Python và hai vòng isolated suite xanh trước merge/release. |
| P0-02 smoke profile | chờ chủ dự án | Chạy checklist trên profile Anki đã backup trước merge/release. |
| P0-05 AI Output Reliability | local implementation xanh | Chat/Card Mode dùng reliability contract hiện hành; còn smoke restart/profile backup và manual large-batch metrics trước khi publish 18.1. |
| P1-07 AI Study Sessions | local implementation xanh | Study Coach có session/context thẻ và checkpoint cục bộ `understood/needs_practice` theo card + study mode; không có Card Mode và không sửa SRS. Còn GUI smoke Anki trên profile backup và CI trước phát hành. |
| V18.2 Contextual AI Workspaces | local implementation xanh | Reviewer sở hữu riêng AI Study Sessions/learning loop; Factory tích hợp Forge theo workbench Blueprint responsive `Source | AI/Artifact | Review/Import`, với composer gồm ô nhập + checkbox Tạo thẻ theo Vocab/Grammar phía trên + nút Gửi. Router/bước xử lý không còn lộ ra; không còn standalone surface hoặc banner quy trình đánh số. Model history + rolling summary vẫn tách theo workspace; candidate bám source, do người dùng chọn và deck match chỉ advisory. Còn GUI smoke Reviewer + Factory trên profile backup và CI trước merge/release. |
| V18.3 Language Study Library | local implementation xanh | Reviewer có Study Pack theo profile + canonical language, ingest/index/quota/delete atomic, retrieval paraphrase bốn ngôn ngữ, Scope Manifest bounded, chọn nguồn mơ hồ và link Markdown nội bộ opt-in. Card Drill chỉ soạn draft; library không vào Forge/session cache/SRS. Còn GUI smoke attach/toggle/delete/restart/ambiguity trên profile backup và CI. |
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | local implementation xanh | Exact curated same-deck warning đã có fixtures bốn ngôn ngữ; chờ smoke profile backup, vẫn chỉ advisory và không tự sửa note/SRS. |

## Evidence and boundaries

- Bằng chứng baseline gần nhất: hai vòng isolated suite `791 passed` sau V18.3 Study Library; targeted library/session/workspace/coaching/output/extractor/token `178 passed`. Trước đó isolated suite `774 passed` sau Blueprint responsive polish. Chi tiết và điều kiện phát hành hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
