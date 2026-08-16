# Release Checklist

Không tăng `manifest.json` version trước khi toàn bộ checklist này được ghi kết quả.

## Trước khi phát hành

- [x] Chạy `scripts/test_isolated.ps1` hai lần và ghi số test của cả hai lượt.
- [ ] Xác nhận CI xanh trên matrix Python đã công bố.
- [ ] Chạy smoke thủ công trong Anki 2.1.50 trên profile đã sao lưu: import/add/update + undo, combo reviewer, TTS cancel/offline, và config migration.
- [ ] Rà `git diff` để không có API key, raw prompt/response, user data hay log profile.
- [ ] Đối chiếu `CHANGELOG.md` với `git log` kể từ bản phát hành gần nhất: mọi thay đổi có thể phát hành đều ở `[Unreleased]`, chỉ mô tả việc đã hoàn tất và có bằng chứng; xem `.claude/CHANGELOG_POLICY.md`.
- [ ] Khi phát hành, chuyển `[Unreleased]` thành `V<manifest.version>` với ngày phát hành; không tạo section version khi CI/smoke Anki còn thiếu.
- [ ] Cập nhật `COMPATIBILITY.md`, `REFACTOR_PLAN.md` và README nếu phạm vi hỗ trợ đổi.
- [ ] Chạy `scripts/build_addon.ps1`; lưu `.ankiaddon`, `.sha256` và `bento-forge.sbom.json` cùng release evidence.
- [ ] Cài artifact vào profile sạch và kiểm tra Tools menu mở Bento Forge.

## Record phát hành

| Phiên bản | Ngày | CI | Smoke Anki thật | Người xác nhận | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 17.2.0 | Chưa phát hành | Chờ CI | Chưa chạy | — | Local 2026-08-16: Python 3.11 compile toàn bộ Python tracked; isolated harness 2 vòng, mỗi vòng 500 passed; ruff + credential scan xanh; build artifact SHA-256 `86c087d7b6249d372855a47082a1d4ae28de8fe9ffd7f13622ffff69d09b3fd9`, giải nén clean-profile tạm và compile xanh. Chưa được tính là cài/smoke Anki thật. `pip-audit` chặn bởi `pytest==8.3.5` / `PYSEC-2026-1845`; bản audit nêu 9.0.3 không hỗ trợ Python 3.9, nên vẫn cần quyết định tương thích/security, CI 3.9/3.11 và smoke Anki thật trước phát hành. |
| 17.1.0 | Chưa phát hành lại | Chờ CI | Chưa chạy | — | P0-A local: `py_compile` và `80 passed` (2026-08-13). P0-B/P0-C local (2026-08-14): metadata/temp regression `119 passed`; hai lần gọi isolated harness, mỗi lần hai vòng `383 passed`, cleanup và worktree check đạt. Vẫn không được tăng version/phát hành cho tới khi CI 3.9/3.11 và smoke Anki thật hoàn thành. |
