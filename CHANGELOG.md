# 📋 CHANGELOG

## [Unreleased]

### 2026-08-31 — Version: `18.3.0` → `18.3.0`

#### 🔧 Changed
- **Bốn ví dụ học từ vựng** — thẻ Nhật, Trung, Hàn và Anh mới bắt buộc có bốn ví dụ cùng nghĩa/cấp độ, mỗi câu ưu tiên một khung ngữ pháp hoặc mục đích câu khác; `Usage Note` nay nêu rõ sắc thái/mức độ dùng khi có căn cứ. Ví dụ 3–4 hiển thị trực tiếp ở mặt đáp án, không còn phần đối chiếu thu gọn. Prompt/cache tăng lên `35`; artifact thẻ cũ dùng schema trước thay đổi sẽ được giữ ở trạng thái chỉ đọc tương thích cũ.

### 2026-08-29 — Version: `18.3.0` → `18.3.0`

#### ✨ Added
- **Deck Manager multi-select** — parent and child decks can now be checked independently, with Select all/Clear checks controls and extended tree selection. Delete applies once per selected root, so checked child decks are never double-deleted when their parent is also checked; create-sub and rename remain explicitly single-deck actions.
- **Deck Center + AI Deck Blueprint** — nút quản lý deck sẵn có trong Forge nay mở một trung tâm duy nhất cho cả cây deck hiện hữu và AI Blueprint; action Blueprint rời đã được gỡ khỏi menu Tools. Blueprint nhận danh sách H1–H6, cho sửa/di chuyển nhánh và chỉ create/reuse các deck đã duyệt sau xác nhận, không rename/delete deck, note hoặc SRS hiện hữu.
- **Blueprint multi-deck import an toàn** — ngay trong Deck Center, cây đã duyệt có thể tạo/reuse deck và nhập note mới theo từng sub-deck sau một màn hình tổng hợp trùng/xung đột/sai schema/chưa gán. Luồng chỉ phát action `add`, không ghi đè note cũ, chưa tạo audio, re-check collection ngay trước ghi và giữ chính xác note ID để hoàn tác batch vừa nhập.
- **Dùng lại Nguồn học liệu trong Deck Center** — khi mở Deck Center từ Forge, AI Deck Blueprint nhận một snapshot của văn bản hiện có, ngôn ngữ đang chọn và số file đã nạp; không cần dán lại, không dùng global cache, không tự chạy AI và không đồng bộ ngược vào nguồn gốc.

#### 🔧 Changed
- **Grammarbook DOCX retrieval** — Study Library now retains Word Title/Heading styles as Markdown during extraction, with a local fallback when `python-docx` is unavailable, so Grammarbook chapters and numbered lessons become searchable section boundaries. Exact numbered requests can match the indexed heading itself; prompts, SRS, card generation, and source quotas are unchanged.
- **Deck organizer giữ provenance của heading** — rich HTML `<h1>`–`<h6>`, Markdown `#`–`######` và marker `H1:`–`H6:` được chuẩn hóa thành source path; AI nhận outline bounded cùng path từng từ, ưu tiên H1–H3 và giữ H4–H6 làm ngữ cảnh để không tạo cây Anki quá sâu. Prompt cache version tăng lên `34`.

### 2026-08-28 — Version: `18.3.0` → `18.3.0`

#### 🔧 Changed
- **Card reading surface** — vocabulary and grammar cards are wider and airier; long headers and examples wrap instead of overflowing, typed-answer feedback is clearer, and the mode selector/self-check inputs reflow on narrow screens. Dark mode and existing SRS/template behavior are unchanged.
- **Study Coach reading order** — the Reviewer dock now gives transcript and composer the centre of the layout, puts six quick prompts in a compact 3×2 grid, and presents the three local coaching actions in one row. The floating default is wider/taller; model and library controls remain on demand behind the existing options button.

> Mỗi ngày có thay đổi có một mục riêng. `Phiên bản` là snapshot `manifest.json` ở đầu và cuối ngày theo lịch sử Git, không phải xác nhận phát hành. Chỉ chuyển các mục phù hợp thành bản phát hành khi có bằng chứng CI và smoke Anki.

### 2026-08-26 — Phiên bản: `18.3.0` → `18.3.0`

#### ✨ Added
- **Production Drill cục bộ trong Reviewer** — thẻ có `Usage Pattern` hoặc `Collocation` nay hiện action **Tự đặt câu** ở mặt câu hỏi. Người học viết câu trước, rồi chủ động mở gợi ý/câu mẫu; draft chỉ tồn tại trong webview hiện tại, không gọi AI, tạo thẻ, chấm điểm hoặc sửa collection/SRS.

#### 🔧 Changed
- **Study Coach compact reading layout** — AI Study Sessions của Reviewer gom ngôn ngữ, model, ngữ cảnh thẻ và Thư viện học vào panel tùy chọn mở theo nhu cầu; transcript và composer giữ vị trí trung tâm. Transcript tự wrap nội dung bảng/từ dài, không sinh thanh cuộn ngang; các thao tác học nhanh co lại theo lưới.
- **Compact Factory controls** — gỡ hướng dẫn kéo phân cách đã lỗi thời, thu nhỏ minimum width của các control và xếp lại cụm Import thành `Xuất bản` + hàng `Hoàn tác/Hủy lô`. Vùng tìm kiếm, chọn và khoảng thẻ cũng co lại theo lưới để không đẩy cột phải tràn ngang.
- **Fixed 6:4 Factory grid** — khóa cột Sản xuất/Kiểm định theo tỉ lệ 60/40, bỏ handle splitter có thể kéo lệch bố cục. Cả hai cột chỉ cuộn dọc khi thiếu chiều cao; thanh cuộn ngang không còn xuất hiện hay che nút Import/Undo/Hủy lô hàng.
- **Release artifact fail-closed** — builder chỉ đóng gói Python runtime và hai JSON phát hành được allowlist; file cấu hình/lịch sử local, cache bytecode và file debug không thể lọt vào stage. Regression nay kiểm đồng thời `workers/`, manifest, SHA-256 và CycloneDX SBOM trước khi artifact được dùng cho clean-profile smoke.

### 2026-08-25 — Phiên bản: `18.3.0` → `18.3.0`

#### 🔧 Changed
- **Study Coach task-priority contract** — ý định trong prompt người học nay quyết định tác vụ; thẻ hiện tại chỉ là ngữ cảnh cho tham chiếu trực tiếp hoặc ví dụ phù hợp. Yêu cầu mục tài liệu được đặt ngay trước prompt hiện tại và thắng lịch sử trả lời sai; prompt version tăng lên `32` để không tái dùng cache theo contract cũ.
- **Study Coach dock ưu tiên hội thoại** — transcript được đưa lên vùng co giãn chính; quick action bố trí hai cột và dock nổi có kích thước tối thiểu lớn hơn, nhưng mọi chức năng học vẫn luôn hiện diện. Trong lúc worker chạy, chỉ báo `AI đang soạn tin…` chạy bằng timer UI, không chặn luồng Anki.

