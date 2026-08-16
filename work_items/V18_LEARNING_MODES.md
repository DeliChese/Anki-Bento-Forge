# V18 — Learning Modes: Language và Knowledge

**Trạng thái:** `Triển khai hoàn tất, chờ release gate ngoài local` — V18-01…05 hoàn thành; V18-06 đã đạt compatibility audit/headless smoke Anki 26.5 và build local, nhưng còn GUI smoke, CI và kiểm chứng endpoint legacy 2.1.50 trước khi bump `18.0.0`.

**Mục tiêu:** Bento Forge trở thành công cụ đúc thẻ học chung, bắt đầu bằng hai mode chuyển đổi rõ ràng:

- `language`: giữ nguyên flow từ vựng/ngữ pháp, ngôn ngữ, ví dụ, phát âm và TTS hiện có.
- `knowledge`: tạo thẻ kiến thức chuyên ngành từ tài liệu hoặc ghi chú, V1 hỗ trợ Q&A, cloze và nguồn tham khảo.

## Quyết định phạm vi V18

1. `Learning Mode` là lớp sản phẩm trên `vocab/grammar`; không đổi ý nghĩa các note type ngôn ngữ đã tạo.
2. Người dùng chọn mode rõ ràng; AI không tự đoán mode. Mỗi deck lưu mode mặc định, nhưng người dùng có thể đổi trước khi tạo thẻ.
3. Lõi chung vẫn là: nhập → AI extract → preview/chỉnh sửa → kiểm tra trùng → import/update → undo → history.
4. `knowledge` V1 không bắt buộc TTS. TTS/voice chỉ là tùy chọn sau này, vì không phải mọi kiến thức chuyên ngành cần âm thanh.
5. V18 không bao gồm AwesomeTTS. [P1-04_AWESOMETTS_SAFE_BATCH.md](P1-04_AWESOMETTS_SAFE_BATCH.md) vẫn là kế hoạch độc lập, có thể vào V18.x hoặc milestone sau khi V18 ổn định.
6. Không đổi version trong `manifest.json`, compatibility matrix hoặc `CHANGELOG.md` cho đến lát cắt V18-06 có bằng chứng test/smoke đầy đủ.

## Contract sản phẩm V1

| Thành phần | `language` | `knowledge` |
| --- | --- | --- |
| Kiểu nội dung | từ vựng, ngữ pháp | khái niệm, cơ chế, quy trình, công thức |
| Card V1 | note type hiện có, không migration bắt buộc | note type mới riêng, không tái dùng model ngôn ngữ |
| Dạng thẻ | vocab/grammar và layout review hiện có | Basic Q&A, Cloze, kèm Explanation và Source |
| Prompt/schema | giữ contract hiện có theo `lang` | schema riêng, không có field đọc/phát âm bắt buộc |
| TTS | có thể bật theo các field hiện hữu | tắt mặc định, không tạo audio tự động |
| Duplicate key | theo front/word + model hiện hữu | `Question`/`Concept` chuẩn hóa trong đúng model+deck |
| History | giữ `lang`, kind vocab/grammar | thêm mode/kind knowledge, không làm hỏng lịch sử cũ |

### Schema tối thiểu cho `knowledge`

```json
{
  "type": "basic | cloze",
  "question": "...",
  "answer": "...",
  "explanation": "...",
  "source": "...",
  "tags": ["..."],
  "cloze_text": "..."
}
```

- Với `basic`, bắt buộc `question` và `answer`.
- Với `cloze`, bắt buộc `cloze_text` có cloze hợp lệ; không dùng AI để tự bịa nguồn.
- `source` hiển thị ở preview; nếu nội dung đầu vào không có nguồn, ghi rõ là trống/không xác định thay vì tạo citation giả.

## Lát cắt triển khai

| Thứ tự | ID | Phạm vi đóng | Model / effort | Hoàn tất khi |
| --- | --- | --- | --- | --- |
| 1 | V18-01 | Tạo contract `learning_mode` thuần, registry mode, persistence mặc định theo deck và compatibility state cũ | `gpt-5.6-terra` / `high` | Unit test cho default/mode switch/persistence; Language flow cũ giữ nguyên |
| 2 | V18-02 | Prompt, schema parser và validation riêng cho Knowledge Q&A/Cloze; không đổi prompt Language | `gpt-5.6-sol` / `high` | Corpus fixture có valid/invalid/source-missing; parser không chấp nhận cấu trúc mơ hồ |
| 3 | V18-03 | Knowledge model lifecycle, fields, templates/CSS và import/duplicate boundary | `gpt-5.6-sol` / `high` | Note type Knowledge mới tạo idempotent; deck/ngôn ngữ cũ không bị migration/ghi đè |
| 4 | V18-04 | UI selector Learning Mode, nội dung/placeholder/preview khác nhau và i18n | `gpt-5.6-terra` / `high` | Đổi mode không mất input; UI không hiển thị control Language không phù hợp trong Knowledge |
| 5 | V18-05 | Nối AI extract, batch, preview, history/undo với Knowledge và duplicate scan theo model mới | `gpt-5.6-sol` / `high` | Cancel/retry/preview/import/update/undo có regression test theo Knowledge |
| 6 | V18-06 | Kiểm thử release, migration/compatibility audit, tài liệu người dùng và nâng version V18 | `gpt-5.6-terra` / `high` + chủ dự án smoke thủ công | Hai vòng harness xanh, smoke profile backup cho cả hai mode, changelog + metadata chính xác |

