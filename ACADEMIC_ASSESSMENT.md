# 🎓 Đánh giá Bento Forge V17.1.0 — Vị thế học thuật & Hướng phát triển

> **Ngày đánh giá:** 2026-08-15
> **Phạm vi:** Toàn bộ add-on (kiến trúc, code, test, tài liệu, bảo mật, UX)
> **Mục tiêu:** Đánh giá hiện trạng và đề xuất lộ trình nâng tầm vị thế học thuật
> **Nguyên tắc cốt lõi:** Bento Forge là **add-on đúc thẻ tự động chất lượng cao** — không phải "everything app". Mọi quyết định phát triển phải phục vụ core competency này.

---

## 1. TỔNG QUAN HIỆN TRẠNG

### 1.1 Điểm mạnh cốt lõi

| Khía cạnh | Đánh giá | Bằng chứng |
|-----------|----------|------------|
| **Đa ngôn ngữ** | ⭐⭐⭐⭐⭐ | 3 ngôn ngữ (Nhật/Trung/Hàn) × 2 chế độ (Từ vựng/Ngữ pháp) × 5 bài tập |
| **Kiến trúc module hóa** | ⭐⭐⭐⭐ | Tách rõ `Language/`, `mode/`, `audio/`, `utils/`, `workers/`, `ui/`, `hooks/` |
| **An toàn dữ liệu** | ⭐⭐⭐⭐⭐ | Profile-scoped persistence, atomic write, migration có backup/rollback |
| **Bảo mật API key** | ⭐⭐⭐⭐⭐ | OS credential store (keyring), không lưu XOR/plaintext, log redaction |
| **Chất lượng test** | ⭐⭐⭐⭐ | ~400 tests, 30 files, isolated harness, CI Python 3.9/3.11 |
| **Tài liệu AI-agent** | ⭐⭐⭐⭐⭐ | Hệ thống `.claude/skills/` 12 skills, progressive disclosure tiết kiệm token |
| **SRS học tập** | ⭐⭐⭐⭐ | Combo mode + SRS độc lập opt-in, migration an toàn, semantics rõ ràng |
| **AI integration** | ⭐⭐⭐⭐⭐ | 6+ providers, prompt editor, field map, cache invalidation, session policy |

### 1.2 Điểm yếu / Khoảng trống

| Khía cạnh | Vấn đề | Mức độ |
|-----------|--------|--------|
| **`i18n.py` quá lớn** | 2.016 dòng — translation dict khổng lồ | 🟡 Trung bình |
| **`templates.py` quá lớn** | 1.315 dòng — HTML template cứng | 🟡 Trung bình |
| **`batch_processor.py` quá lớn** | 1.061 dòng | 🟡 Trung bình |
| **Chi phí AI chưa tối ưu triệt để** | Free tier rất hạn chế — cần tối ưu token/chi phí hơn nữa | 🔴 Cao |
| **Chưa có bằng chứng hiệu quả** | Không có số liệu retention rate, time-to-mastery | 🟡 Trung bình |
| **Chưa có cộng đồng** | Không có forum/discord/reddit | 🟡 Trung bình |

---

## 2. ĐÁNH GIÁ CHI TIẾT THEO TRỤC

### 2.1 Kiến trúc & Kỹ thuật (Điểm: 8.5/10)

**Điểm mạnh:**
- ✅ Tách use-case/adapter boundary (`model_lifecycle.py`, `anki_adapter.py`, `srs_policy.py`)
- ✅ HTTP client thuần stdlib, không phụ thuộc Anki/Qt (`ai_http_client.py`)
- ✅ Document extractors tách riêng (`document_extractors.py`)
- ✅ Thread-safe state (`threading.Lock` trong `audio/engine.py`)
- ✅ Cancellation event xuyên suốt (không `QThread.terminate()`)
- ✅ CollectionOp/QueryOp cho Anki collection access
- ✅ `__init__.py` là compatibility facade; orchestration UI thuộc `ui/factory_dialog.py` (C1 hoàn thành 2026-08-15)
- ✅ `ai_extractor.py` còn 1.489 dòng; HTTP/document/cache/prompt/parser/history có owner riêng (C2 hoàn thành 2026-08-15)

**Điểm yếu:**
- ❌ `i18n.py` translation dict nên tách thành file JSON riêng
- ❌ `templates.py` HTML nên tách thành file template riêng (không hardcode trong Python)

### 2.2 Chất lượng Test (Điểm: 8.0/10)

**Điểm mạnh:**
- ✅ ~400 tests, 30 files — coverage rộng
- ✅ Isolated harness (`scripts/test_isolated.ps1`) — chạy 2 vòng, worktree check
- ✅ Profile-scoped temp paths (`conftest.py`)
- ✅ CI Python 3.9/3.11
- ✅ Smoke harness mock Anki public API

**Điểm yếu:**
- ❌ Chưa có property-based testing (Hypothesis)
- ❌ Chưa có mutation testing (kiểm tra chất lượng test thật sự)
- ❌ Chưa có test cho UI automation (QtTest)

### 2.3 Bảo mật & Quyền riêng tư (Điểm: 9.0/10)

