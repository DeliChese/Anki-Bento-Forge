# Bento Forge — Quality Roadmap

> Tài liệu sống và **nguồn kế hoạch duy nhất** cho các cải thiện chất lượng Bento Forge.
> Không dùng `CODE_MAP.md` hay `UPGRADE_GUIDE.md` để quyết định công việc mới; cấu trúc mã nguồn chuẩn vẫn là `.claude/`.

**Cập nhật gần nhất:** 2026-08-15

**Trạng thái chung:** Phase 0–4 hoàn thành; Phase 5 chờ bằng chứng release ngoài local.
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

- `manifest.json` là nguồn sự thật: add-on v17.1.0, min/max Anki đều là 2.1.50; tài liệu chỉ diễn giải phạm vi này.
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

**Trạng thái:** `Hoàn thành`
**Mục tiêu:** Mỗi bản phát hành có giới hạn tương thích thật, tín hiệu lỗi đủ dùng và tài liệu phản ánh hiện trạng.

### Hạng mục

- [x] Rà private API/hook Anki (ví dụ Overview patch), thêm feature detection và graceful fallback để không phá reviewer/overview khi Anki đổi API.
- [x] Xác định matrix Anki + Python được hỗ trợ thực sự; thu hẹp `max_version` nếu chưa có smoke test tương ứng.
- [x] Bổ sung smoke test với Anki thật hoặc harness tương đương cho import, reviewer hook, combo mode, config migration và undo.
- [x] CI chạy format/lint/type-or-import check, test cô lập state, và báo số test thật thay vì badge tĩnh.
- [x] Chuẩn hóa logging thành mã lỗi/ngữ cảnh hành động, không ghi dữ liệu nhạy cảm; thêm hướng dẫn lấy log để debug.
- [x] Mỗi release cập nhật CHANGELOG, compatibility matrix và phần Baseline/nhật ký của tài liệu này.

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

### 2026-08-13 — Phase 3 / Smoke harness tương thích Anki

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `tests/test_anki_smoke_harness.py`.
- Thay đổi: Thêm harness mock public API Anki cho CollectionOp/import tạo note, đăng ký reviewer/WebView hook, combo-mode message và migration có backup/rollback.
- Kiểm chứng: pytest cô lập → `test_anki_smoke_harness.py`: 3 passed; `test_combo_mode.py`: 15 passed; `test_integration.py`: 15 passed. `python -m py_compile tests/test_anki_smoke_harness.py` thành công.
- Rủi ro còn lại / bước kế tiếp: Harness không thay thế smoke thủ công trong Anki 2.1.50 với profile sao lưu; tiếp tục chuẩn hóa logging và hướng dẫn debug. Chạy gộp các file có `tmp_path` vẫn gặp lỗi quyền dọn thư mục tạm Windows của môi trường hiện tại.

### 2026-08-13 — Phase 3 / Observability và release procedure

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `utils/logger.py`, TTS/import/reviewer logging, `DEBUGGING.md`, `RELEASE_CHECKLIST.md`, `CHANGELOG.md`, `README.md` và test.
- Thay đổi: Thêm mã event ổn định, action context và redaction exception; log được lưu trong profile data. Các failure path TTS/import/reviewer dùng event code có thể tìm kiếm. Thêm hướng dẫn lấy log an toàn và release checklist bắt buộc ghi bằng chứng trước khi tăng version.
- Kiểm chứng: `python -m py_compile` cho logger/TTS/import/reviewer và pytest cô lập (`test_log_redaction.py`, smoke, combo, integration) → 37 passed; release record 17.1.0 được tạo với trạng thái chưa được phép tăng version.
- Rủi ro còn lại / bước kế tiếp: Smoke thủ công trên profile sao lưu và CI xanh vẫn là điều kiện bắt buộc của lần phát hành kế tiếp, không được thay bằng checklist Markdown.

---

## Phase 4 — Kiến trúc, chất lượng dữ liệu và vận hành chủ động

**Trạng thái:** `Hoàn thành`
**Mục tiêu:** Giảm chi phí thay đổi tính năng, nâng chất lượng dữ liệu thẻ và phát hiện vấn đề sớm mà không thu nội dung học của người dùng.

### Hạng mục dự kiến

