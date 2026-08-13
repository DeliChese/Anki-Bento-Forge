"""Sensitive values must never reach a Bento Forge log handler."""


def test_redacts_authorization_and_api_key_fields():
    from utils.logger import redact_sensitive

    value = "Authorization: Bearer sk_abcdefghijklmnopqrstuvwxyz api_key=secret-value"
    redacted = redact_sensitive(value)

    assert "abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "secret-value" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_nested_header_and_config_values():
    from utils.logger import redact_sensitive

    redacted = redact_sensitive({"Authorization": "Bearer secret", "config": {"api_key": "secret"}})

    assert redacted["Authorization"] == "[REDACTED]"
    assert redacted["config"]["api_key"] == "[REDACTED]"


def test_event_format_has_stable_code_and_safe_context():
    from utils.logger import format_event

    event = format_event(
        "IMPORT_AUDIO_TASK_FAILED",
        "continue_import_without_audio",
        error=RuntimeError("user card text must not be logged"),
        provider="edge_tts",
    )

    assert event.startswith("IMPORT_AUDIO_TASK_FAILED: action=continue_import_without_audio")
    assert "error=RuntimeError" in event
    assert "user card text" not in event


def test_event_code_must_be_a_stable_uppercase_identifier():
    import pytest
    from utils.logger import format_event

    with pytest.raises(ValueError):
        format_event("audio failed", "retry")
