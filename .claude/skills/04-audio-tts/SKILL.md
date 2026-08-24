---
name: audio-tts
description: Hệ thống audio/TTS — audio/engine.py (router + voice/speed) + audio/tts.py (Edge/gTTS/VoiceVox). Đọc khi sửa giọng đọc, tốc độ, audio generation.
---

# 🎤 SKILL-04: AUDIO & TTS

## `audio/engine.py` (197 dòng) — ROUTER & STATE

| Symbol | Dòng | Ghi chú |
|--------|------|---------|
| `VOICE_OPTIONS` | 12 | dict `{ja: [...], zh: [...], ko: [...]}` — **ja chỉ còn Nanami & Keita** (Microsoft loại AoiNeural/DaichiNeural 7/2026); zh có 8 giọng (CN/TW/HK); ko có 4 giọng (SunHi/InJoon/JiMin/Hyunsu) |
| `VOICE_SAMPLE` | 47 | text mẫu preview (ja/zh/ko) |
| `_selected_voice` + lock | 61-62 | ⚠️ thread-safe bắt buộc |
| `_default_speed` + lock | 68-69 | ⚠️ thread-safe bắt buộc |
| `TTS_PROVIDERS` + selection | 58, 72-81 | `edge` (default) hoặc `melo`, lock bắt buộc |
| `get_voice_options(lang, provider=None)` | 84 | MeloTTS dùng danh sách voice cục bộ riêng |
| `get_selected_voice(lang, provider=None)` | 93 | voice state tách theo provider + ngôn ngữ |
| `set_selected_voice(lang, id, provider=None)` | 104 | |
| `get_default_speed(lang)` | 111 | default 1.0 |
| `set_default_speed(lang, spd)` | 117 | |
| `_MODEL_LANG_MAP` | 124 | model name → lang code (ja/zh/ko, gồm cả V17 + Grammar models) |
| `detect_lang_from_model(name)` | 151 | dùng bởi reviewer hook |
| `get_audio_multilang(text, lang, voice=None, rate=None)` | 156 | **Router chính**: MeloTTS local (fail closed) hoặc Edge → gTTS fallback. rate là percent string |
| `speed_to_edge_rate(speed)` | 193 | (0.25-4.0) → "-50%"..."+100%", clamp |

## `audio/tts.py` (548 dòng) — PROVIDERS

| Symbol | Dòng | Ghi chú |
|--------|------|---------|
| `_install_edge_tts()` | 93 | chỉ kiểm tra dependency edge-tts |
| `_install_gtts()` | 100 | chỉ kiểm tra dependency gTTS |
| `get_audio_edge_tts(text, voice, lang="ja", rate=None)` | 287 | trả `[sound:filename]` tag |
| `get_audio_gtts(text, lang="ja")` | 342 | Edge fallback |
| `audio/melo.py` + `audio/melo_service.py` | n/a | Python 3.11 sidecar qua loopback token; cache model theo ngôn ngữ, WAV giới hạn 32 MB, atomic media publish |
| `get_audio_voicevox(text, speaker_id=3)` | 481 | local JP, dùng `mw.col.media` |

## LUỒNG GỌI AUDIO (IMPORT)

```python
# ImportWorker (workers/import_worker.py) gọi qua _generate_audio_safe:93
# PreviewThread (workers/ai_workers.py:23) gọi cùng router + speed_to_edge_rate
# Reviewer hook dùng detect_lang_from_model + get_default_speed để inject speed control
get_audio_multilang(text, lang, voice, rate)   # engine.py:156 — điểm vào chính
```

## TRAPS

1. **Thêm giọng**: chỉ thêm vào `VOICE_OPTIONS` — phải chắc chắn giọng còn tồn tại trên Microsoft Edge (AoiNeural/DaichiNeural từng bị loại → lỗi khi gọi).
2. **Thread-safe**: mọi đọc/ghi `_selected_voice`/`_default_speed` PHẢI trong `with _lock:`.
3. **Không import Anki (aqt) ở top-level** trong tts.py ngoài `mw` (đã import từ aqt — giữ nguyên).
4. MeloTTS khởi chạy bằng Python runtime riêng và chỉ lắng nghe `127.0.0.1`; khi Melo được chọn nhưng runtime lỗi thì fail closed, không gửi text qua Edge/gTTS.
5. `get_audio_multilang` fallback gTTS dùng `lang_code` (`"ja"`/`"zh"`/`"ko"`) — V17 đã sửa hardcode `"ja"`.
6. **Audio luôn sinh trong thread** (import/preview) — không gọi sync trong UI thread.

## VERIFY

```
python -m pytest tests/test_audio_engine.py tests/test_integration.py -v
```