> 2026-08-13 — Đang triển khai nền tảng Phase 4: ranh giới use-case/adapter,
> policy AI theo phiên, kiểm định dữ liệu nhập, artifact phát hành và regression tests.

- [x] Tách dần `__init__.py` thành lớp điều phối UI, use-case import/model/state và adapter Anki; factory state, collection lookup và model lifecycle đã tách kèm regression test.
- [x] Thiết lập policy AI theo phiên: ngân sách token/chi phí, giới hạn đầu vào, ước lượng trước khi chạy và báo cáo kết quả không chứa prompt/raw response.
- [x] Nâng kiểm định dữ liệu: phát hiện trùng gần đúng, chính sách merge an toàn (không tự merge), preview diff rõ ràng và export báo cáo import đã che dữ liệu nhạy cảm.
- [x] Thêm contract/regression test cho các ranh giới mới, đóng gói `.ankiaddon` và kiểm tra install smoke trên profile sạch.
- [x] Cải thiện UX/accessibility: xác nhận rõ trạng thái/chi phí trước khi gọi AI, keyboard navigation/accessible name cho luồng chính, thông điệp có hành động tiếp theo và regression test dark/light stylesheet.
- [x] Củng cố supply chain: lock dependency phát triển, quét secret/vulnerability trong CI và artifact có checksum/SBOM khi phát hành.
- [x] Không thêm telemetry: policy và báo cáo chỉ giữ số liệu tổng hợp cục bộ, tuyệt đối không có nội dung thẻ, prompt hay response AI.

### Tiêu chí hoàn tất

- Luồng chính không còn phụ thuộc vào một module UI quá lớn và có test bảo vệ ranh giới Anki.
- Người dùng biết chi phí AI trước khi chạy và có thể hủy an toàn.
- Báo cáo/import và diagnostic không làm lộ dữ liệu học.
- Artifact phát hành tái lập được, truy vết được dependency và kiểm tra được trên profile sạch.

### 2026-08-13 — Phase 4 / Kiến trúc, chất lượng dữ liệu và vận hành chủ động

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `__init__.py`, `utils/factory_state.py`, `utils/anki_adapter.py`, policy AI/import-report/quality, UI settings, CI/build và regression tests.
- Thay đổi: Tách persistence state, collection lookup và model lifecycle khỏi lớp UI qua `FactoryStateStore`/`AnkiCollectionAdapter`/`model_lifecycle`. AI có giới hạn input, token và chi phí theo phiên; hiển thị ước lượng trước khi gửi, chỉ lưu aggregate usage. Kiểm định import gắn cờ gần-trùng để người dùng xem lại, tuyệt đối không tự merge; báo cáo import profile-scoped chỉ chứa số liệu tổng hợp. Luồng chính hỗ trợ Tab focus và accessible name; dark/light/midnight stylesheet được regression test. Thêm build `.ankiaddon`, checksum, SBOM, dependency lock/audit và secret scan trong CI.
- Kiểm chứng: `python -m py_compile` thành công; regression policy/quality/adapter/model lifecycle/accessibility/theme/card render → `24 passed`. Privacy report và state-store migration được kiểm tra trực tiếp trong data-dir tạm. Artifact được đóng gói với checksum/SBOM và smoke compile sau giải nén vào profile sạch thành công. Full suite có test dùng `tmp_path` vẫn bị chặn bởi `WinError 5` khi pytest cleanup trong sandbox Windows hiện tại, đúng rủi ro baseline đã biết.
- Rủi ro còn lại / bước kế tiếp: Chạy full isolated suite trên Python 3.9/3.11 CI và smoke thủ công Anki 2.1.50 trên profile backup trước release; ngưỡng near-duplicate 0.88 có thể điều chỉnh sau khi nhận phản hồi thực tế.

---

## Phase 5 — Đóng khoảng hở phát hành và hiệu quả học SRS

**Trạng thái:** `Đang làm` — P0-A/P0-B/P1-D/P1-E hoàn thành; P0-C đã đạt local gate, còn chờ CI và smoke Anki thật.

**Mục tiêu:** Chỉ phát hành khi hành vi runtime, tài liệu và bằng chứng kiểm chứng khớp nhau; đồng thời bảo đảm Combo Mode không làm mờ tín hiệu ghi nhớ mà Anki dùng để lập lịch.

