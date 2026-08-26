# Release Checklist

Version trong `manifest.json` có thể là release candidate cục bộ; không publish/tag trước khi toàn bộ checklist này được ghi kết quả.

## Trước khi phát hành

- [x] Chạy `scripts/test_isolated.ps1` hai lần và ghi số test của cả hai lượt.
- [ ] Xác nhận CI xanh trên matrix Python đã công bố.
- [ ] Chạy smoke thủ công trong Anki 26.5 trên profile mới/đã sao lưu: import/add/update + undo, combo reviewer, TTS cancel/offline và config migration; smoke endpoint 2.1.50 vẫn cần trước khi phát hành với legacy target.
- [ ] Smoke AI Study Sessions trong Reviewer: dock trái/phải, floating/minimize/maximize, hide/reopen, restart restore, session CRUD và shortcut conflict; ngoài Reviewer phải không mở Forge surface riêng.
  - [ ] Chat đủ dài để context compact, tiếp tục hỏi cùng topic và xác nhận AI không lặp fact bất thường.
  - [ ] Restart Anki, mở lại đúng session và xác nhận mạch học cùng rolling summary vẫn tiếp tục.
- [ ] Smoke Reviewer: Ask AI, quick prompts, current-card context on/off, đổi thẻ khi AI đang chạy, Back to Review và xác nhận SRS không đổi.
  - [ ] Trên một card từ vựng và một card ngữ pháp thật, chỉ hỏi bằng “từ vựng này”/“ngữ pháp này”; xác nhận AI dùng đúng target hiện tại và Study Pack cùng ngôn ngữ, không yêu cầu nhập lại target.
  - [ ] Trên card `看`, hỏi đúng “Tiếp tục cho tôi câu ví dụ lấy điểm ngữ pháp thứ 42 trong tài liệu”; Scope phải hiện `42. Thái tiến hành: 在, 正在, 正, 呢`, Coach phải xác định/thực hiện mục này trước rồi mới cho ví dụ đúng cấu trúc (có thể dùng `看`, như `我正在看书呢。`). Tuyệt đối không thay bằng bài luyện chung cho `看`, trả `是……的` hoặc tự gán Phương vị từ là mục 41. Lặp lại exact-section flow với một card grammar.
  - [ ] Với cùng mục 42, xác nhận Coach không tự gán quy tắc tuyệt đối kiểu `在` “nhanh”, `正…呢` “vừa hay” hoặc `正在` “trang trọng” nếu excerpt không nêu đối chiếu đó; câu trả lời phải phân biệt rõ giới hạn source với ví dụ Coach tạo.
  - [ ] Kiểm transcript trên dock hẹp và floating: heading/list/code/quote không lộ Markdown thô `**`/`***`; bảng 2 cột có chữ dễ đọc, bảng từ 3 cột hiển thị thành các khối thông tin, không tràn ngang hoặc lẫn role người học/Coach.
  - [ ] Khi gửi request, thấy `AI đang soạn tin…` đổi chấm và tự biến mất khi thành công, Stop hoặc lỗi; transcript chiếm phần lớn chiều cao và mọi điều khiển học vẫn hiện diện/dùng được trong dock hoặc floating.
  - [ ] Kiểm tra nút Ask AI trên light/dark: đọc rõ, không che card, click mới mở companion; Esc/Back to Review trả focus.
  - [ ] Smoke Production Drill trên card vocab/grammar có Usage Pattern/Collocation: nút **Tự đặt câu** chỉ hiện ở mặt câu hỏi, nhập được Nhật/Trung/Hàn/Anh, gợi ý/câu mẫu ẩn trước thao tác chủ động, Escape đóng panel và note/SRS không đổi.
- [ ] Smoke dây chuyền Lò đúc AI tích hợp: chỉ có một Nguồn học liệu; không lộ router/bước xử lý; composer chứa ô nhập + checkbox Tạo thẻ + nút Gửi; đổi Vocab/Grammar phía trên làm checkbox và artifact bám đúng loại.
  - [ ] Từ artifact bubble trong transcript, chạy Review và Đưa sang kiểm định; restart/reopen artifact và xác nhận không gọi AI lại hoặc mở cửa sổ Xưởng riêng.