**Điểm mạnh:**
- ✅ API key → OS credential store (keyring)
- ✅ Log redaction (Authorization, api_key, sk-/rk-/pk- patterns)
- ✅ Không telemetry — chỉ aggregate usage cục bộ
- ✅ Profile-scoped data (không ghi vào addon dir)
- ✅ Atomic write + validation + migration backup

**Điểm yếu:**
- ❌ Chưa có threat model document
- ❌ Chưa có security audit bên ngoài

### 2.4 UX & Accessibility (Điểm: 7.5/10)

**Điểm mạnh:**
- ✅ i18n EN/VI
- ✅ Keyboard navigation + accessible name
- ✅ Dark/light/midnight themes
- ✅ Glassmorphism theme engine
- ✅ Speed control, interactive games

**Điểm yếu:**
- ❌ Chưa có screen reader testing
- ❌ Chưa có color contrast audit
- ❌ Chưa có onboarding flow cho người mới

### 2.5 Tài liệu & Cộng đồng (Điểm: 8.0/10)

**Điểm mạnh:**
- ✅ `.claude/skills/` — hệ thống AI-agent documentation xuất sắc
- ✅ README, CHANGELOG, COMPATIBILITY, DEBUGGING, RELEASE_CHECKLIST
- ✅ CONTRIBUTING.md, LICENSE (MIT)
- ✅ CI badge, version badge

**Điểm yếu:**
- ❌ Chưa có user documentation website
- ❌ Chưa có video tutorials
- ❌ Chưa có community forum/discord

---

## 3. ĐÁNH GIÁ CHI TIẾT: TỐI ƯU TOKEN (Điểm: 7.5/10)

### 3.1 Đã làm tốt

| Cơ chế | Mô tả | Bằng chứng |
|--------|-------|------------|
| ✅ **Chỉ gửi từ trùng nội dung** | `_format_existing_context()` — chỉ liệt kê từ ĐÃ CÓ trong deck mà THỰC SỰ xuất hiện trong văn bản đang xử lý, không gửi toàn bộ deck | `ai_extractor.py:1000-1051` |
| ✅ **Giới hạn số từ hiển thị** | `_MAX_EXISTING_SHOWN` — chỉ hiển thị tối đa N từ trùng, phần còn lại chỉ báo số lượng | `ai_extractor.py:1034-1047` |
| ✅ **Cache AI 7-14 ngày** | Cache kết quả AI theo `_PROMPT_VERSION + prompt_signature + lang + instruction + existing_hash + text` — tránh gọi lại cùng nội dung | `ai_result_cache.py:30-160` |
| ✅ **Cache deck vocab 30 phút** | `get_existing_vocab_from_deck()` — cache danh sách từ đã có, không quét lại mỗi lần | `utils/deck_cache.py` |
| ✅ **Chunking 8k ký tự** | Tự chia văn bản dài thành chunk 8k — tránh tràn output token (~8192) | `ai_extractor.py:252` |
| ✅ **Session policy** | Giới hạn input/token/chi phí theo phiên, ước lượng trước khi chạy | `ai_extractor.py:146-176` |
| ✅ **Cost tracking** | Tính chi phí USD từ token usage, hiển thị cho người dùng | `ai_extractor.py:375-400` |
| ✅ **Prompt signature** | `get_prompt_signature()` — md5 phần ghi đè prompt → sửa prompt tự invalidate cache | `ai_extractor.py:413` |
| ✅ **Reasoning effort** | `_apply_reasoning_effort()` — chọn mức suy nghĩ Thấp/TB/Cao | `ai_extractor.py:335-343` |
| ✅ **Truncated output detection** | `_check_truncated_output()` — phát hiện JSON bị cắt, gợi ý giảm chunk | `ai_extractor.py:346-361` |
| ✅ **Safety net lọc trùng** | Lọc lại từ trùng với deck sau khi AI trả về | `ai_extractor.py:1181-1190` |

### 3.2 Chưa làm / Cần cải thiện

| Khoảng trống | Mô tả | Mức độ |
|--------------|-------|--------|
| ❌ **Chưa có Model Routing** | Luôn dùng 1 model cấu hình — không tự chọn model rẻ nhất đủ chất lượng | 🔴 Cao |
| ❌ **Chưa có Semantic Caching** | Cache chỉ exact match — không tận dụng được kết quả tương tự | 🔴 Cao |
| ❌ **Prompt vẫn còn dài** | System prompt ~500-800 ký tự/ngôn ngữ × 2 (VI/EN) × 2 (vocab/grammar) — có thể nén thêm | 🟡 TB |
| ❌ **Chưa có Free Tier Detection** | Không phát hiện provider free tier, không cảnh báo khi sắp hết quota | 🟡 TB |
| ❌ **Chưa có Batch Optimization** | Mỗi request gửi 1 chunk — chưa gộp nhiều từ vào 1 request tối ưu | 🟡 TB |
| ❌ **Chưa có Token Budget UI** | Chưa hiển thị rõ chi phí ước tính trước khi chạy (chỉ hiển thị sau) | 🟡 TB |
| ❌ **Chưa có Local Model Priority** | Ollama/LM Studio có nhưng không được ưu tiên khuyến nghị | 🟢 Dễ |

### 3.3 Ước tính token hiện tại

