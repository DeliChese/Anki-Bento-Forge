"""
Audio engine for Japanese/Chinese vocabulary cards.
Thread-safe voice selection and speed settings.
"""

import threading
from typing import Optional

from .tts import (
    _install_edge_tts, get_audio_azure_tts, get_audio_edge_tts,
    get_cached_azure_voice_options, get_tts_config,
)


VOICE_OPTIONS = {
    "ja": [
        # Chỉ còn 2 giọng GA từ Microsoft (7/2026).
        # AoiNeural & DaichiNeural đã bị Microsoft loại bỏ → lỗi khi gọi.
        {"id": "ja-JP-NanamiNeural", "name": "Nanami (Nữ)",  "gender": "female"},
        {"id": "ja-JP-KeitaNeural",  "name": "Keita (Nam)",  "gender": "male"},
    ],
    "zh": [
        # Giọng Phổ Thông Trung Quốc (zh-CN) — 4 giọng
        {"id": "zh-CN-XiaoxiaoNeural",  "name": "Xiaoxiao (Nữ, CN)",      "gender": "female"},
        {"id": "zh-CN-XiaoyiNeural",    "name": "Xiaoyi (Nữ, CN)",        "gender": "female"},
        {"id": "zh-CN-YunxiNeural",     "name": "Yunxi (Nam, CN)",        "gender": "male"},
        {"id": "zh-CN-YunyangNeural",   "name": "Yunyang (Nam, CN)",      "gender": "male"},
        # Giọng Phổ Thông Đài Loan (zh-TW) — 2 giọng
        {"id": "zh-TW-HsiaoChenNeural", "name": "HsiaoChen (Nữ, TW)",    "gender": "female"},
        {"id": "zh-TW-HsiaoYuNeural",   "name": "HsiaoYu (Nữ, TW)",      "gender": "female"},
        # Giọng Quảng Đông (zh-HK) — 2 giọng
        {"id": "zh-HK-HiuGaaiNeural",   "name": "HiuGaai (Nữ, HK)",      "gender": "female"},
        {"id": "zh-HK-WanLungNeural",   "name": "WanLung (Nam, HK)",     "gender": "male"},
    ],
    "ko": [
        # Giọng Hàn Quốc (ko-KR) — 4 giọng
        {"id": "ko-KR-SunHiNeural",   "name": "SunHi (Nữ)",     "gender": "female"},
        {"id": "ko-KR-InJoonNeural",  "name": "InJoon (Nam)",   "gender": "male"},
        {"id": "ko-KR-JiMinNeural",   "name": "JiMin (Nữ)",     "gender": "female"},
        {"id": "ko-KR-HyunsuNeural",  "name": "Hyunsu (Nam)",   "gender": "male"},
    ],
    "en": [
        {"id": "en-GB-SoniaNeural", "name": "Sonia (Nữ, UK)", "gender": "female"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (Nam, UK)", "gender": "male"},
        {"id": "en-US-JennyNeural", "name": "Jenny (Nữ, US)", "gender": "female"},
        {"id": "en-US-GuyNeural", "name": "Guy (Nam, US)", "gender": "male"},
    ],
}

VOICE_SAMPLE = {
    "ja": "こんにちは、今日もよく頑張りましょう！",
    "zh": "你好，今天也要加油哦！",
    "ko": "안녕하세요, 오늘도 힘내세요!",
    "en": "Hello! Let's make today a good learning day.",
}

# Voice đang được chọn cho mỗi ngôn ngữ (thread-safe)
_selected_voice: dict = {}
_selected_voice_lock = threading.Lock()

# Tốc độ phát mặc định cho mỗi ngôn ngữ (thread-safe)
_default_speed: dict = {}
_default_speed_lock = threading.Lock()


def get_voice_options(lang: str) -> list:
    """Return cached Azure Neural choices when Azure is active, otherwise Edge."""
    if get_tts_config().get("provider") == "azure":
        azure_voices = get_cached_azure_voice_options(lang)
        if azure_voices:
            return azure_voices
    return VOICE_OPTIONS.get(lang, [])


def get_selected_voice(lang: str) -> str:
    """Trả về voice ID đang được chọn (mặc định = giọng đầu tiên)"""
    with _selected_voice_lock:
        if lang not in _selected_voice:
            opts = get_voice_options(lang)
            return opts[0]["id"] if opts else ""
        return _selected_voice[lang]


def set_selected_voice(lang: str, voice_id: str):
    """Lưu voice được chọn cho ngôn ngữ"""
    with _selected_voice_lock:
        _selected_voice[lang] = voice_id


def get_default_speed(lang: str) -> float:
    """Trả về tốc độ phát mặc định cho ngôn ngữ (mặc định 1.0)"""
    with _default_speed_lock:
        return _default_speed.get(lang, 1.0)


def set_default_speed(lang: str, speed: float):
    """Lưu tốc độ phát mặc định cho ngôn ngữ"""
    with _default_speed_lock:
        _default_speed[lang] = speed


# Map model name → language code để reviewer hook có thể phát hiện ngôn ngữ
_MODEL_LANG_MAP = {
    "AnkiTool Japanese V18.3 (Add-on)": "ja",
    "AnkiTool Japanese V18.1 (Add-on)": "ja",
    "AnkiTool Japanese V17.0 (Add-on)": "ja",
    "AnkiTool Japanese V16.0 (Add-on)": "ja",
    "AnkiTool Japanese V15.0 (Add-on)": "ja",
    "Mẫu Từ Vựng Tiếng Nhật V14.0 (Add-on)": "ja",
    "AnkiTool Japanese Grammar V18.3 (Add-on)": "ja",
    "AnkiTool Japanese Grammar V18.1 (Add-on)": "ja",
    "AnkiTool Japanese Grammar V17.0 (Add-on)": "ja",
    "AnkiTool Japanese Grammar V16.0 (Add-on)": "ja",
    "AnkiTool Chinese V18.3 (Add-on)": "zh",
    "AnkiTool Chinese V18.1 (Add-on)": "zh",
    "AnkiTool Chinese V17.0 (Add-on)": "zh",
    "AnkiTool Chinese V16.0 (Add-on)": "zh",
    "AnkiTool Chinese V15.0 (Add-on)": "zh",
    "AnkiTool Chinese Grammar V18.3 (Add-on)": "zh",
    "AnkiTool Chinese Grammar V18.1 (Add-on)": "zh",
    "AnkiTool Chinese Grammar V17.0 (Add-on)": "zh",
    "AnkiTool Chinese Grammar V16.0 (Add-on)": "zh",
    "AnkiTool Korean V18.3 (Add-on)": "ko",
    "AnkiTool Korean V18.1 (Add-on)": "ko",
    "AnkiTool Korean V17.0 (Add-on)": "ko",
    "AnkiTool Korean Grammar V18.3 (Add-on)": "ko",
    "AnkiTool Korean Grammar V18.1 (Add-on)": "ko",
    "AnkiTool Korean Grammar V17.0 (Add-on)": "ko",
    "AnkiTool English V18.3 (Add-on)": "en",
    "AnkiTool English V18.1 (Add-on)": "en",
    "AnkiTool English V17.0 (Add-on)": "en",
    "AnkiTool English Grammar V18.3 (Add-on)": "en",
    "AnkiTool English Grammar V18.1 (Add-on)": "en",
    "AnkiTool English Grammar V17.0 (Add-on)": "en",
}


def detect_lang_from_model(model_name: str) -> str:
    """Phát hiện ngôn ngữ từ tên model của thẻ"""
    return _MODEL_LANG_MAP.get(model_name, "")


def get_audio_multilang(
    text: str,
    lang: str,
    voice: str = None,
    rate: str = None,
    cancel_event: Optional[threading.Event] = None,
    track_usage: bool = True,
) -> Optional[str]:
    """Generate high-quality Neural audio; cancellation reaches the provider.

    gTTS is intentionally not substituted automatically: a transient Edge
    error must not create lower-quality audio mixed into the same deck.
    """
    if not text or not text.strip():
        return ""

    chosen_voice = voice or get_selected_voice(lang)
    if not chosen_voice:
        return ""

    if get_tts_config().get("provider") == "azure":
        return get_audio_azure_tts(
            text, chosen_voice, lang, rate=rate, cancel_event=cancel_event,
            track_usage=track_usage,
        ) or ""
    if not _install_edge_tts():
        return ""
    return get_audio_edge_tts(text, chosen_voice, lang, rate=rate, cancel_event=cancel_event) or ""


def speed_to_edge_rate(speed: float) -> str:
    """Chuyển tốc độ (0.25-4.0) sang edge-tts rate string (-50% → +100%)"""
    pct = (speed - 1.0) * 100
    pct = max(-50, min(100, int(round(pct))))
    return f"{'+' if pct >= 0 else ''}{pct}%"