- [x] Rà `git diff` và credential scan: không có API key, raw response, user data hay log profile trong thay đổi V18.
- [ ] Đối chiếu `CHANGELOG.md` với `git log` kể từ bản phát hành gần nhất: mọi thay đổi có thể phát hành đều ở `[Unreleased]`, chỉ mô tả việc đã hoàn tất và có bằng chứng; xem `.claude/CHANGELOG_POLICY.md`.
- [ ] Khi phát hành, chuyển `[Unreleased]` thành `V<manifest.version>` với ngày phát hành; không tạo section version khi CI/smoke Anki còn thiếu.
- [x] Cập nhật `COMPATIBILITY.md`, `REFACTOR_PLAN.md` và README cho phạm vi Anki 2.1.50 đến 26.5.
- [x] Chạy `scripts/build_addon.ps1`; lưu `.ankiaddon`, `.sha256` và `bento-forge.sbom.json` cùng release evidence.
  - [x] Local 2026-08-26: artifact `18.3.0` có 104 entries, 101 Python files và đủ 5 worker files; clean-profile compile xanh, cache/sensitive state bằng 0, SHA-256 `87049cae063403e84cae70b11009980146f96c3d61de75915d8a9b78ca5efbff` khớp và SBOM liệt kê `edge-tts,gtts`.
- [ ] Cài artifact vào profile sạch và kiểm tra Tools menu mở Bento Forge.

## Knowledge beta (không phải release gate)

Knowledge V18 được giữ lại như beta riêng tư nhưng đã tắt khỏi giao diện để tập trung phát hành workflow ngoại ngữ. Không cần hoàn thành smoke/CI Knowledge cho một bản phát hành Language và không bump `18.0.0` khi beta còn dormant.

- [x] Schema/model/workflow regression và compatibility audit Knowledge đã có test local.
- [x] Draft và preference Knowledge cũ được giữ nguyên; UI luôn mở Language khi beta tắt.
- [ ] Chỉ mở lại checklist `work_items/V18_SMOKE_PROFILE.md` khi chủ dự án quyết định kích hoạt lại beta.

## Record phát hành

| Phiên bản | Ngày | CI | Smoke Anki thật | Người xác nhận | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 18.3.0 | Chưa phát hành | Chờ CI | Re-smoke bắt buộc | — | Task-priority, guard sắc thái, UI Coach và Production Drill local; P0-04 artifact allowlist/clean-profile compile/SHA-256/SBOM xanh. Isolated `805 passed` ×2; critical Ruff xanh, pre-commit chưa có local. Chưa khép V18.3 cho tới khi owner re-smoke vocabulary/grammar + mục 42 + UI đạt. |
| 18.1.0 | Chưa phát hành | Chờ CI | Chờ GUI smoke | — | Local 2026-08-20: compile toàn bộ Python xanh; isolated harness 2 vòng, mỗi vòng `640 passed`; AI Study Sessions delta-summary/theme/artifact polish xanh, chưa publish. |
| 17.2.0 | Chưa phát hành | Chờ CI | Chờ GUI smoke | — | Local 2026-08-16: compatibility mở Anki 2.1.50 đến 26.5; runtime 26.5/Python 3.13.5 chấp nhận packaged manifest và đạt entry/UI/public-hook import cùng collection thật Basic/Cloze add/update/card generation/rollback. Knowledge đã ẩn/chặn workflow Batch Vocabulary của Language và có nút Gửi & tạo thẻ riêng. Isolated harness 2 vòng, mỗi vòng 532 passed; compile toàn bộ Python và diff check xanh. Artifact SHA-256 `8e2d0fc60e725a2ffa728c9f9a35199aa833c8f277aef2cd7a21c7f915a65ea0`. Version vẫn giữ 17.2.0 cho đến khi CI, GUI smoke 26.5 và endpoint legacy đạt. Local ruff chưa chạy vì môi trường thiếu module; `pip-audit` trước đó bị chặn bởi `pytest==8.3.5` / `PYSEC-2026-1845`, nên hai gate này vẫn thuộc CI/security decision trước phát hành. |
| 17.1.0 | Chưa phát hành lại | Chờ CI | Chưa chạy | — | P0-A local: `py_compile` và `80 passed` (2026-08-13). P0-B/P0-C local (2026-08-14): metadata/temp regression `119 passed`; hai lần gọi isolated harness, mỗi lần hai vòng `383 passed`, cleanup và worktree check đạt. Vẫn không được tăng version/phát hành cho tới khi CI 3.9/3.11 và smoke Anki thật hoàn thành. |
