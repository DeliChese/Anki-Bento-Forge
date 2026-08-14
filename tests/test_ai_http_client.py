"""Contract tests for the Anki-independent AI HTTP transport."""

import ast
import json
from pathlib import Path

import pytest


class _FakeResponse:
    def __init__(self, status, body, headers=None, reason="OK"):
        self.status = status
        self.reason = reason
        self._body = body
        self._headers = headers or {}
        self._read = False

    def getheader(self, name, default=None):
        return self._headers.get(name, default)

    def read(self, _size=None):
        if self._read:
            return b""
        self._read = True
        return self._body


class _FakeConnection:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.closed = False

    def request(self, method, path, body=None, headers=None):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


def test_transport_has_no_anki_ui_config_or_subprocess_dependency():
    import utils.ai_http_client as client

    source_path = Path(client.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint({"aqt", "anki", "PyQt5", "PyQt6"})
    assert "ai_extractor" not in source
    assert "user_data" not in source
    assert "subprocess" not in source


def test_ssl_verification_is_relaxed_only_for_loopback_hosts():
    import ssl
    from utils import ai_http_client as client

    assert client._pick_ssl_context("localhost").verify_mode == ssl.CERT_NONE
    assert client._pick_ssl_context("127.0.0.1").verify_mode == ssl.CERT_NONE
    assert client._pick_ssl_context("api.openai.com").verify_mode == ssl.CERT_REQUIRED
    assert client._pick_ssl_context("localhost.example.com").verify_mode == ssl.CERT_REQUIRED


def test_post_json_preserves_request_contract(monkeypatch):
    from utils import ai_http_client as client

    response = _FakeResponse(
        200,
        b'{"choices": []}',
        headers={"Content-Length": "15"},
    )
    connection = _FakeConnection(response)
    monkeypatch.setattr(client, "_get_thread_conn", lambda *args, **kwargs: connection)
    client._reset_rate_limit_delay()

    headers = {"Authorization": "Bearer secret"}
    body = client.post_json(
        "https://example.test/v1/chat/completions?source=anki",
        {"model": "test"},
        headers,
    )

    assert json.loads(body) == {"choices": []}
    method, path, request_body, request_headers = connection.requests[0]
    assert method == "POST"
    assert path == "/v1/chat/completions?source=anki"
    assert json.loads(request_body.decode("utf-8")) == {"model": "test"}
    assert request_headers is headers
    assert int(headers["Content-Length"]) == len(request_body)


def test_rate_limit_retries_on_a_fresh_connection(monkeypatch):
    from utils import ai_http_client as client

    limited = _FakeConnection(
        _FakeResponse(429, b"slow down", headers={"Retry-After": "0"})
    )
    success = _FakeConnection(_FakeResponse(200, b'{"ok": true}'))
    connections = iter([limited, success])
    waits = []
    force_new_values = []

    def get_connection(*_args, **kwargs):
        force_new_values.append(kwargs.get("force_new", False))
        return next(connections)

    monkeypatch.setattr(client, "_get_thread_conn", get_connection)
    monkeypatch.setattr(
        client,
        "abortable_wait",
        lambda seconds, should_abort=None: waits.append(seconds),
    )
    client._reset_rate_limit_delay()

    assert json.loads(client.post_json("https://example.test/v1", {}, {})) == {
        "ok": True
    }
    assert force_new_values == [False, True]
    assert waits == [0.0]
    assert client.get_rate_limit_delay() == 0.0


def test_cancellation_stops_before_opening_connection(monkeypatch):
    from utils import ai_http_client as client

    def unexpected_connection(*_args, **_kwargs):
        pytest.fail("connection must not open after cancellation")

    monkeypatch.setattr(client, "_get_thread_conn", unexpected_connection)
    with pytest.raises(RuntimeError, match="Đã hủy"):
        client.post_json(
            "https://example.test/v1",
            {},
            {},
            should_abort=lambda: True,
        )


def test_ai_extractor_keeps_transport_compatibility_exports(monkeypatch):
    from utils import ai_extractor
    from utils import ai_http_client as client

    assert ai_extractor._http_post_json is client.post_json
    assert ai_extractor._abortable_wait is client.abortable_wait
    assert ai_extractor._get_rate_limit_delay is client.get_rate_limit_delay
    assert ai_extractor.is_openrouter("https://openrouter.ai/api/v1")

    monkeypatch.setattr(
        ai_extractor,
        "get_api_config",
        lambda: {"api_base": "http://localhost:11434/v1"},
    )
    assert not ai_extractor.is_openrouter()
