"""
🤖 AI Vocabulary Extractor — Dùng OpenAI-compatible API để trích xuất từ vựng từ văn bản

Hỗ trợ: OpenAI, DeepSeek, Claude (qua proxy), Ollama, LM Studio, và các API tương thích.
Cache thông minh: cache kết quả AI + cache danh sách từ vựng hiện có trong deck để tiết kiệm token.
Tự động quét deck Anki để tránh trùng lặp từ đã có.
API keys are stored only in the OS credential store (keyring).
"""

import json
import os
import re
import hashlib
import time
import base64
from urllib.parse import urlparse
from typing import Optional, Callable, List

from .credentials import delete_api_key, get_secret_store_status, load_api_key, save_api_key
from .logger import get_logger
from .i18n import t
from .ai_session_policy import get_ai_session_policy
from .ai_http_client import (
    abortable_wait as _abortable_wait,
    get_rate_limit_delay as _get_rate_limit_delay,
    is_openrouter as _is_openrouter_api,
    post_json as _http_post_json,
)
from .ai_result_cache import (
    DEFAULT_MAX_BYTES as _DEFAULT_AI_CACHE_MAX_BYTES,
    DEFAULT_MAX_FILES as _DEFAULT_AI_CACHE_MAX_FILES,
    DEFAULT_PROMPT_VERSION as _DEFAULT_PROMPT_VERSION,
    build_cache_key as _build_ai_cache_key,
    clear_result_cache as _clear_ai_result_cache,
    get_cached_result as _get_cached_ai_result,
    set_cached_result as _set_cached_ai_result,
)
from .ai_response_parser import parse_ai_json_with_comment as _parse_ai_json_with_comment
from .ai_response_guard import (
    adapt_chat_completion_response, enable_deepseek_json_output,
    get_final_model_content,
)
from .ai_reliability import (
    AiOutputFailure,
    extract_optional_card_payload as _extract_optional_card_payload,
    validated_cards_from_result as _validated_cards_from_result,
)
from .ai_text_recovery import recover_text_chunk as _recover_text_chunk
from .ai_output_validation import cache_payload_is_compatible
from .ai_prompt_defaults import KNOWLEDGE_PROMPT_VERSION
from .ai_usage_history import record_usage as _record_usage
from .user_data import (
    atomic_write_json,
    get_user_data_path,
    migrate_legacy_json,
    read_json,
)

logger = get_logger()

# ═══════════════════════════════════════════════════════════
#  PROMPT CONFIG — System prompt + JSON template có thể ghi đè ngoài
#  (utils/ai_prompts.json qua utils/prompt_config.py) mà không sửa code.
#  Lazy import trong prompt_config để tránh circular import.
# ═══════════════════════════════════════════════════════════
from .prompt_config import (
    get_system_prompt as get_effective_system_prompt,
    get_json_template as get_effective_json_template,
    get_signature as get_prompt_signature,
    get_fields as get_prompt_fields,
    get_field_count as get_prompt_field_count,
    save_config as save_prompt_config,
    reset_config as reset_prompt_config,
    get_effective_config as get_effective_prompt_config,
)

# ═══════════════════════════════════════════════════════════
#  LEGACY API KEY MIGRATION
# ═══════════════════════════════════════════════════════════

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


def _get_machine_key() -> bytes:
    """Tạo key từ machine-specific info (username + hostname + salt)."""
    import getpass, socket
    raw = f"{getpass.getuser()}:{socket.gethostname()}:anki_tool_v15_salt"
    return hashlib.sha256(raw.encode()).digest()


def _derive_fernet_key() -> bytes:
    """Derive Fernet key từ machine key + PBKDF2 (nếu có cryptography)."""
    if not _HAS_CRYPTO:
        return _get_machine_key()[:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"anki_tool_fernet_salt_v1",
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(_get_machine_key()))


def _decrypt_legacy_api_key(encrypted_text: str) -> str:
    """Read pre-Phase-2 key formats once, solely to migrate them to keyring."""
    if not encrypted_text:
        return ""
    # Plaintext fallback (old format)
    if not encrypted_text.startswith(("f:", "x:")):
        return encrypted_text
    try:
        prefix = encrypted_text[:2]
        data = base64.b64decode(encrypted_text[2:])
        if prefix == "f:" and _HAS_CRYPTO:
            f = Fernet(_derive_fernet_key())
            return f.decrypt(data).decode("utf-8")
        elif prefix == "x:":
            key = _get_machine_key()[:16]
            decrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
            return decrypted.decode("utf-8")
    except Exception:
        pass
    return encrypted_text

def is_openrouter(api_base: str = None) -> bool:
    """Compatibility wrapper for callers that rely on configured API base."""
    if not api_base:
        cfg = get_api_config()
        api_base = cfg.get("api_base", "")
    return _is_openrouter_api(api_base)

# ═══════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════
_LEGACY_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
# Optional compatibility overrides for tests. Runtime paths are resolved lazily
# because this module can be imported before Anki finishes loading a profile.
_CONFIG_PATH: Optional[str] = None
_CACHE_DIR: Optional[str] = None
_LEGACY_CONFIG_PATH = os.path.join(_LEGACY_CONFIG_DIR, "ai_config.json")
_LEGACY_CACHE_DIR = os.path.join(_LEGACY_CONFIG_DIR, "ai_cache")
_DECK_VOCAB_CACHE_TTL = 30 * 60  # 30 phút
_AI_CACHE_MAX_BYTES = _DEFAULT_AI_CACHE_MAX_BYTES
_AI_CACHE_MAX_FILES = _DEFAULT_AI_CACHE_MAX_FILES

# ── Chi phí AI tích lũy (theo dõi ngân sách) ──
_COST_STATE = {"total_usd": 0.0, "calls": 0, "last": None}


def get_total_cost() -> dict:
    """Trả về chi phí AI tích lũy của phiên làm việc (để hiển thị ở góc UI)."""
    return dict(_COST_STATE)


def reset_cost():
    """Đặt lại bộ đếm chi phí AI."""
    _COST_STATE["total_usd"] = 0.0
    _COST_STATE["calls"] = 0
    _COST_STATE["last"] = None
    get_ai_session_policy().reset()


def get_ai_session_estimate(text: str) -> dict:
    """Estimate a run before sending content; return aggregate data only."""
    cfg = get_api_config()
    policy = get_ai_session_policy()
    policy.configure(
        max_input_chars=cfg.get("session_max_input_chars", 90_000),
        max_tokens=cfg.get("session_max_tokens", 120_000),
        max_cost_usd=cfg.get("session_max_cost_usd", 2.0),
    )
    estimate = policy.estimate(
        text_chars=len(text or ""), model=cfg.get("model", ""),
        max_output_tokens=cfg.get("max_tokens", 8192), chunk_size=cfg.get("chunk_size", 8000),
    )
    result = {
        "input_tokens": estimate.input_tokens, "output_tokens": estimate.output_tokens,
        "total_tokens": estimate.total_tokens, "cost_usd": estimate.cost_usd,
        "calls": estimate.calls, "input_truncated": estimate.input_truncated,
    }
    result.update(policy.snapshot())
    result["blocked_reason"] = policy.check(estimate)
    return result


