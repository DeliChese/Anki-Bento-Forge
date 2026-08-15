# Changelog Policy

`CHANGELOG.md` là bản ghi lịch sử của thay đổi đã hoàn tất và có thể phát hành; không phải roadmap, nhật ký làm việc hay nơi ghi ý tưởng.

## Khi nào phải cập nhật

Cập nhật `CHANGELOG.md` trong **cùng commit/thay đổi** nếu có tác động tới một trong các nhóm sau:

- Hành vi người dùng, UI, API, template, AI hoặc TTS.
- Dữ liệu người dùng, migration, import/export, cache hay khả năng rollback.
- Bảo mật, riêng tư, logging hoặc dependency.
- Tương thích Anki/Python, đóng gói, CI hoặc regression test quan trọng.

Không cần thêm mục cho đổi tên nội bộ thuần túy, format hoặc comment, trừ khi nó giải quyết lỗi hoặc thay đổi một cam kết công khai.

## Cách ghi

1. Thêm một bullet ngắn, hướng theo tác động, vào `## [Unreleased]`.
2. Dùng một trong ba nhóm chuẩn: `✨ Added`, `🔧 Changed`, `🐛 Fixed`.
3. Chỉ ghi điều đã merge và có bằng chứng trong diff, test, issue đã xác nhận hoặc tài liệu kỹ thuật. Không ghi roadmap, mốc kế hoạch hay kết quả smoke/CI chưa chạy.
4. Có thể gom các thay đổi liên quan vào một bullet; không sao chép nguyên văn commit message hoặc liệt kê chi tiết implementation không giúp người dùng/maintainer hiểu tác động.

Ví dụ:

```md
### 🐛 Fixed
- Phản hồi DeepSeek reasoning nay dùng final content khi trường `content` rỗng.
```

## Quy tắc phiên bản

- Mọi thay đổi sau bản phát hành gần nhất ở `[Unreleased]`, kể cả khi `manifest.json` vẫn mang version cũ.
- Chỉ khi release được xác minh mới chuyển toàn bộ mục phù hợp thành `## [V<manifest.version>] — YYYY-MM-DD`.
- Không tạo section version nếu checklist chưa có bằng chứng CI và smoke Anki theo yêu cầu. Không backdate ngày phát hành.
- Nếu release chỉ chọn một phần thay đổi, phần còn lại giữ ở `[Unreleased]` và được đối chiếu lại với `git log`.

## Đối chiếu trước khi bàn giao/phát hành

1. Đọc `git log` từ commit/tag của bản phát hành gần nhất và `git diff` hiện tại.
2. Kiểm tra mọi thay đổi thuộc phạm vi ở trên đều có mô tả ở `[Unreleased]` hoặc section version đúng.
3. Xác nhận không có roadmap, thông tin nhạy cảm, nội dung học của người dùng, hay claim chưa được kiểm chứng.
4. Chạy tối thiểu `python -m pytest tests/test_release_metadata.py -q`; sau đó chạy test phù hợp với thay đổi.

`RELEASE_CHECKLIST.md` là điểm kiểm soát cuối; skill `11-upgrade-playbook` là lối vào khi nâng version hoặc bảo trì phát hành.