Không dùng `gpt-5.6-luna` để sửa lifecycle/template/import/migration. Luna chỉ dùng `low` cho nhật ký, checklist và cập nhật tài liệu sau khi có kết quả đã kiểm chứng.

## Thứ tự và ranh giới kỹ thuật

```text
V18-01 mode contract
   ├── V18-02 schema/prompt ─┐
   └── V18-03 model/template ├── V18-04 UI ──> V18-05 workflow/history ──> V18-06 release
                              ┘
```

- Không chạy V18-03 và V18-04 song song vì cả hai cùng cần chốt field/UI contract.
- Không sửa note type Language để chứa field Knowledge. Model riêng là hàng rào chống migration phá dữ liệu.
- Mỗi lát cắt phải cập nhật chính file này bằng trạng thái, test đã chạy và rủi ro còn lại trước khi mở lát cắt kế tiếp.

## Acceptance checklist của milestone

- Cùng một profile có deck Language và Knowledge, chuyển qua lại mà không đổi note type/default deck của nhau.
- Language vocab/grammar, extract, preview, import/update, undo và TTS regression đều đạt.
- Knowledge tạo được Basic và Cloze từ JSON thủ công lẫn AI output đã preview; không import khi source/schema không hợp lệ theo policy.
- Không có prompt/schema/config bí mật trong history, log hoặc fixture.
- Version V18 chỉ được ghi vào manifest, release checklist và changelog tại V18-06, với bằng chứng tương ứng.

## Lịch sử đợt cập nhật V18

| Ngày | Lát cắt | Trạng thái | Thay đổi / bằng chứng | Rủi ro hoặc bước kế tiếp |
| --- | --- | --- | --- | --- |
| 2026-08-16 | Khởi tạo kế hoạch | `Đã lên kế hoạch` | Chốt hai mode, contract V1, thứ tự triển khai và model/effort | Bắt đầu V18-01; chưa có thay đổi mã hay version |
| 2026-08-16 | V18-01 | `Hoàn thành` | `utils/learning_mode.py`, `utils/factory_state.py`, `ui/factory_dialog.py`; focused pytest — 70 passed, full isolated harness — 504 passed | V18-02: tách prompt/schema/validation Knowledge; selector UI chưa có trước V18-04 |
| 2026-08-16 | V18-02 | `Hoàn thành` | `utils/knowledge_schema.py`, Knowledge defaults trong `utils/ai_prompt_defaults.py`, contract trong `utils/prompt_config.py`, corpus `tests/fixtures/knowledge_cards.json`; full isolated harness — 509 passed | V18-03: tạo lifecycle/model/template Knowledge idempotent; workflow AI/import chưa nối trước V18-05 |
| 2026-08-16 | V18-03 | `Hoàn thành` | `mode/knowledge.py`, `utils/knowledge_model.py`; model Knowledge Basic/Cloze idempotent, không migrate/prune Language, giữ template Knowledge do người dùng thêm; full isolated harness — 512 passed | V18-04: selector Learning Mode, placeholder/preview và i18n; chưa nối worker/import workflow |
| 2026-08-16 | V18-04 | `Hoàn thành` | Selector Learning Mode theo deck trong `ui/factory_dialog.py`, draft `knowledge/default` trong `utils/factory_state.py`, i18n VI/EN; giữ input riêng khi đổi mode, ẩn control Language/TTS/filter trong Knowledge và không tạo model/call workflow; full isolated harness — 515 passed | V18-05: nối extract, preview, duplicate scan, import/update/undo/history Knowledge |
| 2026-08-16 | V18-05 | `Hoàn thành` | `utils/knowledge_extractor.py`, `utils/knowledge_workflow.py`, Knowledge CollectionOp trong `utils/import_operations.py`, worker/preview/factory/history UI; strict AI/manual preview, duplicate đúng model+deck, TTS off, cancel rollback nguyên batch, add/update/history/undo; focused pytest — 54 passed, full isolated harness 2 vòng — 526 passed mỗi vòng | V18-06: audit compatibility/release metadata và smoke thủ công trên profile backup; chưa nâng version/changelog |
| 2026-08-16 | V18-06 | `Local hoàn tất · chờ GUI smoke/CI` | Mở manifest từ Anki 2.1.50 đến 26.5; Anki 26.5 đạt packaged manifest/runtime smoke; Knowledge ẩn Batch Vocabulary, hiển thị `GỬI & TẠO THẺ` cho pipeline schema riêng; isolated harness 2 vòng × 532 passed; artifact `8e2d0fc6…5ea0` | Còn GUI smoke 26.5 theo `V18_SMOKE_PROFILE.md`, CI Python 3.9/3.11 và smoke endpoint legacy 2.1.50 trước khi bump 18.0.0 |

## Mẫu ghi nhận mỗi đợt

```md
| YYYY-MM-DD | V18-0X | Hoàn thành | <files + tests/smoke đã chạy> | <rủi ro còn lại / V18-0Y> |
```

Chỉ ghi `Hoàn thành` khi có bằng chứng test; không đưa kế hoạch hoặc kết quả chưa kiểm chứng vào changelog phát hành.
