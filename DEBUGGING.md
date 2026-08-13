# Debugging Bento Forge

## Lấy log an toàn

1. Đóng Anki sau khi tái hiện lỗi để file log được flush.
2. Mở thư mục profile Anki đang dùng, rồi vào `bento_forge/logs/`.
3. Sao chép `anki_tool.log` (hoặc file rotation `.1`, `.2`, `.3`) và tìm mã sự kiện, ví dụ `IMPORT_AUDIO_TASK_FAILED`.
4. Khi gửi báo lỗi, chỉ gửi mã sự kiện, phiên bản Bento Forge/Anki, hệ điều hành và thời điểm lỗi. Không gửi API key, Authorization header, prompt, response AI, nội dung thẻ, hoặc toàn bộ file log công khai.

File log thuộc dữ liệu profile, không nằm trong thư mục mã add-on và không bị ghi đè khi cập nhật add-on.

## Cách đọc mã sự kiện

Mỗi event có dạng `CODE: action=<next action>; key=value`.

| Code | Ý nghĩa | Hành động người dùng |
| --- | --- | --- |
| `TTS_DEPENDENCY_MISSING` | Thiếu thư viện TTS tùy chọn. | Chạy `install_command` được ghi trong log, trong môi trường Python do bạn chọn. |
| `IMPORT_AUDIO_TASK_FAILED` | Một audio task thất bại; import vẫn tiếp tục. | Kiểm tra kết nối/TTS provider rồi tạo audio lại nếu cần. |
| `IMPORT_AUDIO_WORKER_FAILED` | Audio worker đã dừng bất thường. | Thử lại với ít thẻ hơn; gửi code + thời điểm nếu lặp lại. |
| `HOOK_REVIEWER_UNAVAILABLE` | Phiên bản Anki không có hook công khai cần thiết. | Tính năng liên quan tự tắt; không dùng bản Anki đó để phát hành hỗ trợ. |
| `HOOK_REVIEWER_REGISTER_FAILED` | Đăng ký reviewer hook không thành công. | Khởi động lại Anki, tắt add-on xung đột và gửi mã lỗi nếu còn. |

Logger che API key, token và Authorization header. Exception được ghi theo loại lỗi thay vì nội dung exception để giảm nguy cơ lộ dữ liệu học hoặc phản hồi từ provider.
