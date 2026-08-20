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
            "deepseek-v4-flash",
            "deepseek-v4-pro",
            # Legacy aliases are retained so existing saved configurations keep working.
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "default": "deepseek-v4-flash",
        "color": "#4D6BFE",
        "key_hint": "sk-... (platform.deepseek.com/api_keys)",
        "note": "DeepSeek V4 Flash = nhanh/tiết kiệm; V4 Pro = chất lượng cao hơn. Các alias cũ vẫn được giữ để tương thích cấu hình đã lưu.",
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "base": "https://api.openai.com/v1",
        "models": [
            "gpt-5.6-luna",
            "gpt-5.6-terra",
            "gpt-5.6-sol",
            "gpt-5.6",
            "gpt-5.5",
            "gpt-5.5-pro",
            "gpt-5.4",
            "gpt-5.4-pro",
            "gpt-5.4-mini",
            "gpt-5.4-nano",
            # Previous models remain selectable for existing configurations.
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
        "default": "gpt-5.6-luna",
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
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.1-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ],
        "default": "gemini-3.6-flash",
        "color": "#4285F4",
        "key_hint": "AIza... (https://aistudio.google.com/apikey)",
        "note": (
            "Gemini API — dùng endpoint OpenAI-compatible chính thức của Google.\n"
            "Preset gồm Gemini 3.6/3.5/3.1 hiện hành và các model Gemini 2.5 ổn định.\n"
            "Lấy API key tại: https://aistudio.google.com/apikey (bắt đầu bằng AIza...)"
        ),
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "base": "https://api.anthropic.com/v1",
        "models": [
            "claude-fable-5",
            "claude-opus-5",
            "claude-sonnet-5",
            "claude-haiku-4-5",
            # Previous models remain selectable for existing proxy configurations.
            "claude-opus-4-1",
            "claude-sonnet-4-5",
            "claude-3-7-sonnet",
            "claude-3-5-sonnet-v2",
            "claude-3-5-haiku",
            "claude-3-haiku",
        ],
        "default": "claude-sonnet-5",
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
            "~openai/gpt-latest",
            "openai/gpt-5.5",
            "anthropic/claude-opus-5",
            "anthropic/claude-sonnet-5",
            "google/gemini-3.6-flash",
            "google/gemini-3.5-flash",
            "deepseek/deepseek-v4-flash",
            "deepseek/deepseek-v4-pro",
            # Popular previous slugs are retained for existing configurations.
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
        "default": "~openai/gpt-latest",
        "color": "#835AF9",
        "key_hint": "sk-or-... (https://openrouter.ai/settings/keys)",
        "note": "Một key dùng được ĐỦ model từ nhiều hãng (OpenAI, Claude, Gemini, DeepSeek, Llama...).\n`~openai/gpt-latest` tự theo flagship OpenAI mới nhất; model khác dùng định dạng vendor/ten-model.",
    },
    {
        "id": "ollama",
        "name": "Ollama (local)",
        "base": "http://localhost:11434/v1",
        "models": [
            "qwen3.5",
            "gemma4",
            # Các model dưới đây vẫn phổ biến và được giữ cho máy đã cài sẵn.
            "llama3.1",
            "llama3.2",
            "gemma3",
            "gemma2",
            "mistral",
            "qwen2.5",
            "qwen3",
        ],
        "default": "qwen3.5",
        "color": "#A3E635",
        "key_hint": "(không cần — máy local)",
        "note": "Chạy hoàn toàn local — không cần API Key. Cài một model đã chọn, ví dụ `ollama pull qwen3.5`.",
    },
    {
        "id": "lmstudio",
        "name": "LM Studio (local)",
        "base": "http://localhost:1234/v1",
        "models": [
            "local-model",
            "qwen3.5",
            "gemma4",
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

_PROVIDER_CAPABILITIES = {
    "deepseek": {"supports_json_mode": True, "supports_structured_output": False},
    "openai": {"supports_json_mode": True, "supports_structured_output": True},
    "gemini": {"supports_json_mode": False, "supports_structured_output": True},
    "anthropic": {"supports_json_mode": False, "supports_structured_output": True},
    "openrouter": {"supports_json_mode": False, "supports_structured_output": False},
    "ollama": {"supports_json_mode": False, "supports_structured_output": False},
    "lmstudio": {"supports_json_mode": False, "supports_structured_output": False},
}


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


def get_provider_capabilities(api_base: str, model: str = "") -> dict:
    """Return provider metadata without model-name conditionals in workflows."""
    provider = detect_provider(api_base, model) or "custom"
    capabilities = dict(_PROVIDER_CAPABILITIES.get(provider, {}))
    capabilities.update({
        "provider": provider,
        "finish_reason_truncation": (
            "length", "max_tokens", "max_output_tokens", "incomplete",
        ),
        "known_card_wrappers": ("cards", "items", "results"),
    })
    return capabilities


_MODEL_CONTEXT_WINDOWS = {
    "deepseek-v4-flash": 128_000,
    "deepseek-v4-pro": 128_000,
    "deepseek-chat": 64_000,
    "deepseek-reasoner": 64_000,
    "gpt-5.6-luna": 256_000,
    "gpt-5.6-terra": 256_000,
    "gpt-5.6-sol": 256_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "claude-sonnet-5": 200_000,
    "claude-opus-5": 200_000,
    "gemini-3.6-flash": 1_000_000,
    "gemini-3.5-flash": 1_000_000,
}


def get_model_context_window(model: str, fallback: int = 32_768) -> int:
    """Return trusted local metadata or a conservative unknown-model budget."""
    normalized = str(model or "").strip().lower()
    direct = _MODEL_CONTEXT_WINDOWS.get(normalized)
    if direct:
        return direct
    # OpenRouter uses vendor/model slugs; preserve only a known suffix match.
    for known, window in _MODEL_CONTEXT_WINDOWS.items():
        if normalized.endswith("/" + known):
            return window
    return max(4_096, int(fallback))