#### 🐛 Fixed
- **Study Coach startup on Anki 25.09** — bổ sung import `QTextOption` cho policy wrap transcript; AI Study Sessions không còn crash ngay lúc mở sau compact-layout update.
- **Coach không còn thay tác vụ nguồn bằng bài luyện thẻ** — transcript smoke cho thấy Scope đã đúng mục 42 nhưng prompt cũ vẫn ép thẻ `看` làm chủ đề. Contract mới phân biệt rõ “tham chiếu thẻ trực tiếp” với “yêu cầu nguồn tường minh”; mục nguồn được hoàn thành trước, chỉ dùng target thẻ khi tự nhiên trong ví dụ và coi assistant reply cũ mâu thuẫn là obsolete.
- **Dọn file tạm TTS lúc khởi động** — lượt dọn đầu tiên không còn bị bỏ qua khi `time.monotonic()` chưa vượt interval, nên file tạm Bento cũ vẫn được xóa mà không đụng media thẻ.
- **Transcript Study Coach dễ đọc trong dock hẹp** — Markdown AI nay hiển thị heading, đậm/nghiêng, list, code, quote và đường phân cách thay vì lộ `**`/`***`; bảng hai cột có cỡ chữ/padding dễ đọc, còn bảng nhiều cột tự chuyển thành các khối thông tin để không bị chật hoặc tràn.
- **Coach không còn suy diễn sắc thái ngữ pháp ngoài source** — khi Study Library chỉ liệt kê các biến thể như `在 / 正在 / 正 / 呢` mà không đối chiếu, Coach phải nói giới hạn của trích đoạn và giải thích trung tính; không được biến suy luận thành quy tắc tuyệt đối về “nhanh”, “vừa hay” hay “trang trọng”. Prompt cache version tăng lên `33`.

### 2026-08-24 — Phiên bản: `18.1.0` → `18.3.0`

#### ✨ Added
- **V18.3 Language Study Library** — Study Coach trong Reviewer có thư viện cục bộ theo profile + ngôn ngữ, cho phép gắn/bật/tắt/xóa Study Pack từ `.txt`, Markdown, CSV, PDF text, DOCX và bảng tính qua extractor hiện có; text, hash và index heading/chunk được lưu atomic, có quota, không thuộc hoặc bị xóa theo session.
- **Semantic Scope + provenance** — mỗi request Reviewer tạo Scope Manifest bounded từ đúng các pack cùng ngôn ngữ đang bật, hỗ trợ alias/paraphrase Nhật–Trung–Hàn–Anh, dừng để người học chọn khi nguồn mơ hồ và chỉ theo tối đa hai liên kết Markdown nội bộ khi bật “Ưu tiên học đầy đủ”; Forge không nhận context này và tài liệu luôn bị cô lập như dữ liệu không tin cậy.
- **Card Drill nháp** — action `Bài tập ngắn` chỉ soạn prompt 1–3 câu theo thẻ/chế độ học hiện tại để người dùng tự bấm Gửi; không auto-send, auto-grade, auto-rate hoặc sửa collection/SRS.
- **Forge Source Candidate Manifest** — thêm bước `SOURCE → CANDIDATE → ARTIFACT`: AI chỉ trả manifest vocab/grammar có `surface` và `source_excerpt` kiểm chứng được trong source; output malformed, prose hoặc cắt cụt bị từ chối, candidate trùng nội bộ bị loại trước khi hiển thị.
- **Candidate review có chủ quyền người dùng** — Forge cho chọn/bỏ từng candidate rồi mới soạn sẵn request Card Mode chỉ chứa các mục đã chọn; không tự gọi AI lần hai, không tự tạo artifact và không tự import. Bề mặt đã có trong deck hiện tại chỉ được gắn cảnh báo vì có thể khác nghĩa.
- **Reviewer Learning Checkpoint** — Study Coach có hai điểm kết thúc tường minh theo đúng `card_id + study_mode`: `Đã rõ · tiếp tục ôn` lưu checkpoint cục bộ rồi trả focus về Reviewer, còn `Cần luyện thêm` chỉ soạn sẵn micro-quiz để người dùng chủ động gửi.

#### 🔧 Changed
- **Study Coach prompt/cache contract** — prompt mặc định quy định thẻ Reviewer là đối tượng học chính, Study Library chỉ là tham khảo phụ không tin cậy và mọi tuyên bố số mục phải có số + tiêu đề trong cùng SOURCE; prompt version tăng lên `31` để không tái dùng cache theo contract cũ.
- **Version metadata / Note Types** — nâng release candidate cục bộ lên `18.3.0`; Note Type mới dùng hậu tố `V18.3`, còn các model `V18.1` và cũ hơn vẫn được nhận diện để migrate an toàn.
- **Blueprint AI composer** — ô yêu cầu, checkbox `Tạo thẻ · Từ vựng/Ngữ pháp` và nút **Gửi** nay nằm trong cùng một composer; loại artifact bám trực tiếp chế độ đã chọn phía trên. Factory ẩn router/bước xử lý và các nút AI trùng, nhưng giữ nguyên session, worker, schema, import và undo.
- **Blueprint responsive polish** — ngôn ngữ dùng dropdown đúng bản thiết kế; bỏ nút API trùng trên toolbar; tách trạng thái file/AI khỏi hàng hành động, ưu tiên composer trước transcript/artifact rỗng và tự xếp trạm Kiểm định xuống dưới khi cửa sổ hẹp để không còn cắt chữ hoặc đẩy mất cột.
- **Blueprint production workbench** — sắp xếp lại Factory theo ba vùng co giãn `Nguồn học liệu | AI/Candidate/Artifact + JSON | Kiểm định/Import`, đưa ngôn ngữ và loại thẻ lên khu chọn chung, bỏ banner quy trình đánh số cùng các tiêu đề trùng, giữ nguyên theme/màu cũ và toàn bộ worker/import/undo hiện hành.
- **Dây chuyền Lò đúc AI tích hợp** — bỏ standalone Forge dialog và gắn Candidate/Artifact trực tiếp vào Factory theo tuyến `NGUỒN HỌC LIỆU → CANDIDATE → ARTIFACT → KIỂM ĐỊNH/IMPORT`; “Nạp quặng”/“Source đính kèm” trở thành một source editor duy nhất. Loại thẻ bám Vocab/Grammar đã chọn phía trên; hai quick action vốn chỉ chép prompt mẫu đã được bỏ. AI Study Sessions giữ nguyên tên và chỉ thuộc Reviewer/Study Coach.
- **Reviewer/Forge role split** — Study Coach trong Reviewer nay chỉ phục vụ giải thích, gợi nhớ và kiểm tra mức hiểu trên thẻ hiện tại; Card Mode, artifact controls và artifact transcript chỉ thuộc Forge AI Workshop.
- **Fail-closed card ownership** — workspace policy và AI boundary từ chối mọi `card_mode` của Reviewer kể cả khi caller bỏ qua UI; Forge vẫn dùng Quality V2 và artifact → Xưởng zero-AI như cũ.
- **Checkpoint không can thiệp học lịch** — learning checkpoint dùng message `system_internal`, không đi vào prompt AI/rolling summary, không gọi model tự động và không sửa note, rating, ease, due hay SRS của Anki.
- **Workspace-scoped session memory** — Reviewer và Forge vẫn dùng chung transcript cục bộ để theo dõi, nhưng model history và rolling summary nay được tách theo workspace; assistant reply/candidate/artifact mới đều lưu provenance owner và transcript hiển thị đúng nhãn AI đã tạo message.

