# Bento Forge — Quality Roadmap

> Tài liệu sống và **nguồn kế hoạch duy nhất** cho các cải thiện chất lượng Bento Forge.
> Không dùng `CODE_MAP.md` hay `UPGRADE_GUIDE.md` để quyết định công việc mới; cấu trúc mã nguồn chuẩn vẫn là `.claude/`.

**Cập nhật gần nhất:** 2026-08-13

**Trạng thái chung:** Phase 0–2 hoàn thành; Phase 3 chưa bắt đầu.
**Nguyên tắc:** bảo toàn dữ liệu Anki và dữ liệu cá nhân quan trọng hơn thêm tính năng.

## Quy tắc duy trì bắt buộc

Mỗi phiên làm việc có động đến chất lượng, dữ liệu, worker, AI, TTS, test hoặc tương thích Anki phải cập nhật chính file này.

1. Trước khi sửa: chuyển đúng hạng mục sang `Đang làm`, ghi ngày và phạm vi thay đổi.
2. Sau khi sửa: ghi kết quả, test đã chạy, rủi ro còn lại và chuyển sang `Hoàn thành` chỉ khi đạt tiêu chí hoàn tất.
3. Khi phát hiện rủi ro mới: thêm vào phase phù hợp; không tạo roadmap Markdown thứ hai.
4. Không ghi API key, nội dung học, đường dẫn cá nhân, hay log chứa dữ liệu riêng tư.
5. Nếu ưu tiên thay đổi, giữ lại quyết định cũ ngắn gọn trong **Nhật ký thay đổi** thay vì xóa mất bối cảnh.

| Ký hiệu | Ý nghĩa |
| --- | --- |
| `Chưa bắt đầu` | Chưa có thay đổi mã nguồn cho hạng mục. |
| `Đang làm` | Có một phiên đang triển khai; cần nêu owner/phạm vi. |
| `Bị chặn` | Cần quyết định, quyền truy cập, hoặc tái hiện lỗi. |
| `Hoàn thành` | Đạt đủ tiêu chí hoàn tất và đã ghi kiểm chứng. |

## Baseline đã biết

- Add-on v17.1.0; phạm vi Anki khai báo: 2.1.50–2.1.99.
- Lần đánh giá 2026-08-13 phát hiện test không cô lập hoàn toàn cấu hình i18n: `set_language()` ghi trực tiếp vào `utils/i18n_config.json`.
- Lần chạy `python -m pytest -q` trong sandbox: 271 pass, 20 fail, 57 error. Nhiều error liên quan quyền thư mục tạm; một số test i18n/template/prompt đang kỳ vọng nội dung cũ. Kết quả này là baseline cần tái hiện trong môi trường phát triển bình thường, không phải tiêu chí pass/fail cuối cùng.

---

## Phase 0 — Bảo toàn dữ liệu và làm test đáng tin

**Trạng thái:** `Hoàn thành`
**Mục tiêu:** Không để update, crash hoặc test làm mất/dơ dữ liệu cá nhân; có một test baseline tái lập được.

### Hạng mục

- [x] Chuyển API config, UI language, factory state, import history, prompt override và cache ra khỏi thư mục mã nguồn; dùng cơ chế config/user-data của Anki, có migration một lần.
- [x] Chuẩn hóa mọi ghi JSON quan trọng thành ghi atomic (`tmp` → replace), validation schema và backup tối thiểu trước migration.
- [x] Giới hạn dung lượng/lifetime của AI cache và factory state; không lưu không giới hạn raw text hoặc dữ liệu thẻ nhạy cảm.
- [x] Cô lập mọi test ghi file bằng `tmp_path`/monkeypatch dependency path; đặc biệt i18n không được ghi `utils/i18n_config.json` thật.
- [x] Sửa test cũ theo hành vi đã chấp nhận; không assert nguyên văn UI nếu chỉ copywriting thay đổi.
- [x] Thiết lập lệnh test một dòng dùng thư mục tạm được cấp quyền và kiểm tra worktree không đổi sau test.

### Tiêu chí hoàn tất

- Test không tạo/sửa/xóa bất cứ file persistent nào của người dùng hoặc file tracked.
- Có migration và rollback/backup được kiểm thử.
- `pytest` chạy lặp lại hai lần cho cùng kết quả, không để lại thay đổi worktree.
- Mọi test hiện hành pass trong phiên bản Python được CI hỗ trợ.

### 2026-08-13 — Phase 0 / Lưu trữ dữ liệu và test cô lập

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `utils/user_data.py`, persistence trong `utils/`, factory state, theme và test.
- Thay đổi: Dữ liệu người dùng chuyển sang thư mục profile Anki; JSON ghi atomic, có validation, migration một lần kèm backup/rollback. AI cache bị giới hạn 200 file/25 MiB và TTL; factory state có TTL 7 ngày cùng giới hạn text, JSON và số thẻ. Test dùng data-dir/basetemp riêng, không dùng pytest cache trong worktree.
- Kiểm chứng: `powershell -ExecutionPolicy Bypass -File scripts/test_isolated.ps1` → 354 passed, lặp lại 354 passed; script xác nhận worktree không đổi.
- Rủi ro còn lại / bước kế tiếp: Xác minh migration trên một profile Anki sao lưu trước khi phát hành; Phase 1 xử lý worker/Collection.