def ensure_ai_session_budget(text: str) -> dict:
    """Reject unsafe runs without logging or retaining their content."""
    estimate = get_ai_session_estimate(text)
    if estimate["input_truncated"]:
        raise ValueError(t("error_ai_input_limit"))
    if estimate["blocked_reason"]:
        reason_key = {"estimated token use exceeds the session token limit": "ai_budget_reason_estimate", "remaining session token budget is too small": "ai_budget_reason_tokens", "remaining session cost budget is too small": "ai_budget_reason_cost"}.get(estimate["blocked_reason"])
        raise ValueError(t("error_ai_budget_exceeded", reason=t(reason_key) if reason_key else estimate["blocked_reason"]))
    return estimate


def _record_token_info(
    token_info: dict,
    *,
    operation: str = "unknown",
    started_at: Optional[float] = None,
    duration_seconds: Optional[float] = None,
) -> None:
    """Update session counters and retain safe metadata for the usage dialog."""
    if not token_info:
        return
    get_ai_session_policy().record(token_info)
    try:
        _COST_STATE["total_usd"] = round(
            float(_COST_STATE.get("total_usd", 0.0)) + float(token_info.get("total_cost") or 0), 6
        )
        _COST_STATE["calls"] = int(_COST_STATE.get("calls", 0)) + 1
        _COST_STATE["last"] = dict(token_info)
    except (AttributeError, TypeError, ValueError):
        pass
    _record_usage(
        token_info,
        operation=operation,
        started_at=started_at,
        duration_seconds=duration_seconds,
    )


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
def _load_config() -> dict:
    config_path = _CONFIG_PATH or get_user_data_path("ai_config.json")
    migrate_legacy_json(_LEGACY_CONFIG_PATH, config_path, lambda value: isinstance(value, dict))
    return read_json(config_path, {}, lambda value: isinstance(value, dict))


def _save_config(cfg: dict):
    """Ghi config với atomic write (tmp → rename) để tránh mất dữ liệu nếu crash."""
    atomic_write_json(_CONFIG_PATH or get_user_data_path("ai_config.json"), cfg)


def get_api_key_storage_status() -> dict:
    """Expose credential-store availability to the settings UI."""
    return get_secret_store_status()


def _api_key_scope(provider: str = "", api_base: str = "") -> str:
    """Build a stable credential scope; custom endpoints stay separate too."""
    provider_id = (provider or "").strip().lower()
    if provider_id and provider_id != "__custom__":
        return provider_id
    host = urlparse(api_base or "").netloc.lower()
    return f"custom:{host}" if host else "default"


def get_api_key_for_provider(provider: str = "", api_base: str = "") -> str:
    """Read the key owned by one provider without changing the active config."""
    return load_api_key(_api_key_scope(provider, api_base)) or ""


def _migrate_legacy_api_key(cfg: dict, provider_scope: str) -> str:
    """Move a historical plaintext/Fernet/XOR value out of JSON exactly once."""
    legacy_value = cfg.pop("api_key", "")
    if not legacy_value:
        return ""
    api_key = _decrypt_legacy_api_key(legacy_value)
    if api_key and save_api_key(api_key, provider_scope):
        cfg["api_key_storage"] = "keyring"
        cfg["api_key_provider_migration_done"] = True
        logger.info("Migrated API key from legacy configuration to OS credential store")
        _save_config(cfg)
        return api_key

    # Do not retain plaintext or reversible XOR values after a failed migration.
    cfg["api_key_storage"] = "unavailable"
    _save_config(cfg)
    logger.warning("Legacy API key was removed because no secure credential store is available")
    return ""


def get_api_config() -> dict:
    defaults = {
        # NOTE: "api_key" is intentionally NOT a default here.  The API key is
        # stored only in the OS credential store; injecting it into `cfg` via
        # setdefault() made `if "api_key" in cfg` always true, so the keyring
        # branch below was never reached and a saved key appeared to vanish.
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "provider": "",
        "default_provider": "",
        "default_models": {},
        "temperature": 0.3,
        "max_tokens": 8192,
        # Độ dài nội dung tối đa gửi trong 1 request (ký tự) — DeepSeek 64k context
        "max_chars": 45000,
        # Kích thước chunk khi chia văn bản dài (ký tự).
        # 8k = cắt mịn → chất lượng cao hơn; an toàn với giới hạn OUTPUT ~8192 token.
        "chunk_size": 8000,
        # Mức độ nỗ lực suy nghĩ: "" / auto (không gửi), "low", "medium", "high"
        "reasoning_effort": "",
        "session_max_input_chars": 90000,
        "session_max_tokens": 120000,
        "session_max_cost_usd": 2.0,
    }
    cfg = _load_config()
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    if not isinstance(cfg.get("default_models"), dict):
        cfg["default_models"] = {}
    # Sanitize các giá trị đã lưu (VD bản cũ đang để chunk 45k → gây cắt output)
    try:
        cfg["max_chars"] = max(10000, min(45000, int(cfg.get("max_chars") or 45000)))
        cfg["chunk_size"] = max(3000, min(15000, int(cfg.get("chunk_size") or 8000)))
    except Exception:
        cfg["max_chars"] = 45000
        cfg["chunk_size"] = 8000
    try:
        cfg["session_max_input_chars"] = max(1_000, min(500_000, int(cfg.get("session_max_input_chars") or 90_000)))
        cfg["session_max_tokens"] = max(1_000, min(1_000_000, int(cfg.get("session_max_tokens") or 120_000)))
        cfg["session_max_cost_usd"] = max(0.0, min(1_000.0, float(cfg.get("session_max_cost_usd") or 0.0)))
    except (TypeError, ValueError):
        cfg["session_max_input_chars"] = 90_000
        cfg["session_max_tokens"] = 120_000
        cfg["session_max_cost_usd"] = 2.0
    provider_scope = _api_key_scope(cfg.get("provider", ""), cfg.get("api_base", ""))
    if "api_key" in cfg:
        resolved_api_key = _migrate_legacy_api_key(cfg, provider_scope)
    elif cfg.get("api_key_storage") == "keyring":
        resolved_api_key = load_api_key(provider_scope) or ""
        # Move the one pre-V17.2 generic key into the provider that was active
        # when the user upgrades. It is never used as a fallback afterwards,
        # so selecting another provider cannot expose the previous key.
        if not resolved_api_key and not cfg.get("api_key_provider_migration_done"):
            legacy_key = load_api_key() or ""
            if legacy_key and save_api_key(legacy_key, provider_scope):
                delete_api_key()
                resolved_api_key = legacy_key
            cfg["api_key_provider_migration_done"] = True
            _save_config(cfg)
    else:
        resolved_api_key = ""
    # Keep the returned runtime value separate from the persisted dictionary.
    # This protects against a future caller saving the resolved config by mistake.
    runtime_cfg = dict(cfg)
    runtime_cfg["api_key"] = resolved_api_key
    return runtime_cfg