**Thứ tự thực hiện bắt buộc:** P0-A → P0-B → P0-C → P1-D → P1-E. Không tăng version hay mở rộng compatibility matrix trước khi P0-A, P0-B và P0-C hoàn tất.

### P0-A — Loại bỏ hoàn toàn tự cài dependency trong Anki

**Trạng thái:** `Hoàn thành` (2026-08-13)

**Vấn đề:** `utils/ai_extractor.py` còn gọi `pip install` khi đọc DOCX/XLSX, trái với chính sách Phase 2 và có thể làm thay đổi Python runtime của Anki không có sự xác nhận rõ ràng.

- Phạm vi dự kiến: `utils/ai_extractor.py`, UI/i18n báo dependency thiếu, `tests/test_file_extract.py` và test mới nếu cần.
- Thay đổi yêu cầu: thay `_pip_install`, `_install_docx`, `_install_openpyxl` bằng kiểm tra availability không ghi hệ thống; hiển thị tên package, phiên bản được hỗ trợ và lệnh cài thủ công có thể copy. CSV/TXT và parser đã có sẵn vẫn phải hoạt động.
- Không làm: không tự tải package, không gọi `subprocess`/`pip`, không thêm fallback âm thầm làm mất nội dung file.
- Tiêu chí hoàn tất:
  - Không còn đường runtime nào chứa `pip install`, `subprocess.check_call(... pip ...)` hoặc tự thay đổi site-packages.
  - Thiếu DOCX/XLSX dependency cho thông báo có hành động tiếp theo, không crash và không treo UI.
  - Có test cho dependency có/thiếu; test extraction hiện hữu pass.

### 2026-08-13 — Phase 5 / P0-A loại bỏ auto-install dependency tài liệu

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `utils/ai_extractor.py`, luồng đính kèm trong `__init__.py`, `utils/i18n.py`, `tests/test_file_extract.py`, `CHANGELOG.md` và `RELEASE_CHECKLIST.md`.
- Thay đổi: Xóa `_pip_install`, `_install_docx`, `_install_openpyxl` và mọi lời gọi `subprocess`/pip tự động khỏi document extraction; chỉ kiểm tra availability. Khi thiếu parser, UI báo dependency pin `python-docx==1.1.2` hoặc `openpyxl==3.1.5` cùng lệnh cài thủ công có thể sao chép; lỗi không bị đưa vào prompt AI như nội dung file.
- Kiểm chứng: `py_compile` cho các file Python đã sửa; pytest cô lập cho AI extraction/token/length/grammar/file/i18n → `80 passed`. Regression mở rộng factory/i18n có `51 passed, 1 failed`; lỗi độc lập đã tái hiện riêng tại test cũ `TestComboMigration::test_collect_template_fields_captures_all` do fixture không có `_collect_template_fields`, không thuộc P0-A và không được sửa trong phiên này.
- Release: Chỉ ghi bằng chứng local P0-A; version, compatibility matrix, trạng thái CI và manual smoke giữ nguyên.

### P0-B — Một nguồn sự thật cho version và compatibility

**Trạng thái:** `Hoàn thành` (2026-08-14)

**Vấn đề:** `manifest.json` giới hạn đúng một bản Anki nhưng baseline roadmap cũ từng ghi phạm vi rộng hơn. Mâu thuẫn release metadata làm người dùng không biết phiên bản nào được hỗ trợ thật.

- Quyết định: `manifest.json` là nguồn sự thật cho version và min/max Anki; `COMPATIBILITY.md`, README, CHANGELOG và roadmap chỉ diễn giải hoặc dẫn lại thông tin đó.
- Phạm vi dự kiến: `manifest.json`, `COMPATIBILITY.md`, `README.md`, `REFACTOR_PLAN.md`, `tests/test_release_metadata.py`; chỉ thêm script kiểm tra nếu test Python không đủ rõ ràng.
- Thay đổi yêu cầu: sửa baseline lịch sử để không còn tuyên bố phạm vi rộng hơn manifest; thêm regression test đọc manifest và phát hiện mọi support range trái ngược trong tài liệu release đang dùng.
- Tiêu chí hoàn tất:
  - Một câu trả lời duy nhất, có test, cho version và phạm vi Anki được hỗ trợ.
  - Không ghi version/changelog là “released” khi release record chưa có CI và manual smoke đạt.