| Tình huống | Input token (ước tính) | Output token (ước tính) | Tổng |
|------------|----------------------|------------------------|------|
| Đúc 10 từ (văn bản ngắn 500 ký tự) | ~1.5k (prompt) + ~0.5k (text) | ~1.5k (10 từ × 10 field) | **~3.5k** |
| Đúc 50 từ (văn bản 4k ký tự) | ~1.5k (prompt) + ~4k (text) | ~7.5k (50 từ × 10 field) | **~13k** |
| Đúc 100 từ (văn bản 8k ký tự) | ~1.5k (prompt) + ~8k (text) | ~15k (100 từ × 10 field) | **~24.5k** |

> **Nhận xét:** Với DeepSeek-chat ($0.14/1M input, $0.28/1M output), đúc 100 từ tốn ~$0.008. Với gpt-4o-mini ($0.15/1M input, $0.60/1M output), tốn ~$0.013. **Free tier DeepSeek (~$0.5 credit) đủ đúc ~60.000 từ** — khá tốt nhưng vẫn có thể tối ưu thêm.

---

## 4. ĐÁNH GIÁ CHI TIẾT: CHẤT LƯỢNG THẺ (Điểm: 8.0/10)

### 4.1 Đã làm tốt

| Cơ chế | Mô tả | Bằng chứng |
|--------|-------|------------|
| ✅ **Prompt rất chi tiết** | "VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ" — yêu cầu ví dụ khẩu ngữ đời thực, cảm xúc thật, tránh câu SGK vô hồn | `ai_prompt_defaults.py:28-108` |
| ✅ **2 ví dụ đa dạng** | Ex1: khẩu ngữ đời thực (よ/ね/よね, 어요/아요) — Ex2: trang trọng (です・ます/敬語, 습니다) | `ai_prompt_defaults.py:28-108` |
| ✅ **Cấp độ khớp chuẩn** | JLPT N5→câu cực ngắn, N2-N1→phức tạp; HSK1→cực ngắn, HSK5-6→thành ngữ; TOPIK I→đơn giản | `ai_prompt_defaults.py:28-108` |
| ✅ **Chống trùng lặp** | "CHỐNG TRÙNG: bỏ qua mọi từ trong TỪ ĐÃ CÓ" + safety net lọc lại | `ai_prompt_defaults.py:28-108`, `ai_extractor.py:727-736` |
| ✅ **Grammar đánh dấu pattern** | Bọc `<b>...</b>` quanh pattern trong ví dụ — nổi bật trên thẻ | `ai_prompt_defaults.py:256-352` |
| ✅ **Cùng pattern - khác nghĩa** | Tạo nhiều entry riêng khi pattern có nghĩa khác nhau | `ai_prompt_defaults.py:256-352` |
| ✅ **Như giảng viên đọc giáo trình** | Đọc toàn bộ văn bản, hiểu ngữ cảnh, ví dụ bám ngữ cảnh thực | `ai_prompt_defaults.py:256-352` |
| ✅ **Parse JSON robust** | `parse_ai_json_with_comment()` — xử lý markdown, dict, array, comment | `ai_response_parser.py:9-61` |
| ✅ **Truncated output detection** | Phát hiện JSON bị cắt, gợi ý giảm chunk | `ai_extractor.py:346-361` |
| ✅ **Prompt editor** | Người dùng tự sửa prompt/schema/field map không cần code | `ui/prompt_editor.py` |
| ✅ **Field map editor** | Map key JSON → field Anki, tự thêm field mới vào Note Type | `mode/card_render.py` |

### 4.2 Chưa làm / Cần cải thiện

| Khoảng trống | Mô tả | Mức độ |
|--------------|-------|--------|
| ❌ **Chưa có Quality Scoring** | Không tự đánh giá chất lượng thẻ (điểm 0-100) trước khi xuất | 🔴 Cao |
| ❌ **Chưa có Error Detection** | Không phát hiện lỗi ngữ pháp/ngữ nghĩa trong thẻ AI tạo | 🔴 Cao |
| ❌ **Chưa có Level Validation** | Không kiểm tra từ có đúng cấp độ JLPT/HSK/TOPIK hay không | 🟡 TB |
| ❌ **Chưa có Multi-sense Disambiguation** | Không phân biệt rõ các nghĩa khác nhau của từ đa nghĩa | 🟡 TB |
| ❌ **Chưa có Collocation/Usage Notes** | Không thêm ghi chú cách dùng, collocation, register | 🟡 TB |
| ❌ **Chưa có Context-aware Examples** | Ví dụ phụ thuộc hoàn toàn vào prompt — chưa có validation tự động | 🟡 TB |

### 4.3 Đánh giá prompt hiện tại

| Ngôn ngữ | Độ dài prompt | Chất lượng | Nhận xét |
|----------|--------------|------------|----------|
| **Nhật (vocab)** | ~500 ký tự | ⭐⭐⭐⭐ | Rất tốt — ví dụ có hồn, cấp độ khớp, chống trùng |
| **Trung (vocab)** | ~550 ký tự | ⭐⭐⭐⭐ | Rất tốt — pinyin chuẩn, 2 ví dụ đa dạng |
| **Hàn (vocab)** | ~550 ký tự | ⭐⭐⭐⭐ | Rất tốt — romanization chuẩn, ví dụ tự nhiên |
| **Nhật (grammar)** | ~800 ký tự | ⭐⭐⭐⭐⭐ | Xuất sắc — như giảng viên, đánh dấu pattern, cùng pattern khác nghĩa |
| **Trung (grammar)** | ~850 ký tự | ⭐⭐⭐⭐⭐ | Xuất sắc — pinyin đầy đủ, lỗi người Việt hay mắc |
| **Hàn (grammar)** | ~850 ký tự | ⭐⭐⭐⭐⭐ | Xuất sắc — romanization đầy đủ, lỗi người Việt hay mắc |

