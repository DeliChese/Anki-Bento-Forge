# Current State — Bento Forge

> Status: active  
> Authority: supporting; roadmap remains the canonical backlog  
> Last verified: 2026-09-07
> Read when: every agent session, immediately after `AGENTS.md`

## Operating contract

- Bento Forge là add-on cá nhân, ưu tiên bốn ngôn ngữ Nhật/Trung/Hàn/Anh và các flow: AI extract → preview/import, update/undo, TTS → review.
- Không tự mở rộng public/community, ngôn ngữ mới, OCR/video/image AI, analytics hay big-bang refactor.
- Knowledge beta đang dormant: UI tắt, không phát hành V18 nếu không có yêu cầu rõ ràng từ chủ dự án.

## Active state

| Item | Status | Next action |
|---|---|---|
| P0-01 baseline | local gate xanh | Compile Python/JavaScript xanh; full isolated suite gần nhất `834 passed, 28 skipped`. Giữ gate này xanh trước merge/release. |
| P0-02 smoke profile | local fix, chờ re-smoke | Lỗi Reviewer action bám DOM/card đầu đã được sửa bằng card ID, cleanup và delayed retry; cần re-smoke Anki 26.5/profile `ChinD` backup trên nhiều thẻ/deck. Không rating/mutation trong lượt kiểm tra trước. |
| P0-04 release artifact | cần dựng lại | Runtime Batch/Inventory/Blueprint đã bị gỡ nên artifact cũ không còn đại diện current tree; cần rebuild trước release. |
| LTS Card Contract | local implementation xanh, chờ GUI smoke | Language Note Type khóa tại schema V18.3; migration allowlist/additive, ownership template theo tên/alias lịch sử, không tự prune dữ liệu lạ. Chuẩn nội dung dùng revision riêng và Reviewer upgrade opt-in. Còn smoke V14–V18 trên profile backup trước release. |
| P0-05 AI Output Reliability | local implementation xanh | Luồng nhỏ dùng một request trực tiếp, validate → Preview → Import; danh sách vocab tường minh có kiểm tra đủ mục và giữ thứ tự. Còn smoke restart/profile backup trước publish. |
| P1-07 AI Study Sessions | retired 2026-09-07 | Đã gỡ action trên thẻ, menu và phím tắt; dữ liệu phiên cũ không bị xóa. |
| V18.2 Contextual AI Workspaces | surface đã thu gọn | Reviewer không còn Study Coach; Factory chỉ còn nguồn nhỏ + yêu cầu tùy chọn + một nút tạo 5–20 thẻ → Preview → Import. |
| V18.3 Language Study Library | archived with Study Sessions | Dữ liệu/library backend cũ được giữ để không xóa dữ liệu profile, nhưng không còn surface người dùng sau khi Study Sessions bị retire. |
| Chinese Radical Mindmap | local implementation xanh, chờ GUI smoke | AI schema `Radical Mindmap` chỉ còn glyph+tên bộ thủ (prompt/cache 44). Toàn bộ từ giữ nguyên typography và là một vùng hover/click; không còn nút rời. Panel cố định tự chọn cạnh trái/phải, thẻ dịch nhẹ, có nút đóng; mobile dùng bottom overlay. Targeted `54 passed`, JS syntax xanh; full isolated `829 passed, 28 skipped`. |
| Reviewer Card Upgrade UI | local fix xanh, chờ GUI smoke | Nút đồng bộ theo card ID; dialog có khu vực kết quả rõ ràng và dùng `Qt.CheckState` chuẩn PyQt6. Kiểm tra định danh nhận đúng khóa schema theo ngôn ngữ (`simplified` cho tiếng Trung), còn Apply ánh xạ khóa JSON sang field Anki thật và đồng bộ đúng Note Type trước khi ghi; template tùy chỉnh và SRS giữ nguyên. Targeted `16 passed`; full isolated `829 passed, 28 skipped`. |
| Bulk Card Upgrade | local implementation xanh, chờ GUI smoke | Forge có action theo ngôn ngữ + subtype hiện tại: sync template additive một lần, quét tất cả note của Note Type, chỉ gửi AI tuần tự cho note cũ/thiếu dữ liệu. Mỗi write recheck note ID/identity, ghi undo-aware, lỗi từng note không hủy lô và SRS giữ nguyên. Targeted `22 passed`; full isolated `834 passed, 28 skipped`; chờ smoke profile backup. |
| Language Collocation subtype | local implementation xanh, chờ GUI smoke | Nhật/Trung/Hàn/Anh có lựa chọn Collocation/Thành ngữ chủ động, prompt/schema/candidate/artifact/history và Note Type riêng; hai hướng Nhận diện/Sản xuất, không migrate note/SRS vocab hoặc grammar. Batch danh sách thiếu ngữ cảnh bị chặn. Isolated `838 passed` ×2; còn smoke chọn mode → AI Preview → import → review trên profile backup. |
| Supervised AI Inventory | retired 2026-09-01 | Đã xóa scanner, topic-first gate, checkpoint và UI sản xuất quy mô lớn. XLSX fallback chuẩn vẫn được giữ cho thao tác mở file nhỏ. |
| P1-08 AI Deck Blueprint | retired 2026-09-01 | Đã xóa AI Blueprint/import nhiều deck; Deck Manager cơ bản tạo/đổi tên/xóa deck vẫn giữ nguyên. |
| P1-05 Usage Guide | đã kiểm chứng | Dùng benchmark/fixture hiện có làm regression gate. |
| P1-06 Confusion Guard | local implementation xanh | Exact curated same-deck warning đã có fixtures bốn ngôn ngữ; chờ smoke profile backup, vẫn chỉ advisory và không tự sửa note/SRS. |
| P2-03 Production Drill | local lifecycle fix, chờ re-smoke | Action nay đồng bộ theo card ID, retry sau render và dùng được Example khi Usage Pattern/Collocation trống. Targeted `51 passed`, full isolated `826 passed, 28 skipped`; cần re-smoke nhiều thẻ/deck ở bốn ngôn ngữ. |
| Reviewer Example Versions | local implementation xanh, chờ GUI smoke | Ví dụ 1–4 có model AI riêng tùy chọn theo Provider/API Key hiện dùng, tạo/chỉnh theo độ khó và độ dài, lịch sử phiên bản + audio lưu theo note, tác vụ AI/TTS không modal và tiến độ import tính cả audio lẫn ghi note. Hai isolated suites `777 passed, 28 skipped`; cần smoke trên profile backup trước release. |

