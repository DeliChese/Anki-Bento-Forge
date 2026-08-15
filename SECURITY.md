# Chính sách bảo mật và threat model

Áp dụng cho Bento Forge V17.1.0. Tài liệu này mô tả các ranh giới bảo mật hiện
có, dữ liệu được xử lý, các biện pháp giảm thiểu và cách báo cáo lỗ hổng. Đây
không phải là cam kết rằng dịch vụ AI bên thứ ba, hệ điều hành, hay add-on khác
trên cùng máy an toàn tuyệt đối.

## Phiên bản hỗ trợ

Security fix được đánh giá trước tiên trên bản phát hành V17.1.x mới nhất. Bản
cũ chỉ nhận bản vá khi lỗ hổng nghiêm trọng vẫn tái hiện trên bản hiện hành và
có bản vá tương thích.

## Dữ liệu và ranh giới xử lý

| Dữ liệu | Vị trí/xử lý | Lưu ý quan trọng |
|---|---|---|
| API key | OS credential store qua `keyring`, tách theo profile | Bento Forge từ chối lưu key khi credential store không khả dụng; không dùng obfuscation có thể đảo ngược làm fallback. |
| Cấu hình provider/model và trạng thái UI | Thư mục `bento_forge` dưới Anki profile | Không chứa API key mới. |
| Văn bản học, file tham khảo, Anki context, prompt và phản hồi AI | Chỉ gửi đến provider mà người dùng chọn khi chủ động dùng AI Extract, Batch hoặc AI Chat | Với provider cloud, dữ liệu rời khỏi máy và chịu chính sách của provider đó. Ollama/LM Studio trên loopback xử lý cục bộ. |
| Cache AI, import history, reports và logs | Thư mục dữ liệu theo profile; cache có giới hạn tuổi/dung lượng và có thể xóa từ ứng dụng | Các dữ liệu này có thể chứa nội dung học. Người dùng chịu trách nhiệm bảo vệ Anki profile/backup của mình. |
| Telemetry | Không có telemetry hay upload analytics của Bento Forge | Chỉ có token/chi phí tổng hợp cục bộ trong phiên. |

Không đưa API key, mật khẩu, số định danh hoặc nội dung nhạy cảm vào prompt hay
file tham khảo. Hãy xem kỹ chính sách lưu giữ dữ liệu của provider cloud trước
khi chọn provider đó.

## Threat model

| Bề mặt | Rủi ro | Giảm thiểu hiện có | Giới hạn/rủi ro còn lại |
|---|---|---|---|
| API key | Key bị lưu plaintext, lộ qua log hoặc commit | Lưu bằng OS credential store; filter log redacts `Authorization`, `api_key` và mẫu key; CI quét credential-shaped value trong source đã track | Key vẫn có thể bị lộ nếu OS/profile hoặc tài khoản provider bị compromise. Revoke key ngay tại provider. |
| Kết nối AI cloud | Nghe lén/chèn sửa lưu lượng | Certificate verification mặc định cho cloud provider | Người dùng có thể tự cấu hình endpoint không đáng tin; chỉ dùng endpoint HTTPS của provider tin cậy. |
| Kết nối local | TLS self-signed/local làm hỏng kết nối | Chỉ nới certificate verification cho allowlist endpoint local (`localhost`, `127.0.0.1`, `::1`, `0.0.0.0`) | Không cấu hình DNS/host lạ thành local endpoint; dịch vụ lắng nghe local vẫn thuộc trách nhiệm người dùng. |
| Nội dung AI và prompt injection | Văn bản tham khảo cố điều khiển mô hình, đưa ra thẻ sai hoặc câu trả lời không phù hợp | Prompt cố định schema; preview cho phép xem/sửa/xóa trước import; parser không thực thi nội dung AI | AI output là dữ liệu không tin cậy, không phải nguồn sự thật. Người dùng phải review nội dung trước khi import. |
| Cache/history/log | Lộ nội dung học qua filesystem hoặc diagnostic log | Dữ liệu nằm dưới Anki profile, cache bị giới hạn/prune; chính sách logger yêu cầu metadata thay vì prompt/card text và redaction bí mật | Người khác có quyền đọc profile/backup vẫn có thể đọc dữ liệu học. Xóa cache/history và bảo vệ tài khoản OS khi cần. |
| Dependency/supply chain | Dependency độc hại hoặc bản build bị chèn secret | Dependency dev được pin; CI chạy `pip-audit`, secret scan, test isolated và package smoke | Optional dependency do người dùng cài vẫn cần được lấy từ nguồn tin cậy và cập nhật có chủ đích. |
| Import vào collection | AI output gây dữ liệu sai hoặc thao tác import không mong muốn | Preview, cảnh báo structural completeness, kiểm tra trùng, và thao tác collection theo luồng Anki có Undo khi Anki hỗ trợ | Đây là rủi ro toàn vẹn dữ liệu, không phải xác minh ngữ nghĩa. Sao lưu collection trước import lớn. |

## Ngoài phạm vi

- Hệ điều hành, malware, add-on khác, extension trình duyệt hoặc người dùng có
  quyền truy cập vào Anki profile.
- Chính sách retention/training, availability hay bảo mật nội bộ của AI provider
  do người dùng chọn.
- Độ chính xác ngôn ngữ của mô hình AI; Bento Forge không phải công cụ xác minh
  học thuật.

## Báo cáo lỗ hổng

Không công khai API key, dữ liệu học, proof-of-concept có thể khai thác, hoặc
chi tiết lỗ hổng chưa vá trong issue/discussion công khai.

1. Dùng [GitHub private vulnerability reporting](https://github.com/DeliChese/Anki-Bento-Forge/security/advisories/new) nếu repository bật tính năng này.
2. Nếu không khả dụng, liên hệ maintainer qua kênh liên hệ của repository và ghi rõ `SECURITY` trong tiêu đề.
3. Cung cấp bản Bento Forge/Anki/OS, các bước tái hiện tối thiểu, tác động dự kiến
   và cách liên hệ an toàn. Hãy loại bỏ secret và nội dung học thật khỏi báo cáo.

Maintainer sẽ xác nhận, đánh giá phạm vi, phối hợp bản vá và công bố thông tin
cần thiết sau khi người dùng có cơ hội cập nhật. Không có SLA bảo mật được cam
kết trong tài liệu này.

## Quy tắc cho maintainer và contributor

- Không commit `utils/ai_config.json`, API key, prompt/card text riêng tư, cache,
  import history hay log profile.
- Không thêm cơ chế tự cài dependency tại runtime.
- Không nới TLS cho endpoint cloud; ngoại lệ certificate chỉ được áp dụng cho
  allowlist endpoint local trong HTTP client.
- Thay đổi luồng dữ liệu, persistence, HTTP hoặc credential phải cập nhật tài
  liệu này, có test phù hợp và được review trước phát hành.
- Trước release, chạy isolated tests, kiểm tra package sạch và xử lý phát hiện
  nghiêm trọng từ dependency audit/secret scan.
