# 🌐 Bento Forge — AnkiTool Multi-Language V17.1.0

> **Vocabulary Factory cho Anki** — Tạo thẻ từ vựng tiếng Nhật, Trung & Hàn với AI, TTS, và interactive templates.

[![Version](https://img.shields.io/badge/version-17.1.0-blue)](manifest.json)
[![Anki](https://img.shields.io/badge/anki-2.1.50-green)](COMPATIBILITY.md)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-yellow)](manifest.json)
[![Tests](https://github.com/DeliChese/Anki-Bento-Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/DeliChese/Anki-Bento-Forge/actions/workflows/ci.yml)

Version và phạm vi Anki lấy từ [`manifest.json`](manifest.json); tài liệu không mở rộng phạm vi đó. Xem [Compatibility Matrix](COMPATIBILITY.md), [Debugging Guide](DEBUGGING.md) và trạng thái bằng chứng trong [Release Checklist](RELEASE_CHECKLIST.md) trước khi phát hành.

---

## ✨ Tính năng

### 🇯🇵🇨🇳🇰🇷 Đa ngôn ngữ (3 ngôn ngữ)
| Tính năng | Mô tả |
|-----------|-------|
| 🌍 **3 Ngôn Ngữ** | Nhật Bản, Trung Quốc & **Hàn Quốc** (mới V17.0) — mỗi ngôn ngữ có cấu hình riêng: bộ lọc cấp độ (JLPT N5-N1 / HSK 1-6 / **TOPIK I-II**) |
| 🔤 **Romanization** | Furigana/Pinyin cho Nhật-Trung, **Romanization chuẩn Revised Romanization cho tiếng Hàn** (field + ví dụ hiển thị trên thẻ) |
| 🎤 **TTS Đa Engine** | Edge TTS (chất lượng cao) → gTTS (fallback) → VoiceVox (local JP). Giọng Hàn ko-KR cho tiếng Hàn |

### 🎯 Combo Mode và SRS độc lập
| Tính năng | Mô tả |
|-----------|-------|
| 🎯 **Combo mặc định** | **1 từ = 1 card/1 lịch chung** với 5 bài tập QA, VN, Ghép chữ, Phát âm và Ẩn chữ. Banner trên card nói rõ đổi bài tập không tạo lịch SRS riêng. |
| 🧠 **SRS độc lập (opt-in)** | Có thể chọn theo deck để note nhập mới tạo 5 card/lịch riêng: Nhận diện, Sản xuất, Chính tả, Phát âm và Nhớ mặt chữ; mỗi lần Again/Good chỉ cập nhật kỹ năng ghi trên card. |
| 🎛️ **Mặc định theo deck** | Hướng Combo và policy Combo/Independent được lưu theo deck qua public WebView hook; không patch private API của Overview. |
| 🔁 **Migration an toàn** | Nút chuyển card cũ tạo Anki checkpoint/Undo, giữ nguyên card Nhận diện `ord=0` cùng lịch sử, chỉ sinh thêm 4 lịch; chạy lại không tạo trùng và không xóa card cũ. |

### 🤖 AI & Xử lý nội dung
| Tính năng | Mô tả |
|-----------|-------|
| 📏 **Nội dung dài tới 45.000 ký tự** | Tự chia đoạn ~8k ký tự/lần để chất lượng cao + không tràn token output; văn bản dài hơn `max_chars` (mặc định 45.000, chỉnh được trong Cài Đặt AI) sẽ bị cắt bớt phần dư. |
| 🧠 **Mức độ suy nghĩ AI** | Bộ chọn Thấp/Trung bình/Cao (reasoning_effort) trong Cài Đặt AI → cân bằng chất lượng vs token. |
| ✏️ **Sửa Prompt / Schema / Field Map (không cần code)** | Nút "✏️ Sửa Prompt / Schema AI" trong Cài Đặt AI → chỉnh System Prompt + mẫu JSON + map key→Field Anki (chọn mặt hiển thị: sau/trước/cả hai) cho từng ngôn ngữ; **field mới tự thêm vào Note Type và TỰ HIỆN TRÊN THẺ khi lưu**; sửa prompt → cache AI tự làm mới (`utils/ai_prompts.json`, gitignored). |
| 📎 **Kẹp File Tham Khảo** | Đính kèm TXT/MD/CSV/PDF/DOCX/XLSX làm tài liệu → AI đọc nội dung để trích xuất từ vựng/ngữ pháp. |
| 📘 **Ngữ pháp** | Note Type ngữ pháp riêng cho cả 3 ngôn ngữ: thẻ 2 chiều "Cấu trúc→Nghĩa" & "Nghĩa→Cấu trúc", AI trích xuất pattern + công thức + cách dùng + ví dụ (có đánh dấu `<b>…</b>` trong ví dụ). |
| 🤖 **AI Trích Xuất** | Dùng OpenAI/DeepSeek/Ollama để trích xuất từ vựng từ văn bản. Tự động tránh từ đã có trong deck. |
| 💬 **AI Chat** | Trợ lý học tập thông minh, hiểu ngữ cảnh Anki của bạn. |
| ⚡ **Tối ưu Token** | Chỉ gửi từ vựng/ngữ pháp trùng với nội dung vào prompt (thay vì toàn bộ deck → giảm mạnh input); tổng hợp token/chi phí theo toàn bộ chunk. |
| 💾 **Lưu trạng thái 2 luồng** | Text + file kẹp của Từ vựng và Ngữ pháp (mỗi ngôn ngữ) được lưu riêng, khôi phục khi mở lại Factory — không lẫn nhau, đỡ gọi lại AI. |

### 🗂️ Quản lý & Trải nghiệm
| Tính năng | Mô tả |
|-----------|-------|
| 🗂️ **Deck Manager** | Tạo/đổi tên/xóa deck & sub-deck, xem cây deck và số thẻ (utils/deck_manager.py + ui/deck_manager_dialog.py) |
| 🎮 **Interactive Games** | Word Building (drag & drop, có pool riêng cho Hangul Hàn), Handwriting practice, Letter Gap. |
| 🔍 **Kiểm Định Thông Minh** | Phát hiện từ mới, cập nhật, trùng lặp, và từ cùng mặt chữ khác nghĩa. |
| ⚡ **Speed Control** | Tùy chỉnh tốc độ audio 0.25×–4.0× ngay trên thẻ review. |

---

## 📦 Cài đặt

### Yêu cầu
- Anki 2.1.50 (xem [compatibility matrix](COMPATIBILITY.md))
- Python 3.9 (bundled with the supported Anki runtime)
- `edge-tts` (cài rõ ràng bằng lệnh được hiển thị khi thiếu)
- `gtts` (optional, fallback)

### Cài đặt thủ công
> **⚠️ Bento Forge hiện được tích hợp sẵn trong `Bento Station AIOS`** (thư mục con `Bento Forge/`). Thường bạn chỉ cần cài Bento Station AIOS; Forge tự xuất hiện qua `bento_forge_bridge.py`. Nếu muốn chạy độc lập:

```bash
# 1. Vào thư mục addons của Anki
cd %APPDATA%/Anki2/addons21/

# 2. Clone repo (standalone)
git clone https://github.com/DeliChese/Anki-Bento-Forge.git

# 3. Khởi động lại Anki
```

### Cấu hình AI
1. Mở Anki → Tools → **🧪 Bento Forge** (Ctrl+Shift+I)
2. Bấm **⚙️ Cài Đặt API**
3. Nhập API Key từ [DeepSeek](https://platform.deepseek.com/api_keys) hoặc OpenAI
4. Chọn preset hoặc nhập thủ công Base URL + Model
5. Bấm **🧪 Test Kết Nối** → **💾 Lưu**

### Hỗ trợ AI Providers
- **DeepSeek** (`deepseek-chat`, `deepseek-reasoner`)
- **OpenAI** (`gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`)
- **Ollama** (local, miễn phí)
- **LM Studio** (local, miễn phí)
- **OpenRouter** (multi-model gateway)

---

## 🚀 Sử dụng nhanh

### Cách 1: Import JSON thủ công
```json
[
  {
    "front": "食べる",
    "furigana": "たべる",
    "meaning": "ăn",
    "jlptlevel": "N5",
    "topic": "Động từ",
    "example": "毎日ご飯を食べるよ。",
    "example_vn": "Hàng ngày tớ ăn cơm đó."
  }
]
```
1. Dán JSON vào khung bên trái
2. Chọn Deck đích
3. Bấm **🌪️ Kiểm Định** → kiểm tra kết quả
4. Bấm **🚀 XUẤT XƯỞNG**

### Cách 2: AI Trích Xuất
1. Dán văn bản tiếng Nhật/Trung/Hàn vào ô "📝 Dán văn bản..."
2. (Optional) Thêm lời nhắn: "Chỉ lấy từ N3+, chủ đề ẩm thực"
3. Bấm **🤖 AI Trích Xuất**
4. Xem trước, chỉnh sửa, xóa nếu cần
5. Bấm **✅ CHẤP NHẬN & ĐỔ VÀO XƯỞNG**

### Cách 3: AI Chat
1. Viết câu hỏi/yêu cầu vào ô text
2. Bấm **💬 Gửi**
3. AI sẽ phân tích hệ thống Anki và trả lời
4. Nếu AI đề xuất từ vựng → bấm **✅ Đổ Vào Xưởng**

---

## 🏗️ Cấu trúc dự án

```
Anki-Bento-Forge/          # (đóng gói thành bento-forge.ankiaddon khi release)
├── __init__.py           # Entry point + Main Dialog (AnkiSmartFactory)
├── audio/                # TTS engines (Edge, gTTS, VoiceVox) — router engine.py
├── Language/             # Language configs (Japanese, Chinese, Korean + grammar)
├── mode/                 # Card templates, CSS, JS games (combo mode) + card_render.py (tự append field)
├── ui/                   # UI dialogs (ai_dialogs, ai_preview, batch, deck_manager, theme, prompt_editor, history...)
├── workers/              # Background threads (import, AI, preview, batch, deck scan)
├── utils/                # AI extractor, batch processor, prompt_config, JSON parser, logger, i18n, deck cache, deck manager
├── hooks/                # Reviewer hooks (speed, letter gap) + overview_mode.py (mode selector)
├── tests/                # 411 unit & integration tests (29 file)
├── .claude/              # 🆕 Hệ thống SKILL cho AI — nguồn kiến thức chính thức
│   ├── CLAUDE.md         # Memory gốc + index skills (đọc trước)
│   └── skills/           # 12 skill theo chủ đề (bảo trì/nâng cấp tiết kiệm token)
├── AGENTS.md             # 🆕 Điểm vào cho mọi AI agent → trỏ tới .claude/
├── README.md             # ← File này
├── CODE_MAP.md           # ⚠️ Tài liệu CŨ (lỗi thời) — dùng .claude/ thay thế
├── UPGRADE_GUIDE.md      # ⚠️ Tài liệu CŨ (lỗi thời) — dùng .claude/ thay thế
├── REFACTOR_PLAN.md      # Kế hoạch tái cấu trúc
└── CHANGELOG.md          # Lịch sử phiên bản
```

> 💡 **Dành cho AI/Vibe coding**: đọc [`.claude/CLAUDE.md`](.claude/CLAUDE.md) trước → chọn đúng 1 skill → chỉ đọc đúng file/dòng cần sửa (line number có sẵn trong skill). Hệ thống này giúp tiết kiệm token tối đa mà vẫn chính xác.

---

## 🧪 Chạy tests

```bash
# Cài pytest
pip install pytest

# Chạy tất cả tests (từ thư mục gốc repo Anki-Bento-Forge)
python -m pytest tests/ -v

# Chạy test cụ thể
python -m pytest tests/test_json_parser.py -v
python -m pytest tests/test_audio_engine.py -v
python -m pytest tests/test_combo_mode.py -v
```

---

## 🤝 Đóng góp

1. Fork repo
2. Tạo branch: `git checkout -b feature/tinh-nang-moi`
3. Commit: `git commit -m "Thêm tính năng X"`
4. Push: `git push origin feature/tinh-nang-moi`
5. Tạo Pull Request

**Trước khi PR, vui lòng:**
- [ ] Chạy `python -m pytest tests/ -v`
- [ ] Test trên Anki thật
- [ ] Cập nhật `CHANGELOG.md`
- [ ] Đảm bảo không có API key trong code

---

## 📄 License

MIT License — Xem file `LICENSE`

---

## ⚠️ Bảo mật

- **Không commit `utils/ai_config.json`** — file này đã được thêm vào `.gitignore`
- Dùng `utils/ai_config.example.json` làm mẫu
- Các dữ liệu cá nhân (`utils/import_history.json`, `utils/ai_cache/`, `utils/factory_state.json`) cũng nằm trong `.gitignore`
- Nếu lỡ commit API key, **revoke key ngay** trên dashboard của provider

---

## 🙏 Credits

- [Anki](https://apps.ankiweb.net/) — Nền tảng flashcard mã nguồn mở
- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge TTS Python wrapper
- [DeepSeek](https://deepseek.com/) — AI API giá rẻ cho tiếng Á Đông