def save_api_config(api_key: str, api_base: str, model: str, temperature: float = 0.3,
                    max_chars: int = 45000, chunk_size: int = 8000,
                    reasoning_effort: str = "", session_max_input_chars: int = 90000,
                    session_max_tokens: int = 120000, session_max_cost_usd: float = 2.0,
                    provider: str = "", make_default: bool = False):
    # Sanitize input
    api_base = api_base.strip().rstrip("/")
    if api_base and not api_base.startswith(("http://", "https://")):
        api_base = "https://" + api_base
    model = model.strip()
    temperature = max(0.0, min(2.0, temperature))
    max_chars = max(10000, min(45000, int(max_chars)))
    # 3k-15k — cắt mịn hơn để chất lượng tốt & không tràn output token (DeepSeek ~8192)
    chunk_size = max(3000, min(15000, int(chunk_size)))
    reasoning_effort = (reasoning_effort or "").strip().lower()
    if reasoning_effort not in ("low", "medium", "high"):
        reasoning_effort = ""

    api_key = api_key.strip()
    key_saved = True
    provider_id = (provider or "").strip()
    provider_scope = _api_key_scope(provider_id, api_base)
    if api_key:
        key_saved = save_api_key(api_key, provider_scope)
        key_storage = "keyring" if key_saved else "unavailable"
    else:
        delete_api_key(provider_scope)
        key_storage = "none"

    previous = _load_config()
    default_provider = str(previous.get("default_provider") or "").strip()
    default_models = dict(previous.get("default_models") or {}) \
        if isinstance(previous.get("default_models"), dict) else {}
    if make_default:
        default_provider = provider_id
        if model:
            default_models[provider_id or "__custom__"] = model

    cfg = {
        "api_key_storage": key_storage,
        "api_base": api_base,
        "model": model,
        "provider": provider_id,
        "default_provider": default_provider,
        "default_models": default_models,
        "api_key_provider_migration_done": True,
        "temperature": temperature,
        "max_tokens": 8192,
        "max_chars": max_chars,
        "chunk_size": chunk_size,
        "reasoning_effort": reasoning_effort,
        "session_max_input_chars": max(1_000, min(500_000, int(session_max_input_chars))),
        "session_max_tokens": max(1_000, min(1_000_000, int(session_max_tokens))),
        "session_max_cost_usd": max(0.0, min(1_000.0, float(session_max_cost_usd))),
    }
    _save_config(cfg)
    return key_saved


def _apply_reasoning_effort(payload: dict, cfg: dict):
    """Thêm reasoning_effort vào payload nếu được cấu hình (OpenAI o1/o3/o4, DeepSeek-compatible).

    Mức độ suy nghĩ cao → chất lượng tốt hơn nhưng tốn NHIỀU token output hơn.
    """
    effort = (cfg.get("reasoning_effort") or "").strip().lower()
    if effort in ("low", "medium", "high"):
        payload["reasoning_effort"] = effort
    return payload


def _check_truncated_output(content: str, progress_callback: Optional[Callable[[str], None]] = None):
    """Cảnh báo khi output JSON bị cắt (kết thúc không phải ] hoặc }).

    DeepSeek giới hạn output ~8192 token/response → nếu chunk quá lớn,
    JSON sẽ bị cắt giữa chừng gây lỗi parse.
    """
    if not content:
        return
    c = content.strip()
    if c and not (c.endswith("]") or c.endswith("}")):
        if progress_callback:
            progress_callback(t("warning_output_truncated"))


# ═══════════════════════════════════════════════════════════
#  TOKEN & COST TRACKING
# ═══════════════════════════════════════════════════════════

# DeepSeek pricing per 1M tokens (USD)
_DEEPSEEK_PRICING = {
    "deepseek-v4-flash": (0.14, 0.28),   # current price as of 2026-08-15
    "deepseek-v4-pro":   (0.435, 0.87),
    "deepseek-chat":      (0.14, 0.28),   # input, output
    "deepseek-reasoner":  (0.55, 2.19),
}


def _calculate_cost(
    model: str, prompt_tokens: int, completion_tokens: int, provider_cost=None
) -> dict:
    """Calculate cost from configured pricing, preferring provider-reported cost."""
    input_price, output_price = _DEEPSEEK_PRICING.get(model, (0.14, 0.28))
    input_cost = (prompt_tokens / 1_000_000) * input_price
    output_cost = (completion_tokens / 1_000_000) * output_price
    total = input_cost + output_cost
    cost_source = "configured_price"
    try:
        reported_cost = float(provider_cost)
        if reported_cost >= 0:
            if total > 0:
                input_cost = reported_cost * input_cost / total
                output_cost = reported_cost - input_cost
            else:
                input_cost, output_cost = reported_cost, 0.0
            total = reported_cost
            cost_source = "provider_reported"
    except (TypeError, ValueError):
        pass
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total, 6),
        "cost_source": cost_source,
    }


def _format_token_report(token_info: dict) -> str:
    """Format token + cost thành text hiển thị."""
    tc = token_info
    return t("token_report", input_tokens=tc["prompt_tokens"], output_tokens=tc["completion_tokens"],
             total_tokens=tc["total_tokens"], total_cost=tc["total_cost"],
             input_cost=tc["input_cost"], output_cost=tc["output_cost"])


# ═══════════════════════════════════════════════════════════
#  CACHE (AI results)
# ═══════════════════════════════════════════════════════════
# Bump version mỗi khi thay đổi prompt/chiến lược → invalidate cache cũ.
# Re-exported here for one-release compatibility.
_PROMPT_VERSION = _DEFAULT_PROMPT_VERSION


def _ai_cache_options(kind: str) -> dict:
    prompt_version = KNOWLEDGE_PROMPT_VERSION if kind == "knowledge" else _PROMPT_VERSION
    prompt_signature = "" if kind == "knowledge" else get_prompt_signature()
    return {
        "cache_dir": _CACHE_DIR or get_user_data_path("cache"),
        "legacy_cache_dir": _LEGACY_CACHE_DIR,
        "prompt_signature": prompt_signature,
        "kind": kind,
        "prompt_version": prompt_version,
        "max_bytes": _AI_CACHE_MAX_BYTES,
        "max_files": _AI_CACHE_MAX_FILES,
    }


