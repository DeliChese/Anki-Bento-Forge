# 🌐 Bento Forge 18.3.0

> Factory tạo thẻ ngoại ngữ cho Anki, tập trung vào tiếng Nhật, Trung, Hàn và Anh.

[![Version](https://img.shields.io/badge/version-18.3.0-blue)](manifest.json)
[![Anki](https://img.shields.io/badge/anki-2.1.50_to_26.5-green)](COMPATIBILITY.md)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-yellow)](manifest.json)
[![Tests](https://github.com/DeliChese/Anki-Bento-Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/DeliChese/Anki-Bento-Forge/actions/workflows/ci.yml)

`manifest.json` là nguồn chuẩn cho version và phạm vi tương thích. Bản `18.3.0` hiện là release candidate cục bộ; xem [Release Checklist](RELEASE_CHECKLIST.md) trước khi publish/tag.

## Phạm vi hiện hành

- Tạo thẻ Vocabulary, Grammar và Collocation/Thành ngữ cho bốn ngôn ngữ.
- Nhập từ văn bản, file tham khảo hoặc yêu cầu tạo thẻ trực tiếp; kết quả luôn qua Preview trước Import.
- Chất lượng AI V2.1 với Usage Pattern, Usage Note, ví dụ và kiểm tra đầu ra trước khi ghi collection.
- TTS Edge/Azure tùy cấu hình, audio lưu trong media của Anki và tốc độ phát 0.25×–4.0×.
- Combo mặc định dùng một card với năm bài tập; SRS độc lập là lựa chọn theo deck và có migration giữ lịch sử card cũ.
- Nâng cấp từng thẻ trong Reviewer hoặc đồng bộ toàn bộ Note Type theo mode đang chọn; mọi thay đổi đều có bước xác nhận và giữ nguyên SRS.
- Thẻ tiếng Trung có sơ đồ bộ thủ tương tác; Reviewer hỗ trợ luyện đặt câu và quản lý các phiên bản ví dụ.

### Knowledge beta (đang tắt)

Knowledge beta đang dormant và không nằm trong release gate của luồng Language hiện hành.

## Cài đặt

Yêu cầu: Anki 2.1.50 đến 26.5 và Python 3.9+. Package khai báo `edge-tts`/`gtts`, nhưng lỗi Edge không tự động hạ xuống gTTS. Chi tiết endpoint đã kiểm chứng nằm trong [Compatibility Matrix](COMPATIBILITY.md).

Bento Forge thường được tích hợp trong `Bento Station AIOS`. Khi cài độc lập, đặt hoặc clone repo vào thư mục `addons21`, sau đó khởi động lại Anki:

```powershell
Set-Location $env:APPDATA\Anki2\addons21
git clone https://github.com/DeliChese/Anki-Bento-Forge.git
```

Mở **Tools → 🧪 Bento Forge** hoặc nhấn `Ctrl+Shift+I`.

## Cấu hình AI

1. Mở **⚙️ Cài Đặt API**.
2. Chọn OpenAI, DeepSeek, Ollama, LM Studio hoặc OpenRouter; nhập API key/Base URL/model phù hợp.
3. Bấm **🧪 Test Kết Nối**, rồi lưu cấu hình.
4. Không commit `utils/ai_config.json` hoặc file state/cache cá nhân.

## Flow sử dụng nhanh

1. Chọn ngôn ngữ, Vocabulary/Grammar/Collocation và deck đích.
2. Dán nguồn, đính kèm file hoặc dùng **Chat tạo thẻ**. Một lượt trực tiếp nhận tối đa 4.000 ký tự nguồn và tạo 5–20 thẻ.
3. Chỉnh yêu cầu nếu cần, rồi gọi AI.
4. Kiểm tra/sửa/xóa mục trong Preview.
5. Đưa kết quả vào khu kiểm định và Import. Với collection quan trọng, luôn dùng profile backup và kiểm tra Undo.

Để nâng nội dung cũ, dùng **Nâng cấp thẻ** trong Reviewer cho một note hoặc **🔄 Đồng bộ thẻ cũ** trong Factory cho Note Type đang chọn. Đồng bộ template chạy trước và không tốn AI; chỉ note thiếu/cũ mới được đề xuất gọi AI.

## Kiến trúc ngắn

```text
__init__.py       compatibility facade và public re-export
Language/         cấu hình field/model cho bốn ngôn ngữ
mode/             template, CSS/JS và card rendering
audio/            TTS router và provider
utils/            AI, prompt, parser, cache, import và domain services
workers/          tác vụ nền Qt/Anki
ui/, hooks/       dialog và tích hợp Anki/Reviewer
tests/            regression suite
benchmarks/       bằng chứng chất lượng/cost
```

Tài liệu dành cho maintainer:

- [AGENTS.md](AGENTS.md): điểm vào bắt buộc cho agent.
- [Architecture Overview](docs/architecture.md): ownership ở mức tổng quan.
- [Personal Roadmap](work_items/PERSONAL_ROADMAP.md): backlog và quyết định sản phẩm hiện hành.
- [Work Items Index](work_items/README.md): mục lục tài liệu, trạng thái và đề xuất dọn dẹp.
- [Contributing](CONTRIBUTING.md), [Debugging](DEBUGGING.md), [Security](SECURITY.md).

## Kiểm chứng

```powershell
python -m pytest tests/test_release_metadata.py -q
python -m pytest tests/ -q
```

Trước release, chạy harness cô lập hai vòng, build artifact và hoàn tất smoke Anki thật theo [Release Checklist](RELEASE_CHECKLIST.md). Không coi số test ghi trong tài liệu lịch sử là baseline hiện hành.

## License

MIT License — xem file `LICENSE`.