#### 🐛 Fixed
- **Không còn bịa số mục Study Library** — yêu cầu như “điểm ngữ pháp thứ 42” nay được khóa vào đúng heading đánh số `42.` trong text tài liệu; resolver fail-closed nếu không thấy số + tiêu đề chính xác, không để từ phụ trong pinyin/usage/collocation lấn át số mục. Scope Manifest lưu `section_number`/`section_title`, còn Coach bị cấm suy ra thứ tự từ chunk, mục lân cận, lịch sử hoặc kiến thức chung và phải tách dữ kiện nguồn khỏi ví dụ tự tạo.
- **Thẻ Reviewer là ngữ cảnh chính của Study Coach** — mỗi lần bấm Gửi sẽ đọc lại card hiện tại thay vì tin snapshot lúc mở dock; Note Type tùy biến không còn bị loại chỉ vì thiếu mapping ngôn ngữ chính xác. Payload đặt Study Library ở vai trò tham khảo phụ và đặt card gần câu hỏi hơn với `current_target` bắt buộc; thanh trạng thái hiện trực tiếp `Thẻ chính: <target>` để người học kiểm chứng. Field vocabulary/grammar vẫn qua whitelist và không quét collection/deck.
- **Ngôn ngữ AI của Study Session** — Reviewer có selector `Ngôn ngữ AI` riêng; nút tạo session không còn âm thầm lấy `ai_factory_active_lang` từ Factory. Đổi selector sẽ mở session cùng ngôn ngữ hoặc tạo session mới, không relabel lịch sử cũ; context board chỉ còn hiển thị mặt/chế độ/context thẻ.
- **English study-mode labels and card-history clear** — English no longer falls back to Japanese labels in the study-mode selector; clearing card history now persists an explicitly empty initialized cache, so a later Factory launch cannot repopulate the UI from the collection.
- **TTS local gây tăng RAM** — gỡ MeloTTS sidecar và lựa chọn provider cục bộ; Bento Forge quay lại Edge TTS với gTTS fallback, nên không còn khởi chạy tiến trình model neural riêng.
- **Factory startup** — `_on_lang_changed()` nay lấy `lang_code` từ cấu hình hiện tại trước khi đồng bộ tốc độ, loại bỏ `NameError: lang is not defined` làm Bento Forge không mở được trên Anki 25.09.4.
- **Cross-workspace memory bleed** — request Reviewer không còn nhận lịch sử/summary Forge và ngược lại. Phiên schema cũ vẫn reload, nhưng turn/summary không xác định owner bị loại khỏi request scoped; assistant legacy chỉ được kế thừa owner từ user turn có provenance ngay trước đó.

### 2026-08-21 — Phiên bản: `18.1.0` → `18.1.0`

#### ✨ Added
- **V18.2 Contextual AI Workspaces** — Reviewer nay là Study Coach bám thẻ hiện tại với context an toàn theo mặt/chế độ học, còn Bento Forge mở Forge AI Workshop bám source và instruction tách biệt; hai surface dùng chung Study Sessions/backend nhưng provenance workspace, language, source/card context và request token thuộc từng request.
- **Station UI cho Reviewer/Forge** — hai workspace có header, context board luôn hiển thị đúng AI đang biết gì, quick actions riêng, transcript phân cấp rõ hơn và Forge có route strip `SOURCE → AI → ARTIFACT → XƯỞNG` cùng trạng thái source tường minh, vẫn dùng theme engine/cấu hình hiện hành.

#### 🔧 Changed
- **Workspace-aware study prompts** — persona chat được sở hữu tường minh theo `reviewer`/`forge`; Card Mode vẫn tái sử dụng Quality V2 schema/validation và artifact → Xưởng vẫn là đường zero-AI không tái sinh snapshot.

#### 🐛 Fixed
- **Provenance-aware artifact pruning** — bounded Study Session storage ưu tiên xóa message không được tham chiếu, bảo vệ source message của mọi artifact hiện hành/stale và chỉ loại artifact cũ nhất một cách nhất quán khi dung lượng thực sự bắt buộc.
- **Study Session stale artifact retention** — artifact dùng schema cũ hoặc tương lai không còn biến mất khi reload; session giữ provenance và snapshot ở trạng thái chỉ đọc `stale`, hiển thị cảnh báo không tương thích và vẫn chặn tuyệt đối đường vào Xưởng mà không gọi AI tái tạo.
- **V18.1.1 AI Language Card hardening** — chuẩn hóa ownership ngôn ngữ Nhật/Trung/Hàn/Anh và alias tại một boundary fail-closed; validator chặn schema/kind/level/placeholder/ví dụ thiếu và các mâu thuẫn script có độ chắc chắn cao trước preview, artifact, Xưởng và import.
- **Artifact/Factory determinism** — artifact dùng schema snapshot hiện hành, kiểm tra source message và không còn chạy semantic repair; Xưởng không tự gọi AI để sinh ví dụ hoặc mutate card giữa artifact và import, đồng thời kiểm định lại ngay trước import.
- **AI extraction/Reviewer/request ownership** — long-text còn span chưa phục hồi nay phát lỗi incomplete thay vì báo thành công; dedupe giữ cùng mặt chữ khác nghĩa để review; context Reviewer theo `qa/vn/wb/pron/lg` không lộ đáp án ẩn; callback Study Session dùng request token bất biến nên stale result không thể gắn sang turn/session mới.
- **Prompt and grammar JSON boundaries** — custom card template phải giữ minimum vocab/grammar contract nhưng vẫn cho field mở rộng; grammar practice chỉ nhận đúng một JSON payload hoàn chỉnh, không regex chọn tùy ý từ prose hoặc nhiều payload.

### 2026-08-20 — Phiên bản: `17.2.0` → `18.1.0`

