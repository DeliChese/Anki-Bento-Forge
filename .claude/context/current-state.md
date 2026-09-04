# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-09-04
> Read when: every agent session, immediately after `AGENTS.md`

## Operating contract

- Bento Forge là add-on cá nhân, ưu tiên bốn ngôn ngữ Nhật/Trung/Hàn/Anh và các flow: AI extract → preview/import, update/undo, TTS → review.
- Không tự mở rộng public/community, ngôn ngữ mới, OCR/video/image AI, analytics hay big-bang refactor.
- Knowledge beta đang dormant: UI tắt, không phát hành V18 nếu không có yêu cầu rõ ràng từ chủ dự án.

## Active state

| Item | Status | Next action |
|---|---|---|
| P0-01 baseline | local gate xanh | Compile Python xanh; hai isolated suite gần nhất đều `793 passed, 28 skipped`. Giữ gate này xanh trước merge/release. |
| P0-02 smoke profile | partial smoke, blocked | Anki 26.5/profile `ChinD` backup: Factory, combo/Usage Guide, Study Coach context và role split pass; Reviewer không inject `Hỏi AI`/`Tự đặt câu` trên card `看`. Không rating/mutation; sửa hook trước khi tiếp tục. |
| P0-04 release artifact | cần dựng lại | Runtime Batch/Inventory/Blueprint đã bị gỡ nên artifact cũ không còn đại diện current tree; cần rebuild trước release. |
| LTS Card Contract | local implementation xanh, chờ GUI smoke | Language Note Type khóa tại schema V18.3; migration allowlist/additive, ownership template theo tên/alias lịch sử, không tự prune dữ liệu lạ. Chuẩn nội dung dùng revision riêng và Reviewer upgrade opt-in. Còn smoke V14–V18 trên profile backup trước release. |
| P0-05 AI Output Reliability | local implementation xanh | Luồng nhỏ dùng một request trực tiếp, validate → Preview → Import; danh sách vocab tường minh có kiểm tra đủ mục và giữ thứ tự. Còn smoke restart/profile backup trước publish. |
| P1-07 AI Study Sessions | menu/context smoke pass, card action blocked | Study Coach mở từ menu, nhận đúng `REVIEWER · QA · Mặt câu hỏi · Thẻ chính: 看`, quick actions/library hiện đủ và ngoài Reviewer fail-closed; `Hỏi AI` trên card vắng mặt. Còn fix/restart/concurrency/mục 42 và CI. |
| V18.2 Contextual AI Workspaces | Factory đã thu gọn | Reviewer vẫn sở hữu Study Coach; Factory không còn nhúng Forge chat/artifact station. Production chỉ còn nguồn nhỏ + yêu cầu tùy chọn + một nút tạo 5–20 thẻ → Preview → Import. |
| V18.3 Language Study Library | guard sắc thái + UI local, chờ re-smoke | Scope mục 42 đúng; prompt/context đặt ý định người học lên trước, cấm suy diễn sắc thái/độ trang trọng giữa biến thể ngữ pháp khi excerpt không đối chiếu và coi history mâu thuẫn là obsolete. Chat dock ưu tiên transcript, toàn bộ chức năng học luôn hiện diện và có chỉ báo AI đang soạn. Isolated `805 passed` ×2. Chưa khép cho tới khi owner re-smoke mục 42 + UI trên thẻ vocabulary/grammar. |
| Language Collocation subtype | local implementation xanh, chờ GUI smoke | Nhật/Trung/Hàn/Anh có lựa chọn Collocation/Thành ngữ chủ động, prompt/schema/candidate/artifact/history và Note Type riêng; hai hướng Nhận diện/Sản xuất, không migrate note/SRS vocab hoặc grammar. Batch danh sách thiếu ngữ cảnh bị chặn. Isolated `838 passed` ×2; còn smoke chọn mode → AI Preview → import → review trên profile backup. |
| Supervised AI Inventory | retired 2026-09-01 | Đã xóa scanner, topic-first gate, checkpoint và UI sản xuất quy mô lớn. XLSX fallback chuẩn vẫn được giữ cho thao tác mở file nhỏ. |
| P1-08 AI Deck Blueprint | retired 2026-09-01 | Đã xóa AI Blueprint/import nhiều deck; Deck Manager cơ bản tạo/đổi tên/xóa deck vẫn giữ nguyên. |
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | local implementation xanh | Exact curated same-deck warning đã có fixtures bốn ngôn ngữ; chờ smoke profile backup, vẫn chỉ advisory và không tự sửa note/SRS. |
| P2-03 Production Drill | GUI smoke fail | Anki 26.5 không hiện `Tự đặt câu` trên card `看` dù có Usage Pattern/Collocation; local suite vẫn `805 passed` ×2. Cần sửa hook injection rồi re-smoke bốn ngôn ngữ; không note/SRS mutation trong phiên phát hiện. |
| Reviewer Example Versions | local implementation xanh, chờ GUI smoke | Ví dụ 1–4 có model AI riêng tùy chọn theo Provider/API Key hiện dùng, tạo/chỉnh theo độ khó và độ dài, lịch sử phiên bản + audio lưu theo note, tác vụ AI/TTS không modal và tiến độ import tính cả audio lẫn ghi note. Hai isolated suites `777 passed, 28 skipped`; cần smoke trên profile backup trước release. |

