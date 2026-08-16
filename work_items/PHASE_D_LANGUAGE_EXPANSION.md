# Phase D — Mở rộng ngôn ngữ

> Status: frozen
> Authority: historical plan; not active without an explicit roadmap reference
> Read when: chủ dự án mở P2-02 hoặc task tham chiếu trực tiếp

> **QUYẾT ĐỊNH THAY THẾ (2026-08-16):** `Đóng băng theo personal scope`. Không có roadmap 12 ngôn ngữ hay mục tiêu mở rộng thị trường. Nhật / Trung / Hàn được giữ nguyên; chỉ mở đúng một ngôn ngữ mới nếu chủ dự án học nó đều, gặp ma sát tạo thẻ ít nhất ba lần trong hai tuần, và có corpus 20–30 mục để test.
> **Ưu tiên / độ khó / model:** Khi đủ điều kiện, tạo `P2-02` trong `PERSONAL_ROADMAP.md`: P2, 🟠 Khó, `gpt-5.6-sol` / `high`, 8–20 giờ. Mọi mục D1–D4 phía dưới chỉ là tham chiếu lịch sử, không được tự mở lại.

> **Nguồn:** `ACADEMIC_ASSESSMENT.md` — Phase D (SAU khi hoàn thành Phase A + C)
> **Trạng thái:** `Hoãn` — chỉ pilot một ngôn ngữ sau khi có nhu cầu người dùng, specification và bộ test đại diện.
> **Mục tiêu:** Mở rộng dần theo độ khó, 1 ngôn ngữ/tháng

## Bối cảnh

⚠️ **QUAN TRỌNG:** Mở rộng 12 ngôn ngữ là **KHÔNG NÊN LÀM NGAY** vì:
1. **Chưa tối ưu chi phí AI** — mở rộng ngôn ngữ trước khi tối ưu token sẽ làm chi phí tăng vọt
2. **Chưa tách `__init__.py`/`ai_extractor.py`** — thêm 12 ngôn ngữ vào file 2.461 dòng sẽ không thể bảo trì
3. **Chưa có cộng đồng** — mở rộng ngôn ngữ mà không có người dùng sẽ lãng phí

**Điều kiện tiên quyết:** Nhu cầu người dùng đã xác nhận, specification ngôn ngữ đích, corpus kiểm thử và boundary prompt/template đủ rõ. Không cần hoàn thành toàn bộ Phase A/C.

## Kiến trúc hiện tại — Mức độ sẵn sàng mở rộng

| Thành phần | Cấu trúc hiện tại | Mức độ sẵn sàng |
|------------|-------------------|-----------------|
| **`Language/__init__.py`** | Chỉ cần thêm import + config dict | 🟢 Rất dễ |
| **`Language/{lang}.py`** | Mỗi ngôn ngữ 1 file config (fields, levels, audio) | 🟢 Dễ |
| **`mode/templates.py`** | Mỗi ngôn ngữ cần template riêng (HTML) | 🟡 TB |
| **`mode/css.py`** | CSS riêng cho mỗi ngôn ngữ | 🟡 TB |
| **`audio/engine.py`** | Voice options riêng cho mỗi ngôn ngữ | 🟢 Dễ |
| **`utils/ai_extractor.py`** | Prompt riêng cho mỗi ngôn ngữ (VI + EN) | 🟡 TB |
| **`utils/i18n.py`** | Chỉ là ngôn ngữ giao diện VI/EN, không phải tiền đề cho ngôn ngữ đích | 🟢 Không phụ thuộc |
| **`utils/prompt_config.py`** | `LANGS = ("japanese", "chinese", "korean")` — cần mở rộng | 🟢 Dễ |
| **`manifest.json`** | `languages` array — cần mở rộng | 🟢 Dễ |

> **Kết luận:** Kiến trúc có các điểm mở rộng rõ, nhưng chưa đủ bằng chứng để mở rộng hàng loạt. Mỗi ngôn ngữ mới cần:
> 1. 1 file config trong `Language/`
> 2. Template HTML trong `mode/templates.py`
> 3. Prompt AI trong `utils/ai_extractor.py`
> 4. Voice options trong `audio/engine.py`
> 5. Translation keys trong `utils/i18n.py`

## 12 ngôn ngữ tiềm năng (đánh giá theo độ khó)

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

## Hạng mục

### D1. Thêm Tiếng Việt + Tiếng Anh

**Trạng thái:** `Chưa lên lịch — cần làm rõ đây là ngôn ngữ đích, không nhầm với i18n VI/EN`

**Vấn đề:** Chưa hỗ trợ 2 ngôn ngữ dễ nhất — test thị trường.

