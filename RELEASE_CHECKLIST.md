# Release Checklist

Không tăng `manifest.json` version trước khi toàn bộ checklist này được ghi kết quả.

## Trước khi phát hành

- [x] Chạy `scripts/test_isolated.ps1` hai lần và ghi số test của cả hai lượt.
- [ ] Xác nhận CI xanh trên matrix Python đã công bố.
- [ ] Chạy smoke thủ công trong Anki 2.1.50 trên profile đã sao lưu: import/add/update + undo, combo reviewer, TTS cancel/offline, và config migration.
- [ ] Rà `git diff` để không có API key, raw prompt/response, user data hay log profile.
- [ ] Cập nhật `CHANGELOG.md`, `COMPATIBILITY.md`, `REFACTOR_PLAN.md` và README nếu phạm vi hỗ trợ đổi.
- [ ] Chạy `scripts/build_addon.ps1`; lưu `.ankiaddon`, `.sha256` và `bento-forge.sbom.json` cùng release evidence.
- [ ] Cài artifact vào profile sạch và kiểm tra Tools menu mở Bento Forge.

## Record phát hành

| Phiên bản | Ngày | CI | Smoke Anki thật | Người xác nhận | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 17.1.0 | Chưa phát hành lại | Chờ CI | Chưa chạy | — | P0-A local: `py_compile` và `80 passed` (2026-08-13). P0-B/P0-C local (2026-08-14): metadata/temp regression `119 passed`; hai lần gọi isolated harness, mỗi lần hai vòng `383 passed`, cleanup và worktree check đạt. Vẫn không được tăng version/phát hành cho tới khi CI 3.9/3.11 và smoke Anki thật hoàn thành. |
