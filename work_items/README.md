# Bento Forge — Work Items Index

> Status: active
> Authority: supporting index; `PERSONAL_ROADMAP.md` is canonical
> Last verified: 2026-09-08
> Read when: cần tìm backlog, checklist hoặc hồ sơ lịch sử

## Nguồn hiện hành

| Tài liệu | Vai trò |
| --- | --- |
| [Personal Roadmap](PERSONAL_ROADMAP.md) | Backlog, quyết định sản phẩm và trạng thái hiện hành duy nhất. |
| [P0-02 Anki Smoke](P0-02_ANKI_SMOKE_CHECKLIST.md) | Checklist thao tác trên profile backup; cần đồng bộ với `RELEASE_CHECKLIST.md`. |
| [AI Output Reliability](P0-05_AI_OUTPUT_RELIABILITY.md) | Contract/evidence của parser, schema và Quality V2; chi tiết Batch cũ chỉ là lịch sử. |
| [Language Card Quality V2](LANGUAGE_CARD_QUALITY_V2.md) | Contract chất lượng và Confusion Guard đang được dùng. |
| [AwesomeTTS Safe Batch](P1-04_AWESOMETTS_SAFE_BATCH.md) | Kế hoạch chưa triển khai; chỉ mở khi roadmap cho phép. |
| [Knowledge reactivation](V18_LEARNING_MODES.md) | Kế hoạch khôi phục beta dormant; không phải release gate hiện tại. |

Mọi tài liệu khác trong thư mục này là supporting, frozen, dormant hoặc historical. Không dùng trạng thái/test count trong chúng để ghi đè roadmap hay `.claude/context/current-state.md`.

## Hồ sơ không còn là backlog

| Nhóm | Trạng thái hiện tại |
| --- | --- |
| `PHASE_A_*` đến `PHASE_F_*` | Frozen historical plans. Chỉ đọc khi một item hiện hành liên kết trực tiếp. |
| `AI_DECK_BLUEPRINT.md` | Retired 2026-09-01; implementation surface đã gỡ. |
| `V18_SMOKE_PROFILE.md` | Dormant; chỉ dùng khi chủ dự án bật lại Knowledge beta. |
| `P1-05_USAGE_GUIDE_V1.md` | Contract V1 lịch sử; Quality V2.1/current roadmap có quyền cao hơn. |
| `QUALITY_TESTING.md`, `SECURITY_PRIVACY.md`, `UX_ACCESSIBILITY.md` | Supporting checklists; gate hiện hành nằm ở roadmap/release checklist. |
| [history/2026-08.md](history/2026-08.md) | Evidence và quyết định đã đóng trong tháng 8/2026. |

## Đề xuất dọn dẹp cần chủ dự án quyết định

Không mục nào dưới đây ảnh hưởng trực tiếp tới luồng chạy nếu chỉ di chuyển tài liệu và cập nhật liên kết. Tuy nhiên nên làm thành commit riêng để history dễ review.

| Đề xuất | Lợi ích | Ảnh hưởng/rủi ro | Khuyến nghị |
| --- | --- | --- | --- |
| Chuyển `ACADEMIC_ASSESSMENT.md`, `REFACTOR_PLAN.md` vào `work_items/history/` | Gốc repo gọn hơn khoảng 70 KB tài liệu lịch sử | Phải sửa link và `tests/test_release_metadata.py` đang đọc `REFACTOR_PLAN.md` | Nên làm ở commit docs riêng. |
| Chuyển Phase A–F và plan Blueprint vào `work_items/history/` | Thư mục work item chỉ còn việc đang dùng | Nhiều liên kết nội bộ cần đổi; không được làm mất provenance | Nên làm sau khi chạy link checker. |
| Giữ `CODE_MAP.md`, `UPGRADE_GUIDE.md` dưới dạng redirect ngắn | Không làm hỏng bookmark/link cũ | Còn hai file nhỏ ở root | Nên giữ. |
| Xóa benchmark/evidence cũ | Giảm dung lượng | Mất baseline so sánh chất lượng/cost | Không khuyến nghị; giữ và gắn nhãn historical. |

## Quy tắc duy trì

1. Task mới chỉ mở trong `PERSONAL_ROADMAP.md`; không tạo thêm phase roadmap song song.
2. Tài liệu có trạng thái `historical`, `frozen` hoặc `dormant` phải nói rõ nguồn hiện hành thay thế.
3. Không hardcode tổng số test trong README/contributing; lấy baseline đã kiểm chứng từ current-state/roadmap.
4. Khi retire một surface, cập nhật cùng lúc manifest/README, roadmap, release checklist và mục lục này.
5. Khi di chuyển tài liệu, chạy link checker, release-metadata test và xem toàn bộ diff trước khi commit.