> **Nhận xét:** Prompt grammar xuất sắc hơn prompt vocab — có thêm "NHƯ GIẢNG VIÊN ĐỌC GIÁO TRÌNH", "CÙNG PATTERN – KHÁC NGHĨA", "ĐÁNH DẤU PATTERN". Prompt vocab có thể học hỏi thêm từ prompt grammar.

---

## 5. PHÂN TÍCH MỞ RỘNG 12 NGÔN NGỮ (Tổng 15)

> **Câu hỏi người dùng:** "Nếu add-on được mở rộng lên vài ngôn ngữ nữa, khoảng 12 ngôn ngữ nữa thì không biết sẽ ra sao?"

### 5.1 Cấu trúc hiện tại — Mức độ sẵn sàng mở rộng

| Thành phần | Cấu trúc hiện tại | Mức độ sẵn sàng |
|------------|-------------------|-----------------|
| **`Language/__init__.py`** | Chỉ cần thêm import + config dict | 🟢 Rất dễ |
| **`Language/{lang}.py`** | Mỗi ngôn ngữ 1 file config (fields, levels, audio) | 🟢 Dễ |
| **`mode/templates.py`** | Mỗi ngôn ngữ cần template riêng (HTML) | 🟡 TB |
| **`mode/css.py`** | CSS riêng cho mỗi ngôn ngữ | 🟡 TB |
| **`audio/engine.py`** | Voice options riêng cho mỗi ngôn ngữ | 🟢 Dễ |
| **`utils/ai_extractor.py`** | Prompt riêng cho mỗi ngôn ngữ (VI + EN) | 🟡 TB |
| **`utils/i18n.py`** | Translation keys riêng | 🟢 Dễ |
| **`utils/prompt_config.py`** | `LANGS = ("japanese", "chinese", "korean")` — cần mở rộng | 🟢 Dễ |
| **`manifest.json`** | `languages` array — cần mở rộng | 🟢 Dễ |

> **Kết luận:** Kiến trúc hiện tại **RẤT SẴN SÀNG** cho việc mở rộng ngôn ngữ. Mỗi ngôn ngữ mới chỉ cần:
> 1. 1 file config trong `Language/`
> 2. Template HTML trong `mode/templates.py`
> 3. Prompt AI trong `utils/ai_extractor.py`
> 4. Voice options trong `audio/engine.py`
> 5. Translation keys trong `utils/i18n.py`

### 5.2 12 ngôn ngữ tiềm năng (đánh giá theo độ khó)

| # | Ngôn ngữ | Mã | Độ khó | Lý do |
|---|----------|-----|--------|-------|
| 1 | **Tiếng Việt** | vi | 🟢 Rất dễ | Ngôn ngữ mẹ đẻ — không cần dịch nghĩa, chỉ cần từ vựng + ví dụ |
| 2 | **Tiếng Anh** | en | 🟢 Rất dễ | Ngôn ngữ phổ biến nhất — AI rất mạnh, TTS đầy đủ |
| 3 | **Tiếng Thái** | th | 🟢 Dễ | Chữ Thái đơn giản, TTS có sẵn, cộng đồng học lớn |
| 4 | **Tiếng Tây Ban Nha** | es | 🟢 Dễ | Chữ Latin, TTS đầy đủ, cộng đồng học lớn |
| 5 | **Tiếng Pháp** | fr | 🟢 Dễ | Chữ Latin, TTS đầy đủ |
| 6 | **Tiếng Đức** | de | 🟢 Dễ | Chữ Latin, TTS đầy đủ |
| 7 | **Tiếng Ý** | it | 🟢 Dễ | Chữ Latin, TTS đầy đủ |
| 8 | **Tiếng Bồ Đào Nha** | pt | 🟢 Dễ | Chữ Latin, TTS đầy đủ |
| 9 | **Tiếng Nga** | ru | 🟡 TB | Chữ Cyrillic, cần font + TTS riêng |
| 10 | **Tiếng Ả Rập** | ar | 🟡 TB | Chữ Ả Rập (RTL), cần template riêng |
| 11 | **Tiếng Hindi** | hi | 🟡 TB | Chữ Devanagari, cần font + TTS riêng |
| 12 | **Tiếng Indonesia** | id | 🟢 Dễ | Chữ Latin, TTS có sẵn, cộng đồng Đông Nam Á |

### 5.3 Phân loại theo độ khó

| Độ khó | Ngôn ngữ | Số lượng |
|--------|----------|----------|
| 🟢 **Rất dễ** (Chữ Latin, TTS đầy đủ) | Việt, Anh, Tây Ban Nha, Pháp, Đức, Ý, Bồ Đào Nha, Indonesia | **8** |
| 🟡 **Trung bình** (Chữ đặc biệt, cần font/TTS riêng) | Thái, Nga, Ả Rập, Hindi | **4** |