#### ✨ Added
- **AI Study Sessions / Dockable Learning Companion** — companion dùng chung cho Reviewer và Xưởng, hỗ trợ dock trái/phải, floating, collapse/hide, khôi phục UI state, nhiều phiên cục bộ, rename/delete session và phím tắt `Ctrl+Shift+A` có kiểm tra xung đột.
- **Reviewer-aware context** — nút Ask AI không gây rối, snapshot tối thiểu của đúng thẻ hiện tại, quick prompts, tùy chọn bỏ context thẻ và hành động quay lại Reviewer; không tự gọi AI, không quét collection và không sửa SRS.
- **Explicit Card Mode artifacts** — Vocab/Grammar Card Mode là hành động one-shot tường minh, tái dùng reliability pipeline hiện có rồi lưu artifact có schema snapshot để xem lại hoặc gửi sang Xưởng không cần gọi AI lần nữa.
- **Session memory + token controls** — lưu hội thoại theo profile bằng atomic write/retention, tóm tắt cục bộ theo cửa sổ context của model và ghi usage theo provider/session.
- AI Output Reliability release gate: provider-neutral response adapter, deterministic JSON extraction (raw/fenced/prose/known wrapper/native structured data), language/mode schema validation, minimum semantic checks, requested/received reconciliation, bounded partial retry và adaptive batch splitting; Chat snapshot đúng vocab/grammar để grammar RAW vào Xưởng qua cùng reliability contract, trong khi prose vẫn là prose, và text split recovery không cộng lại provisional prefix gây trùng; valid partial cards vẫn có thể vào preview an toàn.
- Cài đặt AI có nút đặt provider + model mặc định theo provider; config, cache và usage history resolve đường dẫn profile khi đọc/ghi để không rơi vào thư mục temp nếu add-on được import trước lúc profile Anki sẵn sàng. API key vẫn chỉ lưu trong OS credential store; usage history vẫn chỉ chứa metadata.
- Language Card Quality V2 cho vocab/grammar Nhật–Trung–Hàn–Anh: Usage Pattern/Note/Collocation hỗ trợ tối đa ba mục có information gain riêng; Example3/4 là field tùy chọn không audio, chỉ hiện thu gọn ở mặt sau; benchmark V2 đo density/size nhưng không thưởng quota.
- Confusion Guard lát cắt đầu tiên: cảnh báo advisory-only khi entry mới có exact curated near-confusable pair trong cùng deck; không chặn import, không merge, không tạo card và không đổi SRS.
- Usage Guide V1 cho vocab Nhật/Trung/Hàn/Anh: ba field tùy chọn `Usage Pattern`, `Usage Note`, `Collocation` (tối đa một cụm có nghĩa) hiển thị riêng ở mặt sau và tự ẩn khi trống. Output AI được chuẩn hóa để bỏ placeholder, nội dung lặp, collocation thiếu nghĩa và ví dụ thứ hai trùng; migration chỉ thêm field/template còn thiếu, không tạo card hay lịch SRS mới.
- Usage Guide quality gate đạt `19/20` (`95%`) trên benchmark model thật bốn ngôn ngữ với chi phí final `$0.002035` và `1.69 giây/card`; smoke runtime Anki 26.5 xác nhận migration/import/update/undo/rollback và render mặt sau trên collection tạm.
- Mã beta Knowledge được giữ riêng với Language (model Basic Q&A/Cloze, Explanation, Source và Tags) để có thể khôi phục khi cần; beta không hiện trên UI và không thuộc phạm vi phát hành hiện tại.
- Quality baselines: fixed 20-item English, Japanese, Chinese, and Korean corpora with reviewed run reports. Candidate cards now surface missing English IPA/CJK pronunciation, and Korean headword romanization with a hyphen, before import.
- Tiếng Anh trở thành ngôn ngữ đích thứ tư: có Note Type từ vựng/ngữ pháp, CEFR A1–C2, IPA, 5 chế độ học, prompt VI/EN, AI preview/chat, lịch sử, Edge TTS giọng UK/US và regression test riêng.
#### 🔧 Changed
- **Study Sessions surfaces/theme** — Factory giờ mở AI Study Sessions trong dialog độc lập như Settings/Lịch sử; chỉ Reviewer mới dùng dock panel. Companion dùng palette glassmorphism hiện hành thay cho màu sáng hard-code, giữ độ tương phản nhất quán giữa Glass Dark, Glass Light và Midnight.
- **Version metadata / Note Types** — nâng release candidate cục bộ lên `18.1.0`; note type hiện hành dùng hậu tố `V18.1` và vẫn nhận diện/migrate các model `V17.0`.
- **Chat prompt separation** — hội thoại thường dùng compact study-chat prompt, không còn chèn schema card; chỉ Card Mode mới nạp Quality V2 prompt/schema và validation/repair/retry pipeline.
- Quality V2 batch policy dùng giới hạn bảo thủ 8–12 card/request tùy language/mode và output budget thay cho mặc định 80; cache AI/batch tăng schema boundary để không hồi sinh partial hoặc wrong-language payload.
- Prompt cache mặc định và batch-cache boundary được tăng/ghép prompt signature để kết quả trước Quality V2 hoặc override cũ không bị tái sử dụng; migration Example3/4 chỉ thêm field còn thiếu và chạy lặp an toàn.
#### 🐛 Fixed
- **AI Study Sessions final polish** — rolling summary dùng marker message bền vững để chỉ compact phần delta chưa từng tóm tắt, giữ recent turns raw và migrate session cũ không marker an toàn; nút Ask AI trong Reviewer dùng màu neutral/translucent thích nghi light/dark thay cho palette sáng cố định. Artifact bubble nay gọi trực tiếp cùng owner Review/Đưa vào Xưởng theo `artifact_id`, không sao chép state hoặc gọi AI lần hai.
- English AI output chứa `hsk_level`, response sai vocab/grammar mode, prose-only, wrapper không whitelist hoặc JSON chỉ hoàn thành một phần không còn silently lọt vào Xưởng; truncated tail không được tự đóng ngoặc hay bịa field.

### 2026-08-16 — Phiên bản: `17.2.0` → `17.2.0`

#### ✨ Added
- Usage Guide V1 cho vocab Nhật/Trung/Hàn/Anh: ba field tùy chọn `Usage Pattern`, `Usage Note`, `Collocation` (tối đa một cụm có nghĩa) hiển thị riêng ở mặt sau và tự ẩn khi trống. Output AI được chuẩn hóa để bỏ placeholder, nội dung lặp, collocation thiếu nghĩa và ví dụ thứ hai trùng; migration chỉ thêm field/template còn thiếu, không tạo card hay lịch SRS mới.
- Usage Guide quality gate đạt `19/20` (`95%`) trên benchmark model thật bốn ngôn ngữ với chi phí final `$0.002035` và `1.69 giây/card`; smoke runtime Anki 26.5 xác nhận migration/import/update/undo/rollback và render mặt sau trên collection tạm.
- Mã beta Knowledge được giữ riêng với Language (model Basic Q&A/Cloze, Explanation, Source và Tags) để có thể khôi phục khi cần; beta không hiện trên UI và không thuộc phạm vi phát hành hiện tại.
- Quality baselines: fixed 20-item English, Japanese, Chinese, and Korean corpora with reviewed run reports. Candidate cards now surface missing English IPA/CJK pronunciation, and Korean headword romanization with a hyphen, before import.
- Tiếng Anh trở thành ngôn ngữ đích thứ tư: có Note Type từ vựng/ngữ pháp, CEFR A1–C2, IPA, 5 chế độ học, prompt VI/EN, AI preview/chat, lịch sử, Edge TTS giọng UK/US và regression test riêng.

