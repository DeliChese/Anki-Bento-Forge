"""Bounded output-token policy shared by AI extraction configuration."""

DEFAULT_MAX_OUTPUT_TOKENS = 10_240
_LEGACY_DEFAULT_MAX_OUTPUT_TOKENS = 8_192


def normalize_output_token_budget(value: object) -> int:
    """Upgrade the former hidden default while preserving deliberate overrides."""
    try:
        tokens = int(value or DEFAULT_MAX_OUTPUT_TOKENS)
    except (TypeError, ValueError):
        return DEFAULT_MAX_OUTPUT_TOKENS
    if tokens == _LEGACY_DEFAULT_MAX_OUTPUT_TOKENS:
        tokens = DEFAULT_MAX_OUTPUT_TOKENS
    return max(1_024, min(32_768, tokens))


__all__ = ["DEFAULT_MAX_OUTPUT_TOKENS", "normalize_output_token_budget"]