## Evidence and boundaries

- LTS Card Contract giữ version add-on độc lập với schema Note Type V18.3. Template Bento được cập nhật theo tên hoặc alias lịch sử; template/field/card/media/SRS ngoài ownership được giữ nguyên. Legacy multi-card migration yêu cầu xác nhận + checkpoint. Verification 2026-09-04: targeted `111 passed, 1 skipped`; compile Python xanh; full isolated `793 passed, 28 skipped` ×2. Chưa thay thế GUI smoke V14–V18 trên profile backup.

- Factory production hiện là một lượt trực tiếp, tối đa 4.000 ký tự nguồn và 5–20 thẻ; không gọi Inventory Scanner, không chunk/batch và luôn đi qua AI Preview trước JSON/import. Danh sách từ vựng tường minh dùng xuống dòng, `、`, dấu phẩy hoặc chấm phẩy được tách cục bộ, tự nâng mục tiêu để bao phủ đủ mục trong giới hạn 20 và fail-closed nếu AI trả thiếu. Callback chất lượng của Preview được ngắt khi dialog kết thúc để không chạm vào QObject đã bị Qt hủy, đồng thời bỏ qua `itemChanged` tái nhập phát ra khi chính callback cập nhật tooltip. Review có nút cục bộ ẩn/hiện Pinyin, IPA, Furigana và Romanization mà không đổi dữ liệu thẻ hay SRS. Verification 2026-09-03: Preview lifecycle targeted `3 passed`; full isolated `760 passed, 28 skipped` (toàn bộ skip là regression cũ của Batch đã retired).

- Factory Language có `Chat tạo thẻ`: yêu cầu tự nhiên không cần tài liệu được gắn rõ là direct generation, có cache key riêng, đối chiếu deck tránh trùng và Preview-first Import như source flow. Coordinator chuyển cờ này tới worker mà không làm đổi worker cũ. Knowledge không hiển thị lối vào này vì yêu cầu nguồn để giữ schema. Verification 2026-09-04: targeted `42 passed, 1 skipped`; full isolated `780 passed, 28 skipped`.

- Reviewer Example Versions giữ câu gốc và mọi lần tạo lại trong field `Example Versions`, đồng thời materialize phiên bản đang chọn về các field Example/reading/translation/audio hiện hữu để template và sync Anki tiếp tục hoạt động. AI chỉ nhận context gọn của thẻ cùng tối đa tám ví dụ cần tránh; có thể dùng model riêng cùng Provider/API Key đang chọn; TTS lưu sound tag một lần và dùng lại. Verification 2026-09-04: compile Python xanh và full isolated `777 passed, 28 skipped` ×2; chưa thay thế GUI smoke trên profile backup.

- Bằng chứng V18.3 hiện tại: transcript profile thật xác nhận manifest đúng mục `42. Thái tiến hành: 在, 正在, 正, 呢`; guard mới cấm biến việc liệt kê dạng thành quy tắc sắc thái tuyệt đối. Renderer có fixture heading/list/code/quote/bảng hẹp/rộng; dock có transcript ưu tiên, các chức năng học luôn hiện diện và typing indicator. Hai isolated suites `805 passed`. Đây là bằng chứng local, không thay thế re-smoke Anki thật đang mở. Chi tiết và điều kiện phát hành hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