#### 🔧 Changed
- Knowledge beta được giữ trong mã nguồn nhưng tắt trên giao diện; profile/deck đã từng chọn Knowledge tự quay về Language mà không ghi đè preference hoặc draft beta. Manifest và tài liệu hiện chỉ công bố workflow ngoại ngữ, không bump `18.0.0`.
- Mở compatibility manifest từ Anki 2.1.50 đến 26.5, bổ sung metadata cài `.ankiaddon` chuẩn (`package`/point version), và dùng `Collection.update_note()` để add/update/rollback nằm trong undo-aware operation trên Anki hiện tại; vẫn giữ fallback cho runtime legacy.
- Knowledge dùng prompt/parser/cache version riêng, schema JSON nghiêm ngặt và history namespace riêng. Source thiếu được giữ rỗng thay vì tự suy đoán; các control Language/TTS không xuất hiện trong Knowledge.
- English vocabulary extraction now keeps a supplied source meaning consistent across the card, both examples, and both translations; the cache prompt version was advanced so stale results are not reused.
- Built-in CJK prompts now require contextual meanings, faithful example translations, and language-specific pronunciation/form accuracy. A narrowly scoped Japanese repair corrects the proven `質問を聞きました`/“ask” contradiction without changing legitimate “hear a question” output.
- Prompt tiếng Anh ưu tiên đúng nghĩa ngữ cảnh, lemma/IPA/CEFR, collocation/register và ví dụ tự nhiên ngắn; prompt batch/chat bỏ phần hướng dẫn lặp để tăng chất lượng với ít input token hơn. Prompt mặc định/cache được nâng version để không dùng lại kết quả cũ.
- DeepSeek V4 card generation now explicitly defaults to non-thinking mode, selected by the Japanese 3×20 benchmark: the same 100% quality score as Flash thinking and Pro non-thinking at materially lower measured cost and latency.

#### 🐛 Fixed
- Knowledge đổi hành động AI thành `GỬI & TẠO THẺ`, làm rõ ô `Yêu cầu thêm` và giữ nó trên pipeline tạo thẻ/schema Knowledge thay vì AI Chat của Language.
- Knowledge không còn hiển thị hoặc gọi gián tiếp công cụ `Batch Từ Vựng`; nhiều Knowledge card tiếp tục đi qua AI extract/schema riêng có chunking thay vì workflow Vocabulary/Grammar của Language.
- Import Knowledge chỉ quét duplicate theo Question/Concept đã chuẩn hóa trong đúng Knowledge model + deck; cancel giữa batch tự phục hồi phần đã ghi và Undo batch gần nhất xóa note mới đồng thời khôi phục note đã update mà không chạm note Language.
- Opening Bento Forge no longer performs a TTL-triggered collection scan on the UI thread. The one-time history bootstrap is serialized through Anki `QueryOp`, reports progress, can be cancelled without saving partial results, and subsequent imports keep history current incrementally.
- Release artifacts now include the required `workers/` package and exclude `__pycache__`, `.pyc`, and `.pyo` bytecode files.
- Prompt Editor trong Cài đặt AI nay nạp sẵn cả tab Từ vựng lẫn Ngữ pháp và lưu nội dung theo ngôn ngữ vừa rời khỏi, tránh tab prompt rỗng hoặc ghi nhầm dữ liệu khi đổi ngôn ngữ.
- Compile gate now covers every tracked Python file, including `scripts/`; invalid markers that prevented `scripts/fetch_ankiforge_info.py` from compiling were removed.

### 2026-08-15 — Phiên bản: `17.1.0` → `17.2.0`

#### ✨ Added
- V17.2: Nhấp vào thanh chi phí AI ở góc dưới trái để xem lịch sử từng request theo model, thời điểm, thời lượng, loại công việc, input/output token và chi phí. Có lọc theo model/công việc/ngày hoặc khoảng ngày, sắp xếp chi phí và input/output cao–thấp, tổng cho tập dữ liệu đang lọc, cùng thao tác xóa lịch sử. Lịch sử chỉ giữ metadata usage (tối đa 2.000 lượt) trong Anki profile; không giữ prompt, phản hồi, API key hay URL API.
- B6: Thẻ từ vựng mặc định có field `Usage Note` hiển thị ở mặt sau khi có nội dung; prompt chỉ yêu cầu ghi chú collocation/register ngắn khi thực sự giúp phân biệt cách dùng. Field `Usage` của thẻ ngữ pháp cũng nhận thêm ghi chú này khi cần, không thêm schema/output field mới.
- Bộ benchmark AI có phiên bản hóa cho cùng một danh sách 20 từ tiếng Nhật: runner tự gọi nhiều model/chế độ thinking qua provider đã cấu hình, lưu card/run JSON và bảng so sánh coverage, cấu trúc có thể đưa vào Xưởng, cảnh báo xác định được, token/chi phí/thời gian mỗi thẻ cùng rubric review ngữ nghĩa. Báo cáo local không chứa API key hoặc dữ liệu benchmark riêng.
- Dữ liệu người dùng (cấu hình, trạng thái Factory, lịch sử import và cache) được lưu theo Anki profile, ghi JSON atomic, có migration/backup và giới hạn dung lượng hoặc TTL.
- API key sử dụng OS credential store; log tự che API key, token và Authorization header. AI, batch và import có cancellation xuyên suốt để dừng tác vụ dài an toàn hơn.
- Giới hạn phiên AI theo ký tự đầu vào, token và chi phí; UI hiển thị ước lượng trước khi chạy nhưng chỉ lưu số liệu tổng hợp.
- Lựa chọn SRS theo deck: Combo mặc định giữ một lịch chung; chế độ độc lập tạo năm lịch kỹ năng. Migration có checkpoint/Undo, giữ lịch sử `ord=0` và có thể chạy lặp lại an toàn.
- Preset AI provider và thông báo lỗi kết nối/cấu hình đầy đủ hơn; bổ sung hợp đồng kiểm thử cho preset và khả năng tương thích thao tác Anki.
- Thêm các owner thuần Python cho HTTP AI, trích xuất tài liệu, cache kết quả, parse phản hồi và lịch sử import; các API cũ vẫn được re-export để giữ tương thích.
- Tách template thẻ và prompt mặc định theo từng ngôn ngữ Nhật/Trung/Hàn, có regression test để bảo toàn nội dung và registry hiện có.
- Thêm `DEBUGGING.md`, `COMPATIBILITY.md`, `RELEASE_CHECKLIST.md`, artifact build có SHA-256/SBOM, cùng harness kiểm thử cô lập hai vòng dùng chung với CI.