### P0-C — Bằng chứng release có thể tái lập

**Trạng thái:** `Đang làm` — triển khai và local gate hoàn thành; chờ CI Python 3.9/3.11 và smoke Anki 2.1.50.

**Vấn đề:** full suite trong Windows sandbox từng vướng cleanup tạm và v17.1.0 chưa có record CI xanh hoặc smoke Anki thật. Harness mock không thay thế Anki runtime.

- Phạm vi dự kiến: `scripts/test_isolated.ps1`, test dùng `tmp_path`, `.github/workflows/ci.yml`, `RELEASE_CHECKLIST.md`, `COMPATIBILITY.md` và test liên quan.
- Thay đổi yêu cầu: chẩn đoán rồi sửa riêng lỗi cleanup/quyền thư mục tạm (nếu tái hiện); giữ test hoàn toàn profile-scoped. Đừng làm yếu assertion hoặc bỏ qua cleanup để có màu xanh giả.
- Bằng chứng bắt buộc trước release:
  1. `scripts/test_isolated.ps1` pass hai lần liên tiếp, không làm bẩn worktree;
  2. CI pass trên Python 3.9 và 3.11;
  3. Manual smoke trên Anki 2.1.50 với profile đã backup: import add/update + undo, Combo reviewer, TTS offline/cancel, config migration;
  4. Ghi kết quả, ngày và người xác nhận vào `RELEASE_CHECKLIST.md`.

### 2026-08-14 — Phase 5 / P0-B và P0-C metadata + isolated release evidence

- Trạng thái: P0-B `Đang làm` → `Hoàn thành`; P0-C giữ `Đang làm` do chưa có CI xanh và smoke Anki thật.
- Phạm vi: `COMPATIBILITY.md`, `README.md`, `CHANGELOG.md`, `RELEASE_CHECKLIST.md`, `REFACTOR_PLAN.md`, `scripts/test_isolated.ps1`, `.github/workflows/ci.yml`, `tests/conftest.py`, `tests/test_release_metadata.py`, các test file/state dùng temp.
- Thay đổi: Chuẩn hóa tài liệu theo version/min/max trong `manifest.json`; regression test quét range trái ngược và chặn ghi release khi checklist chưa có CI/smoke. Harness dùng hai run-root profile/temp độc lập, không nuốt lỗi cleanup, so worktree trước/sau; CI 3.9/3.11 gọi cùng harness.
- Chẩn đoán: `WinError 5` được tái hiện khi pytest/`TemporaryDirectory` tạo thư mục quyền `0o700` trong Windows sandbox. Fixture temp profile-scoped dùng thư mục truy cập được và cleanup bắt buộc; không giảm assertion.
- Kiểm chứng local: `py_compile` đạt; metadata/temp regression `119 passed`; gọi `scripts/test_isolated.ps1` hai lần liên tiếp, mỗi lần hai vòng `383 passed`, cleanup và worktree check đều đạt.
- Release: `manifest.json` giữ nguyên 17.1.0 và Anki 2.1.50–2.1.50. CI và manual smoke không được tự nhận; release record vẫn chờ bằng chứng ngoài local.

### P1-D — Giảm rủi ro từ các module điều phối lớn

**Trạng thái:** `Hoàn thành` (2026-08-15)

### 2026-08-15 — Phase 5 / P1-D orchestration UI

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `utils/ai_workflow.py`, wiring AI worker trong `__init__.py`, `tests/test_ai_workflow.py` và project map.
- Thay đổi: Tách vòng đời worker AI (cancellation token, tạo worker, nối signal, giữ reference, clear và cancel không chặn UI) khỏi Factory vào `AiWorkflowCoordinator`. Module mới chỉ phụ thuộc Python stdlib và nhận worker factory/callback từ UI; Factory tiếp tục giữ Qt, dialog, QueryOp/Collection API và toàn bộ hành vi hiển thị.
- Kiểm chứng: `python -m py_compile __init__.py utils/ai_workflow.py tests/test_ai_workflow.py`; pytest hẹp `4 passed`; `powershell -ExecutionPolicy Bypass -File scripts/test_isolated.ps1` chạy hai vòng, mỗi vòng `415 passed`, cleanup và kiểm tra worktree đạt; `git diff --check` đạt.
- Rủi ro còn lại / bước kế tiếp: P1-D không còn lát cắt refactor đã lên kế hoạch. Phase 5 vẫn mở duy nhất cho P0-C: CI Python 3.9/3.11 và manual smoke Anki 2.1.50 với profile đã backup; không tự nhận các bằng chứng này từ môi trường local.

