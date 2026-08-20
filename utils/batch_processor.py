"""
🚀 Batch Processor — Xử lý danh sách từ vựng LỚN qua AI một cách thông minh.

Chiến lược:
1. SMART CHUNKING: Nhóm từ theo chủ đề/cấp độ trước khi gửi AI
2. TWO-PASS AI:
   - Pass 1: Trích xuất/xử lý từ vựng theo batch (30-50 từ/batch)
   - Pass 2: AI phân tích toàn bộ, đề xuất cấu trúc deck (parent/sub)
3. RATE LIMITING: Delay giữa các batch, retry với exponential backoff
4. CACHE: Cache từng batch riêng biệt + cache tổng hợp
5. PROGRESS: Callback chi tiết từng bước
"""

import json
import os
import re
import time
import hashlib
import urllib.request
import urllib.error
from dataclasses import dataclass, replace
from typing import Optional, Callable, List, Dict

from .logger import get_logger
from .i18n import get_language, t
from .user_data import atomic_write_json, get_user_data_path, migrate_legacy_directory, prune_cache_dir, read_json
from .ai_extractor import (
    get_api_config,
    _make_existing_hash,
    _apply_reasoning_effort,
    _calculate_cost,
    _record_token_info,
    get_existing_vocab_from_deck,
    is_openrouter,
)
from .ai_response_parser import parse_ai_json_with_comment as _parse_ai_json_with_comment
from .ai_response_guard import adapt_chat_completion_response, enable_deepseek_json_output
from .ai_reliability import (
    AiCardResponse,
    AiOutputFailure,
    reconcile_expected_candidates,
)
from .ai_output_validation import (
    AI_OUTPUT_SCHEMA_VERSION,
    cache_payload_is_compatible,
)
from .ai_output_repairs import repair_vocabulary_cards
from .usage_guide import normalize_language_cards
from .ai_result_cache import DEFAULT_PROMPT_VERSION
from .ai_http_client import (
    get_rate_limit_delay as _get_rate_limit_delay,
    post_json as _http_post_json,
)
from .prompt_config import (
    get_system_prompt, get_json_template, get_signature,
)

logger = get_logger()

_LEVEL_RE = re.compile(r"^(?:N[1-5]|HSK[1-6]|TOPIK\s*(?:I{1,2}|[1-6])|[ABC][12])$", re.IGNORECASE)


def _normalized_level(value: str) -> str:
    value = str(value or "").strip().upper()
    return re.sub(r"^TOPIK\s*", "TOPIK ", value) if value.startswith("TOPIK") else value

# ═══════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════
DEFAULT_BATCH_SIZE = 10          # Conservative Quality V2 request size
MAX_WORDS_PER_REQUEST = 30       # UI ceiling; policy may choose a smaller size
MIN_DELAY_BETWEEN_BATCHES = 1.5  # Giây delay giữa các batch
MAX_RECOVERY_RETRIES = 2
MIN_ADAPTIVE_BATCH_SIZE = 1
_LEGACY_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_cache")
CACHE_DIR = get_user_data_path("cache")
CACHE_TTL = 14 * 24 * 3600       # Cache 14 ngày


