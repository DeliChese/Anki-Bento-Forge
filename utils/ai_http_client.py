"""HTTP transport for OpenAI-compatible AI providers.

This module owns only network concerns: TLS policy, per-thread connection reuse,
rate-limit backoff, retry, cancellation, and bounded response reads. It remains
independent from Anki/Qt, user configuration, prompts, and response parsing.
"""

import http.client
import json
import ssl
import threading
import time
from typing import Callable, Optional
from urllib.parse import urlparse

from .i18n import t


_SSL_CONTEXT_SECURE = ssl.create_default_context()
_SSL_CONTEXT_LOCAL = ssl.create_default_context()
_SSL_CONTEXT_LOCAL.check_hostname = False
_SSL_CONTEXT_LOCAL.verify_mode = ssl.CERT_NONE

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_OPENROUTER_MARKERS = ("openrouter.ai", "openrouter")
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024


class ResponseTooLargeError(RuntimeError):
    """Raised when an AI provider response exceeds the transport safety bound."""


def is_openrouter(api_base: str) -> bool:
    """Return whether *api_base* points at an OpenRouter-compatible endpoint."""
    base = (api_base or "").lower()
    return any(marker in base for marker in _OPENROUTER_MARKERS)


def _pick_ssl_context(host: str) -> ssl.SSLContext:
    """Disable certificate verification only for an explicit loopback host."""
    if (host or "").lower() in _LOCAL_HOSTS:
        return _SSL_CONTEXT_LOCAL
    return _SSL_CONTEXT_SECURE


def _parse_http_url(url: str):
    """Validate an HTTP(S) endpoint and return connection components."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("AI endpoint must be an absolute http:// or https:// URL")
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return parsed.scheme, host, port, path


_conn_pool_local = threading.local()
_rate_limit_state = threading.local()


def _create_conn(host: str, port: int, use_ssl: bool, timeout: int, ssl_context=None):
    """Create an HTTP connection with the caller's per-request timeout."""
    if use_ssl:
        return http.client.HTTPSConnection(
            host, port, timeout=timeout, context=ssl_context
        )
    return http.client.HTTPConnection(host, port, timeout=timeout)


def _get_thread_conn(
    pool_key: str,
    host: str,
    port: int,
    use_ssl: bool,
    timeout: int,
    ssl_context=None,
    force_new: bool = False,
):
    """Get or replace the current thread's connection for *pool_key*."""
    pool = getattr(_conn_pool_local, "pool", None)
    if pool is None:
        pool = {}
        _conn_pool_local.pool = pool
    conn = pool.get(pool_key)
    if force_new or conn is None:
        if conn is not None:
            conn.close()
        conn = _create_conn(host, port, use_ssl, timeout, ssl_context)
        pool[pool_key] = conn
    return conn


def get_rate_limit_delay() -> float:
    """Return the adaptive delay recorded for the current worker thread."""
    return getattr(_rate_limit_state, "delay", 0.0)


def _bump_rate_limit_delay():
    current = getattr(_rate_limit_state, "delay", 0.0)
    if current == 0.0:
        _rate_limit_state.delay = 3.2
    else:
        _rate_limit_state.delay = min(10.0, current * 1.5)


def _reset_rate_limit_delay():
    _rate_limit_state.delay = 0.0


def abortable_wait(
    seconds: float,
    should_abort: Optional[Callable[[], bool]] = None,
):
    """Wait in short increments so cancellation is observed promptly."""
    deadline = time.monotonic() + max(0.0, seconds)
    while time.monotonic() < deadline:
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        before = time.monotonic()
        time.sleep(min(0.1, deadline - before))
        if time.monotonic() <= before:
            return