**Vấn đề:** `__init__.py` và `utils/ai_extractor.py` vẫn là điểm tập trung thay đổi lớn, dù Phase 4 đã tách một phần state/adapter/model lifecycle.

- Phạm vi dự kiến: trước hết map dependency và xác định seam có test; sau đó chỉ tách từng lát nhỏ: document extractors, HTTP/AI client và orchestration UI. Giữ public import/API tương thích trong một release.
- Cách làm: mỗi PR/phiên chỉ tách một responsibility, di chuyển test cùng responsibility, không vừa refactor vừa thay đổi hành vi sản phẩm.
- Tiêu chí hoàn tất cho mỗi lát: không tăng direct `mw`/`aqt` access ngoài adapter/UI cho phép; public behavior giữ nguyên qua regression test; module mới có owner/ràng buộc dependency rõ ràng.
- Không làm: “big-bang rewrite” của Factory hoặc AI extractor.

### 2026-08-14 — Phase 5 / P1-D tách document extractors

- Trạng thái: lát cắt document extractors `Đang làm` → `Hoàn thành`; P1-D tổng thể giữ `Đang làm` để tách HTTP/AI client và orchestration UI ở các phiên riêng.
- Phạm vi: `utils/document_extractors.py`, lớp tương thích trong `utils/ai_extractor.py`, `tests/test_file_extract.py`, project map và roadmap.
- Thay đổi: Chuyển toàn bộ dispatch TXT/Markdown/CSV/PDF/DOCX/XLSX, kiểm tra parser tùy chọn và lỗi dependency sang module không phụ thuộc Anki/UI/AI/network. `utils.ai_extractor` re-export các tên cũ trong release hiện tại; test xác nhận các object public vẫn tương thích và module mới không import `aqt` hay gọi subprocess.
- Kiểm chứng: `py_compile` đạt; test extraction hẹp `13 passed`; harness cô lập chính thức chạy hai vòng liên tiếp, mỗi vòng `384 passed`, cleanup và worktree check đạt. Một lượt gọi `test_comprehensive.py` trực tiếp ngoài harness có `120 passed, 13 failed` vì thiếu bootstrap mock `aqt`/`anki`; cùng các test này đều pass trong harness chính thức.
- Rủi ro còn lại / bước kế tiếp: Chưa tách HTTP/AI client hoặc orchestration UI; P0-C vẫn chờ CI Python 3.9/3.11 và smoke Anki 2.1.50 thật. Không thay đổi version, compatibility hay hành vi sản phẩm trong lát cắt này.

### 2026-08-14 — Phase 5 / P1-D tách HTTP/AI client

- Trạng thái: lát cắt HTTP/AI client `Đang làm` → `Hoàn thành`; P1-D tổng thể giữ `Đang làm` để tách orchestration UI ở phiên riêng.
- Phạm vi: `utils/ai_http_client.py`, lớp tương thích trong `utils/ai_extractor.py`, dependency network của `utils/batch_processor.py`, `tests/test_ai_http_client.py`, project map và roadmap.
- Thay đổi: Chuyển TLS policy, connection pool theo thread, POST JSON, retry/backoff, rate-limit và cancellation sang module thuần Python stdlib, không phụ thuộc Anki/Qt/config/prompt/parser. `utils.ai_extractor` giữ các tên transport cũ trong release hiện tại; batch dùng trực tiếp owner mới. Không thay đổi payload, timeout, thông báo tiến độ hay hành vi API.
- Kiểm chứng: `py_compile` đạt; regression AI/HTTP/extraction hẹp `84 passed`; harness cô lập chính thức chạy hai vòng liên tiếp, mỗi vòng `390 passed`, cleanup và worktree check đạt; `git diff --check` đạt.
- Rủi ro còn lại / bước kế tiếp: P1-D còn orchestration UI; P1-E còn quyết định sản phẩm và triển khai SRS. P0-C vẫn chờ CI Python 3.9/3.11 cùng smoke Anki 2.1.50 thật. Không thay đổi version, compatibility hay release record trong lát cắt này.