## Evidence and boundaries

- LTS Card Contract giữ version add-on độc lập với schema Note Type V18.3. Template Bento được cập nhật theo tên hoặc alias lịch sử; template/field/card/media/SRS ngoài ownership được giữ nguyên. Legacy multi-card migration yêu cầu xác nhận + checkpoint. Verification 2026-09-04: targeted `111 passed, 1 skipped`; compile Python xanh; full isolated `793 passed, 28 skipped` ×2. Chưa thay thế GUI smoke V14–V18 trên profile backup.

- Factory production hiện là một lượt trực tiếp, tối đa 4.000 ký tự nguồn và 5–20 thẻ; không gọi Inventory Scanner, không chunk/batch và luôn đi qua AI Preview trước JSON/import. Danh sách từ vựng tường minh dùng xuống dòng, `、`, dấu phẩy hoặc chấm phẩy được tách cục bộ, tự nâng mục tiêu để bao phủ đủ mục trong giới hạn 20 và fail-closed nếu AI trả thiếu. Callback chất lượng của Preview được ngắt khi dialog kết thúc để không chạm vào QObject đã bị Qt hủy, đồng thời bỏ qua `itemChanged` tái nhập phát ra khi chính callback cập nhật tooltip. Review có nút cục bộ ẩn/hiện Pinyin, IPA, Furigana và Romanization mà không đổi dữ liệu thẻ hay SRS. Verification 2026-09-03: Preview lifecycle targeted `3 passed`; full isolated `760 passed, 28 skipped` (toàn bộ skip là regression cũ của Batch đã retired).

