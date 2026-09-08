# P0-02 — Manual Anki Smoke Checklist

> Status: active; current tree needs re-smoke
> Authority: owner-operated evidence for `RELEASE_CHECKLIST.md`
> Last verified: 2026-09-08

Chỉ chạy trên profile Anki đã backup. Không đánh dấu `PASS` từ test mock/headless hoặc từ kết quả của tree cũ.

## Phạm vi và an toàn

- Add-on/version lấy từ `manifest.json`; target chính hiện tại là Anki `26.5`.
- Endpoint `2.1.50` là smoke tương thích riêng trước release.
- Ghi số note/media trước và sau; dùng 1–2 note dễ nhận diện và không ghi dữ liệu học nhạy cảm vào repo.
- Lượt kiểm tra Reviewer đầu chỉ quan sát render/action; không rating hoặc mutation cho tới khi đúng card/deck được xác nhận.
- Không chạy Bulk Card Upgrade trên collection chính. Khi test mutation, dùng deck nhỏ trong profile bản sao và kiểm tra Undo.

## Thông tin lần chạy mới

| Trường | Giá trị |
| --- | --- |
| Ngày/giờ | Chưa chạy |
| Anki / hệ điều hành | Chưa ghi |
| Profile backup | Chủ dự án xác nhận; không ghi đường dẫn nhạy cảm |
| Deck/tag thử nghiệm | Chưa ghi |
| Version add-on | `18.3.0` |
| Kết quả tổng | `PENDING` |

## Preflight

- [ ] Backup collection, media và config đã hoàn tất.
- [ ] Mở **Tools → 🧪 Bento Forge** hoặc `Ctrl+Shift+I` không lỗi.
- [ ] Ghi baseline note/media của deck thử nghiệm.
- [ ] Xác nhận Knowledge selector, AI Study Sessions, Inventory và Blueprint không xuất hiện.

## Flow bắt buộc

| Flow | Quan sát bắt buộc | Kết quả |
| --- | --- | --- |
| Factory | Chọn Nhật/Trung/Hàn/Anh và Vocab/Grammar/Collocation; state không lẫn flow | PENDING |
| AI → Preview | Chạy nguồn nhỏ và Chat tạo thẻ; output đúng ngôn ngữ/mode, Preview cho sửa/xóa | PENDING |
| Import/update | Add đúng note, update không nhân bản, lỗi từng mục rõ ràng | PENDING |
| Undo/safety | Undo khôi phục đúng note; dữ liệu/SRS ngoài phạm vi không đổi | PENDING |
| TTS | Online/offline/cancel, stored media và tốc độ phát hoạt động đúng | PENDING |
| Combo/Independent | Combo đổi năm bài tập trong một card; Independent có lịch riêng và migration có checkpoint | PENDING |
| Reviewer lifecycle | `Tự đặt câu`, `Nâng cấp thẻ`, Ví dụ 1–4 bám đúng card khi lật/đổi nhiều thẻ/deck | PENDING |
| Bulk upgrade | Báo số request, chỉ xử lý note cũ/thiếu, lỗi riêng không dừng lô, Undo/SRS đúng | PENDING |
| Chinese Radical | Trigger toàn từ, panel/close/Escape/mobile fallback và typography không đổi | PENDING |
| LTS V14–V18 | Chỉ field/template Bento được cập nhật; field/template/card/media/SRS lạ được giữ | PENDING |
| Restart | Config/draft hợp lệ, note/media thử nghiệm nhất quán sau khi mở lại Anki | PENDING |

## Nhật ký lỗi lần chạy mới

| Thời điểm | Flow | Mong đợi | Thực tế | Evidence | Quyết định |
| --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — |

## Bằng chứng lịch sử

Lần smoke 2026-08-26 trên Anki 26.5/profile backup chỉ đạt một phần: Factory và Combo render được, nhưng action Reviewer không bám đúng card `看`. AI Study Sessions khi đó còn tồn tại. Current tree đã retire Study Sessions và đã sửa lifecycle action bằng card ID, cleanup DOM cũ cùng delayed retry; vì vậy kết quả cũ không còn là blocker đã xác minh và không thay thế re-smoke hiện tại.

## Quy tắc kết thúc

- `PASS`: mọi flow bắt buộc đạt, note/media/config/SRS ngoài phạm vi không đổi.
- `FAIL`: mất dữ liệu, duplicate ngoài dự kiến, Undo sai hoặc lỗi chặn flow.
- `BLOCKED`: backup/target không hợp lệ hoặc một flow không thể chạy; không coi là pass.

Sau khi chủ dự án chạy xong, cập nhật evidence tại đây, `PERSONAL_ROADMAP.md`, `.claude/context/current-state.md` và record trong `RELEASE_CHECKLIST.md`.
