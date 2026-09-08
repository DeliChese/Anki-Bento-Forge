# Release Checklist

> Status: active
> Authority: release gate
> Last verified: 2026-09-08

Version trong `manifest.json` có thể là release candidate cục bộ. Không publish/tag trước khi CI, artifact và smoke Anki thật bên dưới có bằng chứng.

## Gate tự động

- [ ] Chạy `scripts/test_isolated.ps1` hai lần trên current tree và ghi kết quả.
- [ ] Xác nhận CI xanh trên matrix Python đã công bố.
- [ ] Chạy `python -m pytest tests/test_release_metadata.py -q`.
- [ ] Đối chiếu `CHANGELOG.md` với `git log`; mọi thay đổi phát hành nằm trong `[Unreleased]` đúng ngày/version.
- [ ] Rà credential và dữ liệu profile: không có API key, raw response, nội dung học, cache hoặc state cá nhân trong diff/artifact.

## Artifact

- [ ] Dựng lại bằng `scripts/build_addon.ps1`. Artifact cũ có Batch/Inventory/Blueprint không còn đại diện current tree.
- [ ] Xác nhận allowlist có đủ runtime `workers/`, không chứa Python cache/state local.
- [ ] Xác nhận clean-profile compile, SHA-256 và CycloneDX SBOM khớp artifact mới.
- [ ] Cài artifact vào profile sạch và mở **Tools → 🧪 Bento Forge**.

## Smoke Anki 26.5 trên profile backup

- [ ] Mở Factory, chọn đủ bốn ngôn ngữ và Vocabulary/Grammar/Collocation; draft theo flow không lẫn nhau.
- [ ] Chạy nguồn nhỏ và Chat tạo thẻ → Preview → kiểm định → Import; xác nhận số mục, duplicate/update và lỗi từng mục.
- [ ] Import note mới, update note cũ rồi Undo; note/media/config và lịch SRS ngoài phạm vi không đổi.
- [ ] Kiểm TTS online/offline/cancel, stored media và tốc độ phát trên card.
- [ ] Kiểm Combo và SRS độc lập; migration chỉ chạy sau xác nhận/checkpoint và giữ lịch card cũ.
- [ ] Re-smoke Reviewer trên nhiều thẻ/deck: Nâng cấp thẻ, Tự đặt câu, phiên bản Ví dụ 1–4 và lifecycle khi đổi/lật thẻ.
- [ ] Kiểm Bulk Card Upgrade: báo trước số request, chỉ nâng note cũ/thiếu, lỗi riêng lẻ không dừng lô và SRS không đổi.
- [ ] Kiểm Radical Mindmap tiếng Trung: trigger toàn từ, panel/close/Escape, mobile fallback và typography không đổi.
- [ ] LTS regression V14–V18: field/template Bento được thêm hoặc refresh đúng ownership; field/template/card/media/SRS lạ được giữ nguyên.

## Endpoint và phạm vi

- [ ] Smoke endpoint Anki 2.1.50 trước khi tiếp tục công bố legacy target.
- [x] Runtime không còn import module của AI Study Sessions, Supervised Inventory hoặc AI Deck Blueprint.

## Knowledge beta (không phải release gate)

Knowledge beta vẫn ẩn. Chỉ dùng `work_items/V18_SMOKE_PROFILE.md` nếu chủ dự án chủ động bật lại; không bump `18.0.0` hoặc mở lại release gate Knowledge từ tài liệu lịch sử.

## Đóng release

- [ ] Chuyển `[Unreleased]` thành `## [V<manifest.version>] — YYYY-MM-DD` chỉ sau khi các gate bắt buộc đạt.
- [ ] Ghi CI, smoke, người xác nhận và checksum vào record phát hành.
- [ ] Tag/publish đúng version trong `manifest.json`; không đổi tên Note Type LTS V18.3 chỉ vì bump version add-on.

## Record phát hành

| Phiên bản | Ngày | CI | Smoke Anki thật | Người xác nhận | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 18.3.0 | Chưa phát hành | Chờ CI | Re-smoke bắt buộc | — | Current tree đã xóa các subsystem Study Sessions/Inventory/Blueprint và có Quality V2.1, Bulk Card Upgrade, Collocation, Radical Mindmap, Production Drill cùng Example Versions. Cần baseline cuối, artifact mới và smoke profile backup trước release. |
| 18.1.0 | Chưa phát hành | Chờ CI | Chờ GUI smoke | — | Snapshot lịch sử 2026-08-20; không phải trạng thái current tree. |
| 17.2.0 | Chưa phát hành | Chờ CI | Chờ GUI smoke | — | Snapshot lịch sử 2026-08-16; không phải trạng thái current tree. |
| 17.1.0 | Chưa phát hành lại | Chờ CI | Chưa chạy | — | Snapshot lịch sử 2026-08-13/14; không phải trạng thái current tree. |