### 2026-08-13 — Phase 1 / Worker, hủy tác vụ và Collection

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `__init__.py`, `workers/`, `ui/batch_dialog.py`, `utils/anki_ops.py`, `utils/import_operations.py`, AI/batch/deck-cache và test.
- Thay đổi: Collection read dùng `QueryOp`; import và tạo deck dùng `CollectionOp`. Audio/AI/batch worker chỉ giữ network work. Cancellation dùng `threading.Event`, không còn `QThread.terminate()`, đồng thời retry/backoff có thể dừng và request có timeout tổng. Import báo note thêm/cập nhật, audio thành công/thất bại; undo-aware operation và rollback note mới vẫn khả dụng.
- Kiểm chứng: `powershell -ExecutionPolicy Bypass -File scripts/test_isolated.ps1` → 357 passed, lặp lại 357 passed; test bổ sung cover audio import, import bị hủy và backoff bị hủy.
- Rủi ro còn lại / bước kế tiếp: Kiểm tra thủ công trên profile Anki sao lưu để xác nhận UI/progress và undo của phiên bản Anki mục tiêu trước khi phát hành; tiếp tục Phase 2.

---

## Phase 1 — Worker, hủy tác vụ và an toàn Collection

**Trạng thái:** `Hoàn thành`
**Mục tiêu:** Không treo UI, không hủy thread cưỡng bức, không truy cập/ghi Anki Collection theo cách không được quản lý.

### Hạng mục

- [x] Thay các `QThread` tự quản lý đang đọc/ghi `mw.col` bằng Anki `QueryOp` cho đọc và `CollectionOp` cho thay đổi có undo.
- [x] Tách network-only operation khỏi Collection để có thể chạy song song đúng cách; mọi cập nhật Qt/UI quay lại main thread.
- [x] Thay `terminate()` và cờ boolean rời rạc bằng cancellation event xuyên suốt AI extract, chat, batch, retry và backoff.
- [x] Biến mọi khoảng chờ/retry thành có thể hủy; đặt timeout tổng và timeout mỗi request rõ ràng.
- [x] Gom import thành transaction/undo step có báo cáo chính xác: note mới, note cập nhật, audio thất bại và rollback an toàn.

### Tiêu chí hoàn tất

- Bấm Dừng phản hồi nhanh, không sinh callback/UI update muộn và không gọi `QThread.terminate()`.
- Import/update có undo hoặc rollback đã được test trên collection thử nghiệm.
- Không còn `mw.col` mutation trực tiếp trong worker tự tạo.
- Có test cho cancel khi đang request, retry và import có audio.

---

## Phase 2 — TTS, dependency và bí mật

**Trạng thái:** `Hoàn thành`
**Mục tiêu:** Audio và AI thất bại minh bạch, không treo, không làm hỏng Python environment, và không tạo cảm giác an toàn giả cho API key.

### Hạng mục

- [x] Bỏ tự động `pip install` thầm lặng trong Anki; thay bằng dependency check + thao tác cài đặt rõ ràng, version được pin và thông báo lỗi hữu ích.
- [x] Thêm connect/read timeout, cancellation, lock theo cache key và ghi file audio atomic cho Edge TTS, gTTS, VoiceVox.
- [x] Giới hạn cache VoiceVox/audio và có cơ chế dọn file orphan an toàn.
- [x] Thay fallback XOR của API key bằng OS credential store/keyring; nếu không thể bảo vệ thì thông báo chính xác thay vì gọi là encryption.
- [x] Không log API key, Authorization header, raw prompt hoặc raw response trừ khi người dùng chủ động bật debug có che dữ liệu.

### 2026-08-13 — Phase 2 / Dependency, TTS và bí mật

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `audio/`, `workers/import_worker.py`, `workers/ai_workers.py`, `utils/credentials.py`, `utils/ai_extractor.py`, `utils/logger.py`, UI AI settings và test.
- Thay đổi: Bỏ `pip install` tự động; thêm kiểm tra dependency và lệnh cài đặt pin rõ ràng. Edge/gTTS/VoiceVox có timeout, nhận cancellation event, khóa theo audio cache key, và chỉ publish media bằng ghi file tạm rồi atomic replace. Cache query VoiceVox có giới hạn; chỉ dọn file tạm Bento Forge quá hạn, không xóa Anki media có thể đang được thẻ tham chiếu. API key đã chuyển sang OS credential store/keyring theo profile; migration xóa key Fernet/XOR/plaintext khỏi JSON, failure mode không lưu secret. Logger redacts Authorization, api_key và token phổ biến trước khi ghi handler.
- Kiểm chứng: `powershell -ExecutionPolicy Bypass -File scripts/test_isolated.ps1` → 360 passed, lặp lại 360 passed; test bao phủ TTS safety, migration keyring/failure mode và log redaction.
- Rủi ro còn lại / bước kế tiếp: Xác minh thủ công trên profile Anki sao lưu: keyring của hệ điều hành mục tiêu, TTS server offline và hủy giữa request trước khi phát hành; tiếp tục Phase 3.

