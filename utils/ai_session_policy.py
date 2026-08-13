"""Privacy-preserving limits and estimates for one AI session.

The policy deliberately retains aggregate usage only.  It never stores prompt,
response, card, or conversation content.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from typing import Dict, Optional


_PRICING = {
    "deepseek-chat": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
}


@dataclass(frozen=True)
class AiRunEstimate:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    calls: int
    input_truncated: bool


class AiSessionPolicy:
    """Thread-safe aggregate AI budget for the current Bento Forge process."""

    def __init__(self, *, max_input_chars=90_000, max_tokens=120_000, max_cost_usd=2.0):
        self._lock = threading.Lock()
        self.configure(max_input_chars=max_input_chars, max_tokens=max_tokens, max_cost_usd=max_cost_usd)
        self.reset()

    def configure(self, *, max_input_chars: int, max_tokens: int, max_cost_usd: float) -> None:
        self.max_input_chars = max(1_000, int(max_input_chars))
        self.max_tokens = max(1_000, int(max_tokens))
        self.max_cost_usd = max(0.0, float(max_cost_usd))

    def reset(self) -> None:
        with self._lock:
            self._used_tokens = 0
            self._used_cost_usd = 0.0
            self._calls = 0

    def estimate(self, *, text_chars: int, model: str, max_output_tokens: int, chunk_size: int) -> AiRunEstimate:
        text_chars = max(0, int(text_chars))
        processed_chars = min(text_chars, self.max_input_chars)
        chunk_size = max(1_000, int(chunk_size))
        calls = max(1, math.ceil(processed_chars / chunk_size))
        input_tokens = math.ceil(processed_chars / 4) + 600 * calls
        output_tokens = max(1, int(max_output_tokens)) * calls
        in_price, out_price = _PRICING.get(model, (0.14, 0.28))
        cost = (input_tokens * in_price + output_tokens * out_price) / 1_000_000
        return AiRunEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=round(cost, 6),
            calls=calls,
            input_truncated=text_chars > processed_chars,
        )

    def check(self, estimate: AiRunEstimate) -> Optional[str]:
        """Return a safe, content-free reason when a run exceeds its budget."""
        with self._lock:
            if estimate.total_tokens > self.max_tokens:
                return "estimated token use exceeds the session token limit"
            if self._used_tokens + estimate.total_tokens > self.max_tokens:
                return "remaining session token budget is too small"
            if self.max_cost_usd and self._used_cost_usd + estimate.cost_usd > self.max_cost_usd:
                return "remaining session cost budget is too small"
        return None

    def record(self, token_info: Dict) -> None:
        """Record provider-reported aggregate usage; malformed data is ignored."""
        try:
            tokens = max(0, int(token_info.get("total_tokens", 0)))
            cost = max(0.0, float(token_info.get("total_cost", 0.0)))
        except (AttributeError, TypeError, ValueError):
            return
        with self._lock:
            self._used_tokens += tokens
            self._used_cost_usd = round(self._used_cost_usd + cost, 6)
            self._calls += 1

    def snapshot(self) -> Dict:
        with self._lock:
            return {
                "used_tokens": self._used_tokens,
                "used_cost_usd": self._used_cost_usd,
                "calls": self._calls,
                "max_tokens": self.max_tokens,
                "max_cost_usd": self.max_cost_usd,
                "max_input_chars": self.max_input_chars,
            }


_POLICY = AiSessionPolicy()


def get_ai_session_policy() -> AiSessionPolicy:
    return _POLICY