def _ai_cache_key(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> str:
    # get_prompt_signature() = md5 phần ghi đè prompt (utils/ai_prompts.json)
    # → người dùng sửa prompt/schema trong editor → cache tự invalidate (quy tắc #9)
    prompt_version = KNOWLEDGE_PROMPT_VERSION if kind == "knowledge" else _PROMPT_VERSION
    prompt_signature = "" if kind == "knowledge" else get_prompt_signature()
    return _build_ai_cache_key(
        text, lang, instruction, existing_hash, kind=kind,
        prompt_version=prompt_version, prompt_signature=prompt_signature,
    )


def _ai_cache_get(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> Optional[list]:
    return _get_cached_ai_result(
        text, lang, instruction, existing_hash,
        is_openrouter=is_openrouter, **_ai_cache_options(kind),
    )


def _ai_cache_set(text: str, lang: str, instruction: str, existing_hash: str, vocab_list: list, kind: str = "vocab"):
    _set_cached_ai_result(
        text, lang, instruction, existing_hash, vocab_list,
        **_ai_cache_options(kind),
    )


def clear_cache():
    """Xóa toàn bộ cache"""
    _clear_ai_result_cache(_CACHE_DIR or get_user_data_path("cache"))


# ═══════════════════════════════════════════════════════════
#  DECK VOCAB CACHE (re-export from utils/deck_cache.py)
# ═══════════════════════════════════════════════════════════
from .deck_cache import (
    get_existing_vocab_from_deck,
    invalidate_deck_cache,
    make_existing_hash as _make_existing_hash,
)

# ═══════════════════════════════════════════════════════════
#  PROMPT DEFAULTS (compatibility re-exports)
# ═══════════════════════════════════════════════════════════
from .ai_prompt_defaults import (
    _CHINESE_JSON_TEMPLATE,
    _CHINESE_SYSTEM_PROMPT,
    _JAPANESE_JSON_TEMPLATE,
    _JAPANESE_SYSTEM_PROMPT,
    _KOREAN_JSON_TEMPLATE,
    _KOREAN_SYSTEM_PROMPT,
    _ENGLISH_JSON_TEMPLATE,
    _ENGLISH_SYSTEM_PROMPT,
    _JAPANESE_JSON_TEMPLATE_EN,
    _JAPANESE_SYSTEM_PROMPT_EN,
    _CHINESE_JSON_TEMPLATE_EN,
    _CHINESE_SYSTEM_PROMPT_EN,
    _KOREAN_JSON_TEMPLATE_EN,
    _KOREAN_SYSTEM_PROMPT_EN,
    _ENGLISH_JSON_TEMPLATE_EN,
    _ENGLISH_SYSTEM_PROMPT_EN,
    _SYSTEM_PROMPTS,
    _JSON_TEMPLATES,
    _SYSTEM_PROMPTS_EN,
    _JSON_TEMPLATES_EN,
    _JAPANESE_GRAMMAR_JSON_TEMPLATE,
    _JAPANESE_GRAMMAR_SYSTEM_PROMPT,
    _CHINESE_GRAMMAR_JSON_TEMPLATE,
    _CHINESE_GRAMMAR_SYSTEM_PROMPT,
    _KOREAN_GRAMMAR_JSON_TEMPLATE,
    _KOREAN_GRAMMAR_SYSTEM_PROMPT,
    _ENGLISH_GRAMMAR_JSON_TEMPLATE,
    _ENGLISH_GRAMMAR_SYSTEM_PROMPT,
    _JAPANESE_GRAMMAR_JSON_TEMPLATE_EN,
    _JAPANESE_GRAMMAR_SYSTEM_PROMPT_EN,
    _CHINESE_GRAMMAR_JSON_TEMPLATE_EN,
    _CHINESE_GRAMMAR_SYSTEM_PROMPT_EN,
    _KOREAN_GRAMMAR_JSON_TEMPLATE_EN,
    _KOREAN_GRAMMAR_SYSTEM_PROMPT_EN,
    _ENGLISH_GRAMMAR_JSON_TEMPLATE_EN,
    _ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN,
    _GRAMMAR_SYSTEM_PROMPTS,
    _GRAMMAR_JSON_TEMPLATES,
    _GRAMMAR_SYSTEM_PROMPTS_EN,
    _GRAMMAR_JSON_TEMPLATES_EN,
    _KNOWLEDGE_JSON_TEMPLATE,
    _KNOWLEDGE_SYSTEM_PROMPT,
)


def get_json_template(lang: str, kind: str = "vocab") -> str:
    """Template JSON hiệu lực — tôn trọng ghi đè trong prompt_config (ai_prompts.json)."""
    return get_effective_json_template(lang, kind)


def get_grammar_json_template(lang: str) -> str:
    return get_effective_json_template(lang, "grammar")


# ═══════════════════════════════════════════════════════════
#  TEXT EXTRACTION — đọc nội dung file làm tài liệu tham khảo
#  Hỗ trợ: txt, md, csv, pdf, docx, doc, xlsx, xls
#  Lưu ý: DeepSeek/OpenAI chat chỉ nhận TEXT → trích text tại máy.
# ═══════════════════════════════════════════════════════════

# Compatibility re-exports: callers may keep importing these names from
# utils.ai_extractor for this release while the implementation has one owner.
from .document_extractors import (  # noqa: E402
    MissingDocumentDependencyError,
    _document_dependency_available,
    _extract_csv_text,
    _extract_docx_text,
    _extract_pdf_text,
    _extract_sheet_text,
    extract_text_from_file,
    extract_text_from_files,
    get_document_install_command,
)

# ═══════════════════════════════════════════════════════════
#  AI API CALL (cache + existing_words context)
# ═══════════════════════════════════════════════════════════

# Số mục tối đa đưa vào prompt (giới hạn token input)
_MAX_EXISTING_SHOWN = 400


def _ui_lang_en() -> bool:
    """UI đang ở tiếng Anh? (dùng để chọn prompt AI sinh nội dung tiếng Anh)."""
    try:
        from utils.i18n import get_language
        return get_language() == "en"
    except Exception:
        return False


def _format_existing_context(existing: List[str], text: str, label: str = "TỪ") -> str:
    """Tạo chuỗi 'mục đã có' GỌN cho prompt — tối ưu token input.

    Chỉ liệt kê các mục THỰC SỰ xuất hiện trong nội dung đang xử lý
    (khả năng AI trùng cao nhất), không gửi toàn bộ deck hàng nghìn từ.
    Không có mục trùng → chỉ báo tổng số, AI cứ trích xuất bình thường.
    """
    if not existing:
        return ""
    en = _ui_lang_en()
    text_lower = text.lower()
    overlap = []
    seen = set()
    for w in existing:
        w = (w or "").strip()
        if not w:
            continue
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        if key in text_lower:
            overlap.append(w)

    if not overlap:
        if en:
            return (
                f"\n\n⚠️ DECK ALREADY HAS {len(existing)} {label} (NONE MATCH "
                f"the content above) → extract normally, no need to worry about duplicates."
            )
        return (
            f"\n\n⚠️ DECK ĐÃ CÓ {len(existing)} {label} (KHÔNG CÓ MỤC NÀO TRÙNG "
            f"với nội dung trên) → cứ trích xuất bình thường, không cần lo trùng."
        )

    if len(overlap) > _MAX_EXISTING_SHOWN:
        shown = overlap[:_MAX_EXISTING_SHOWN]
        note = (
            f"\n({len(overlap) - _MAX_EXISTING_SHOWN} more matching items; deck total {len(existing)})"
            if en else
            f"\n(Còn {len(overlap) - _MAX_EXISTING_SHOWN} mục khác trùng nội dung; tổng deck {len(existing)} mục)"
        )
    else:
        shown = overlap
        note = (
            f"\n(Deck total {len(existing)} items — only listing items matching the content)"
            if en else
            f"\n(Tổng deck {len(existing)} mục — chỉ liệt kê mục trùng với nội dung)"
        )

    header = f"\n\n⚠️ {label} ALREADY IN DECK — DO NOT OUTPUT:\n" if en else \
        f"\n\n⚠️ {label} ĐÃ CÓ TRONG DECK — TUYỆT ĐỐI KHÔNG XUẤT RA:\n"
    return header + ", ".join(shown) + note


def extract_vocabulary_with_ai(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    token_callback: Optional[Callable[[dict], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """
    Gửi văn bản đến AI API để trích xuất từ vựng. Cache thông minh.

    Args:
        text: Văn bản nguồn
        lang: "japanese" hoặc "chinese"
        custom_instruction: Hướng dẫn bổ sung
        existing_words: Danh sách mặt chữ ĐÃ CÓ trong deck (để AI tránh trùng)
        progress_callback: Callback trạng thái
        force_refresh: Bỏ qua cache

    Returns:
        List các dict từ vựng (chỉ từ mới, không trùng deck)
    """
    existing_hash = _make_existing_hash(existing_words or [])
    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))

    # Cache
    if not force_refresh:
        cached = _ai_cache_get(text, lang, custom_instruction, existing_hash)
        if cached is not None and cache_payload_is_compatible(cached, lang=lang, kind="vocab"):
            if progress_callback:
                progress_callback(t("status_cache_vocab", count=len(cached)))
            return cached

    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError(t("error_api_key_missing"))

    system_prompt = get_effective_system_prompt(lang, "vocab")

    # Giới hạn text — có thể cấu hình (mặc định 45k ký tự, DeepSeek 64k context)
    max_chars = cfg.get("max_chars", 45000)
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(t("status_text_truncated", length=len(text), limit=max_chars))
        text = text[:max_chars]

    if progress_callback:
        progress_callback(t("status_calling_model", model=cfg["model"]))

    # User message: text + existing words context (đã lọc gọn để tiết kiệm token)
    request = "Extract all vocabulary from the following text:" if _ui_lang_en() \
        else "Hãy trích xuất tất cả từ vựng từ văn bản sau:"
    user_msg = f"{request}\n\n{text}"

    if existing_words and len(existing_words) > 0:
        user_msg += _format_existing_context(existing_words, text, label="WORDS" if _ui_lang_en() else "TỪ")

    if custom_instruction.strip():
        heading = "ADDITIONAL REQUIREMENT (highest priority)" if _ui_lang_en() \
            else "YÊU CẦU BỔ SUNG (ưu tiên cao nhất)"
        user_msg += f"\n\n{heading}:\n{custom_instruction.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)
    enable_deepseek_json_output(payload, cfg)

    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }

    if progress_callback:
        progress_callback(t("status_waiting_ai"))

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    body = _http_post_json(url, payload, headers, timeout=_timeout,
                           progress_callback=progress_callback, should_abort=should_abort)

    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        raise RuntimeError(t("error_api_no_result", details=body[:500]))

    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            usage.get("cost"),
        )
        _record_token_info(
            token_info,
            operation="vocab_extraction",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
        )
        if token_callback:
            try:
                token_callback(token_info)
            except Exception:
                pass

    if progress_callback:
        progress_callback(t("status_parsing_json"))

    vocab_list, comment = _validated_cards_from_result(
        result, cfg, lang=lang, kind="vocab", progress_callback=progress_callback,
    )

    # Lọc bỏ từ trùng với existing_words (safety net)
    if existing_words:
        existing_set = set(w.lower().strip() for w in existing_words)
        original_count = len(vocab_list)
        vocab_list = [
            v for v in vocab_list
            if (v.get("front") or v.get("simplified") or "").lower().strip() not in existing_set
        ]
        if len(vocab_list) < original_count and progress_callback:
            progress_callback(t("status_filtered_vocab", count=original_count - len(vocab_list)))

    if progress_callback:
        msg = t("status_new_vocab", count=len(vocab_list))
        if comment:
            msg += f"\n💬 {comment[:100]}"
        if token_info:
            msg += f"\n{_format_token_report(token_info)}"
        progress_callback(msg)

    # Lưu cache
    if vocab_list:
        _ai_cache_set(text, lang, custom_instruction, existing_hash, vocab_list)

    return vocab_list


# ═══════════════════════════════════════════════════════════
#  SMART ANKI QUERY — truy vấn thông minh, không quét toàn bộ
# ═══════════════════════════════════════════════════════════

def query_anki_context(user_message: str, lang: str = "japanese", collection=None) -> dict:
    """
    Thu thập ngữ cảnh Anki MỘT CÁCH THÔNG MINH dựa trên yêu cầu của người dùng.
    Chỉ query những gì liên quan, không quét toàn bộ database.
    
    Returns:
        dict với các key: decks, current_deck_stats, language, query_hint
    """
    context = {
        "language": lang,
        "decks": [],
        "current_deck_stats": {},
        "note": "",
    }
    
    try:
        if collection is None:
            from aqt import mw
            collection = mw.col
        
        # 1. Lấy danh sách deck (nhẹ, chỉ tên + số lượng)
        deck_names = collection.decks.all_names()
        deck_list = []
        for name in deck_names:
            try:
                did = collection.decks.id(name)
                # Chỉ đếm số thẻ trong deck này (có giới hạn)
                count = collection.decks.card_count(did, include_subdecks=False)
                deck_list.append({"name": name, "card_count": count})
            except Exception:
                deck_list.append({"name": name, "card_count": "?"})
        context["decks"] = deck_list
        
        # 2. Nếu user đề cập đến deck cụ thể, lấy thêm stats
        msg_lower = user_message.lower()
        for d in deck_list:
            if d["name"].lower() in msg_lower:
                try:
                    did = collection.decks.id(d["name"])
                    # Stats cơ bản (không quét từng thẻ)
                    due_count = 0
                    new_count = 0
                    try:
                        # Due cards
                        due = collection.find_cards(f'"deck:{d["name"]}" is:due')
                        due_count = len(due) if due else 0
                        # New cards
                        new = collection.find_cards(f'"deck:{d["name"]}" is:new')
                        new_count = len(new) if new else 0
                    except Exception:
                        pass
                    
                    context["current_deck_stats"] = {
                        "name": d["name"],
                        "total_cards": d["card_count"],
                        "due_cards": due_count,
                        "new_cards": new_count,
                    }
                except Exception:
                    pass
                break
        
        # Nếu không tìm thấy deck cụ thể, dùng deck đầu tiên
        if not context["current_deck_stats"] and deck_list:
            d = deck_list[0]
            try:
                did = collection.decks.id(d["name"])
                due = collection.find_cards(f'"deck:{d["name"]}" is:due')
                due_count = len(due) if due else 0
                new = collection.find_cards(f'"deck:{d["name"]}" is:new')
                new_count = len(new) if new else 0
                context["current_deck_stats"] = {
                    "name": d["name"],
                    "total_cards": d["card_count"],
                    "due_cards": due_count,
                    "new_cards": new_count,
                }
            except Exception:
                pass
    
    except Exception as e:
        context["note"] = t("ai_context_query_failed", error=e)
    
    return context


def _build_anki_context_text(context: dict) -> str:
    """Xây dựng text mô tả ngữ cảnh Anki để gửi cho AI, kèm lịch sử import"""
    parts = [t("ai_context_language", language=context.get("language", "japanese"))]
    
    decks = context.get("decks", [])
    if decks:
        parts.append("\n" + t("ai_context_deck_list", count=len(decks)))
        for d in decks[:20]:  # Giới hạn 20 deck
            count = t("ai_context_card_count", count=d["card_count"])
            parts.append(f"   - {d['name']} ({count})")
        if len(decks) > 20:
            parts.append("   " + t("ai_context_other_decks", count=len(decks) - 20))
    
    stats = context.get("current_deck_stats", {})
    if stats:
        parts.append("\n" + t("ai_context_current_deck", name=stats.get("name", "?")))
        for label_key, value_key in (
            ("ai_context_total", "total_cards"),
            ("ai_context_due", "due_cards"),
            ("ai_context_new", "new_cards"),
        ):
            count = stats.get(value_key, "?")
            parts.append(f"   - {t(label_key)}: {t('ai_context_card_count', count=count)}")
    
    note = context.get("note", "")
    if note:
        parts.append(f"\n⚠️ {note}")

    # Thêm lịch sử import (chỉ lấy summary, không chi tiết từng từ để tiết kiệm token)
    try:
        lang = context.get('language', 'japanese')
        history_text = get_history_summary_text(lang=lang, max_words_for_ai=30)
        if history_text:
            parts.append(f"\n{'═' * 40}")
            parts.append(history_text)
    except Exception:
        pass
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  AI CHAT — giao tiếp tự do với AI, không cần text trích xuất
# ═══════════════════════════════════════════════════════════

_CHAT_PROMPT_COMPACT_VI = """Bạn là gia sư {target} cho người Việt: ấm áp, chính xác và ngắn gọn.
- Ưu tiên cách dùng tự nhiên có ngữ cảnh; nêu register/sắc thái và đối chiếu gần nghĩa khi hữu ích.
- Ví dụ ngắn, đa dạng, đúng cấp độ; không bịa nghĩa, collocation hoặc quy tắc.
- Khi sửa lỗi: nói rõ phần đúng, lỗi, lý do và một bản sửa tự nhiên.
- Chỉ dùng dữ liệu Anki được cung cấp; không đề xuất lại mục đã có.
- Xưởng hiện ở chế độ {card_kind_label}. Nếu người dùng muốn nhập thẻ, chỉ trả đúng JSON theo schema hiện tại trong một khối ```json```; ngoài trường hợp đó không ép trả JSON.
Schema hiện tại: {card_schema}
Trả lời bằng tiếng Việt."""

_CHAT_PROMPT_COMPACT_EN = """You are a warm, precise, concise {target} tutor for English speakers.
- Prioritize natural contextual usage; explain register/nuance and near-synonym contrasts when useful.
- Keep examples short, varied, and level-appropriate; never invent senses, collocations, or rules.
- For corrections, identify what works, the error, why, and one natural revision.
- Use only the supplied Anki data and never resuggest an existing item.
- The Factory is currently in {card_kind_label} mode. If the user requests importable cards, return only the exact current schema below in one ```json``` block; otherwise do not force JSON.
Current schema: {card_schema}
Reply in English."""


def _get_chat_system_prompt(
    lang: str = "japanese", card_kind: str = "vocab",
) -> str:
    """Compact target-aware Chat prompt with one explicit Factory card kind."""
    if card_kind not in {"vocab", "grammar"}:
        raise ValueError("unsupported chat card kind")
    target = {
        "japanese": "Japanese", "chinese": "Chinese",
        "korean": "Korean", "english": "English",
    }.get(lang, "Japanese")
    english_ui = _ui_lang_en()
    base = _CHAT_PROMPT_COMPACT_EN if english_ui else _CHAT_PROMPT_COMPACT_VI
    card_kind_label = (
        ("grammar" if card_kind == "grammar" else "vocabulary")
        if english_ui else ("ngữ pháp" if card_kind == "grammar" else "từ vựng")
    )
    return base.format(
        target=target,
        card_kind_label=card_kind_label,
        card_schema=get_effective_json_template(lang, card_kind),
    )


def chat_with_ai(
    user_message: str,
    lang: str = "japanese",
    conversation_history: Optional[List[dict]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    quick: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
    anki_context: Optional[dict] = None,
    card_kind: str = "vocab",
) -> dict:
    """
    Gửi tin nhắn đến AI và nhận phản hồi. AI có ngữ cảnh Anki.
    
    Args:
        user_message: Tin nhắn của người dùng
        lang: "japanese" hoặc "chinese"
        conversation_history: Lịch sử hội thoại (list of {"role":"user"/"assistant", "content":"..."})
        progress_callback: Callback trạng thái
    
    Returns:
        dict với keys: "reply" (text phản hồi), "vocab_json" (nếu AI xuất từ vựng), "error"
    """
    if card_kind not in {"vocab", "grammar"}:
        raise ValueError("unsupported chat card kind")
    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        return {"reply": "", "vocab_json": None, "error": t("error_api_key_missing")}
    try:
        ensure_ai_session_budget(user_message)
    except ValueError as error:
        return {"reply": "", "vocab_json": None, "token_info": None, "error": str(error)}
    
    # Thu thập ngữ cảnh Anki THÔNG MINH dựa trên yêu cầu.
    # quick=True → BỎ qua truy vấn context Anki (nhanh hơn) — dùng cho sinh câu ngữ pháp.
    if quick:
        target = {
            "japanese": "Japanese", "chinese": "Chinese",
            "korean": "Korean", "english": "English",
        }.get(lang, "Japanese")
        system_content = (
            f"You are a concise {target} language tutor. "
            "Answer exactly what is asked, no extra commentary."
        )
        if progress_callback:
            progress_callback(t("status_calling_model", model=cfg["model"]))
    else:
        if progress_callback:
            progress_callback(t("worker_progress_context"))
        context = anki_context if anki_context is not None else query_anki_context(user_message, lang)
        context_text = _build_anki_context_text(context)
        if progress_callback:
            progress_callback(t("status_calling_model", model=cfg["model"]))
        system_content = _get_chat_system_prompt(lang, card_kind) + "\n\n" + "═" * 50 + "\n"
        system_content += (
            "ANKI SYSTEM CONTEXT (use only this data):\n" if _ui_lang_en()
            else "THÔNG TIN HỆ THỐNG ANKI (chỉ dùng dữ liệu này):\n"
        ) + context_text
    
    messages = [{"role": "system", "content": system_content}]
    
    # Thêm lịch sử hội thoại (giới hạn 10 tin gần nhất để tiết kiệm token)
    if conversation_history:
        for msg in conversation_history[-20:]:
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)
    
    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    
    if progress_callback:
        progress_callback(t("status_waiting_ai"))

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    try:
        body = _http_post_json(url, payload, headers, timeout=_timeout,
                               progress_callback=progress_callback, should_abort=should_abort)
    except RuntimeError as e:
        return {"reply": "", "vocab_json": None, "token_info": None, "error": str(e)}
    
    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        return {"reply": "", "vocab_json": None, "token_info": None,
                "error": t("error_api_no_result", details=body[:500])}
    
    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            usage.get("cost"),
        )
        _record_token_info(
            token_info,
            operation="ai_chat",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
        )
    
    try:
        adapted = adapt_chat_completion_response(result, cfg)
    except RuntimeError as error:
        return {
            "reply": "", "vocab_json": None, "token_info": token_info,
            "error": str(error),
        }

    optional_cards = _extract_optional_card_payload(
        adapted, lang=lang, kind=card_kind,
    )
    reply_text = optional_cards.reply
    vocab_json = list(optional_cards.cards) or None
    warning_key = {
        "truncation": "chat_card_warning_truncation",
        "schema_mismatch": "chat_card_warning_schema",
        "ambiguous_json_payloads": "chat_card_warning_ambiguous",
    }.get(optional_cards.rejection_category, "chat_card_warning_rejected")
    card_warning = (
        t(warning_key) if optional_cards.rejection_category else None
    )
    
    if progress_callback:
        end_msg = t("status_complete")
        if token_info:
            end_msg += f"\n{_format_token_report(token_info)}"
        progress_callback(end_msg)
    
    return {
        "reply": reply_text,
        "vocab_json": vocab_json,
        "card_json": vocab_json,
        "card_kind": card_kind,
        "token_info": token_info,
        "error": None,
        "card_error": optional_cards.rejection_category,
        "card_warning": card_warning,
    }


