"""AI transport orchestration for strict Forge source-candidate manifests."""

from __future__ import annotations

import json
import time
from typing import Callable, Optional

from . import ai_extractor as _api
from .ai_response_guard import adapt_chat_completion_response, enable_deepseek_json_output
from .ai_source_candidates import (
    CandidateOutputError, build_candidate_prompt, parse_source_candidate_response,
)
from .ai_workspace import validate_workspace_request, workspace_context_message
from .i18n import t


def extract_source_candidates_with_ai(
    user_instruction: str,
    *,
    lang: str,
    workspace_request,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    session_id: str = "",
    runtime_config: Optional[dict] = None,
) -> dict:
    """Return a strict Forge candidate manifest for the current request source."""
    workspace = validate_workspace_request("forge", lang, workspace_request)
    if workspace != "forge" or workspace_request is None:
        raise ValueError("Forge candidate request context is required")
    if workspace_request.learning_mode != "language":
        raise ValueError("Forge candidates require the language workflow")
    if workspace_request.lane not in {"vocab", "grammar"}:
        raise ValueError("unsupported Forge candidate lane")
    source_text = str(workspace_request.source_text or "").strip()
    if not source_text:
        raise ValueError("Forge candidates require an attached source")

    instruction = str(user_instruction or workspace_request.user_instruction or "").strip()
    cfg = dict(runtime_config) if isinstance(runtime_config, dict) else _api.get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        return {"candidate_manifest": None, "error": t("error_api_key_missing")}
    try:
        _api.ensure_ai_session_budget(source_text + "\n" + instruction)
    except ValueError as error:
        return {"candidate_manifest": None, "error": str(error)}
    if progress_callback:
        progress_callback(t("status_calling_model", model=cfg["model"]))

    messages = [
        {"role": "system", "content": build_candidate_prompt(
            lang, workspace_request.lane, english_ui=_api._ui_lang_en(),
        )},
        workspace_context_message(workspace_request),
        {"role": "user", "content": instruction or t("study_candidates_default_instruction")},
    ]
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": min(float(cfg.get("temperature", 0.2)), 0.2),
        "max_tokens": min(int(cfg.get("max_tokens", 8192)), 4096),
    }
    _api._apply_reasoning_effort(payload, cfg)
    enable_deepseek_json_output(payload, cfg)
    url = f"{cfg['api_base'].rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    if progress_callback:
        progress_callback(t("status_waiting_ai"))
    request_started_at = time.time()
    request_started_monotonic = time.monotonic()
    timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    try:
        body = _api._http_post_json(
            url, payload, headers, timeout=timeout,
            progress_callback=progress_callback, should_abort=should_abort,
        )
        adapted = adapt_chat_completion_response(json.loads(body), cfg)
    except (RuntimeError, ValueError) as error:
        return {"candidate_manifest": None, "error": str(error)}

    usage = adapted.usage
    token_info = None
    if usage.get("total_tokens"):
        token_info = _api._calculate_cost(
            cfg["model"], usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0), usage.get("cost"),
        )
        _api._record_token_info(
            token_info, operation="forge_candidates",
            started_at=request_started_at,
            duration_seconds=time.monotonic() - request_started_monotonic,
            provider=adapted.provider, session_id=session_id,
        )
    try:
        manifest = parse_source_candidate_response(
            adapted, source_text=source_text, language=lang,
            lane=workspace_request.lane,
        )
    except CandidateOutputError as error:
        return {
            "candidate_manifest": None,
            "token_info": token_info,
            "candidate_error": error.category,
            "error": t("study_candidates_invalid", error=error.category),
        }
    if progress_callback:
        progress_callback(t("status_complete"))
    return {
        "candidate_manifest": manifest,
        "token_info": token_info,
        "candidate_error": None,
        "error": None,
    }


__all__ = ["extract_source_candidates_with_ai"]