#### 🔧 Changed
- V17.2: Cập nhật preset model AI theo catalog hiện hành: DeepSeek V4 Flash/Pro, OpenAI GPT-5.6 (Sol/Terra/Luna), Gemini 3.6/3.5/3.1 và 2.5, Claude 5/Haiku 4.5; OpenRouter có alias `~openai/gpt-latest`; Ollama/LM Studio thêm Qwen 3.5 và Gemma 4. Các model cũ phổ biến vẫn còn để không làm hỏng cấu hình đã lưu.
- `AnkiSmartFactory` và wiring Qt/Anki chuyển sang `ui/factory_dialog.py`; package root chỉ còn compatibility facade.
- Thao tác Collection, import, model lifecycle và kiểm định thẻ được cô lập rõ hơn; phát hiện near-duplicate nhưng không tự merge, báo cáo import không chứa nội dung thẻ hoặc lỗi chi tiết.
- Bỏ tự động cài `python-docx`/`openpyxl`; dependency thiếu được báo bằng thông điệp VI/EN và hướng dẫn cài thủ công.
- Chuẩn hóa compatibility theo `manifest.json`, diagnostic event code và logging theo Anki profile.

#### 🐛 Fixed
- V17.2: API key nay được cô lập theo từng AI provider (và từng endpoint Custom). Chuyển provider trong Cài đặt AI sẽ nạp key đã lưu của provider đó, không còn dùng hoặc ghi đè key của provider trước.
- **Kiểm định lô hàng chống lách theo mode/lô AI:** Chuẩn hóa Unicode, khoảng trắng và dấu câu trước khi đối chiếu; lập chỉ mục cả các mục đã được chấp nhận trong lô hiện tại để chặn mục lặp xuất hiện sau đó. So khớp cùng nghĩa không còn phụ thuộc vào việc chọn cấp độ. Cùng mặt chữ/pattern nhưng khác nghĩa, kể cả Grammar mode, luôn phải được người dùng phê duyệt rõ ràng trước khi thêm.
- Phản hồi từ DeepSeek reasoning model nay lấy đúng final content khi `content` rỗng, đồng thời bật JSON mode cho API gốc để giảm lỗi parse JSON.
- Cấu hình provider không còn tự chèn API key mặc định; các truy vấn Anki có nhánh tương thích và thông báo lỗi rõ ràng hơn.

## [V17.1] — 2026-08-12

### ✨ Added
- **🌐 Chế độ chuyển ngôn ngữ EN–VI (không hardcode)**: Hệ thống i18n `t()` phủ rộng lên UI/workers; vẫn còn vài chỗ hổng sẽ hoàn thiện dần (utils/i18n.py).
- **📜 LICENSE (MIT)** + **⚙️ GitHub Actions CI** (chạy pytest 3.11/3.12) + **🤝 CONTRIBUTING.md** — nâng mức sẵn sàng cộng đồng.
- **✏️ Sửa Prompt & Schema AI (không cần sửa code)**: Nút "✏️ Sửa Prompt / Schema AI" trong Cài Đặt AI mở dialog chỉnh System Prompt + mẫu JSON cho từng ngôn ngữ (Từ vựng & Ngữ pháp) — đổi luật trích xuất, schema, field_count ngay trên giao diện (ui/prompt_editor.py).
- **🗂 Field Map Editor (Mức 1 — đóng "schema lock-in" ở lớp thẻ)**: Tab "🗂 Field Map" trong dialog — bảng map key JSON (tự sinh từ template đã sửa) → Field Anki (chỉnh được, key mới tự suy tên field). Khi Lưu: **tự THÊM field mới vào Note Type** (6 model: 3 ngôn ngữ × từ vựng/ngữ pháp nếu đã tồn tại); mọi nơi dùng `self._cfg()` (kiểm định/merge/import/tạo model) đều nhận `json_field_map` + `all_fields` HIỆU LỰC (defaults + ghi đè). Lưu trong `utils/ai_prompts.json` (`field_map`).
- **🃏 Card Render tự động (Mức 2 — field mới TỰ HIỆN TRÊN THẺ)**: `mode/card_render.py` — sau khi thêm field mới, khối "extra fields" được APPEND vào cuối template thẻ (không phá template gốc), mỗi field bọc `{{#Field}}...{{/Field}}` (rỗng thì ẩn) + inline styles. Cột **"Hiển thị"** trong Field Map chọn vị trí: Chỉ mặt sau / Cả hai mặt / Chỉ mặt trước (`card_show` trong `ai_prompts.json`). `get_or_create_model`/`_force_rebuild_model`/editor save đều dùng builder → **Lưu xong là thẻ hiện field mới ngay**, không cần sửa template tay.
- **🎛️ Prompt Config ra ngoài**: Prompt + JSON template lưu trong `utils/ai_prompts.json` (gitignored) qua `utils/prompt_config.py`; `get_system_prompt()`/`get_json_template()` trả giá trị hiệu lực (defaults + ghi đè), có validate JSON, preview prompt đầy đủ, Reset mặc định.
- **⚡ Cache tự invalidate khi sửa prompt**: Cache key của AI giờ gồm `get_prompt_signature()` (md5 phần ghi đè prompt) → sửa prompt/schema → kết quả AI cũ tự bị bỏ, không dùng lại.

### 🔧 Changed
- **utils/batch_processor.py**: chuyển từ dùng `_SYSTEM_PROMPTS/_JSON_TEMPLATES/_GRAMMAR_*` (dict cứng) sang `get_system_prompt()`/`get_json_template()` (tôn trọng ghi đè).
- **utils/ai_extractor.py**: `_PROMPT_VERSION` 3 → 4 (đổi format cache key); `get_json_template()`/`get_grammar_json_template()` giờ đọc từ prompt_config.
- **__init__.py `_cfg()`**: bơm `apply_field_map_to_cfg()` → json_field_map/all_fields/card_show hiệu lực cho mọi flow (kiểm định, merge, import, tạo model).
- **__init__.py get_or_create_model/_force_rebuild_model**: dùng `mode.card_render.build_qfmt/build_afmt` → template thẻ tự append field tuỳ chỉnh.
- **Sửa lỗi gõ lặp** trong prompt Hàn: "(습니다/습니다/존댓말)" → "(습니다/존댓말)" (giúp prompt compact lại dưới 1400 ký tự).

## [V17.0] — 2026-08

