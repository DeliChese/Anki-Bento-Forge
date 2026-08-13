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