### 5.4 Chi phí phát triển mỗi ngôn ngữ

| Hạng mục | Ước tính thời gian | Ghi chú |
|----------|-------------------|---------|
| Config file (`Language/{lang}.py`) | 2-4 giờ | Fields, levels, audio fields |
| Template HTML (`mode/templates.py`) | 4-8 giờ | 5 chế độ × 2 mặt (qfmt/afmt) |
| Prompt AI (`utils/ai_extractor.py`) | 4-8 giờ | Vocab + Grammar × VI/EN |
| Voice options (`audio/engine.py`) | 1-2 giờ | Tra cứu Edge TTS voices |
| Translation keys (`utils/i18n.py`) | 2-4 giờ | ~50 keys/ngôn ngữ |
| CSS (`mode/css.py`) | 2-4 giờ | Font, RTL support nếu cần |
| **Tổng** | **15-30 giờ/ngôn ngữ** | |

> **12 ngôn ngữ × 15-30 giờ = 180-360 giờ phát triển** (~1-2 tháng full-time)

### 5.5 Rủi ro khi mở rộng 12 ngôn ngữ

| Rủi ro | Mức độ | Giải pháp |
|--------|--------|-----------|
| **`templates.py` phình to** | 🔴 Cao | 15 ngôn ngữ × 5 chế độ × 2 mặt = 150 template — cần tách file riêng |
| **`ai_extractor.py` phình to** | 🔴 Cao | 15 ngôn ngữ × 2 chế độ × 2 ngôn ngữ UI = 60 prompt — cần tách file riêng |
| **`i18n.py` phình to** | 🟡 TB | 15 ngôn ngữ × ~50 keys = 750 keys — cần tách JSON |
| **Chất lượng prompt giảm** | 🟡 TB | Prompt cho ngôn ngữ mới chưa được tinh chỉnh như Nhật/Trung/Hàn |
| **TTS không có voice** | 🟡 TB | Một số ngôn ngữ Edge TTS không hỗ trợ — cần fallback |
| **Font không hiển thị** | 🟡 TB | Ả Rập (RTL), Hindi (Devanagari), Nga (Cyrillic) cần font riêng |
| **Test phình to** | 🟡 TB | Mỗi ngôn ngữ cần test riêng — 15 ngôn ngữ × test hiện tại |
| **Bảo trì tăng** | 🟡 TB | Mỗi thay đổi prompt/template cần cập nhật 15 ngôn ngữ |

### 5.6 Lợi ích khi mở rộng 12 ngôn ngữ

| Lợi ích | Mô tả |
|---------|-------|
| **Tăng user base** | Từ 3 ngôn ngữ → 15 ngôn ngữ — phục vụ cộng đồng học ngôn ngữ toàn cầu |
| **Vị thế học thuật** | Trở thành add-on đúc thẻ đa ngôn ngữ LỚN NHẤT trên Anki |
| **Cạnh tranh** | Không add-on nào hỗ trợ 15 ngôn ngữ với AI + TTS + interactive templates |
| **Cộng đồng** | Mỗi ngôn ngữ mới = cộng đồng người dùng mới |
| **Data học thuật** | Nhiều ngôn ngữ = nhiều data học tập = whitepaper mạnh hơn |

### 5.7 Khuyến nghị chiến lược mở rộng

> **⚠️ QUAN TRỌNG:** Mở rộng 12 ngôn ngữ là **KHÔNG NÊN LÀM NGAY** vì:
> 1. **Chưa tối ưu chi phí AI** — mở rộng ngôn ngữ trước khi tối ưu token sẽ làm chi phí tăng vọt
> 2. **Chưa tách `__init__.py`/`ai_extractor.py`** — thêm 12 ngôn ngữ vào file 2.461 dòng sẽ không thể bảo trì
> 3. **Chưa có cộng đồng** — mở rộng ngôn ngữ mà không có người dùng sẽ lãng phí

**Lộ trình mở rộng đúng đắn:**

| Giai đoạn | Hành động | Lý do |
|-----------|-----------|-------|
| **Giai đoạn 1 (Tháng 1-2)** | Tối ưu chi phí AI + Tách `__init__.py`/`ai_extractor.py` | Nền tảng trước khi mở rộng |
| **Giai đoạn 2 (Tháng 3-4)** | Thêm **2 ngôn ngữ dễ nhất**: Tiếng Việt + Tiếng Anh | Ngôn ngữ mẹ đẻ + phổ biến nhất — test thị trường |
| **Giai đoạn 3 (Tháng 5-6)** | Thêm **3 ngôn ngữ Latin**: Tây Ban Nha + Pháp + Đức | Chữ Latin — dễ nhất, cộng đồng lớn |
| **Giai đoạn 4 (Tháng 7-9)** | Thêm **3 ngôn ngữ nữa**: Ý + Bồ Đào Nha + Indonesia | Chữ Latin — mở rộng dần |
| **Giai đoạn 5 (Tháng 10-12)** | Thêm **4 ngôn ngữ đặc biệt**: Thái + Nga + Ả Rập + Hindi | Chữ đặc biệt — cần font/TTS riêng |

> **Tổng thời gian:** 12 tháng để thêm 12 ngôn ngữ (1 ngôn ngữ/tháng trung bình)

