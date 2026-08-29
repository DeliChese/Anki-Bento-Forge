# AI Deck Blueprint — Kế hoạch triển khai

> Status: card-import slice locally implemented; GUI smoke pending
> Authority: supporting; `PERSONAL_ROADMAP.md` vẫn là backlog chuẩn  
> Opened: 2026-08-29  
> Owner: Bento Forge personal workflow

## Mục tiêu

Tạo một cửa sổ **AI Deck Blueprint** được mở từ điểm vào **Deck Center** duy nhất
trong Forge. Người dùng có thể quản lý deck hiện hữu hoặc dán danh sách từ vựng
có H1–H6, xem outline, yêu cầu AI đề xuất cây `Parent::Sub`, sửa trực tiếp và
chỉ ghi vào Anki sau khi duyệt.

Kết quả quan sát được:

1. Source editor mặc định gọn, có nút mở rộng/thu gọn.
2. Khi mở từ Deck Center trong Forge, source editor nhận snapshot văn bản/file đã nạp
   và ngôn ngữ hiện tại; không yêu cầu dán lại và không đồng bộ ngược.
3. Heading HTML `<h1>`…`<h6>`, Markdown `#`…`######` và nhãn văn bản
   `H1:`…`H6:` được chuẩn hóa thành section path.
4. AI nhận từng từ cùng đường dẫn section thay vì một danh sách phẳng.
5. Cây đề xuất cho phép đổi tên, thêm/xóa và kéo thả trước khi lưu.
6. Lưu chỉ tạo đúng các deck đã duyệt; không đổi tên hoặc xóa deck hiện hữu.

## Không làm

- Không chèn thêm panel/cây vào Forge Workshop hiện tại.
- Không biến nguyên H1–H6 thành cây Anki sáu tầng; H4–H6 chủ yếu là ngữ cảnh.
- Không tự động xóa, đổi tên hoặc di chuyển deck/note/SRS hiện hữu.
- Không coi heading là từ vựng.
- Không tự động import note trong lát cắt đầu tiên. Card import nhiều deck chỉ
  mở sau khi có duplicate review, undo token và smoke trên profile backup.
- Không thêm ngôn ngữ ngoài Nhật/Trung/Hàn/Anh.

## Nguồn đã đọc

- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`.
- `.claude/skills/11-upgrade-playbook/SKILL.md`.
- `utils/batch_processor.py:organize_decks_with_ai` và
  `create_decks_from_organization`.
- `workers/batch_workers.py:DeckOrganizerThread`.
- `ui/deck_manager_dialog.py:DeckManagerDialog`.
- `ui/factory_dialog.py:_register_tools_menu_action`.

## Bất biến và rủi ro

- Parser/normalizer là domain thuần, không import `aqt`.
- Network AI chạy ngoài UI thread; collection mutation chạy qua Anki operation.
- Mỗi từ chỉ thuộc tối đa một sub-deck trong blueprint hợp lệ.
- Tên deck được trim, loại `::` trong từng segment và bỏ node rỗng/trùng.
- Rich-text clipboard có thể mất heading; Markdown và `Hn:` là fallback rõ ràng.
- Nếu AI lỗi, fallback phải bám source section/topic và không crash dialog.
- Prompt thay đổi phải bump prompt version/cache contract.
- Worktree đã có thay đổi multi-select Deck Manager; tính năng này không được
  ghi đè hoặc đảo ngược chúng.

## Thiết kế dữ liệu

### Source section

```json
{
  "id": "section-3",
  "level": 3,
  "title": "Check-in",
  "path": ["Japanese Travel", "Airport", "Check-in"],
  "content": "搭乗券\n預け荷物",
  "word_count": 2
}
```

### Deck blueprint

```json
{
  "suggestion": "Bám cấu trúc nguồn và gộp các mục nhỏ",
  "decks": [
    {
      "parent": "Japanese Travel",
      "sub_decks": [
        {
          "name": "Airport & Check-in",
          "description": "Từ ở các section Airport/Check-in",
          "word_count": 24,
          "words": ["搭乗券", "預け荷物"]
        }
      ]
    }
  ]
}
```

## Kế hoạch từng bước

### Bước 1 — Parser và outline thuần

- Parse HTML heading, Markdown heading và `Hn:`.
- Giữ preamble trong section mức 1 tổng quát.
- Xây stack heading để sinh `path` chính xác khi level nhảy cóc.
- Tách nội dung khỏi heading và lập lookup từ → source path.
- Test Unicode Nhật/Trung/Hàn/Anh, heading trùng, section rỗng và source phẳng.

### Bước 2 — Blueprint contract và AI orchestration

- Mở rộng organizer để nhận `source_sections` và `custom_instruction` tùy chọn.
- Gửi outline bounded cùng source path trên từng word summary.
- Yêu cầu AI ưu tiên H1–H3, chỉ dùng H4–H6 làm context nếu nhóm quá nhỏ.
- Chuẩn hóa output: tên hợp lệ, bỏ trùng từ, tính lại count, giữ từ chưa được
  gán trong một nhánh fallback có thể nhìn thấy.
- Fallback theo section path/topic khi API/parser lỗi.

### Bước 3 — Worker độc lập

- Worker nhận source plain text + HTML, ngôn ngữ và instruction.
- Parse source → enrich batch → gắn section context → organize blueprint.
- Có progress, cancel và error signal; không đụng collection.

### Bước 4 — Cửa sổ AI Deck Blueprint

- Source editor cao khoảng 130–150 px, nút Mở rộng/Thu gọn.
- Outline preview nhỏ xác nhận H1–H6 đã đọc đúng.
- Tree chiếm phần lớn diện tích; item editable và drag/drop nội bộ.
- Nút thêm parent/sub, xóa nhánh, tạo lại và xem từ của nhánh.
- Nút Lưu cây deck tách khỏi Tạo lại bằng AI.

### Bước 5 — Mutation an toàn và Deck Center

- Dùng nút quản lý deck sẵn có trong Forge làm điểm vào Deck Center.
- Deck Center mở cả quản lý deck và AI Blueprint; không thêm action Blueprint rời ở Tools.
- Trước lưu: hiển thị danh sách deck mới/trùng và yêu cầu xác nhận.
- Collection operation chỉ gọi `decks.id()` cho tên đã duyệt.
- Deck trùng được tái sử dụng; không rename/delete/move bất kỳ deck cũ nào.

### Bước 6 — Card import nhiều deck (gate sau)

- [x] Tái dùng schema validation và chuẩn duplicate Unicode/punctuation của Factory;
  scan toàn note type để đổi target deck không trở thành cách lách duplicate.
- [x] Preview tổng add/duplicate/conflict/invalid/unassigned trước mutation; lát cắt này
  fail-closed, chỉ phát `add`, không update note cũ và chưa tạo audio.
- [x] Re-check collection ngay trong một CollectionOp để đóng khe đua sau preview;
  giữ exact added note IDs và có nút rollback đúng batch vừa nhập.
- [ ] Smoke trên profile backup: import vào ít nhất hai sub-deck, thử duplicate/conflict,
  undo batch và restart. Chưa coi là verified/release-ready trước gate này.

## Acceptance criteria

- [x] Parser giữ đúng path cho H1–H6 ở HTML, Markdown và plain marker.
- [x] Heading không lọt vào danh sách vocab.
- [x] Word summary gửi AI có source path và instruction người dùng.
- [x] Output AI sai/trùng được normalize hoặc fallback hữu hạn.
- [x] Source editor mặc định gọn và mở rộng được.
- [x] Nguồn học liệu đang dán/nạp file trong Forge được chuyển vào Blueprint bằng
  snapshot khi mở Deck Center; nguồn rỗng và entry ngoài Factory vẫn an toàn.
- [x] Cây proposal sửa được trước khi lưu.
- [x] Không có mutation trước confirmation.
- [x] Lưu chỉ tạo parent/sub deck; deck hiện hữu không bị đổi/xóa.
- [x] Một điểm vào Deck Center trong Forge; menu Tools không có action Blueprint rời.
- [x] Import nhiều deck chỉ thêm note mới sau preview; duplicate/conflict/invalid fail-closed.
- [x] Final re-check chạy trong CollectionOp và rollback chỉ nhận note ID vừa thêm.
- [x] Đổi ngôn ngữ sau khi sinh cây chặn import cho tới khi tạo lại Blueprint.
- [x] Targeted tests và `tests/test_release_metadata.py` xanh.
- [x] Full isolated suite xanh trước khi báo sẵn sàng release.
- [x] GUI smoke Anki/profile backup còn được ghi rõ nếu chưa chạy.

## Handoff / kết quả

- Quyết định: một nút Deck Center trong Forge gom quản lý deck + Blueprint; parser quyết định cấu trúc, AI tổ chức/gộp/đề xuất. Lưu cây vẫn create/reuse-only; import riêng là add-only, không audio/update.
- Files đã đổi: thêm `utils/deck_blueprint_import.py`; mở rộng contract/scan/re-check ở `utils/deck_blueprint.py`, UI Blueprint, i18n, tests và tài liệu trạng thái/changelog.
- Kiểm chứng: `py_compile` sạch; gate source-transfer/Deck Center/UI/i18n `97 passed`;
  full isolated suite cuối sau lát cắt dùng lại nguồn `831 passed`.
- Còn lại / blocker: GUI smoke paste rich text/drag-edit/save, import ít nhất hai sub-deck, duplicate/conflict, undo và restart trên Anki 26.5 profile backup.
