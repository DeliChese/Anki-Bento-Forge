# Release Checklist

Không tăng `manifest.json` version trước khi toàn bộ checklist này được ghi kết quả.

## Trước khi phát hành

- [x] Chạy `scripts/test_isolated.ps1` hai lần và ghi số test của cả hai lượt.
- [ ] Xác nhận CI xanh trên matrix Python đã công bố.
- [ ] Chạy smoke thủ công trong Anki 26.5 trên profile mới/đã sao lưu: import/add/update + undo, combo reviewer, TTS cancel/offline và config migration; smoke endpoint 2.1.50 vẫn cần trước khi phát hành với legacy target.
- [x] Rà `git diff` và credential scan: không có API key, raw response, user data hay log profile trong thay đổi V18.
- [ ] Đối chiếu `CHANGELOG.md` với `git log` kể từ bản phát hành gần nhất: mọi thay đổi có thể phát hành đều ở `[Unreleased]`, chỉ mô tả việc đã hoàn tất và có bằng chứng; xem `.claude/CHANGELOG_POLICY.md`.
- [ ] Khi phát hành, chuyển `[Unreleased]` thành `V<manifest.version>` với ngày phát hành; không tạo section version khi CI/smoke Anki còn thiếu.
- [x] Cập nhật `COMPATIBILITY.md`, `REFACTOR_PLAN.md` và README cho phạm vi Anki 2.1.50 đến 26.5.
- [x] Chạy `scripts/build_addon.ps1`; lưu `.ankiaddon`, `.sha256` và `bento-forge.sbom.json` cùng release evidence.
- [ ] Cài artifact vào profile sạch và kiểm tra Tools menu mở Bento Forge.

## Knowledge beta (không phải release gate)

Knowledge V18 được giữ lại như beta riêng tư nhưng đã tắt khỏi giao diện để tập trung phát hành workflow ngoại ngữ. Không cần hoàn thành smoke/CI Knowledge cho một bản phát hành Language và không bump `18.0.0` khi beta còn dormant.

- [x] Schema/model/workflow regression và compatibility audit Knowledge đã có test local.
- [x] Draft và preference Knowledge cũ được giữ nguyên; UI luôn mở Language khi beta tắt.
- [ ] Chỉ mở lại checklist `work_items/V18_SMOKE_PROFILE.md` khi chủ dự án quyết định kích hoạt lại beta.

## Record phát hành

| Phiên bản | Ngày | CI | Smoke Anki thật | Người xác nhận | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 17.2.0 | Chưa phát hành | Chờ CI | Chờ GUI smoke | — | Local 2026-08-16: compatibility mở Anki 2.1.50 đến 26.5; runtime 26.5/Python 3.13.5 chấp nhận packaged manifest và đạt entry/UI/public-hook import cùng collection thật Basic/Cloze add/update/card generation/rollback. Knowledge đã ẩn/chặn workflow Batch Vocabulary của Language và có nút Gửi & tạo thẻ riêng. Isolated harness 2 vòng, mỗi vòng 532 passed; compile toàn bộ Python và diff check xanh. Artifact SHA-256 `8e2d0fc60e725a2ffa728c9f9a35199aa833c8f277aef2cd7a21c7f915a65ea0`. Version vẫn giữ 17.2.0 cho đến khi CI, GUI smoke 26.5 và endpoint legacy đạt. Local ruff chưa chạy vì môi trường thiếu module; `pip-audit` trước đó bị chặn bởi `pytest==8.3.5` / `PYSEC-2026-1845`, nên hai gate này vẫn thuộc CI/security decision trước phát hành. |
| 17.1.0 | Chưa phát hành lại | Chờ CI | Chưa chạy | — | P0-A local: `py_compile` và `80 passed` (2026-08-13). P0-B/P0-C local (2026-08-14): metadata/temp regression `119 passed`; hai lần gọi isolated harness, mỗi lần hai vòng `383 passed`, cleanup và worktree check đạt. Vẫn không được tăng version/phát hành cho tới khi CI 3.9/3.11 và smoke Anki thật hoàn thành. |