### 5.8 Kiến trúc cần thay đổi trước khi mở rộng

| Thay đổi | Mô tả | Ưu tiên |
|----------|-------|---------|
| **Tách `templates.py` → `templates/{lang}.py`** | Mỗi ngôn ngữ 1 file template riêng | 🔥 Cao |
| **Tách `ai_extractor.py` → `prompts/{lang}.py`** | Mỗi ngôn ngữ 1 file prompt riêng | 🔥 Cao |
| **Tách `i18n.py` → `i18n/{lang}.json`** | Mỗi ngôn ngữ 1 file JSON translation | 🔥 Cao |
| **Tách `css.py` → `css/{lang}.py`** | Mỗi ngôn ngữ 1 file CSS riêng | 🟡 TB |
| **Plugin API** | Cho phép cộng đồng tự thêm ngôn ngữ | 🟡 TB |

---

## 6. ĐỊNH HƯỚNG CHIẾN LƯỢC (SAU PHẢN HỒI)

> **Phản hồi quan trọng từ người dùng:**
> 1. "Đây chỉ là add-on đúc thẻ" — không nên phình to thành everything app
> 2. "API Free tier tốn rất nhanh nếu không tối ưu chất lượng kịp thời" — chi phí AI là sống còn
> 3. "Game họ có thể cài add-on khác" — game/analytics/gamification không phải core competency
> 4. "Mở rộng 12 ngôn ngữ nữa" — cần phân tích kỹ trước khi làm

### 6.1 Nguyên tắc chiến lược mới

| Nguyên tắc | Mô tả |
|------------|-------|
| **🎯 Core competency** | Bento Forge = **đúc thẻ tự động chất lượng cao** với AI. Mọi tính năng phải phục vụ mục tiêu này. |
| **💰 Tối ưu chi phí AI** | Free tier rất hạn chế — tối ưu token/chi phí là ưu tiên #1, không phải thêm tính năng. |
| **🔌 Không phình to** | Game/analytics/gamification KHÔNG nhét vào core. Nếu làm thì là plugin riêng biệt. |
| **📊 Tận dụng Anki data** | Retention analytics dùng **review log có sẵn của Anki** — không cần AI, không cần phình to. |
| **🌍 Mở rộng ngôn ngữ có chiến lược** | Mở rộng dần theo độ khó, không mở rộng ồ ạt 12 ngôn ngữ cùng lúc. |
| **🤝 Cộng tác ecosystem** | Khuyến khích người dùng dùng add-on khác cho game/analytics — Bento Forge tập trung đúc thẻ. |

### 6.2 Vì sao KHÔNG nên phình to

| Tính năng | Vấn đề nếu nhét vào core | Giải pháp đúng |
|-----------|--------------------------|----------------|
| **Game (Word Building, Handwriting...)** | Người dùng đã có add-on chuyên game; phình to làm add-on nặng, khó bảo trì | Giữ game hiện tại nhưng KHÔNG phát triển thêm; tập trung vào đúc thẻ |
| **Retention Analytics** | Cần hook vào reviewer data — phức tạp, dễ phá Anki | Dùng **Anki review log có sẵn** (đã có sẵn trong collection) — chỉ cần đọc, không cần AI |
| **Gamification (Streak/XP)** | Không phải core competency; người dùng có add-on chuyên gamification | Không làm — hoặc làm plugin riêng biệt |
| **AI Tutor Chat** | Tốn token rất nhanh; không phải chức năng đúc thẻ | Giữ chat hiện tại nhưng tối ưu chi phí; không mở rộng thêm |
| **Adaptive Learning** | Cần AI liên tục → tốn token khổng lồ | Không làm — dùng SRS có sẵn của Anki |

---

## 7. LỘ TRÌNH PHÁT TRIỂN (TẬP TRUNG CORE COMPETENCY)

### Phase A — Tối ưu chi phí AI (Ưu tiên #1 — SỐNG CÒN)

**Mục tiêu:** Giảm token/chi phí tối đa cho free tier

| Hạng mục | Mô tả | Độ khó | Ưu tiên |
|----------|-------|--------|---------|
| **A1. Model Routing thông minh** | Tự chọn model rẻ nhất đủ chất lượng (gpt-4o-mini cho đơn giản, reasoner cho phức tạp) | 🟡 TB | 🔥 Cao |
| **A2. Semantic Caching** | Cache theo semantic similarity (không chỉ exact match) — tận dụng kết quả tương tự | 🟠 Khó | 🔥 Cao |
| **A3. Prompt Compression** | Nén system prompt thêm 30-50% — giảm input token | 🟢 Dễ | 🔥 Cao |
| **A4. Batch Optimization** | Gộp nhiều từ vào 1 request — giảm overhead | 🟡 TB | 🔥 Cao |
| **A5. Local Model Priority** | Ưu tiên khuyến nghị Ollama/LM Studio — 0 chi phí | 🟢 Dễ | 🔥 Cao |
| **A6. Token Budget UI** | Hiển thị rõ chi phí ước tính TRƯỚC khi chạy | 🟢 Dễ | 🟡 TB |
| **A7. Free Tier Detection** | Phát hiện provider free tier, cảnh báo khi sắp hết quota | 🟡 TB | 🟡 TB |