# ═══════════════════════════════════════════════════════════
#  XỬ LÝ VĂN BẢN DÀI
# ═══════════════════════════════════════════════════════════

def extract_vocabulary_long_text(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI, loại trùng, tổng hợp token."""
    ensure_ai_session_budget(text)
    if chunk_size is None:
        chunk_size = get_api_config().get("chunk_size", 8000)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if progress_callback:
        progress_callback(t("status_chunks_vocab", count=len(chunks)))

    all_vocab = []
    seen = set()
    existing_set = set(w.lower().strip() for w in (existing_words or []))
    # Từ đã trích ở đoạn trước → bổ sung vào danh sách "đã có" cho đoạn sau
    # (giúp AI không trích trùng qua biên giới đoạn → chất lượng + tiết kiệm output)
    prior_fronts = []

    # Bộ gộp token/chi phí toàn bộ lần chạy
    agg = {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0,
    }

    def _acc(ti: dict):
        agg["prompt_tokens"] += ti.get("prompt_tokens", 0)
        agg["completion_tokens"] += ti.get("completion_tokens", 0)
        agg["total_tokens"] += ti.get("total_tokens", 0)
        agg["input_cost"] += ti.get("input_cost", 0)
        agg["output_cost"] += ti.get("output_cost", 0)
        agg["total_cost"] += ti.get("total_cost", 0)

    for idx, chunk in enumerate(chunks):
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        if progress_callback:
            progress_callback(t("status_chunk", current=idx + 1, total=len(chunks)))

        try:
            combined_existing = (existing_words or []) + prior_fronts

            def _call_vocab(source):
                return extract_vocabulary_with_ai(
                    source, lang, custom_instruction, combined_existing,
                    progress_callback=None, force_refresh=force_refresh,
                    token_callback=_acc,
                    should_abort=should_abort,
                )

            vocab_chunk, unresolved_spans = _recover_text_chunk(
                _call_vocab, chunk, progress_callback=progress_callback,
                should_abort=should_abort, kind="vocab",
            )
            for item in vocab_chunk:
                if not isinstance(item, dict):
                    continue
                front = (item.get("front") or item.get("simplified") or "").strip().lower()
                meaning = (item.get("meaning") or "").strip().lower()
                key = f"{front}|{meaning}"
                if front and key not in seen and front not in existing_set:
                    seen.add(key)
                    all_vocab.append(item)
                    prior_fronts.append(front)
            if unresolved_spans and progress_callback:
                progress_callback(t(
                    "status_ai_partial_spans",
                    valid=len(all_vocab), unresolved=unresolved_spans,
                ))
            # Giới hạn danh sách prior để tránh phình prompt
            if len(prior_fronts) > 400:
                prior_fronts = prior_fronts[-400:]
        except Exception as e:
            if progress_callback:
                progress_callback(t("status_chunk_error", current=idx + 1, error=e))

    if progress_callback:
        summary = t("status_total_vocab", count=len(all_vocab))
        if agg["total_tokens"] > 0:
            progress_callback(t("status_total_with_tokens", summary=summary,
                                tokens=agg["total_tokens"], input_tokens=agg["prompt_tokens"],
                                output_tokens=agg["completion_tokens"], cost=agg["total_cost"]))
        else:
            progress_callback(summary)

    return all_vocab


# ═══════════════════════════════════════════════════════════
#  GRAMMAR EXTRACTION — trích xuất NGỮ PHÁP qua AI
#  (Note Type ngữ pháp riêng, dùng prompt riêng)
# ═══════════════════════════════════════════════════════════

def extract_grammar_with_ai(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_patterns: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    token_callback: Optional[Callable[[dict], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """
    Gửi văn bản đến AI API để trích xuất CẤU TRÚC NGỮ PHÁP (khác từ vựng).

    Args:
        text: Văn bản nguồn
        lang: "japanese" hoặc "chinese"
        custom_instruction: Hướng dẫn bổ sung
        existing_patterns: Danh sách pattern ĐÃ CÓ trong deck (để AI tránh trùng)
        progress_callback: Callback trạng thái
        force_refresh: Bỏ qua cache

    Returns:
        List các dict ngữ pháp (chỉ pattern mới, không trùng deck)
    """
    existing_hash = _make_existing_hash(existing_patterns or [])
    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))

    # Cache
    if not force_refresh:
        cached = _ai_cache_get(text, lang, custom_instruction, existing_hash, kind="grammar")
        if cached is not None and cache_payload_is_compatible(cached, lang=lang, kind="grammar"):
            if progress_callback:
                progress_callback(t("status_cache_grammar", count=len(cached)))
            return cached

    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError(t("error_api_key_missing"))

    system_prompt = get_effective_system_prompt(lang, "grammar")

    # Giới hạn text — có thể cấu hình (mặc định 45k ký tự, DeepSeek 64k context)
    max_chars = cfg.get("max_chars", 45000)
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(t("status_text_truncated", length=len(text), limit=max_chars))
        text = text[:max_chars]

    if progress_callback:
        progress_callback(t("status_calling_model", model=cfg["model"]))

    # User message: text + existing patterns context (đã lọc gọn để tiết kiệm token)
    request = "Extract all grammar patterns from the following text:" if _ui_lang_en() \
        else "Hãy trích xuất tất cả cấu trúc ngữ pháp từ văn bản sau:"
    user_msg = f"{request}\n\n{text}"

    if existing_patterns and len(existing_patterns) > 0:
        label = "GRAMMAR PATTERNS" if _ui_lang_en() else "CẤU TRÚC NGỮ PHÁP"
        user_msg += _format_existing_context(existing_patterns, text, label=label)

    if custom_instruction.strip():
        heading = "ADDITIONAL REQUIREMENT (highest priority)" if _ui_lang_en() \
            else "YÊU CẦU BỔ SUNG (ưu tiên cao nhất)"
        user_msg += f"\n\n{heading}:\n{custom_instruction.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)
    enable_deepseek_json_output(payload, cfg)

    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }

    if progress_callback:
        progress_callback(t("status_waiting_ai"))

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    body = _http_post_json(url, payload, headers, timeout=_timeout,
                           progress_callback=progress_callback, should_abort=should_abort)

    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        raise RuntimeError(t("error_api_no_result", details=body[:500]))

    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            usage.get("cost"),
        )
        _record_token_info(
            token_info,
            operation="grammar_extraction",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
        )
        if token_callback:
            try:
                token_callback(token_info)
            except Exception:
                pass

    if progress_callback:
        progress_callback(t("status_parsing_json"))

    grammar_list, comment = _validated_cards_from_result(
        result, cfg, lang=lang, kind="grammar", progress_callback=progress_callback,
    )

    # Chỉ giữ các item có pattern
    grammar_list = [
        g for g in grammar_list
        if isinstance(g, dict) and (g.get("pattern") or "").strip()
    ]

    # Lọc bỏ pattern trùng với existing_patterns (safety net)
    if existing_patterns:
        existing_set = set(p.lower().strip() for p in existing_patterns)
        original_count = len(grammar_list)
        grammar_list = [
            g for g in grammar_list
            if (g.get("pattern") or "").strip().lower() not in existing_set
        ]
        if len(grammar_list) < original_count and progress_callback:
            progress_callback(t("status_filtered_grammar", count=original_count - len(grammar_list)))

    if progress_callback:
        msg2 = t("status_new_grammar", count=len(grammar_list))
        if comment:
            msg2 += f"\n💬 {comment[:100]}"
        if token_info:
            msg2 += f"\n{_format_token_report(token_info)}"
        progress_callback(msg2)

    # Lưu cache
    if grammar_list:
        _ai_cache_set(text, lang, custom_instruction, existing_hash, grammar_list, kind="grammar")

    return grammar_list


def extract_grammar_long_text(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_patterns: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI trích ngữ pháp, loại trùng, tổng hợp token."""
    ensure_ai_session_budget(text)
    if chunk_size is None:
        chunk_size = get_api_config().get("chunk_size", 8000)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if progress_callback:
        progress_callback(t("status_chunks_grammar", count=len(chunks)))

    all_grammar = []
    seen = set()
    existing_set = set(p.lower().strip() for p in (existing_patterns or []))
    # Dedup theo (pattern|meaning) → cho phép cùng pattern, khác nghĩa = thẻ riêng

    agg = {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0,
    }

    def _acc(ti: dict):
        agg["prompt_tokens"] += ti.get("prompt_tokens", 0)
        agg["completion_tokens"] += ti.get("completion_tokens", 0)
        agg["total_tokens"] += ti.get("total_tokens", 0)
        agg["input_cost"] += ti.get("input_cost", 0)
        agg["output_cost"] += ti.get("output_cost", 0)
        agg["total_cost"] += ti.get("total_cost", 0)

    for idx, chunk in enumerate(chunks):
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        if progress_callback:
            progress_callback(t("status_chunk", current=idx + 1, total=len(chunks)))

        try:
            def _call_grammar(source):
                return extract_grammar_with_ai(
                    source, lang, custom_instruction, existing_patterns,
                    progress_callback=None, force_refresh=force_refresh,
                    token_callback=_acc,
                    should_abort=should_abort,
                )

            grammar_chunk, unresolved_spans = _recover_text_chunk(
                _call_grammar, chunk, progress_callback=progress_callback,
                should_abort=should_abort, kind="grammar",
            )
            for item in grammar_chunk:
                if not isinstance(item, dict):
                    continue
                pat = (item.get("pattern") or "").strip().lower()
                mean = (item.get("meaning") or "").strip().lower()
                key = f"{pat}|{mean}"
                if pat and key not in seen and pat not in existing_set:
                    seen.add(key)
                    all_grammar.append(item)
            if unresolved_spans and progress_callback:
                progress_callback(t(
                    "status_ai_partial_spans",
                    valid=len(all_grammar), unresolved=unresolved_spans,
                ))
        except Exception as e:
            if progress_callback:
                progress_callback(t("status_chunk_error", current=idx + 1, error=e))

    if progress_callback:
        summary = t("status_total_grammar", count=len(all_grammar))
        if agg["total_tokens"] > 0:
            progress_callback(t("status_total_with_tokens", summary=summary,
                                tokens=agg["total_tokens"], input_tokens=agg["prompt_tokens"],
                                output_tokens=agg["completion_tokens"], cost=agg["total_cost"]))
        else:
            progress_callback(summary)

    return all_grammar


# ═══════════════════════════════════════════════════════════
#  IMPORT HISTORY (compatibility re-exports)
# ═══════════════════════════════════════════════════════════
from . import import_history as _import_history

_HISTORY_PATH = _import_history._HISTORY_PATH
_LEGACY_HISTORY_PATH = _import_history._LEGACY_HISTORY_PATH
_HISTORY_VERSION = _import_history._HISTORY_VERSION
_HISTORY_SCAN_TTL = _import_history._HISTORY_SCAN_TTL
_load_history = _import_history._load_history
_save_history = _import_history._save_history
clear_import_history = _import_history.clear_import_history
add_to_import_history = _import_history.add_to_import_history
get_import_history = _import_history.get_import_history
get_import_history_items = _import_history.get_import_history_items
search_import_history = _import_history.search_import_history
get_history_summary_text = _import_history.get_history_summary_text
_build_single_lang_summary = _import_history._build_single_lang_summary


def init_import_history(force_rescan: bool = False, scan_context_factory=None,
                        cancel_event=None, progress_callback=None) -> dict:
    """Compatibility entry point for callers already inside Anki ``QueryOp``.

    ``scan_context_factory`` must supply the collection owned by that QueryOp.
    This layer intentionally never imports or accesses ``mw``; doing so would
    permit an unsafe synchronous collection scan.
    """
    return _import_history.init_import_history(
        force_rescan=force_rescan,
        scan_context_factory=scan_context_factory,
        cancel_event=cancel_event,
        progress_callback=progress_callback,
    )