def _read_bounded_response(
    resp,
    progress_callback: Optional[Callable[[str], None]],
    should_abort: Optional[Callable[[], bool]],
    conn,
) -> str:
    """Read a response body without allowing an unbounded allocation."""
    raw_length = resp.getheader("Content-Length")
    try:
        content_length = int(raw_length) if raw_length is not None else 0
    except (TypeError, ValueError):
        content_length = 0

    if content_length > _MAX_RESPONSE_BYTES:
        conn.close()
        raise ResponseTooLargeError(
            f"AI response exceeds {_MAX_RESPONSE_BYTES} byte safety limit"
        )

    chunks = []
    total_read = 0
    while True:
        if should_abort and should_abort():
            conn.close()
            raise RuntimeError(t("error_cancelled_by_user"))
        chunk = resp.read(8192)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > _MAX_RESPONSE_BYTES:
            conn.close()
            raise ResponseTooLargeError(
                f"AI response exceeds {_MAX_RESPONSE_BYTES} byte safety limit"
            )
        chunks.append(chunk)
        if (
            progress_callback
            and content_length > 0
            and total_read % 65536 < 8192
        ):
            pct = min(99, total_read * 100 // content_length)
            progress_callback(t("status_receiving_data", percent=pct))

    return b"".join(chunks).decode("utf-8")


def post_json(
    url: str,
    payload: dict,
    headers: dict,
    timeout: int = 300,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    total_timeout: int = 900,
) -> str:
    """POST JSON and return a decoded, size-bounded response body."""
    scheme, host, port, path = _parse_http_url(url)
    use_ssl = scheme == "https"
    ssl_context = _pick_ssl_context(host)

    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))
    deadline = time.monotonic() + total_timeout
    pool_key = f"{scheme}://{host}:{port}|timeout={timeout}"
    conn = _get_thread_conn(pool_key, host, port, use_ssl, timeout, ssl_context)

    body_bytes = json.dumps(payload).encode("utf-8")
    request_headers = dict(headers or {})
    request_headers["Content-Length"] = str(len(body_bytes))

    rate_delay = get_rate_limit_delay()
    if rate_delay > 0:
        if progress_callback:
            progress_callback(t("status_rate_limit_wait", seconds=rate_delay))
        abortable_wait(rate_delay, should_abort)

    last_error = None
    max_retries = 5
    for attempt in range(max_retries + 1):
        try:
            if should_abort and should_abort():
                raise RuntimeError(t("error_cancelled_by_user"))
            if time.monotonic() >= deadline:
                raise RuntimeError(t("error_ai_total_timeout"))
            if attempt > 0:
                conn = _get_thread_conn(
                    pool_key,
                    host,
                    port,
                    use_ssl,
                    timeout,
                    ssl_context,
                    force_new=True,
                )

            conn.request("POST", path, body=body_bytes, headers=request_headers)
            resp = conn.getresponse()

            if resp.status == 429:
                retry_after = resp.getheader("Retry-After")
                err_body = resp.read().decode("utf-8", errors="replace")[:300]
                _bump_rate_limit_delay()
                if retry_after:
                    try:
                        wait = max(0.0, float(retry_after))
                    except ValueError:
                        wait = 30.0
                else:
                    wait = 30.0
                if progress_callback:
                    progress_callback(t("status_rate_limited", seconds=wait))
                abortable_wait(
                    min(wait, max(0.0, deadline - time.monotonic())),
                    should_abort,
                )
                last_error = http.client.HTTPException(
                    f"HTTP 429 Rate Limit: {err_body}"
                )
                continue

            if resp.status >= 400:
                err_body = resp.read().decode("utf-8", errors="replace")[:500]
                raise http.client.HTTPException(
                    f"HTTP {resp.status} {resp.reason}: {err_body}"
                )

            body = _read_bounded_response(
                resp, progress_callback, should_abort, conn
            )
            _reset_rate_limit_delay()
            return body

        except (http.client.HTTPException, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < max_retries:
                delay = 2.0 * (2 ** attempt)
                if progress_callback:
                    progress_callback(
                        t(
                            "status_retrying",
                            attempt=attempt + 1,
                            maximum=max_retries,
                            seconds=delay,
                        )
                    )
                abortable_wait(
                    min(delay, max(0.0, deadline - time.monotonic())),
                    should_abort,
                )
                continue
            raise RuntimeError(
                t(
                    "error_connection_retries",
                    attempts=max_retries + 1,
                    error=last_error,
                )
            )

    raise RuntimeError(t("error_connection", error=last_error))