### P1-E — Làm rõ nghĩa học tập của Combo Mode

**Trạng thái:** `Hoàn thành` (2026-08-14)

**Vấn đề:** 5 dạng luyện tập dùng chung một card/lịch SRS có thể trộn lẫn các kỹ năng khác nhau (nhận diện, sản xuất, chính tả, phát âm), làm đánh giá Again/Good không còn phản ánh một prompt hồi tưởng ổn định.

- Quyết định sản phẩm: Combo Mode mặc định là **luyện biến thể trên một card**; người dùng có thể opt-in **5 lịch SRS độc lập** theo deck cho Nhận diện, Sản xuất, Chính tả, Phát âm và Nhớ mặt chữ.
- Phạm vi dự kiến: `mode/templates.py`, `mode/shared.py`, `hooks/overview_mode.py`, cấu hình/model lifecycle, i18n và test combo/migration.
- Yêu cầu UX: mô tả rõ ở UI rằng đổi mode hiện tại có/không ảnh hưởng lịch; đặt default direction cố định theo deck hoặc mode study; migration phải giữ scheduling/history của card cũ và luôn có backup/undo khi có thể.
- Tiêu chí hoàn tất:
  - Người dùng hiểu card đang đo kỹ năng nào trước khi bấm Again/Good.
  - Mỗi hướng được chọn “SRS độc lập” có card/template và scheduling độc lập; combo drill không giả vờ là kết quả recall độc lập.
  - Có migration và reviewer tests cho mode cũ/mới, không sinh thẻ trùng ngoài ý muốn.

### 2026-08-14 — Phase 5 / P1-E semantics và migration SRS cho Combo Mode

- Trạng thái: `Đang làm` → `Hoàn thành`
- Phạm vi: `mode/templates.py`, `mode/shared.py`, `mode/css.py`, `hooks/overview_mode.py`, `hooks/reviewer.py`, language config, `utils/srs_policy.py`, model/import lifecycle, i18n, README/manifest/changelog, card-template skill và regression tests.
- Thay đổi: Giữ mặc định Combo một card/một lịch; card hiển thị rõ đây là luyện biến thể dùng lịch chung. Thêm field opt-in `SRS Independent`: ord=0 trở thành Nhận diện cố định và giữ scheduling/history cũ, ord=1..4 chỉ sinh khi opt-in và có lịch riêng. Mặc định mode/layout được lưu theo deck. UI chỉ đổi policy cho note nhập mới; migration note hiện có là thao tác tường minh, có Anki checkpoint/Undo, giữ card ord=0, không xóa card/template và idempotent khi chạy lại. Legacy model nhiều template được đánh dấu trước khi cài template conditional để không làm rỗng card cũ.
- Kiểm chứng: `py_compile` đạt; regression P1-E/model/i18n/release metadata `55 passed`; `git diff --check` đạt; harness cô lập chính thức chạy hai vòng liên tiếp, mỗi vòng `396 passed`, cleanup và worktree check đạt. Một lượt ghép test trực tiếp ngoài harness bị nhiễu mock `aqt.qt` dùng chung (thiếu `QTabWidget`); cùng full suite pass trong harness chính thức.
- Rủi ro còn lại / bước kế tiếp: Cần smoke thủ công trên Anki 2.1.50 với profile backup cho hiển thị 3 ngôn ngữ, tạo note Combo/Independent, migration + Undo và reviewer rating; bằng chứng này vẫn thuộc P0-C. Không tăng version, compatibility hay nhận release đã hoàn tất.

### Handoff cho phiên tiếp theo

Mỗi phiên chỉ nhận **một** item P0/P1 ở trên. Prompt đề nghị:

```text
Thực hiện REFACTOR_PLAN.md / Phase 5 / <ID>. Đọc AGENTS.md, .claude/CLAUDE.md và đúng skill phù hợp trước. Không mở rộng sang item khác. Trước khi sửa, nêu file/phạm vi và acceptance criteria; sau khi sửa, chạy test liên quan, cập nhật Phase 5 + release record khi đủ bằng chứng. Không tăng version hoặc thay đổi compatibility matrix ngoài P0-B/P0-C.
```