### ✨ Added
- **🇰🇷 Ngôn ngữ Hàn Quốc (Korean)**: Ngôn ngữ thứ 3 — từ vựng & ngữ pháp tiếng Hàn với đầy đủ 5 chế độ học (Hàn→Việt, Việt→Hàn, Ghép chữ, Romanization, Ẩn chữ), Note Type riêng, AI prompt trích xuất (Hangul + Romanization chuẩn Revised Romanization), TTS giọng Hàn (ko-KR), bộ lọc cấp độ TOPIK I/II (Language/korean.py, mode/templates.py, mode/css.py, audio/engine.py, utils/ai_extractor.py)
- **🔤 Romanization cho tiếng Hàn**: Field Romanization + Example Romanization/Example2 Romanization hiển thị trên thẻ, đọc/ghi đầy đủ trong JSON (Language/korean.py, mode/templates.py)
- **🎓 Bộ lọc TOPIK Level**: level_choices TOPIK I/TOPIK II/1-6 trong bộ lọc cấp độ (Language/korean.py)
- **🧩 KO_WB_POOL**: Word-Building ghép chữ Hangul cho tiếng Hàn (mode/shared.py)
- **🎯 Chọn lọc & xuất xưởng theo lựa chọn**: Sau khi bấm Kiểm Định, "Thẻ chờ xuất xưởng" hỗ trợ tìm kiếm theo từ/nghĩa, lọc nhanh theo loại (✨ Mới / 🔄 Cập nhật / ⚠️ Trùng mờ / 🔍 Nghĩa khác), tích chọn từng thẻ hoặc chọn theo khoảng số "Từ-đến" — **đổi khoảng là TỰ ĐỘNG tích chọn** các thẻ trong khoảng đó (theo danh sách đang hiển thị), chọn deck đích qua deck_chooser để đẩy vào — sau khi xuất, danh sách tự cập nhật bỏ các thẻ đã xuất, cho phép đẩy tiếp nhóm còn lại sang deck khác (__init__.py)
- **💾 Giữ thẻ trong xưởng khi đóng cửa sổ**: Thẻ chờ xuất xưởng + kho hàng được lưu vào factory_state.json theo từng luồng (ngôn ngữ × từ vựng/ngữ pháp) và khôi phục khi mở lại Factory; thẻ chỉ bị xóa khi người dùng chủ động bấm "🧹 Hủy Hàng" — xóa toàn bộ hoặc xóa các thẻ đã chọn (__init__.py)
- **📚 Lịch Sử AI (xem lại & import lại)**: Nút "Lịch Sử AI" mở dialog liệt kê toàn bộ từ vựng đã lưu (AI trích xuất / import) — tìm theo từ/nghĩa, lọc theo ngôn ngữ, tích chọn nhiều từ rồi "📥 Đưa Vào Xưởng" để Kiểm Định & xuất xưởng lại, xem được ngay cả sau khi đóng Factory. `add_to_import_history` giờ lưu cả item gốc để tái dựng đầy đủ (ui/history_dialog.py, utils/ai_extractor.py: get_import_history_items)

### 🔧 Changed
- **Version bump**: Tất cả model names V16.0 → V17.0 (Language/japanese.py, Language/chinese.py)
- **old_model_names**: Thêm V16.0 vào danh sách migration cho Nhật & Trung
- **audio/engine.py**: `_MODEL_LANG_MAP` thêm V17.0 + Korean models (ko)
- **i18n**: Thêm `lang_korean`, cập nhật title/version sang V17.0 (utils/i18n.py)
- **manifest.json**: version 17.0.0, thêm `korean` vào languages/keywords
- **AI prompts**: `_PROMPT_VERSION` 2 → 3 (invalidate cache) do thêm Korean prompts (utils/ai_extractor.py)

### 🐛 Fixed
- N/A

## [V16.1] — 2026-08

### ✨ Added
- **🎯 Card gộp 5 chế độ (1 từ = 1 card)**: Thay vì 1 từ tạo 5 card riêng (Nhật→Việt, Việt→Nhật, Ghép chữ, Furigana, Ẩn chữ) giờ chỉ tạo **1 card duy nhất** → deck đếm đúng số từ vựng, hết tình trạng số thẻ học nhân 5. Trong card có **thanh chọn chế độ** chuyển đổi bằng JS (mode/), đồng bộ mode qua `pycmd('ai_factory_set_mode:...')`
- **🎛️ Nút chọn chế độ học ở màn hình Overview**: Patch `Overview._table` (wrap, không ghi đè Onigiri) → chèn bộ chọn mode + nút "Study now" cạnh nút của Onigiri; mode lưu vào `mw.col.conf` (hooks/overview_mode.py)
- **🔁 Migration tự động 5-card → 1-card**: Model cũ (5 template) khi tái tạo sẽ giữ card mode chính + lịch sử học, xóa 4 card thừa của từng note (__init__.py: `_drop_extra_combo_cards`)
- **⬇️ Dropdown chọn mode trong Factory**: Thêm chọn chế độ học mặc định trong add-on, đồng bộ với Study now (__init__.py)