def recommended_quality_v2_batch_size(
    lang: str,
    *,
    grammar: bool = False,
    max_output_tokens: int = 8192,
) -> int:
    """Return a conservative, deterministic Quality V2 output budget."""
    vocab_sizes = {"english": 12, "japanese": 10, "chinese": 8, "korean": 8}
    grammar_sizes = {"english": 10, "japanese": 8, "chinese": 8, "korean": 8}
    size = (grammar_sizes if grammar else vocab_sizes).get(lang, 8)
    tokens = max(1, int(max_output_tokens or 8192))
    if tokens < 4096:
        size = max(3, size // 2)
    elif tokens < 6144:
        size = max(4, round(size * 0.7))
    return size


def _wait_for_cancel(seconds: float, should_abort: Optional[Callable[[], bool]] = None):
    """Cancelable inter-batch delay; avoids a UI Stop waiting for sleep()."""
    deadline = time.monotonic() + max(0.0, seconds)
    while time.monotonic() < deadline:
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        before = time.monotonic()
        time.sleep(min(0.1, deadline - before))
        if time.monotonic() <= before:
            return


# ═══════════════════════════════════════════════════════════
#  WORD LIST PARSER — Parse danh sách từ từ nhiều format
# ═══════════════════════════════════════════════════════════

def parse_word_list(raw_text: str, lang: str = "japanese") -> List[Dict[str, str]]:
    """
    Parse danh sách từ vựng từ text paste của người dùng.
    
    Hỗ trợ nhiều format:
    - Mỗi dòng 1 từ: "食べる"
    - Từ + nghĩa: "食べる : ăn"
    - Từ + nghĩa + cấp độ: "食べる : ăn : N5"
    - CSV-style: "食べる,たべる,ăn,N5"
    - JSON array: [{"front":"食べる","meaning":"ăn"},...]
    
    Args:
        raw_text: Text người dùng paste vào
        lang: target-language key (japanese/chinese/korean/english)
    
    Returns:
        List[Dict] với keys: front, meaning (nếu có), level (nếu có)
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return []
    
    # Thử parse JSON trước
    if raw_text.startswith("["):
        try:
            data = json.loads(raw_text)
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, dict):
                        result.append({
                            "front": str(
                                item.get("front") or item.get("simplified")
                                or item.get("word") or item.get("pattern") or ""
                            ).strip(),
                            "meaning": str(item.get("meaning") or "").strip(),
                            "level": str(item.get("jlptlevel") or item.get("hsk_level") or item.get("topik_level") or item.get("cefr_level") or item.get("level") or "").strip(),
                            "topic": str(item.get("topic") or "").strip(),
                        })
                    elif isinstance(item, str):
                        result.append({"front": item.strip(), "meaning": "", "level": "", "topic": ""})
                return [r for r in result if r["front"]]
        except json.JSONDecodeError:
            pass
    
    # Parse từng dòng
    lines = raw_text.split("\n")
    result = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        
        # Thử các delimiter
        parsed = None
        
        # Tab-separated
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t")]
        # CSV (comma)
        elif "," in line and not (lang == "chinese" and any(c in line for c in "，")):
            parts = [p.strip() for p in line.split(",")]
        # Colon-separated
        elif ":" in line:
            parts = [p.strip() for p in line.split(":")]
        # Semicolon
        elif ";" in line:
            parts = [p.strip() for p in line.split(";")]
        # Dấu gạch ngang
        elif " - " in line:
            parts = [p.strip() for p in line.split(" - ")]
        elif "–" in line or "—" in line:
            parts = [p.strip() for p in re.split(r'[–—]', line)]
        else:
            parts = [line]
        
        entry = {"front": parts[0] if len(parts) > 0 else "", 
                  "meaning": "", "level": "", "topic": ""}
        
        if len(parts) >= 2:
            # Check if second part looks like a level (N5, HSK1, etc.)
            second = parts[1]
            if _LEVEL_RE.match(second):
                entry["level"] = _normalized_level(second)
            else:
                entry["meaning"] = second
        
        if len(parts) >= 3:
            # Third part: level or topic
            third = parts[2]
            if _LEVEL_RE.match(third):
                entry["level"] = _normalized_level(third)
            elif not entry["level"]:
                entry["level"] = third
            else:
                entry["topic"] = third
        
        if len(parts) >= 4:
            entry["topic"] = parts[3]
        
        if entry["front"]:
            result.append(entry)
    
    logger.info("Parsed %d words from raw text", len(result))
    return result


# ═══════════════════════════════════════════════════════════
#  SMART GROUPING — Nhóm từ thông minh trước khi gửi AI
# ═══════════════════════════════════════════════════════════

def smart_group_words(words: List[Dict[str, str]], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[Dict[str, str]]]:
    """
    Nhóm từ thông minh để tối ưu chất lượng AI.
    
    Chiến lược:
    1. Nhóm theo level (JLPT/HSK/TOPIK/CEFR) nếu có
    2. Trong cùng level, nhóm theo độ dài từ (ngắn trước, dài sau)
    3. Đảm bảo mỗi batch có độ đa dạng topic
    
    Returns:
        List of batches, mỗi batch là list các dict từ
    """
    if not words:
        return []
    
    # Phân loại: có level vs không có level
    with_level = [w for w in words if w.get("level")]
    without_level = [w for w in words if not w.get("level")]
    
    # Sort by level
    level_order = {
        "N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4,
        "HSK1": 0, "HSK2": 1, "HSK3": 2, "HSK4": 3, "HSK5": 4, "HSK6": 5,
        "TOPIK I": 0, "TOPIK II": 1,
        "A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5,
    }
    
    with_level.sort(key=lambda w: (level_order.get(w["level"].upper(), 99), len(w["front"])))
    without_level.sort(key=lambda w: len(w["front"]))
    
    # Interleave: trộn có level + không level để đa dạng
    all_sorted = with_level + without_level
    
    batches = []
    for i in range(0, len(all_sorted), batch_size):
        batch = all_sorted[i:i + batch_size]
        batches.append(batch)
    
    logger.info("Grouped %d words into %d batches (avg %d/batch)", 
                len(words), len(batches), len(words) // max(1, len(batches)))
    return batches


# ═══════════════════════════════════════════════════════════
#  BATCH AI CALL — Gọi AI cho một batch từ
# ═══════════════════════════════════════════════════════════

def _build_batch_user_prompt(
    words: List[Dict[str, str]],
    lang: str,
    existing_words: List[str],
    custom_instruction: str = "",
    batch_num: int = 1,
    total_batches: int = 1,
    grammar: bool = False,
) -> str:
    """Xây dựng user prompt cho một batch từ (hoặc cấu trúc ngữ pháp)"""
    template = get_json_template(lang, "grammar" if grammar else "vocab")
    
    # Liệt kê từ/pattern cần xử lý
    try:
        from utils.ai_extractor import _ui_lang_en
        en = _ui_lang_en()
    except Exception:
        en = False
    meaning_label = "meaning" if en else "nghĩa"

    word_list_str = "\n".join(
        f"{i+1}. {w['front']}"
        + (f" ({meaning_label}: {w['meaning']})" if w.get("meaning") else "")
        + (f" [{w['level']}]" if w.get("level") else "")
        for i, w in enumerate(words)
    )
    
    if grammar:
        if en:
            prompt = f"""📝 BATCH {batch_num}/{total_batches} — PROCESSING {len(words)} GRAMMAR PATTERNS

LIST OF PATTERNS TO PROCESS:
{word_list_str}

🎯 TASK:
For EACH pattern in the list above, create a complete JSON object following this template:
{template}

QUALITY: Preserve any supplied meaning/level. Follow the system rules exactly; keep one
context-supported sense per item, concise usage/explanation, and natural distinct examples
at the assigned proficiency level. Fill every schema field; never invent missing facts.
"""
        else:
            prompt = f"""📝 BATCH {batch_num}/{total_batches} — XỬ LÝ {len(words)} CẤU TRÚC NGỮ PHÁP

DANH SÁCH CẤU TRÚC CẦN XỬ LÝ:
{word_list_str}

🎯 NHIỆM VỤ:
Với MỖI cấu trúc trong danh sách trên, tạo một object JSON đầy đủ theo mẫu:
{template}

CHẤT LƯỢNG: Giữ nghĩa/cấp độ đã cung cấp. Tuân thủ chính xác system prompt; mỗi item
chỉ giữ một nghĩa có bằng chứng ngữ cảnh, usage/explanation gọn, hai ví dụ tự nhiên khác
ngữ cảnh và đúng cấp độ đã gán. Điền đủ schema; không bịa dữ kiện còn thiếu.
"""
    else:
        if en:
            prompt = f"""📝 BATCH {batch_num}/{total_batches} — PROCESSING {len(words)} WORDS

LIST OF WORDS TO PROCESS:
{word_list_str}

🎯 TASK:
For EACH word in the list above, create a complete JSON object following this template:
{template}

QUALITY: Preserve any supplied meaning/level. If a meaning is supplied, use it consistently
in meaning, both examples, and both translations; never switch to another sense. Follow the
system rules exactly; keep correct form/usage, concise topic, and two natural distinct examples
at the assigned proficiency level. Fill every schema field; never invent missing facts.
"""
        else:
            prompt = f"""📝 BATCH {batch_num}/{total_batches} — XỬ LÝ {len(words)} TỪ VỰNG

DANH SÁCH TỪ CẦN XỬ LÝ:
{word_list_str}

🎯 NHIỆM VỤ:
Với MỖI từ trong danh sách trên, tạo một object JSON đầy đủ theo mẫu:
{template}

CHẤT LƯỢNG: Giữ nghĩa/cấp độ đã cung cấp. Nếu có nghĩa, meaning, hai ví dụ và hai bản dịch
phải cùng nghĩa đó, không đổi sang nghĩa khác. Tuân thủ system prompt; giữ dạng từ/cách dùng
chuẩn, topic gọn và hai ví dụ tự nhiên khác ngữ cảnh, đúng cấp độ đã gán. Điền đủ schema;
không bịa dữ kiện còn thiếu.
"""
    
    # Thêm existing words context — CHỈ gửi từ trùng với batch này (tối ưu token)
    if existing_words:
        batch_fronts = [w["front"].lower().strip() for w in words if w.get("front")]
        _cap = 400
        overlap = []
        seen = set()
        for w in existing_words:
            key = (w or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            if key in batch_fronts:
                overlap.append(w.strip())
        if overlap:
            if len(overlap) > _cap:
                shown = overlap[:_cap]
                note = (
                    f"\n({len(overlap) - _cap} more words matching this batch; deck total {len(existing_words)})"
                    if en else
                    f"\n(Còn {len(overlap) - _cap} từ khác trùng batch; tổng deck {len(existing_words)} từ)"
                )
            else:
                shown = overlap
                note = (
                    f"\n(Deck total {len(existing_words)} words — only listing words matching this batch)"
                    if en else
                    f"\n(Tổng deck {len(existing_words)} từ — chỉ liệt kê từ trùng batch này)"
                )
            header = (
                "\n⚠️ WORDS ALREADY IN DECK — DO NOT OUTPUT:\n" if en else
                "\n⚠️ TỪ ĐÃ CÓ TRONG DECK — TUYỆT ĐỐI KHÔNG XUẤT RA:\n"
            )
            prompt += header + ", ".join(shown) + note + "\n"
        else:
            prompt += (
                f"\n⚠️ DECK ALREADY HAS {len(existing_words)} WORDS (none match this batch) → process normally.\n"
                if en else
                f"\n⚠️ DECK ĐÃ CÓ {len(existing_words)} TỪ (không trùng batch này) → cứ xử lý bình thường.\n"
            )
    
    if custom_instruction.strip():
        prompt += (
            f"\n📌 EXTRA REQUIREMENTS (highest priority):\n{custom_instruction.strip()}\n"
            if en else
            f"\n📌 YÊU CẦU BỔ SUNG (ưu tiên cao nhất):\n{custom_instruction.strip()}\n"
        )
    
    prompt += "\nOUTPUT: Plain JSON array [...]. No markdown." if en else "\nĐẦU RA: Mảng JSON thuần [...]. Không markdown."
    
    return prompt


def _call_ai_for_batch_response(
    words: List[Dict[str, str]],
    lang: str,
    existing_words: List[str],
    custom_instruction: str = "",
    batch_num: int = 1,
    total_batches: int = 1,
    progress_callback: Optional[Callable[[str], None]] = None,
    grammar: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
) -> AiCardResponse:
    """Call one batch and return validated response diagnostics."""
    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError(t("error_api_key_missing"))
    
    system_prompt = get_system_prompt(lang, "grammar" if grammar else "vocab")
    user_prompt = _build_batch_user_prompt(
        words, lang, existing_words, custom_instruction, batch_num, total_batches, grammar
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
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

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    try:
        body = _http_post_json(url, payload, headers, timeout=_timeout,
                               progress_callback=progress_callback, should_abort=should_abort)
    except RuntimeError as e:
        raise RuntimeError(t("batch_error_api", error=e))
    
    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        raise RuntimeError(t("error_api_no_result", details=body[:500]))

    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"], usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), usage.get("cost")
        )
        _record_token_info(
            token_info,
            operation="batch_grammar" if grammar else "batch_vocabulary",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
        )
    
    adapted = adapt_chat_completion_response(result, cfg)
    from .ai_reliability import process_ai_card_response

    try:
        response = process_ai_card_response(
            adapted, lang=lang, kind="grammar" if grammar else "vocab",
        )
    except AiOutputFailure as exc:
        cards = list(exc.cards)
        cards = (
            normalize_language_cards(cards)
            if grammar else repair_vocabulary_cards(cards, lang)
        )
        raise AiOutputFailure(exc.category, cards=cards, message=str(exc)) from exc

    cards = list(response.cards)
    cards = (
        normalize_language_cards(cards)
        if grammar else repair_vocabulary_cards(cards, lang)
    )
    response = replace(response, cards=tuple(cards))
    
    if progress_callback and response.comment:
        progress_callback(f"  💬 {response.comment[:100]}")
    
    logger.info(
        "Batch AI output provider=%s model=%s lang=%s kind=%s requested=%d raw=%d valid=%d invalid=%d duplicates=%d recovery=%s",
        response.provider, response.model, lang, "grammar" if grammar else "vocab",
        len(words), response.raw_count, len(response.cards), len(response.invalid),
        response.duplicate_count, response.recovery,
    )
    return response


def _call_ai_for_batch(*args, **kwargs) -> list:
    """Compatibility wrapper returning only validated cards."""
    return list(_call_ai_for_batch_response(*args, **kwargs).cards)


# ═══════════════════════════════════════════════════════════
#  BATCH CACHE
# ═══════════════════════════════════════════════════════════

def _ensure_cache_dir():
    migrate_legacy_directory(_LEGACY_CACHE_DIR, CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)
    prune_cache_dir(CACHE_DIR, max_age_seconds=CACHE_TTL,
                    max_bytes=25 * 1024 * 1024, max_files=200)


def _batch_cache_key(words: List[Dict[str, str]], lang: str, instruction: str, existing_hash: str, grammar: bool = False) -> str:
    """Tạo cache key cho một batch"""
    kind = "grammar" if grammar else "vocab"
    candidates = json.dumps(
        [
            {
                "front": w.get("front", ""),
                "meaning": w.get("meaning", ""),
                "level": w.get("level", ""),
                "topic": w.get("topic", ""),
            }
            for w in words
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    raw = (
        f"batch|prompt:{DEFAULT_PROMPT_VERSION}|signature:{get_signature()}|"
        f"{kind}|{lang}|{instruction}|{existing_hash}|{candidates}"
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _batch_cache_get(words: List[Dict[str, str]], lang: str, instruction: str, existing_hash: str, grammar: bool = False) -> Optional[list]:
    """Đọc cache cho batch"""
    _ensure_cache_dir()
    key = _batch_cache_key(words, lang, instruction, existing_hash, grammar=grammar)
    cache_file = os.path.join(CACHE_DIR, f"batch_{key}.json")
    if os.path.exists(cache_file):
        try:
            data = read_json(cache_file, {}, lambda value: isinstance(value, dict))
            kind = "grammar" if grammar else "vocab"
            cards = data.get("vocab", [])
            if (
                data.get("_schema_version") == AI_OUTPUT_SCHEMA_VERSION
                and data.get("_lang") == lang
                and data.get("_kind") == kind
                and data.get("_count") == len(words)
                and time.time() - data.get("_cached_at", 0) < CACHE_TTL
                and cache_payload_is_compatible(cards, lang=lang, kind=kind)
            ):
                return cards
        except Exception:
            pass
    return None


def _batch_cache_set(words: List[Dict[str, str]], lang: str, instruction: str, existing_hash: str, vocab_list: list, grammar: bool = False):
    """Ghi cache cho batch"""
    _ensure_cache_dir()
    key = _batch_cache_key(words, lang, instruction, existing_hash, grammar=grammar)
    cache_file = os.path.join(CACHE_DIR, f"batch_{key}.json")
    try:
        atomic_write_json(cache_file, {
            "vocab": vocab_list,
            "_cached_at": time.time(),
            "_lang": lang,
            "_kind": "grammar" if grammar else "vocab",
            "_schema_version": AI_OUTPUT_SCHEMA_VERSION,
            "_count": len(vocab_list),
        })
    except Exception:
        pass


@dataclass(frozen=True)
class BatchResolution:
    cards: tuple[dict, ...]
    unresolved: tuple[dict, ...]
    invalid: int = 0
    duplicates: int = 0
    unexpected: int = 0
    attempts: int = 0
    truncations: int = 0
    reasons: tuple[str, ...] = ()


def _resolve_batch_adaptively(
    batch: List[Dict[str, str]],
    lang: str,
    existing_words: List[str],
    custom_instruction: str,
    batch_num: int,
    total_batches: int,
    progress_callback: Optional[Callable[[str], None]],
    *,
    grammar: bool,
    should_abort: Optional[Callable[[], bool]],
    depth: int = 0,
) -> BatchResolution:
    """Keep valid cards, retry unresolved identities, and split boundedly."""
    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))

    invalid = duplicates = unexpected = truncations = 0
    reasons: tuple[str, ...] = ()
    try:
        response = _call_ai_for_batch_response(
            batch, lang, existing_words, custom_instruction,
            batch_num, total_batches, progress_callback, grammar=grammar,
            should_abort=should_abort,
        )
        cards = list(response.cards)
        invalid = len(response.invalid)
        duplicates = response.duplicate_count
    except AiOutputFailure as exc:
        cards = list(exc.cards)
        reasons = (exc.category,)
        truncations = int(exc.category == "truncation")

    reconciliation = reconcile_expected_candidates(
        batch, cards, kind="grammar" if grammar else "vocab",
        invalid_count=invalid, duplicate_count=duplicates,
        truncated=bool(truncations),
    )
    invalid = reconciliation.invalid
    duplicates = reconciliation.duplicates
    unexpected = reconciliation.unexpected
    if not reconciliation.unresolved or depth >= MAX_RECOVERY_RETRIES:
        return BatchResolution(
            reconciliation.cards, reconciliation.unresolved, invalid, duplicates,
            unexpected, 1, truncations, reasons,
        )

    unresolved = list(reconciliation.unresolved)
    if progress_callback:
        progress_callback(t(
            "batch_status_partial_retry",
            valid=len(reconciliation.cards), missing=len(unresolved),
            attempt=depth + 1, maximum=MAX_RECOVERY_RETRIES,
        ))

    # A total failure proves the current output budget unsafe. Split it. A
    # partial success already identifies the smaller unresolved sub-batch.
    if len(unresolved) == len(batch) and len(unresolved) > MIN_ADAPTIVE_BATCH_SIZE:
        midpoint = max(1, len(unresolved) // 2)
        retry_groups = [unresolved[:midpoint], unresolved[midpoint:]]
    else:
        retry_groups = [unresolved]

    retry_cards = []
    attempts = 1
    for retry_group in retry_groups:
        if not retry_group:
            continue
        child = _resolve_batch_adaptively(
            retry_group, lang, existing_words, custom_instruction,
            batch_num, total_batches, progress_callback, grammar=grammar,
            should_abort=should_abort, depth=depth + 1,
        )
        retry_cards.extend(child.cards)
        invalid += child.invalid
        duplicates += child.duplicates
        unexpected += child.unexpected
        attempts += child.attempts
        truncations += child.truncations
        reasons += child.reasons

    merged = reconcile_expected_candidates(
        batch, [*reconciliation.cards, *retry_cards],
        kind="grammar" if grammar else "vocab",
        invalid_count=invalid, duplicate_count=duplicates,
        truncated=bool(truncations),
    )
    return BatchResolution(
        merged.cards, merged.unresolved, merged.invalid, merged.duplicates,
        unexpected + merged.unexpected, attempts, truncations,
        tuple(dict.fromkeys(reasons)),
    )


# ═══════════════════════════════════════════════════════════
#  MAIN: Process Large Word List
# ═══════════════════════════════════════════════════════════

def process_large_word_list(
    raw_text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    grammar: bool = False,
    slow_mode: bool = False,
    report_callback: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """
    🚀 XỬ LÝ DANH SÁCH TỪ VỰNG LỚN QUA AI.
    
    Flow:
    1. Parse text → list of {front, meaning, level}
    2. Lọc bỏ từ đã có trong existing_words
    3. Smart grouping → batches
    4. Gọi AI cho từng batch (có cache + rate limiting)
    5. Gộp kết quả, loại trùng
    
    Args:
        raw_text: Text paste của người dùng (danh sách từ)
        lang: "japanese" hoặc "chinese"
        custom_instruction: Hướng dẫn bổ sung cho AI
        existing_words: Danh sách mặt chữ đã có trong deck
        batch_size: Số từ mỗi batch (mặc định 40)
        progress_callback: Callback(status_text) cho UI
        should_abort: Callback() → True nếu user bấm hủy
    
    Returns:
        List[dict] từ vựng đã được AI làm giàu (đầy đủ trường)
    """
    label = t("batch_item_pattern") if grammar else t("batch_item_word")
    short_label = t("batch_item_pattern_short") if grammar else t("batch_item_word_short")
    
    # ── Step 1: Parse ─────────────────────────────────────
    if progress_callback:
        progress_callback(t("batch_status_parsing", label=label))
    
    words = parse_word_list(raw_text, lang)
    if not words:
        raise ValueError(t("batch_error_no_items", label=label))
    
    if progress_callback:
        progress_callback(t("batch_status_parsed", count=len(words), label=label))
    
    # ── Step 2: Lọc đã có ─────────────────────────────
    if existing_words:
        existing_set = set(w.lower().strip() for w in existing_words)
        original_count = len(words)
        words = [w for w in words if w["front"].lower().strip() not in existing_set]
        filtered_count = original_count - len(words)
        if progress_callback and filtered_count > 0:
            progress_callback(t("batch_status_filtered", count=filtered_count, label=label))
    
    if not words:
        raise ValueError(t("batch_error_all_existing", label=label))
    
    if progress_callback:
        progress_callback(t("batch_status_remaining", count=len(words), label=label))
    
    # ── Step 3: Output-budget-aware grouping ──────────────
    cfg = get_api_config()
    policy_size = recommended_quality_v2_batch_size(
        lang, grammar=grammar, max_output_tokens=cfg.get("max_tokens", 8192),
    )
    effective_batch_size = max(1, min(int(batch_size or DEFAULT_BATCH_SIZE), policy_size))
    batches = smart_group_words(words, effective_batch_size)
    
    if progress_callback:
        progress_callback(t(
            "batch_status_groups",
            batches=len(batches),
            size=effective_batch_size,
            label=label,
        ))
    
    # ── Step 4: Process từng batch ────────────────────────
    existing_hash = _make_existing_hash(existing_words or [])
    all_vocab = []
    seen_cards = set()
    existing_set = set(w.lower().strip() for w in (existing_words or []))
    total_batches = len(batches)
    total_errors = 0
    requested_count = len(words)
    total_invalid = 0
    total_duplicates = 0
    total_unexpected = 0
    total_retries = 0
    total_truncations = 0
    unresolved_inputs = []

    # Rate limit theo provider + slow_mode:
    # - slow_mode=True (mặc định khi OpenRouter): delay 3.2s/batch → ~18 req/phút (an toàn < 20)
    # - slow_mode=False & không OpenRouter: giữ 1.5s như cũ (nhanh hơn)
    # - slow_mode=False & OpenRouter: cho phép 1.5s (user chủ động chấp nhận rủi ro rate limit)
    if slow_mode:
        base_delay = 3.2
    else:
        base_delay = MIN_DELAY_BETWEEN_BATCHES
    if is_openrouter() and slow_mode and progress_callback:
        progress_callback(t(
            "batch_openrouter_safe",
            delay=base_delay,
            rate=int(60 / base_delay),
        ))
    elif is_openrouter() and not slow_mode and progress_callback:
        progress_callback(t("batch_openrouter_fast", delay=base_delay))
    
    for idx, batch in enumerate(batches):
        # Check abort
        if should_abort and should_abort():
            unresolved_inputs.extend(
                item for pending in batches[idx:] for item in pending
            )
            if progress_callback:
                progress_callback(t(
                    "batch_status_cancelled", current=idx, total=total_batches
                ))
            break
        
        batch_num = idx + 1
        
        if progress_callback:
            batch_preview = ", ".join(w["front"] for w in batch[:3])
            if len(batch) > 3:
                batch_preview += f", ... (+{len(batch) - 3})"
            progress_callback(f"🔄 Batch {batch_num}/{total_batches}: {batch_preview}")
        
        # Check cache
        cached = _batch_cache_get(batch, lang, custom_instruction, existing_hash, grammar=grammar)
        was_cache_hit = cached is not None
        if was_cache_hit:
            if progress_callback:
                progress_callback(t(
                    "batch_status_cache_hit", count=len(cached), label=short_label
                ))
            new_count = 0
            for item in cached:
                front = (
                    (item.get("pattern") or "") if grammar
                    else (item.get("front") or item.get("simplified") or "")
                ).strip().lower()
                card_key = (front, (item.get("meaning") or "").strip().lower())
                if front and card_key not in seen_cards and front not in existing_set:
                    seen_cards.add(card_key)
                    all_vocab.append(item)
                    new_count += 1
            if progress_callback:
                progress_callback(t(
                    "batch_status_added",
                    count=new_count,
                    label=short_label,
                    total=len(all_vocab),
                ))
        
        else:
            # Gọi AI với completeness reconciliation + bounded recovery.
            try:
                resolution = _resolve_batch_adaptively(
                    batch, lang, existing_words or [], custom_instruction,
                    batch_num, total_batches, progress_callback, grammar=grammar,
                    should_abort=should_abort,
                )
                vocab_batch = list(resolution.cards)
                total_invalid += resolution.invalid
                total_duplicates += resolution.duplicates
                total_unexpected += resolution.unexpected
                total_retries += max(0, resolution.attempts - 1)
                total_truncations += resolution.truncations
                unresolved_inputs.extend(resolution.unresolved)
                if resolution.unresolved:
                    total_errors += 1
                 
                # Lọc trùng
                new_count = 0
                for item in vocab_batch:
                    if not isinstance(item, dict):
                        continue
                    front = (
                        (item.get("pattern") or "") if grammar
                        else (item.get("front") or item.get("simplified") or "")
                    ).strip().lower()
                    card_key = (front, (item.get("meaning") or "").strip().lower())
                    if front and card_key not in seen_cards and front not in existing_set:
                        seen_cards.add(card_key)
                        all_vocab.append(item)
                        new_count += 1
                 
                if progress_callback:
                    progress_callback(t(
                        "batch_status_added",
                        count=new_count,
                        label=short_label,
                        total=len(all_vocab),
                    ))
                 
                # Cache kết quả
                if vocab_batch and not resolution.unresolved and len(vocab_batch) == len(batch):
                    _batch_cache_set(batch, lang, custom_instruction, existing_hash, vocab_batch, grammar=grammar)
                
            except Exception as e:
                total_errors += 1
                logger.warning("Batch %d error: %s", batch_num, e)
                if progress_callback:
                    progress_callback(t(
                        "batch_progress_error", batch=batch_num, error=e
                    ))
                
                unresolved_inputs.extend(batch)
        
        # Rate limiting giữa các batch — CHỈ khi không phải cache hit (tiết kiệm thời gian)
        # Dùng delay động: nếu đang bị rate limit (từ _http_post_json), tăng dần
        if idx < total_batches - 1 and not was_cache_hit:
            # Nếu _http_post_json đã tự tăng delay (gặp 429), dùng delay đó
            current_delay = _get_rate_limit_delay()
            delay = current_delay if current_delay > 0 else base_delay
            if delay > base_delay and progress_callback:
                progress_callback(t("batch_status_rate_wait", seconds=delay))
            _wait_for_cancel(delay, should_abort)
    
    # ── Step 5: Completeness summary ──────────────────────
    summary_report = {
        "requested": requested_count,
        "valid": len(all_vocab),
        "invalid": total_invalid,
        "duplicates": total_duplicates,
        "missing": len(unresolved_inputs),
        "unexpected": total_unexpected,
        "retries": total_retries,
        "truncations": total_truncations,
        "batch_size": effective_batch_size,
        "batches": total_batches,
        "complete": len(unresolved_inputs) == 0,
    }
    if report_callback:
        report_callback(dict(summary_report))
    if progress_callback:
        if unresolved_inputs:
            progress_callback(t(
                "batch_status_partial_complete",
                requested=requested_count, valid=len(all_vocab),
                unresolved=len(unresolved_inputs), retries=total_retries,
            ))
        else:
            progress_callback(t(
                "batch_status_complete",
                count=len(all_vocab),
                label=label,
                batches=total_batches,
                errors=total_errors,
            ))

    logger.info(
        "Batch reliability lang=%s kind=%s requested=%d valid=%d invalid=%d duplicates=%d missing=%d unexpected=%d retries=%d truncations=%d batch_size=%d",
        lang, "grammar" if grammar else "vocab", requested_count,
        len(all_vocab), total_invalid, total_duplicates, len(unresolved_inputs),
        total_unexpected, total_retries, total_truncations, effective_batch_size,
    )
    
    return all_vocab


# ═══════════════════════════════════════════════════════════
#  DECK ORGANIZER — AI đề xuất cấu trúc Parent/Sub Deck
# ═══════════════════════════════════════════════════════════

_DECK_ORGANIZER_SYSTEM_PROMPT = """Bạn là chuyên gia tổ chức từ vựng cho hệ thống Spaced Repetition (Anki).

NHIỆM VỤ: Phân tích danh sách từ vựng đã được trích xuất và đề xuất cấu trúc DECK (parent deck + sub decks) tối ưu cho việc học.

NGUYÊN TẮC TỔ CHỨC:
1. PARENT DECK: Nhóm theo ngữ cảnh lớn (VD: "Tiếng Nhật Giao Tiếp", "Tiếng Trung HSK", "Kanji Theo Chủ Đề")
2. SUB DECKS: Mỗi sub deck nên có 20-50 từ, đủ nhỏ để học trong 1-2 ngày nhưng đủ lớn để có context
3. TIÊU CHÍ PHÂN NHÓM (theo thứ tự ưu tiên):
   a. CHỦ ĐỀ (topic): Động vật, Thực phẩm, Công việc, Gia đình, Du lịch...
   b. CẤP ĐỘ: N5→N1 hoặc HSK1→HSK6
   c. LOẠI TỪ: Động từ, Danh từ, Tính từ, Trạng từ...
   d. ĐỘ KHÓ/TẦN SUẤT: Từ phổ biến → hiếm gặp
4. TÊN DECK: Ngắn gọn, có ý nghĩa, dùng tiếng Việt
5. Mỗi từ CHỈ xuất hiện trong 1 deck (không trùng lặp)

ĐẦU RA JSON:
{
  "suggestion": "Mô tả ngắn về chiến lược tổ chức",
  "decks": [
    {
      "parent": "Tiếng Nhật Giao Tiếp",
      "sub_decks": [
        {
          "name": "Chào Hỏi & Gặp Gỡ",
          "description": "Từ vựng dùng khi gặp gỡ, chào hỏi",
          "word_count": 25,
          "words": ["食べる", "飲む", ...]
        }
      ]
    }
  ]
}"""

_DECK_ORGANIZER_SYSTEM_PROMPT_EN = """You are an expert at organizing vocabulary for a spaced-repetition system (Anki).

TASK: Analyze the extracted vocabulary and propose an effective deck hierarchy (parent decks + subdecks).

ORGANIZATION RULES:
1. PARENT DECKS: Group by broad learning context (for example, "Japanese Conversation" or "Chinese HSK").
2. SUBDECKS: Aim for 20–50 words per subdeck so each group is focused but still has useful context.
3. GROUPING PRIORITY: topic, proficiency level, part of speech, then difficulty/frequency.
4. DECK NAMES: Use concise, meaningful English names.
5. Assign each word to exactly one deck.

JSON OUTPUT:
{
  "suggestion": "Short description of the organization strategy",
  "decks": [
    {
      "parent": "Japanese Conversation",
      "sub_decks": [
        {
          "name": "Greetings & Introductions",
          "description": "Vocabulary used when greeting and meeting people",
          "word_count": 25,
          "words": ["食べる", "飲む"]
        }
      ]
    }
  ]
}"""


def organize_decks_with_ai(
    vocab_list: List[dict],
    lang: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
) -> dict:
    """
    🤖 Dùng AI để đề xuất cấu trúc Parent Deck + Sub Decks dựa trên từ vựng đã trích xuất.
    
    Args:
        vocab_list: Danh sách từ vựng (đã có topic, level...)
        lang: "japanese" hoặc "chinese"
        progress_callback: Callback trạng thái
    
    Returns:
        dict với keys: suggestion, decks (list parent + sub_decks)
    """
    if not vocab_list:
        return {"suggestion": t("organizer_empty"), "decks": []}
    
    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError(t("error_api_key_missing"))
    
    if progress_callback:
        progress_callback(t("organizer_status_analyzing"))
    
    # Xây dựng summary cho AI (không gửi toàn bộ chi tiết để tiết kiệm token)
    word_summaries = []
    for item in vocab_list:
        front = item.get("front") or item.get("simplified") or ""
        meaning = item.get("meaning") or ""
        level = item.get("jlptlevel") or item.get("hsk_level") or ""
        topic = item.get("topic") or ""
        word_summaries.append(f"{front} | {meaning} | {level} | {topic}")
    
    # Giới hạn: nếu quá nhiều từ, chỉ gửi summary
    MAX_WORDS_FOR_ORG = 500
    if len(word_summaries) > MAX_WORDS_FOR_ORG:
        # Sampling: lấy mỗi N từ
        step = max(1, len(word_summaries) // MAX_WORDS_FOR_ORG)
        sampled = word_summaries[::step][:MAX_WORDS_FOR_ORG]
        word_text = "\n".join(sampled)
        word_text += (
            f"\n\n(Total: {len(word_summaries)} words; showing {len(sampled)} samples)"
            if get_language() == "en"
            else f"\n\n(Tổng cộng {len(word_summaries)} từ, hiển thị {len(sampled)} từ mẫu)"
        )
    else:
        word_text = "\n".join(word_summaries)
    
    if get_language() == "en":
        user_prompt = f"""Analyze the following {len(vocab_list)} vocabulary items and propose an effective deck hierarchy:

{word_text}

Organize them into parent decks and subdecks by topic, level, and part of speech.
Each subdeck should contain about 20–50 words.
Use concise, clear English deck names.

Output a JSON object matching the system prompt."""
        organizer_prompt = _DECK_ORGANIZER_SYSTEM_PROMPT_EN
    else:
        user_prompt = f"""Phân tích danh sách {len(vocab_list)} từ vựng sau và đề xuất cấu trúc deck tối ưu:

{word_text}

Hãy tổ chức thành Parent Decks và Sub Decks theo chủ đề, cấp độ, và loại từ.
Mỗi sub deck nên có 20-50 từ.
Tên deck bằng tiếng Việt, ngắn gọn, dễ hiểu.

Đầu ra: JSON object với cấu trúc như system prompt yêu cầu."""
        organizer_prompt = _DECK_ORGANIZER_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": organizer_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    _apply_reasoning_effort(payload, cfg)
    
    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    
    if progress_callback:
        progress_callback(t("organizer_status_waiting"))

    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    try:
        body = _http_post_json(url, payload, headers, timeout=300,
                               progress_callback=progress_callback, should_abort=should_abort)
    except Exception as e:
        logger.warning("Deck organizer error: %s", e)
        # Fallback: tự tổ chức đơn giản
        return _fallback_deck_organization(vocab_list, lang)
    
    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        return _fallback_deck_organization(vocab_list, lang)

    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"], usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), usage.get("cost")
        )
        _record_token_info(
            token_info,
            operation="deck_organization",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
        )
    
    content = result["choices"][0]["message"].get("content", "") or ""
    
    # Parse JSON từ response
    try:
        # Thử parse trực tiếp
        org_result = json.loads(content)
    except json.JSONDecodeError:
        # Thử tìm JSON block
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
        if json_match:
            try:
                org_result = json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                return _fallback_deck_organization(vocab_list, lang)
        else:
            # Thử tìm object
            obj_match = re.search(r'\{.*\}', content, re.DOTALL)
            if obj_match:
                try:
                    org_result = json.loads(obj_match.group(0))
                except json.JSONDecodeError:
                    return _fallback_deck_organization(vocab_list, lang)
            else:
                return _fallback_deck_organization(vocab_list, lang)
    
    if progress_callback:
        deck_count = sum(len(p.get("sub_decks", [])) for p in org_result.get("decks", []))
        progress_callback(t(
            "organizer_status_suggested",
            parents=len(org_result.get("decks", [])),
            subs=deck_count,
        ))
    
    return org_result


def _fallback_deck_organization(vocab_list: List[dict], lang: str) -> dict:
    """
    Fallback: Tự tổ chức deck đơn giản khi AI không khả dụng.
    Nhóm theo topic → level.
    """
    # Nhóm theo topic
    by_topic = {}
    no_topic = []
    
    for item in vocab_list:
        topic = (item.get("topic") or "").strip()
        if topic:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(item)
        else:
            no_topic.append(item)
    
    # Nhóm theo level trong mỗi topic
    decks = []
    lang_label = t({
        "japanese": "organizer_lang_japanese",
        "chinese": "organizer_lang_chinese",
        "korean": "organizer_lang_korean",
        "english": "organizer_lang_english",
    }.get(lang, "organizer_lang_japanese"))
    
    if by_topic:
        sub_decks = []
        for topic, words in sorted(by_topic.items(), key=lambda x: -len(x[1])):
            # Nếu topic có quá nhiều từ, chia theo level
            if len(words) > 50:
                by_level = {}
                for w in words:
                    level = (
                        w.get("jlptlevel") or w.get("hsk_level")
                        or w.get("topik_level") or t("organizer_other")
                    )
                    if level not in by_level:
                        by_level[level] = []
                    by_level[level].append(w)
                
                for level, lvl_words in sorted(by_level.items()):
                    sub_decks.append({
                        "name": f"{topic} - {level}",
                        "description": t(
                            "organizer_level_description", level=f"{topic} {level}"
                        ),
                        "word_count": len(lvl_words),
                        "words": [w.get("front") or w.get("simplified") or "" for w in lvl_words],
                    })
            else:
                sub_decks.append({
                    "name": topic,
                    "description": t(
                        "organizer_topic_description", topic=topic.lower()
                    ),
                    "word_count": len(words),
                    "words": [w.get("front") or w.get("simplified") or "" for w in words],
                })
        
        decks.append({
            "parent": t("organizer_topic_parent", language=lang_label),
            "sub_decks": sub_decks,
        })
    
    if no_topic:
        # Nhóm theo level
        by_level = {}
        for w in no_topic:
            level = (
                w.get("jlptlevel") or w.get("hsk_level")
                or w.get("topik_level") or t("organizer_uncategorized")
            )
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(w)
        
        sub_decks = []
        for level, lvl_words in sorted(by_level.items()):
            sub_decks.append({
                "name": t("organizer_level_name", level=level),
                "description": t("organizer_level_description", level=level),
                "word_count": len(lvl_words),
                "words": [w.get("front") or w.get("simplified") or "" for w in lvl_words],
            })
        
        decks.append({
            "parent": t("organizer_level_parent", language=lang_label),
            "sub_decks": sub_decks,
        })
    
    return {
        "suggestion": t("organizer_fallback_suggestion"),
        "decks": decks,
    }


# ═══════════════════════════════════════════════════════════
#  AUTO-CREATE DECKS IN ANKI
# ═══════════════════════════════════════════════════════════

def create_decks_from_organization(
    organization: dict,
    vocab_list: List[dict],
    lang: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    collection=None,
    should_abort: Optional[Callable[[], bool]] = None,
) -> Dict[str, int]:
    """
    📦 Tự động tạo parent deck + sub decks trong Anki dựa trên đề xuất của AI.
    
    Args:
        organization: Kết quả từ organize_decks_with_ai()
        vocab_list: Danh sách từ vựng gốc
        lang: "japanese" hoặc "chinese"
        progress_callback: Callback trạng thái
    
    Returns:
        Dict mapping deck_name → deck_id đã tạo
    """
    try:
        if collection is None:
            from aqt import mw
            collection = mw.col
    except ImportError:
        raise RuntimeError(t("organizer_anki_unavailable"))
    
    created_decks = {}
    
    # Build lookup: front → vocab item
    front_to_item = {}
    for item in vocab_list:
        front = (item.get("front") or item.get("simplified") or "").strip()
        if front:
            front_to_item[front] = item
    
    total_decks = sum(len(p.get("sub_decks", [])) for p in organization.get("decks", []))
    deck_count = 0
    
    for parent_info in organization.get("decks", []):
        if should_abort and should_abort():
            break
        parent_name = parent_info.get("parent", t("organizer_default_parent")).strip()
        
        # Tạo parent deck nếu chưa có
        try:
            parent_id = collection.decks.id(parent_name, create=False)
        except Exception:
            parent_id = None
        
        if parent_id is None:
            try:
                parent_id = collection.decks.id(parent_name)
                if progress_callback:
                    progress_callback(t("organizer_status_create_parent", name=parent_name))
            except Exception as e:
                logger.warning("Không tạo được parent deck '%s': %s", parent_name, e)
                continue
        
        created_decks[parent_name] = parent_id
        
        for sub_info in parent_info.get("sub_decks", []):
            if should_abort and should_abort():
                break
            sub_name = sub_info.get("name", "Sub Deck").strip()
            full_name = f"{parent_name}::{sub_name}"
            
            deck_count += 1
            if progress_callback:
                progress_callback(f"  📁 [{deck_count}/{total_decks}] {full_name}")
            
            # Tạo sub deck
            try:
                sub_id = collection.decks.id(full_name)
                created_decks[full_name] = sub_id
            except Exception as e:
                logger.warning("Không tạo được sub deck '%s': %s", full_name, e)
    
    if progress_callback:
        progress_callback(t("organizer_status_created", count=len(created_decks)))
    
    return created_decks


# ═══════════════════════════════════════════════════════════
#  UTILITY: Estimate cost
# ═══════════════════════════════════════════════════════════

def estimate_batch_cost(
    word_count: int,
    lang: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    *,
    grammar: bool = False,
) -> dict:
    """
    Ước tính chi phí API cho việc xử lý batch.
    
    Returns:
        dict với estimated_batches, estimated_tokens, estimated_cost (USD)
    """
    max_tokens = get_api_config().get("max_tokens", 8192)
    effective_size = min(
        max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
        recommended_quality_v2_batch_size(
            lang, grammar=grammar, max_output_tokens=max_tokens,
        ),
    )
    batches = max(1, (word_count + effective_size - 1) // effective_size)
    
    # Quality V2 carries more examples/usage data than the legacy card schema.
    input_tokens = word_count * 200 + batches * 800
    output_tokens = word_count * (800 if grammar else 650)
    
    # Giá tham khảo (DeepSeek):
    # deepseek-chat: $0.14/1M input, $0.28/1M output
    # gpt-4o-mini: $0.15/1M input, $0.60/1M output
    cost_input = input_tokens / 1_000_000 * 0.14
    cost_output = output_tokens / 1_000_000 * 0.28
    total_cost = cost_input + cost_output
    
    return {
        "total_words": word_count,
        "batch_size": effective_size,
        "requested_batch_size": batch_size,
        "estimated_batches": batches,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "estimated_time_seconds": batches * 10,  # ~10s/batch
    }