### Tiêu chí hoàn tất

- TTS server treo/offline không khóa worker quá timeout đã định.
- Hai audio task trùng nhau không tạo file hỏng.
- Cài dependency không xảy ra ngoài thao tác người dùng đã xác nhận.
- API key không còn được lưu bằng XOR; có test migration/failure mode.

---

## Phase 3 — Tương thích, quan sát và phát hành bền vững

**Trạng thái:** `Đang làm`
**Mục tiêu:** Mỗi bản phát hành có giới hạn tương thích thật, tín hiệu lỗi đủ dùng và tài liệu phản ánh hiện trạng.

### Hạng mục

- [x] Rà private API/hook Anki (ví dụ Overview patch), thêm feature detection và graceful fallback để không phá reviewer/overview khi Anki đổi API.
- [x] Xác định matrix Anki + Python được hỗ trợ thực sự; thu hẹp `max_version` nếu chưa có smoke test tương ứng.
- [ ] Bổ sung smoke test với Anki thật hoặc harness tương đương cho import, reviewer hook, combo mode, config migration và undo.
- [x] CI chạy format/lint/type-or-import check, test cô lập state, và báo số test thật thay vì badge tĩnh.
- [ ] Chuẩn hóa logging thành mã lỗi/ngữ cảnh hành động, không ghi dữ liệu nhạy cảm; thêm hướng dẫn lấy log để debug.
- [ ] Mỗi release cập nhật CHANGELOG, compatibility matrix và phần Baseline/nhật ký của tài liệu này.

### Tiêu chí hoàn tất

- CI xanh trên toàn matrix đã công bố; badge lấy từ CI hoặc được cập nhật tự động.
- Hook không tương thích tự tắt có cảnh báo thay vì làm hỏng UI Anki.
- Release checklist được chạy và ghi kết quả trước khi tăng version.

### 2026-08-13 — Phase 3 / Hook compatibility, matrix và CI

- Trạng thái: `Đang làm`
- Phạm vi: `hooks/`, `manifest.json`, `COMPATIBILITY.md`, `README.md`, `.github/workflows/ci.yml`, `utils/logger.py` và test.
- Thay đổi: Loại bỏ đường patch private `Overview._table`; reviewer và WebView hook dùng feature detection, đăng ký idempotent và fallback theo từng hook. Thu hẹp release matrix về Anki 2.1.50/Python 3.9, thêm tài liệu matrix; README dùng CI badge thay vì badge test tĩnh. CI chạy critical lint, test state cô lập và compile check trên Python 3.9/3.11.
- Kiểm chứng: `python -m py_compile hooks/reviewer.py hooks/overview_mode.py utils/logger.py tests/test_combo_mode.py tests/test_release_metadata.py` và pytest cô lập cho `test_combo_mode.py`, `test_release_metadata.py` → 16 passed.
- Rủi ro còn lại / bước kế tiếp: Chưa có smoke test Anki thật cho import, reviewer, combo, migration và undo; cần chạy trên profile sao lưu trước khi mở rộng matrix hoặc tăng version. Full isolated suite đã được khởi chạy nhưng chưa trả kết quả trong hơn sáu phút, cần tái chạy trong môi trường CI/phát triển trước release.

---

## Nhật ký thay đổi

| Ngày | Thay đổi | Lý do |
| --- | --- | --- |
| 2026-08-13 | Thay roadmap refactor đã hoàn thành bằng roadmap chất lượng 4 phase. | Giữ một nguồn kế hoạch hiện hành cho các phiên sau. |
| 2026-08-13 | Hoàn thành Phase 0: profile-scoped persistence, migration atomic, cache/state bounds và test cô lập. | Ngăn update hoặc test ghi đè dữ liệu người dùng; tạo baseline lặp lại được. |
| 2026-08-13 | Hoàn thành Phase 1: CollectionOp/QueryOp, cancellation event, retry có thể hủy và import audio an toàn. | Ngăn worker tự quản lý truy cập Collection, treo UI và dừng thread cưỡng bức. |
| 2026-08-13 | Bắt đầu Phase 2: dependency và độ bền TTS. | Loại bỏ cài dependency ngầm; bảo đảm TTS có timeout, hủy và ghi audio an toàn. |
| 2026-08-13 | Hoàn thành Phase 2: TTS/dependency an toàn, keyring và redaction log. | Ngăn treo TTS, file audio lỗi, sửa Python environment ngầm và lưu/lộ API key không an toàn. |

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase N / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
```
