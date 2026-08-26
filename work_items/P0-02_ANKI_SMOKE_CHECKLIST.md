# P0-02 — Manual Anki Smoke Checklist

> Mục tiêu: xác nhận workflow cá nhân trên một profile Anki **đã sao lưu**. Đây là kiểm chứng thủ công; chỉ đánh dấu `PASS` khi thao tác trực tiếp trong Anki thật.

## Phạm vi và an toàn dữ liệu

- Add-on: Bento Forge `18.3.0` (theo `manifest.json`).
- Phiên bản Anki mục tiêu hiện tại: `26.5`; endpoint legacy `2.1.50` là smoke tương thích riêng trước phát hành (xem `manifest.json` và `COMPATIBILITY.md`). Nếu Anki thực tế ngoài khoảng hỗ trợ, ghi rõ phiên bản và dừng để triage.
- Dùng một profile bản sao hoặc profile đã backup đầy đủ (`collection.anki2`, thư mục `collection.media`, cấu hình profile). Ghi đường dẫn hoặc vị trí backup, không ghi dữ liệu nhạy cảm.
- Chỉ dùng 1–2 mục thử nghiệm có thể nhận diện được (ví dụ tag `bento-smoke-YYYYMMDD`); không chạy batch trên collection chính.
- Không xóa backup cho đến khi toàn bộ checklist có kết quả `PASS`.

## Nhật ký lần chạy

| Trường | Giá trị |
| --- | --- |
| Ngày / giờ | 2026-08-26 08:27–09:23 (UTC+07) |
| Phiên bản Anki (Help → About) | `26.5` (xác nhận từ installed package metadata `anki-26.5`) |
| Hệ điều hành | Windows NT `10.0.26200.0`, 64-bit |
| Profile / vị trí backup | `ChinD`; chủ dự án xác nhận profile đã backup, không ghi đường dẫn backup |
| Deck và tag thử nghiệm | `Tiếng Trung::Từ vựng`; chỉ xem card `看`, không tạo tag/note mới |
| Version add-on | 18.3.0 |
| Kết quả tổng | `BLOCKED` — preflight/Reviewer partial pass; action `Hỏi AI` và `Tự đặt câu` không được inject |

## Trước khi chạy

- [x] Đóng Anki và hoàn tất backup; mở lại đúng profile bản sao/đã backup.
- [x] Xác nhận Anki `26.5` nằm trong phạm vi hỗ trợ hiện hành; endpoint legacy `2.1.50` chưa chạy trong phiên này.
- [x] Mở **Tools → 🧪 Bento Forge** (hoặc `Ctrl+Shift+I`) không có lỗi khởi động.
- [ ] Chụp/ghi lại số note trong deck thử nghiệm và danh sách media liên quan trước thử nghiệm.

## Luồng bắt buộc

| Flow | Các bước quan sát | Kết quả | Bằng chứng / ghi chú |
| --- | --- | --- | --- |
| Factory / Study Coach preflight | Mở Factory, kiểm production workbench; mở Study Coach trong/ngoài Reviewer và kiểm role split | PASS một phần | Factory theme tối hiển thị đủ `Nguồn | AI/Artifact | Kiểm định/Import`; composer có checkbox tạo thẻ + Gửi. Trong Reviewer, Study Coach nhận `REVIEWER · QA · Mặt câu hỏi · Thẻ chính: 看`, quick actions/context/library hiện đủ. Ngoài Reviewer, menu chỉ hiện thông báo đúng boundary, không mở standalone surface. |
| Extract | Nhập một mục thử nghiệm → chạy AI extract → dữ liệu trả về đúng ngôn ngữ và không có lỗi UI | Chưa chạy |  |
| Preview / chỉnh sửa | Mở preview → sửa một field nhận diện được → xác nhận nội dung sửa vẫn còn trước khi import | Chưa chạy |  |
| Import (add) | Import note mới vào deck thử nghiệm → mở Browser và xác nhận đúng 1 note, field/tag/template mong đợi | Chưa chạy |  |
| Update | Chạy lại cùng mục với thay đổi nhận diện được → chọn update theo flow hiện có → xác nhận đúng note được cập nhật, không nhân bản | Chưa chạy |  |
| Undo | Dùng Undo của Anki ngay sau import/update → xác nhận note/field trở về trạng thái trước thao tác | Chưa chạy |  |
| TTS | Phát audio từ note thử nghiệm → xác nhận phát được và media xuất hiện/chỉ dùng media mong đợi; thử dừng nếu UI có nút dừng | Chưa chạy |  |
| Review | Học/review note thử nghiệm → kiểm tra render template, âm thanh và các mode đang dùng; chấm một lần → sync trạng thái review trong Browser | `BLOCKED` | Card `看` render đủ 5 combo modes; mặt sau có Usage Pattern/Usage Note/Collocation/ví dụ. Không thấy action `Hỏi AI` hoặc `Tự đặt câu` ở mặt hỏi dù card có Usage Pattern/Collocation. Chỉ mở mặt đáp án rồi thoát bằng Decks, không chọn rating. |

## Kiểm tra sau chạy

- [ ] Đối chiếu số note trước/sau: chỉ thay đổi đúng theo bước add/update/undo đã ghi.
- [ ] Đối chiếu media mới: chỉ có file TTS mong đợi, không có media bị mất.
- [ ] Đóng/mở lại Anki và xác nhận config Bento Forge còn đọc được, note và media thử nghiệm vẫn nhất quán.
- [ ] Nếu có lỗi: giữ nguyên backup, không thử tiếp trên collection chính; ghi stack trace, bước tái hiện tối thiểu và kết quả mong đợi/thực tế bên dưới.

## Triage lỗi

| Thời điểm | Flow | Kết quả mong đợi | Kết quả thực tế | Log / ảnh chụp | Quyết định |
| --- | --- | --- | --- | --- | --- |
| 2026-08-26 08:35–09:23 | Reviewer actions / Production Drill | Mặt hỏi có `Hỏi AI`; card có Usage Pattern/Collocation có thêm `Tự đặt câu`, gợi ý ẩn mặc định | Cả hai action vắng mặt trên card `看`; Study Coach vẫn mở đúng từ menu và nhận đúng context | UI Automation + quan sát trực tiếp Anki 26.5; log hiện hành không có hook exception | Dừng smoke mutation; mở bug hook injection trước khi chạy tiếp P0-02/P2-03 |

## Quy tắc kết thúc

- `PASS`: tất cả flow bắt buộc và kiểm tra sau chạy đạt; không mất note, media hay config.
- `FAIL`: có mất dữ liệu, duplicate ngoài dự kiến, undo không khôi phục đúng, hoặc lỗi chặn flow.
- `BLOCKED`: phiên bản Anki ngoài phạm vi, backup chưa xác nhận, hoặc không thể chạy một flow; không coi là pass.

Khi hoàn thành, cập nhật bảng nhật ký, từng ô kết quả và thêm một mục `Personal / P0-02` vào `PERSONAL_ROADMAP.md`. Không đánh dấu release smoke trong `RELEASE_CHECKLIST.md` nếu checklist chưa có bằng chứng `PASS`.
