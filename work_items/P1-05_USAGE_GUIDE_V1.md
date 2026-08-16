# P1-05 — Usage Guide V1

## Contract

- Áp dụng cho vocab Nhật / Trung / Hàn / Anh; grammar và Knowledge không đổi.
- `Usage Pattern`: tối đa một khung tái dùng, đặc thù ngôn ngữ, không chép nguyên ví dụ.
- `Usage Note`: chỉ chứa sắc thái, register hoặc cảnh báo dùng sai có ích.
- `Collocation`: tối đa một cụm đúng nghĩa đang học, luôn có nghĩa sau dấu ` — `.
- Cả ba field là tùy chọn, tự ẩn khi trống và chỉ xuất hiện ở mặt sau; V1 không tạo card/lịch SRS mới.

## Rubric review

Mỗi mục đạt khi pattern dùng đúng particle/preposition/complement của ngôn ngữ, note không phát biểu chung chung, collocation tự nhiên và đúng sense, ba nội dung không lặp nhau hoặc lặp hai ví dụ. Ngưỡng phát hành là ít nhất 18/20 mục đạt toàn bộ rubric (90%).

Corpus tham chiếu cố định nằm tại `benchmarks/usage_guide_v1.json`: 5 mục/ngôn ngữ, ưu tiên các boundary người học dễ sai. Corpus này dùng cho review thủ công và regression cấu trúc; không được xem là kết quả benchmark model trực tuyến.

Bốn case thực thi `usage_guide_{language}_5_v1.json` được sinh cố định từ cùng corpus và giữ nghĩa đích để model không tự chọn sense khác. Model gate là `deepseek-v4-flash@disabled` đã được P1-01 chọn. Ngưỡng vận hành cho vòng 20 mục: tổng chi phí không quá `$0.005`, trung bình không quá `3 giây/card`; chất lượng vẫn ưu tiên và phải đạt ít nhất 18/20 mục theo toàn bộ rubric.

## Migration

`all_fields` và `json_field_map` của bốn note type vocab là nguồn migration. Model lifecycle chỉ thêm field còn thiếu, đồng bộ lại template hiện có và giữ nguyên note/card/SRS cũ. Chạy lại migration không thêm field hoặc card trùng.

## Kết quả gate

- Benchmark model thật đạt `19/20` (`95%`), coverage/factory-ready `20/20`, tổng chi phí final `$0.002035` và trung bình `1.69 giây/card`. Bằng chứng chấm nằm tại `benchmarks/usage_guide_review_v1.json` và `benchmarks/USAGE_GUIDE_QUALITY.md`.
- Regression xác nhận preview giữ ba cột có thể sửa, normalizer bỏ placeholder/lặp/collocation không hợp lệ và migration chạy lặp không tăng field/template/card.
- Compile toàn bộ Python tracked xanh; hai vòng full suite dùng data root tách biệt đều đạt `547 passed`.
- Smoke bằng Python đi kèm Anki `26.5` trên collection tạm xác nhận đủ bốn ngôn ngữ: migration model, import, update, native undo, rollback đúng note, một card mặc định và Usage Guide chỉ render ở mặt sau. Lệnh: `.venv/Scripts/python.exe scripts/smoke_anki_26_5.py` từ thư mục cài Anki.
- P1-05 đủ gate để mở P1-06. Smoke trực quan toàn flow trên bản sao profile cá nhân vẫn thuộc P0-02 và là gate trước merge/release, không còn là điều kiện mở task kế tiếp.