**Bằng chứng cần đạt:**
- Giảm 50%+ token/chi phí so với hiện tại
- Đúc 100 từ tiêu tốn < 10k token (hiện tại ~24.5k)
- Free tier DeepSeek/OpenAI đủ dùng 1 tháng cho người dùng thường

### Phase B — Chất lượng thẻ (Core competency)

**Mục tiêu:** Thẻ tạo ra phải là tốt nhất thị trường

| Hạng mục | Mô tả | Độ khó | Ưu tiên |
|----------|-------|--------|---------|
| **B1. Quality Scoring** | Tự đánh giá chất lượng thẻ (điểm 0-100) trước khi xuất | 🟡 TB | 🔥 Cao |
| **B2. Error Detection** | Phát hiện lỗi ngữ pháp/ngữ nghĩa trong thẻ AI tạo | 🟡 TB | 🔥 Cao |
| **B3. Level Validation** | Kiểm tra từ có đúng cấp độ JLPT/HSK/TOPIK hay không | 🟡 TB | 🔥 Cao |
| **B4. Context-aware Examples** | Ví dụ phù hợp ngữ cảnh, không generic | 🟡 TB | 🔥 Cao |
| **B5. Multi-sense Disambiguation** | Phân biệt rõ các nghĩa khác nhau của từ đa nghĩa | 🟠 Khó | 🟡 TB |
| **B6. Collocation/Usage Notes** | Thêm ghi chú cách dùng, collocation, register | 🟡 TB | 🟡 TB |

### Phase C — Kiến trúc (Giảm nợ kỹ thuật — TIỀN ĐỀ cho mở rộng ngôn ngữ)

**Mục tiêu:** Giảm chi phí bảo trì, tăng tốc phát triển, CHUẨN BỊ cho 12 ngôn ngữ

| Hạng mục | Mô tả | Độ khó | Ưu tiên |
|----------|-------|--------|---------|
| **C1. Tách `__init__.py`** | Hoàn thành P1-D: tách orchestration UI thành module riêng | 🟠 Khó | 🔥 Cao |
| **C2. Tách `ai_extractor.py`** | Tách prompt/cache/parse thành module riêng | 🟠 Khó | 🔥 Cao |
| **C3. Tách `templates.py` → `templates/{lang}.py`** | Mỗi ngôn ngữ 1 file template riêng — TIỀN ĐỀ cho 15 ngôn ngữ | 🟡 TB | 🔥 Cao |
| **C4. Tách `i18n.py` → `i18n/{lang}.json`** | Mỗi ngôn ngữ 1 file JSON translation — TIỀN ĐỀ cho 15 ngôn ngữ | 🟢 Dễ | 🔥 Cao |
| **C5. Tách `prompts` → `prompts/{lang}.py`** | Mỗi ngôn ngữ 1 file prompt riêng — TIỀN ĐỀ cho 15 ngôn ngữ | 🟡 TB | 🔥 Cao |
| **C6. Plugin API** | Public API cho nhà phát triển thứ 3 (hooks, events, data access) | 🟠 Khó | 🟢 Thấp |

### Phase D — Mở rộng ngôn ngữ (SAU khi hoàn thành Phase A + C)

**Mục tiêu:** Mở rộng dần theo độ khó, 1 ngôn ngữ/tháng

| Giai đoạn | Ngôn ngữ | Độ khó | Lý do |
|-----------|----------|--------|-------|
| **D1 (Tháng 3-4)** | Tiếng Việt + Tiếng Anh | 🟢 Rất dễ | Ngôn ngữ mẹ đẻ + phổ biến nhất — test thị trường |
| **D2 (Tháng 5-6)** | Tây Ban Nha + Pháp + Đức | 🟢 Dễ | Chữ Latin, cộng đồng lớn |
| **D3 (Tháng 7-9)** | Ý + Bồ Đào Nha + Indonesia | 🟢 Dễ | Chữ Latin, mở rộng dần |
| **D4 (Tháng 10-12)** | Thái + Nga + Ả Rập + Hindi | 🟡 TB | Chữ đặc biệt — cần font/TTS riêng |

### Phase E — Bằng chứng học thuật (Không phình to)

**Mục tiêu:** Dùng **Anki review log có sẵn** — không cần AI, không cần phình to

| Hạng mục | Mô tả | Độ khó | Ưu tiên |
|----------|-------|--------|---------|
| **E1. Retention Report** | Đọc Anki review log → tính retention rate theo kỹ năng (đã có sẵn trong collection) | 🟡 TB | 🟡 TB |
| **E2. Whitepaper** | Viết paper về phương pháp học dựa trên data thực tế | 🟠 Khó | 🟢 Thấp |

> **Lưu ý:** Retention analytics KHÔNG cần AI. Anki đã lưu toàn bộ review log (lịch sử Again/Good/Hard/Easy theo từng card). Chỉ cần đọc `revlog` table + `cards` table → tính retention rate. Đây là tính năng nhẹ, không tốn token, không phình to.

### Phase F — Cộng đồng (Tăng user base)

**Mục tiêu:** Xây dựng cộng đồng người dùng