- **Độ khó:** 🟢 Rất dễ
- **Ưu tiên:** 🔥 Cao (sau Phase A + C)
- **Thời gian dự kiến:** 30-60 giờ (2 ngôn ngữ × 15-30 giờ)
- **Phạm vi dự kiến:** `Language/vi.py`, `Language/en.py`, `mode/templates.py`, `mode/css.py`, `audio/engine.py`, `utils/ai_extractor.py`, `utils/i18n.py`, `utils/prompt_config.py`, `manifest.json`, `tests/`
- **Thay đổi yêu cầu:**
  - Config file (`Language/{lang}.py`) — 2-4 giờ/ngôn ngữ
  - Template HTML (`mode/templates.py`) — 4-8 giờ/ngôn ngữ
  - Prompt AI (`utils/ai_extractor.py`) — 4-8 giờ/ngôn ngữ
  - Voice options (`audio/engine.py`) — 1-2 giờ/ngôn ngữ
  - Translation keys (`utils/i18n.py`) — 2-4 giờ/ngôn ngữ
  - CSS (`mode/css.py`) — 2-4 giờ/ngôn ngữ
- **Tiêu chí hoàn tất:**
  - Có test cho cả 2 ngôn ngữ mới
  - TTS hoạt động cho cả 2 ngôn ngữ
  - Prompt chất lượng tương đương Nhật/Trung/Hàn

### D2. Thêm Tây Ban Nha + Pháp + Đức

**Trạng thái:** `Chưa lên lịch — sau pilot D1 thành công và có năng lực bảo trì`

**Vấn đề:** Chưa hỗ trợ 3 ngôn ngữ Latin phổ biến.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🟡 Trung bình (sau D1)
- **Thời gian dự kiến:** 45-90 giờ (3 ngôn ngữ × 15-30 giờ)
- **Phạm vi dự kiến:** `Language/es.py`, `Language/fr.py`, `Language/de.py`, `mode/templates.py`, `mode/css.py`, `audio/engine.py`, `utils/ai_extractor.py`, `utils/i18n.py`, `utils/prompt_config.py`, `manifest.json`, `tests/`
- **Thay đổi yêu cầu:** Tương tự D1 cho 3 ngôn ngữ Latin
- **Tiêu chí hoàn tất:**
  - Có test cho cả 3 ngôn ngữ mới
  - TTS hoạt động cho cả 3 ngôn ngữ
  - Prompt chất lượng tương đương Nhật/Trung/Hàn

### D3. Thêm Ý + Bồ Đào Nha + Indonesia

**Trạng thái:** `Chưa lên lịch — sau D2 và có nhu cầu xác nhận`

**Vấn đề:** Chưa hỗ trợ 3 ngôn ngữ Latin mở rộng.

- **Độ khó:** 🟢 Dễ
- **Ưu tiên:** 🟡 Trung bình (sau D2)
- **Thời gian dự kiến:** 45-90 giờ (3 ngôn ngữ × 15-30 giờ)
- **Phạm vi dự kiến:** `Language/it.py`, `Language/pt.py`, `Language/id.py`, `mode/templates.py`, `mode/css.py`, `audio/engine.py`, `utils/ai_extractor.py`, `utils/i18n.py`, `utils/prompt_config.py`, `manifest.json`, `tests/`
- **Thay đổi yêu cầu:** Tương tự D1 cho 3 ngôn ngữ Latin
- **Tiêu chí hoàn tất:**
  - Có test cho cả 3 ngôn ngữ mới
  - TTS hoạt động cho cả 3 ngôn ngữ
  - Prompt chất lượng tương đương Nhật/Trung/Hàn

### D4. Thêm Thái + Nga + Ả Rập + Hindi

**Trạng thái:** `Không lên lịch — cần nghiên cứu riêng RTL/font/TTS và nhu cầu thực tế`

**Vấn đề:** Chưa hỗ trợ 4 ngôn ngữ chữ đặc biệt.

- **Độ khó:** 🟡 Trung bình
- **Ưu tiên:** 🟢 Thấp (sau D3)
- **Thời gian dự kiến:** 60-120 giờ (4 ngôn ngữ × 15-30 giờ)
- **Phạm vi dự kiến:** `Language/th.py`, `Language/ru.py`, `Language/ar.py`, `Language/hi.py`, `mode/templates.py`, `mode/css.py`, `audio/engine.py`, `utils/ai_extractor.py`, `utils/i18n.py`, `utils/prompt_config.py`, `manifest.json`, `tests/`
- **Thay đổi yêu cầu:**
  - Chữ đặc biệt — cần font/TTS riêng
  - Ả Rập (RTL) — cần template riêng
  - Nga (Cyrillic), Hindi (Devanagari) — cần font riêng
- **Tiêu chí hoàn tất:**
  - Có test cho cả 4 ngôn ngữ mới
  - TTS hoạt động cho cả 4 ngôn ngữ (hoặc fallback rõ ràng)
  - Font hiển thị đúng cho chữ đặc biệt

## Chi phí phát triển mỗi ngôn ngữ