- Factory Language có `Chat tạo thẻ`: yêu cầu tự nhiên không cần tài liệu được gắn rõ là direct generation, có cache key riêng, đối chiếu deck tránh trùng và Preview-first Import như source flow. Coordinator chuyển cờ này tới worker mà không làm đổi worker cũ. Knowledge không hiển thị lối vào này vì yêu cầu nguồn để giữ schema. Verification 2026-09-04: targeted `42 passed, 1 skipped`; full isolated `780 passed, 28 skipped`.

- Reviewer Example Versions giữ câu gốc và mọi lần tạo lại trong field `Example Versions`, đồng thời materialize phiên bản đang chọn về các field Example/reading/translation/audio hiện hữu để template và sync Anki tiếp tục hoạt động. AI chỉ nhận context gọn của thẻ cùng tối đa tám ví dụ cần tránh; có thể dùng model riêng cùng Provider/API Key đang chọn; TTS lưu sound tag một lần và dùng lại. Verification 2026-09-04: compile Python xanh và full isolated `777 passed, 28 skipped` ×2; chưa thay thế GUI smoke trên profile backup.

- Bằng chứng V18.3 Study Sessions/Library trước khi retire nằm trong lịch sử tháng 8; backend và dữ liệu cũ được giữ nhưng không còn là gate phát hành UI. Chi tiết hiện hành ở [Personal Roadmap](../../work_items/PERSONAL_ROADMAP.md).
- Bằng chứng Radical Mindmap 2026-09-07: schema song ngữ tối giản mỗi component còn glyph+name, structured field serialize JSON ổn định khi import/nâng cấp, toàn bộ 10 template Chinese Vocabulary tham chiếu field tùy chọn. Whole-word trigger không thay DOM chữ; side panel fixed có close/focus/Escape và mobile fallback. Targeted `54 passed`, JS qua `node --check`, full isolated `829 passed, 28 skipped`; còn GUI smoke profile backup.
- Bằng chứng Card Upgrade UI 2026-09-07: cầu nối `pycmd` có test mở dialog, snapshot lúc inject được giữ làm fallback, bảng kết quả dùng enum PyQt6 và luôn có trạng thái chờ/thành công/lỗi; targeted `45 passed`, full isolated `823 passed, 28 skipped`. Còn GUI smoke một thẻ Language cũ trong Anki thật.
- Bằng chứng Reviewer lifecycle fix 2026-09-07: Hán tự mặt sau dùng DOM-node state thay cho attribute bị clone; Upgrade/Production action có card ID, token hủy render cũ, cleanup khi lật mặt và retry 80/240 ms. Targeted `51 passed`, JavaScript qua `node --check`, full isolated `826 passed, 28 skipped`. Còn re-smoke nhiều thẻ/deck trên profile backup.
- Bằng chứng P1-05: `19/20` (`95%`), `$0.002035`, `1.69 giây/card`; xem [benchmark](../../benchmarks/usage_guide_review_v1.json).
- Trước mutation collection, cần backup/undo và smoke liên quan. Con người xác nhận mọi thao tác Anki thật.
- Không coi số liệu trong tài liệu `historical` là trạng thái hiện tại nếu chúng mâu thuẫn roadmap/evidence mới hơn.

## Context policy

Context mặc định chỉ gồm `AGENTS.md`, `CLAUDE.md`, file này và một skill. Chỉ thêm source/test/benchmark sau khi `rg` xác nhận chúng thuộc task; dùng [task contract](task-contract-template.md) khi chuyển lượt hoặc đổi model.
