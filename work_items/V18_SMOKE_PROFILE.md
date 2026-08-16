# V18 Learning Modes — Smoke trên profile Anki 26.5 tách biệt

> **Dormant beta:** Không chạy checklist này như release gate hiện tại. Knowledge đã tắt khỏi giao diện để tập trung Language; chỉ dùng lại khi chủ dự án chủ động bật beta.

Chỉ chạy checklist này trên **profile Anki 26.5 mới hoặc bản sao đã backup**.
Không dùng profile học chính. Đây là gate GUI bổ sung cho smoke headless đã đạt;
test mock/headless không thay thế thao tác thật trong Anki.

## Bằng chứng tự động đã đạt

- [x] Anki 26.5 / Python 3.13.5 import được entry point, UI, public hooks,
  `QueryOp` và `CollectionOp`.
- [x] `scripts/smoke_anki_26_5.py` tạo collection tạm bằng backend thật và xác
  nhận Knowledge Basic/Cloze sinh card, add/update hoạt động, rollback chỉ xóa
  note mới và khôi phục note đã update (2026-08-16).
- [x] Luồng lưu dùng `Collection.update_note()` trên Anki hiện tại và chỉ fallback
  `Note.flush()` cho runtime legacy/test double.

## Thông tin phiên chạy GUI

- Ngày: `____-__-__`
- Người xác nhận: `________`
- Anki: `26.5` (Help → About)
- Profile mới/bản sao: `________`
- Artifact SHA-256: `________`

## Language không regression

- [ ] Tools → Bento Forge mở dialog không có lỗi add-on.
- [ ] Mở deck chỉ có note Language: không tự tạo/migrate Knowledge model hay note.
- [ ] Language → Knowledge → Language giữ đúng deck, draft chưa gửi và subtype Vocab/Grammar.
- [ ] Language Vocab/Grammar preview, import và update được; Anki Undo đảo đúng batch vừa làm.
- [ ] TTS Language tạo audio; cancel/offline có thông báo và không để media/note hỏng.
- [ ] Reviewer Combo mở được; mode sync, letter-gap và speed control hoạt động.

## Knowledge end-to-end

- [ ] Chọn Knowledge; control ngôn ngữ, level, TTS và `Batch Từ Vựng` được ẩn/tắt; AI Extract vẫn nhận nhiều Knowledge card qua schema riêng.
- [ ] Knowledge hiển thị nút `GỬI & TẠO THẺ`; nhập nguồn học và `Yêu cầu thêm`, bấm nút để mở preview Knowledge (không dùng AI Chat/Vocabulary của Language).
- [ ] JSON Basic thiếu `source` preview hợp lệ và Source để trống.
- [ ] JSON Cloze hợp lệ preview/import đúng Knowledge model và tạo card Cloze.
- [ ] JSON thiếu Question/Answer, cloze sai hoặc có field lạ chặn toàn batch, không sinh note partial.
- [ ] AI extract → preview → sửa → import thành công; Stop rồi Retry hoạt động.
- [ ] Trùng Question/Concept trong cùng deck được nhận diện; deck khác không bị quét chéo.
- [ ] Batch gồm add + update; Undo khôi phục update, xóa đúng add và không đổi note Language.
- [ ] History lọc Knowledge/re-import được; history Language cũ vẫn hoạt động.

## Kết luận

- [ ] Đạt toàn bộ.
- [ ] Không đạt — issue/log đã che dữ liệu nhạy cảm: `________`

Sau khi đạt, cập nhật `RELEASE_CHECKLIST.md` với ngày/người xác nhận. CI xanh và
GUI smoke endpoint là điều kiện riêng trước khi bump `manifest.json` lên `18.0.0`.
