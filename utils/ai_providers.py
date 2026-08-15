"""
🎛️ AI Provider Presets — danh sách nhà cung cấp + model chính xác theo nhà cung cấp.

Mỗi provider có:
- id: định danh (lưu vào ai_config.json)
- name: tên hiển thị
- base: API Base URL mặc định
- models: danh sách model CHÍNH XÁC của nhà cung cấp đó
- default_model: model mặc định
- color: màu đặc trưng (dùng cho hiệu ứng glow/hover)
- note: ghi chú (tùy chọn)
"""

# ═══════════════════════════════════════════════════════════
#  PROVIDER PRESETS
# ═══════════════════════════════════════════════════════════

AI_PROVIDERS = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "base": "https://api.deepseek.com/v1",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "default": "deepseek-chat",
        "color": "#4D6BFE",
        "key_hint": "sk-... (platform.deepseek.com/api_keys)",
        "note": "deepseek-chat = nhanh/rẻ; deepseek-reasoner = suy nghĩ sâu (đắt hơn, chậm hơn).",
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "base": "https://api.openai.com/v1",
        "models": [
            "gpt-5",
            "gpt-5-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "o3",
            "o3-mini",
            "o4-mini",
            "gpt-3.5-turbo",
        ],
        "default": "gpt-4o-mini",
        "color": "#10A37F",
        "key_hint": "sk-... (https://platform.openai.com/api-keys)",
        "note": "Mô hình GPT + o-series chính thức của OpenAI.",
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-3.6-flash",
            "gemini-3.6-pro",
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-3-flash",
            "gemini-3-pro",
        ],
        "default": "gemini-3.6-flash",
        "color": "#4285F4",
        "key_hint": "AIza... (https://aistudio.google.com/apikey)",
        "note": (
            "Gemini API — dùng endpoint OpenAI-compatible chính thức của Google.\n"
            "Cập nhật các model Gemini thế hệ 3.x mới nhất (gemini-3.6-flash, gemini-3.6-pro...).\n"
            "Lấy API key tại: https://aistudio.google.com/apikey (bắt đầu bằng AIza...)"
        ),
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "base": "https://api.anthropic.com/v1",
        "models": [
            "claude-opus-4-1",
            "claude-sonnet-4-5",
            "claude-3-7-sonnet",
            "claude-3-5-sonnet-v2",
            "claude-3-5-haiku",
            "claude-3-haiku",
        ],
        "default": "claude-sonnet-4-5",
        "color": "#D97757",
        "key_hint": "sk-ant-... (https://console.anthropic.com/settings/keys)",
        "note": (
            "Đây là các model Claude chính xác. Bento Forge gọi API kiểu OpenAI-compatible, "
            "do đó với Anthropic bạn cần một proxy compatible (ví dụ LiteLLM / 1Backend) "
            "hoặc đổi API Base URL về proxy bạn đang dùng."
        ),
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "base": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4.5",
            "anthropic/claude-3.7-sonnet",
            "google/gemini-3.6-flash",
            "google/gemini-3.5-flash",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-r1",
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-small-3.2-24b-instruct",
            "qwen/qwen-3-235b-a22b",
        ],
        "default": "openai/gpt-4o-mini",
        "color": "#835AF9",
        "key_hint": "sk-or-... (https://openrouter.ai/settings/keys)",
        "note": "Một key dùng được ĐỦ model từ nhiều hãng (OpenAI, Claude, Gemini, DeepSeek, Llama...).\nChú ý định dạng model: vendor/ten-model.",
    },
    {
        "id": "ollama",
        "name": "Ollama (local)",
        "base": "http://localhost:11434/v1",
        "models": [
            "llama3.1",
            "llama3.2",
            "gemma3",
            "gemma2",
            "mistral",
            "qwen2.5",
            "qwen3",
        ],
        "default": "llama3.1",
        "color": "#A3E635",
        "key_hint": "(không cần — máy local)",
        "note": "Chạy hoàn toàn local — không cần API Key. Cài model bằng `ollama pull llama3.1`.",
    },
    {
        "id": "lmstudio",
        "name": "LM Studio (local)",
        "base": "http://localhost:1234/v1",
        "models": [
            "local-model",
            "llama-3.1-8b-instruct",
            "qwen2.5-7b-instruct",
            "gemma-3-12b-it",
        ],
        "default": "local-model",
        "color": "#7C8CF8",
        "key_hint": "(không cần — máy local)",
        "note": "Mở LM Studio → Start Server. Model Combo có thể đổi thành tên model bạn đã tải về.",
    },
]

PROVIDER_MAP = {p["id"]: p for p in AI_PROVIDERS}


def get_providers():
    """Trả về danh sách provider preset (bản copy)."""
    return [dict(p, models=list(p["models"])) for p in AI_PROVIDERS]


def get_provider(provider_id):
    """Trả provider dict theo id (hoặc None)."""
    return PROVIDER_MAP.get(provider_id)


def detect_provider(api_base, model=""):
    """Nhận diện provider từ API Base URL (và model nếu URL không đủ).

    Dùng khi mở Cài Đặt AI để tự chọn đúng provider đang cấu hình.
    """
    if not api_base:
        return ""
    base = api_base.lower()
    if "openrouter" in base:
        return "openrouter"
    if "generativelanguage" in base or "googleapis" in base:
        return "gemini"
    if "api.anthropic.com" in base or "claude" in base or "anthropic" in base:
        return "anthropic"
    if "deepseek" in base:
        return "deepseek"
    if "11434" in base:
        return "ollama"
    if "1234" in base:
        return "lmstudio"
    if "openai" in base or base == "https://api.openai.com/v1":
        return "openai"
    return ""