### 🔧 Changed
- **LANG_TEMPLATES**: Mỗi ngôn ngữ chỉ còn 1 cặp template combo (trước đây 5 cặp)
- **template_names**: "1. Nhật → Việt" → "1. Tổng hợp (5 chế độ)" (Language/*.py)
- **manifest.json**: `template_count` 5 → 1, thêm `study_modes`
- **Type answer**: Mode chính (Nhật→Việt) dùng `{{type:Meaning}}` chuẩn Anki; Việt→Nhật & Furigana/Pinyin tự kiểm tra bằng JS (mode/shared.py `_COMBO_MODE_JS`)

## [V16.0] — 2026-08

### ✨ Added
- **💾 Lưu trạng thái 2 luồng × 2 ngôn ngữ**: Text + file kẹp của Từ vựng & Ngữ pháp (mỗi ngôn ngữ) được lưu riêng vào factory_state.json, khôi phục khi mở lại Factory — không lẫn nhau, đỡ phải gửi/gọi lại AI. "Xóa Text"/"Bỏ File" sẽ xóa luồng đó (__init__.py)
- **🔪 Cắt đoạn mịn hơn**: chunk mặc định 12k → **8k ký tự/lần** (config 3k-15k) → chất lượng ví dụ/ngữ pháp cao hơn, vẫn xử lý hết văn bản dài (utils/ai_extractor.py, ui/ai_settings.py)
- ** Ngữ pháp như giảng viên đọc giáo trình**: Prompt ngữ pháp mới — đọc toàn bộ văn bản để hiểu ngữ cảnh + từ vựng đi kèm, tạo ví dụ đa dạng; CÙNG PATTERN–KHÁC NGHĨA → nhiều thẻ riêng; ĐÁNH DẤU pattern trong ví dụ bằng `<b>…</b>` + CSS màu nổi bật (utils/ai_extractor.py, mode/css.py)
- **🐛 Fix "Đổ vào xưởng" ở chế độ ngữ pháp**: Dialog Xem Trước giờ hiểu chế độ ngữ pháp (cột Pattern/Usage/Explanation thay vì simplified/traditional), lọc đúng key pattern, tái tạo dùng prompt ngữ pháp; Kiểm Định coi "cùng pattern–khác nghĩa" là thẻ MỚI (ui/ai_preview.py, __init__.py)
- **📏 Mở rộng nội dung xử lý**: Văn bản dài 50k-100k+ được xử lý HẾT nhờ tự chia đoạn (chunk 8k mặc định, config 3k-15k) → không còn bị cắt. AI Chat cap đọc theo cài đặt (mặc định 45k) (utils/ai_extractor.py, __init__.py, ui/ai_settings.py)
- **🐛 Fix JSON bị cắt (tràn output)**: DeepSeek giới hạn output ~8192 token/response → chunk quá lớn khiến JSON đứt giữa chừng. Đã: chunk mặc định 8k + cap 15k, tự hạ config cũ (45k→15k) khi đọc, cảnh báo rõ khi output bị cắt, và thông báo lỗi gợi ý giảm độ dài (utils/ai_extractor.py, ui/ai_settings.py)
- **🧠 Mức độ suy nghĩ (reasoning_effort)**: Bộ chọn Thấp/Trung bình/Cao trong Cài Đặt AI → truyền `reasoning_effort` vào mọi request (trích xuất, ngữ pháp, batch, chat). DeepSeek: chat = nhanh/rẻ, reasoner = sâu/đắt (utils/ai_extractor.py, utils/batch_processor.py, ui/ai_settings.py)
- **⚡ Tối ưu Token & chất lượng AI**: Chỉ gửi từ vựng/ngữ pháp trùng với nội dung vào prompt (thay vì toàn bộ deck → giảm mạnh input); nén system prompt giữ nguyên chất lượng; hướng dẫn output gọn (explanation ≤2 câu, ví dụ 5-12 từ); tổng hợp token/chi phí theo toàn bộ chunk; tránh trích trùng qua biên giới đoạn (utils/ai_extractor.py, utils/batch_processor.py)
- **📎 Kẹp file tài liệu tham khảo**: Đính kèm TXT/MD/CSV/PDF/DOCX/XLSX → AI đọc nội dung file làm tài liệu để trích xuất từ vựng/ngữ pháp. Auto-cài python-docx/openpyxl khi thiếu (utils/ai_extractor.py, __init__.py)
- **📘 Ngữ pháp (Grammar Note Type)**: Chế độ thẻ ngữ pháp riêng cho tiếng Nhật & Trung — Note Type riêng + template 2 chiều (Cấu trúc→Nghĩa, Nghĩa→Cấu trúc) + AI prompt trích xuất pattern/cách dùng/công thức (Language/*.py, mode/templates.py, mode/css.py, utils/ai_extractor.py)
- **Batch AI Processing**: Xử lý danh sách hàng trăm/nghìn từ qua AI (ui/batch_dialog.py, utils/batch_processor.py, workers/batch_workers.py)
- **Two-Pass AI Architecture**: Pass 1 làm giàu từ vựng, Pass 2 AI tổ chức Parent/Sub Deck
- **i18n**: Hỗ trợ tiếng Việt + English (utils/i18n.py, 70+ translation keys)
- **AES-GCM Encryption**: Mã hóa API key at rest với Fernet/PBKDF2
- **Incremental Deck Cache**: Cache thông minh, chỉ query notes mới (utils/deck_cache.py)
- **Pre-commit Hooks**: black, ruff, security scanning (.pre-commit-config.yaml)
- **Kiến trúc module hóa**: Tách deck_cache, i18n, workers, UI dialogs, hooks
- **56 automated tests**: Unit + integration + batch processor tests

### 🔧 Changed
- **Version bump**: Tất cả model names V15.0 → V16.0
- **old_model_names**: Thêm V15.0 vào danh sách migration
- **Logging system**: Thay thế toàn bộ print() bằng logging module
- **CSS refactored**: Shared base CSS, giảm 80% trùng lặp
- **Thread safety**: threading.Lock cho voice/speed settings
- **Background Deck Scan**: Không chặn UI khi quét deck lớn
- **API key**: Xóa khỏi source code, thêm .gitignore + example file

### 🐛 Fixed
- 36 bare `except:` → `except Exception:`
- 18 `print()` → logging
- `AudioEngine` thread safety (Lock cho shared state)
- Deck scan chặn UI → DeckScanWorker background thread

---

## [V15.0] — 2024-07

### ✨ Added
- AI Chat với system prompt "GIA SƯ NGÔN NGỮ" có context Anki
- Lịch sử import từ vựng (import_history.json) — AI biết từ nào đã có
- Dialog "Nghĩa Khác" — phát hiện từ cùng mặt chữ nhưng khác nghĩa
- Tốc độ phát audio tùy chỉnh (0.25×–4.0×), lưu riêng từng ngôn ngữ
- Speed Control overlay khi review thẻ
- Nút dừng AI (chat + extract)
- Đồng hồ đếm thời gian AI đang chạy
- Retry logic cho API calls (2 lần, timeout thông minh)
- Fallback reasoning_content cho DeepSeek Reasoner
- Hỗ trợ OpenRouter, LM Studio presets
- Nút "Tái Tạo Model" cập nhật template/CSS

### 🔧 Changed
- Voice JA: chỉ còn Nanami & Keita (AoiNeural, DaichiNeural đã bị Microsoft loại bỏ)
- Cache AI: TTL 7 ngày (từ permanent)
- System prompt AI: yêu cầu ví dụ "có hồn", khẩu ngữ tự nhiên
- Import history: tách biệt Japanese/Chinese rõ ràng
- UI: thêm preset buttons cho API settings

### 🐛 Fixed
- DeepSeek Reasoner trả về content rỗng → fallback reasoning_content
- Timeout khi gọi model reasoning → timeout 600s
- Lỗi font tiếng Trung trên một số system

---

## [V14.0] — 2024-06

### ✨ Added
- Hỗ trợ tiếng Trung (Chinese)
- Multi-language architecture (Language/ package)
- AI trích xuất từ vựng (OpenAI/DeepSeek/Ollama)
- Preview & chỉnh sửa thẻ sau AI extract
- TTS đa engine: Edge TTS, gTTS, VoiceVox
- 5 loại thẻ: Nhật→Việt, Việt→Nhật, Ghép chữ, Furigana, Ẩn chữ cái
- Word Building game (drag & drop tiles)
- Handwriting practice canvas
- Letter Gap game (điền chữ cái bị ẩn)
- Kiểm định lô hàng (verify batch) với phát hiện trùng lặp
- Import từ JSON/TXT file

---

## [V13.0 và trước] — 2024-05

- Chỉ hỗ trợ tiếng Nhật
- Import JSON thủ công
- Template cơ bản
- Audio với Google TTS