| Hạng mục | Ước tính thời gian | Ghi chú |
|----------|-------------------|---------|
| Config file (`Language/{lang}.py`) | 2-4 giờ | Fields, levels, audio fields |
| Template HTML (`mode/templates.py`) | 4-8 giờ | 5 chế độ × 2 mặt (qfmt/afmt) |
| Prompt AI (`utils/ai_extractor.py`) | 4-8 giờ | Vocab + Grammar × VI/EN |
| Voice options (`audio/engine.py`) | 1-2 giờ | Tra cứu Edge TTS voices |
| Translation keys (`utils/i18n.py`) | 2-4 giờ | ~50 keys/ngôn ngữ |
| CSS (`mode/css.py`) | 2-4 giờ | Font, RTL support nếu cần |
| **Tổng** | Cần ước lượng lại sau pilot; 15-30 giờ chưa gồm QA template, grammar, TTS và corpus kiểm thử | |

> **12 ngôn ngữ × 15-30 giờ = 180-360 giờ phát triển** (~1-2 tháng full-time)

## Rủi ro khi mở rộng 12 ngôn ngữ

| Rủi ro | Mức độ | Giải pháp |
|--------|--------|-----------|
| **`templates.py` phình to** | 🔴 Cao | 15 ngôn ngữ × 5 chế độ × 2 mặt = 150 template — cần tách file riêng (Phase C3) |
| **`ai_extractor.py` phình to** | 🔴 Cao | 15 ngôn ngữ × 2 chế độ × 2 ngôn ngữ UI = 60 prompt — cần tách file riêng (Phase C5) |
| **`i18n.py` phình to** | 🟡 TB | 15 ngôn ngữ × ~50 keys = 750 keys — cần tách JSON (Phase C4) |
| **Chất lượng prompt giảm** | 🟡 TB | Prompt cho ngôn ngữ mới chưa được tinh chỉnh như Nhật/Trung/Hàn |
| **TTS không có voice** | 🟡 TB | Một số ngôn ngữ Edge TTS không hỗ trợ — cần fallback |
| **Font không hiển thị** | 🟡 TB | Ả Rập (RTL), Hindi (Devanagari), Nga (Cyrillic) cần font riêng |
| **Test phình to** | 🟡 TB | Mỗi ngôn ngữ cần test riêng — 15 ngôn ngữ × test hiện tại |
| **Bảo trì tăng** | 🟡 TB | Mỗi thay đổi prompt/template cần cập nhật 15 ngôn ngữ |

## Lợi ích khi mở rộng 12 ngôn ngữ

| Lợi ích | Mô tả |
|---------|-------|
| **Tăng user base** | Từ 3 ngôn ngữ → 15 ngôn ngữ — phục vụ cộng đồng học ngôn ngữ toàn cầu |
| **Vị thế học thuật** | Trở thành add-on đúc thẻ đa ngôn ngữ LỚN NHẤT trên Anki |
| **Cạnh tranh** | Không add-on nào hỗ trợ 15 ngôn ngữ với AI + TTS + interactive templates |
| **Cộng đồng** | Mỗi ngôn ngữ mới = cộng đồng người dùng mới |
| **Data học thuật** | Nhiều ngôn ngữ = nhiều data học tập = whitepaper mạnh hơn |

## Lộ trình mở rộng lịch sử (đã đóng băng)

| Giai đoạn | Hành động | Lý do |
|-----------|-----------|-------|
| **Giai đoạn 1 (Tháng 1-2)** | Tối ưu chi phí AI + Tách `__init__.py`/`ai_extractor.py` | Nền tảng trước khi mở rộng |
| **Giai đoạn 2 (Tháng 3-4)** | Thêm **2 ngôn ngữ dễ nhất**: Tiếng Việt + Tiếng Anh | Ngôn ngữ mẹ đẻ + phổ biến nhất — test thị trường |
| **Giai đoạn 3 (Tháng 5-6)** | Thêm **3 ngôn ngữ Latin**: Tây Ban Nha + Pháp + Đức | Chữ Latin — dễ nhất, cộng đồng lớn |
| **Giai đoạn 4 (Tháng 7-9)** | Thêm **3 ngôn ngữ nữa**: Ý + Bồ Đào Nha + Indonesia | Chữ Latin — mở rộng dần |
| **Giai đoạn 5 (Tháng 10-12)** | Thêm **4 ngôn ngữ đặc biệt**: Thái + Nga + Ả Rập + Hindi | Chữ đặc biệt — cần font/TTS riêng |

> **Tổng thời gian:** 12 tháng để thêm 12 ngôn ngữ (1 ngôn ngữ/tháng trung bình)

## Thứ tự thực hiện bắt buộc

D1 → D2 → D3 → D4. Mỗi phiên chỉ nhận **một** ngôn ngữ.

## Mẫu cập nhật cho phiên tiếp theo

```md
### YYYY-MM-DD — Phase D / <hạng mục>

- Trạng thái: `Đang làm` → `Hoàn thành` / `Bị chặn`
- Phạm vi: `<file hoặc module>`
- Thay đổi: `<tóm tắt ngắn>`
- Kiểm chứng: `<lệnh test + kết quả>`
- Rủi ro còn lại / bước kế tiếp: `<ngắn gọn>`
