---
name: learning-modes
description: Triển khai V18 Learning Mode Language/Knowledge mà không phá note type, import, history hay flow ngôn ngữ hiện hữu.
---

# SKILL-13: LEARNING MODES (V18)

## Khi nào dùng

- Làm bất kỳ lát cắt `V18-01` đến `V18-06` trong `work_items/V18_LEARNING_MODES.md`.
- Sửa contract chuyển `language` / `knowledge`, schema Knowledge, model/template, UI mode selector hoặc workflow của Knowledge.

## Luật không được vi phạm

1. `language` và `knowledge` dùng note type riêng. Không thêm field Knowledge vào Language model và không migration note cũ một cách ngầm định.
2. Mode do người dùng chọn, lưu theo deck; AI không suy đoán mode từ input.
3. `vocab`/`grammar` là subtype của `language`, không phải đối thủ của `knowledge`.
4. Prompt, parser và validation Knowledge tách khỏi Language. Sửa prompt phải tăng phiên bản cache đúng boundary.
5. Cùng profile phải chuyển mode an toàn: không mất input chưa gửi, không đổi deck hiện tại, không lẫn history/duplicate scan.
6. Tất cả UI strings đi qua `t()`, log qua `get_logger()`, collection/media chỉ đi qua Anki operation phù hợp.
7. Không nâng version/changelog phát hành trước V18-06 có test và smoke trên profile backup.

## Source map cần đọc theo lát cắt

| Lát cắt | Đọc trước khi sửa | Boundary cần giữ |
| --- | --- | --- |
| V18-01 | `ui/factory_dialog.py:165-323`, `utils/user_data.py`, `utils/deck_cache.py` | State flow hiện theo `(lang, vocab|grammar)`; chuyển sang key mode rõ ràng và migration đọc được state cũ |
| V18-02 | `utils/ai_prompt_defaults.py`, `utils/ai_response_parser.py`, `utils/prompt_config.py`, `utils/ai_extractor.py` prompt version | Schema/validator Knowledge thuần Python, không import `aqt` |
| V18-03 | `Language/*.py`, `utils/model_lifecycle.py`, `mode/card_render.py`, `mode/templates.py`, `mode/css.py`, `ui/factory_dialog.py:2312-2360` | Tạo model idempotent, không rename/prune template Language |
| V18-04 | `ui/factory_dialog.py:397-848`, `ui/factory_dialog.py:1037-1111`, `ui/factory_dialog.py:1233-1308`, `utils/i18n.py` | UI selector và placeholder không hardcode; lưu input riêng theo mode |
| V18-05 | `ui/factory_dialog.py:1631-2255`, `ui/factory_dialog.py:2540-2986`, `ui/ai_preview.py`, `workers/ai_workers.py`, `workers/import_worker.py`, `utils/import_history.py` | Preview → import/update → undo/history; không dùng worker thread để gọi Collection trực tiếp |
| V18-06 | `manifest.json`, `CHANGELOG.md`, `RELEASE_CHECKLIST.md`, `scripts/test_isolated.ps1`, tests liên quan | Metadata chỉ phản ánh bằng chứng; chạy harness hai lần và smoke thủ công |

## Quy trình một lát cắt

1. Mở đúng một ID trong `V18_LEARNING_MODES.md`, đọc các file/dòng tương ứng ở bảng trên.
2. Nêu mode contract, file sẽ sửa, dữ liệu cũ phải giữ và acceptance criteria trước khi đổi mã.
3. Viết test cho boundary mới trước hoặc cùng thay đổi.
4. Chạy test hẹp; sau đó chạy harness theo skill testing nếu lát cắt sửa code phát hành được.
5. Cập nhật bảng **Lịch sử đợt cập nhật V18**: trạng thái, files/test đã chạy, rủi ro, ID kế tiếp.
6. Không mở lát cắt tiếp theo khi test hiện tại đỏ hoặc state/model migration chưa rõ.

## Kiểm chứng tối thiểu theo mode

| Tình huống | Kỳ vọng |
| --- | --- |
| Mở collection chỉ có note Language cũ | Không tạo/migrate/đổi template cho đến khi người dùng chọn import Knowledge |
| Chuyển Language → Knowledge → Language | Input và selector mỗi mode khôi phục đúng; deck không đổi ngoài lựa chọn chủ động |
| AI trả JSON Knowledge thiếu trường bắt buộc | Preview báo lỗi rõ; không import partial note |
| Hai note cùng khái niệm ở hai mode | Không bị xem là duplicate chéo model nếu người dùng không chọn policy đó |
| Undo Knowledge import | Chỉ đảo thao tác Knowledge vừa làm; không làm ảnh hưởng note Language |

## Handoff bắt buộc

```text
Thực hiện work_items/V18_LEARNING_MODES.md / <V18-0X>.
Đọc AGENTS.md, .Codex/AGENTS.md và SKILL-13 trước. Chỉ làm lát cắt này.
Nêu contract/state cũ cần giữ, file dự kiến sửa và acceptance criteria.
Sau khi sửa, chạy test liên quan, cập nhật bảng Lịch sử V18 với bằng chứng.
Không nâng version hoặc đánh dấu release trước V18-06.
```
