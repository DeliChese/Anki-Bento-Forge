# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-08-16  
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
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | đủ điều kiện mở | Chưa triển khai; chỉ advisory, không tự sửa note hay SRS. |

## Evidence and boundaries

- Bằng chứng baseline gần nhất: `547 passed` trong hai vòng isolated suite; chi tiết và điều kiện hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