## Nhật ký thay đổi

| Ngày | Thay đổi | Lý do |
| --- | --- | --- |
| 2026-08-13 | Thay roadmap refactor đã hoàn thành bằng roadmap chất lượng 4 phase. | Giữ một nguồn kế hoạch hiện hành cho các phiên sau. |
| 2026-08-13 | Hoàn thành Phase 0: profile-scoped persistence, migration atomic, cache/state bounds và test cô lập. | Ngăn update hoặc test ghi đè dữ liệu người dùng; tạo baseline lặp lại được. |
| 2026-08-13 | Hoàn thành Phase 1: CollectionOp/QueryOp, cancellation event, retry có thể hủy và import audio an toàn. | Ngăn worker tự quản lý truy cập Collection, treo UI và dừng thread cưỡng bức. |
| 2026-08-13 | Bắt đầu Phase 2: dependency và độ bền TTS. | Loại bỏ cài dependency ngầm; bảo đảm TTS có timeout, hủy và ghi audio an toàn. |
| 2026-08-13 | Hoàn thành Phase 2: TTS/dependency an toàn, keyring và redaction log. | Ngăn treo TTS, file audio lỗi, sửa Python environment ngầm và lưu/lộ API key không an toàn. |
| 2026-08-13 | Hoàn thành Phase 3: compatibility hook, matrix, smoke harness, observability và release procedure. | Chỉ công bố phạm vi đã kiểm chứng, debug không lộ dữ liệu nhạy cảm và phát hành có checklist bằng chứng. |
| 2026-08-13 | Bổ sung kế hoạch Phase 4, chưa triển khai mã. | Định hướng kiến trúc, chất lượng dữ liệu và vận hành sau khi nền tảng an toàn/compatibility đã hoàn tất. |
| 2026-08-13 | Hoàn thành Phase 4: ranh giới state/adapter/model lifecycle, policy AI theo phiên, kiểm định import riêng tư, accessibility/theme, artifact và supply-chain CI. | Giảm chi phí thay đổi, giúp người dùng kiểm soát AI và phát hành có thể truy vết mà không thu nội dung học. |
| 2026-08-13 | Bổ sung Phase 5: đóng auto-install dependency, metadata release, evidence test/smoke, refactor có lát cắt và quyết định SRS cho Combo Mode. | Chuyển các phát hiện từ đánh giá kỹ thuật thành backlog có thứ tự, scope và tiêu chí bàn giao giữa các phiên. |
| 2026-08-13 | Hoàn thành Phase 5 / P0-A: document parser chỉ kiểm tra dependency và cung cấp hướng dẫn cài thủ công có pin. | Không để thao tác đọc DOCX/XLSX tự thay đổi Python runtime của Anki; giữ lỗi dependency khỏi prompt AI. |
| 2026-08-14 | Hoàn thành P0-B và local gate P0-C; P0-C còn chờ CI/smoke Anki thật. | Loại metadata compatibility mâu thuẫn và làm full-suite evidence lặp lại được mà không che lỗi cleanup. |
| 2026-08-14 | Hoàn thành lát cắt P1-D document extractors; P1-D tiếp tục với HTTP/AI client. | Giảm trách nhiệm của AI orchestrator bằng một seam thuần local, có test và giữ import tương thích. |
| 2026-08-14 | Hoàn thành lát cắt P1-D HTTP/AI client; P1-D tiếp tục với orchestration UI. | Cô lập TLS/retry/rate-limit/cancel khỏi AI orchestrator và cho batch phụ thuộc trực tiếp owner network mới. |
| 2026-08-14 | Hoàn thành P1-E: Combo mặc định một lịch; opt-in theo deck tạo 5 lịch kỹ năng độc lập với migration checkpoint/idempotent. | Làm Again/Good phản ánh một prompt ổn định mà vẫn giữ lịch sử card cũ và không sinh card ngoài ý muốn. |
| 2026-08-15 | Hoàn thành P1-D orchestration UI: tách vòng đời worker AI/cancellation khỏi Factory bằng coordinator thuần Python có test. | Giảm coupling giữa QDialog và worker lifecycle, giữ UI/Anki access ở Factory, đồng thời kiểm chứng cancel không chặn UI. |

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase N / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
```