| Hạng mục | Mô tả | Độ khó | Ưu tiên |
|----------|-------|--------|---------|
| **F1. User Documentation Site** | Website tài liệu (GitHub Pages/MkDocs) | 🟢 Dễ | 🟡 TB |
| **F2. Community Forum** | Discord/Reddit cho người dùng | 🟢 Dễ | 🟢 Thấp |
| **F3. Video Tutorials** | Series video hướng dẫn | 🟢 Dễ | 🟢 Thấp |
| **F4. Case Studies** | Thu thập câu chuyện thành công | 🟢 Dễ | 🟢 Thấp |

---

## 8. ƯU TIÊN ĐỀ XUẤT (ROADMAP 12 THÁNG)

### Tháng 1-2: Nền tảng (Phase A + C) — SỐNG CÒN
- [ ] A1: Model Routing thông minh
- [ ] A2: Semantic Caching
- [ ] A3: Prompt Compression — giảm 30-50% input token
- [ ] A5: Local Model Priority
- [x] C1: Tách `__init__.py` (hoàn thành P1-D)
- [x] C2: Tách `ai_extractor.py`
- [ ] C3: Tách `templates.py` → `templates/{lang}.py`
- [ ] C4: Tách `i18n.py` → `i18n/{lang}.json`
- [ ] C5: Tách `prompts` → `prompts/{lang}.py`

### Tháng 3-4: Chất lượng thẻ + Ngôn ngữ đầu tiên (Phase B + D1)
- [ ] B1: Quality Scoring — tự đánh giá chất lượng thẻ
- [ ] B2: Error Detection — phát hiện lỗi ngữ pháp/ngữ nghĩa
- [ ] B3: Level Validation — kiểm tra cấp độ JLPT/HSK/TOPIK
- [ ] D1: Thêm Tiếng Việt + Tiếng Anh

### Tháng 5-6: Mở rộng ngôn ngữ (Phase D2)
- [ ] D2: Thêm Tây Ban Nha + Pháp + Đức

### Tháng 7-9: Mở rộng ngôn ngữ (Phase D3)
- [ ] D3: Thêm Ý + Bồ Đào Nha + Indonesia

### Tháng 10-12: Mở rộng ngôn ngữ đặc biệt (Phase D4)
- [ ] D4: Thêm Thái + Nga + Ả Rập + Hindi
- [ ] E1: Retention Report — dùng Anki review log có sẵn
- [ ] F1: User Documentation Site

---

## 9. KẾT LUẬN

### Điểm tổng thể: **8.2/10**

| Trục | Điểm |
|------|------|
| Kiến trúc & Kỹ thuật | 8.5 |
| Chất lượng Test | 8.0 |
| Bảo mật & Quyền riêng tư | 9.0 |
| UX & Accessibility | 7.5 |
| Tài liệu & Cộng đồng | 8.0 |
| **Tối ưu Token** | **7.5** |
| **Chất lượng Thẻ** | **8.0** |
| **Trung bình** | **8.1** |

### Điểm mạnh nổi bật
1. **Bảo mật xuất sắc** (9.0) — keyring, redaction, profile-scoped, không telemetry
2. **Kiến trúc module hóa tốt** (8.5) — use-case/adapter boundary, thread-safe
3. **Prompt chất lượng cao** (8.0) — ví dụ có hồn, cấp độ khớp, chống trùng
4. **Tối ưu token khá tốt** (7.5) — chỉ gửi từ trùng, cache thông minh, session policy

### Điểm cần cải thiện nhất (theo phản hồi)
1. **Tối ưu chi phí AI** — cần Model Routing + Semantic Caching + Prompt Compression
2. **Chất lượng thẻ** — cần Quality Scoring + Error Detection + Level Validation
3. **Giảm nợ kỹ thuật** — tách `__init__.py`/`ai_extractor.py`/`templates.py`/`i18n.py`
4. **Mở rộng ngôn ngữ có chiến lược** — 12 ngôn ngữ cần 12 tháng, không làm ồ ạt

### Khuyến nghị chiến lược (sau phản hồi)
> **Ưu tiên #1:** **Tối ưu chi phí AI** — đây là vấn đề sống còn. Free tier rất hạn chế, nếu không tối ưu token/chi phí, người dùng sẽ bỏ vì tốn tiền. Model Routing + Semantic Caching + Prompt Compression + Local Model Priority.
>
> **Ưu tiên #2:** **Tập trung chất lượng thẻ** — đây là core competency. Thẻ tạo ra phải tốt nhất thị trường: Quality Scoring + Error Detection + Level Validation.
>
> **Ưu tiên #3:** **Tách kiến trúc trước khi mở rộng ngôn ngữ** — `templates.py`/`i18n.py`/`prompts` phải tách file riêng trước khi thêm 12 ngôn ngữ. Nếu không, file 2.461 dòng sẽ thành 10.000+ dòng không thể bảo trì.
>
> **Ưu tiên #4:** **Mở rộng ngôn ngữ dần dần** — bắt đầu với Tiếng Việt + Tiếng Anh (dễ nhất), sau đó Latin (Tây Ban Nha/Pháp/Đức), cuối cùng là chữ đặc biệt (Thái/Nga/Ả Rập/Hindi). 1 ngôn ngữ/tháng = 12 tháng cho 12 ngôn ngữ.
>
> **KHÔNG làm:** Game mới, gamification, adaptive learning, AI tutor mở rộng — những thứ này không phải core competency và tốn token khổng lồ. Người dùng có thể cài add-on khác cho game/analytics.
