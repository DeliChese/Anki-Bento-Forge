"""HTTP transport for OpenAI-compatible AI providers.

This module owns only network concerns: TLS policy, per-thread connection reuse,
rate-limit backoff, retry, cancellation, and bounded response reads.  It must
remain independent from Anki/Qt, user configuration, prompts, and AI response
parsing so callers can use and test it outside the Anki runtime.
"""

import http.client
import json
import ssl
import threading
import time
from typing import Callable, Optional
from urllib.parse import urlparse


# Cloud providers use normal certificate verification.  The relaxed context is
# limited to loopback hosts used by local Ollama/LM Studio installations.
_SSL_CONTEXT_SECURE = ssl.create_default_context()
_SSL_CONTEXT_LOCAL = ssl.create_default_context()
_SSL_CONTEXT_LOCAL.check_hostname = False
_SSL_CONTEXT_LOCAL.verify_mode = ssl.CERT_NONE

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_OPENROUTER_MARKERS = ("openrouter.ai", "openrouter")


def is_openrouter(api_base: str) -> bool:
    """Return whether *api_base* points at an OpenRouter-compatible endpoint."""
    base = (api_base or "").lower()
    return any(marker in base for marker in _OPENROUTER_MARKERS)


def _pick_ssl_context(host: str) -> ssl.SSLContext:
    """Disable certificate verification only for an explicit loopback host."""
    if (host or "").lower() in _LOCAL_HOSTS:
        return _SSL_CONTEXT_LOCAL
    return _SSL_CONTEXT_SECURE


# Connections and adaptive delay are thread-local: callers may run concurrent
# AI tasks without sharing a non-thread-safe HTTPConnection or throttling state.
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
            raise RuntimeError("⏹ Đã hủy bởi người dùng")
        before = time.monotonic()
        time.sleep(min(0.1, deadline - before))
        # Test doubles may replace sleep() with a no-op. Avoid spinning for the
        # real-time duration when the monotonic clock does not advance.
        if time.monotonic() <= before:
            return


def post_json(
    url: str,
    payload: dict,
    headers: dict,
    timeout: int = 300,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
    total_timeout: int = 900,
) -> str:
    """POST JSON and return a decoded response body.

    The transport reuses one HTTP/1.1 connection per worker thread, streams the
    response in chunks, retries transient connection failures, and treats HTTP
    429 with its Retry-After value plus adaptive per-thread throttling.
    """
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path + ("?" + parsed.query if parsed.query else "")
    use_ssl = parsed.scheme == "https"
    ssl_context = _pick_ssl_context(host)

    if should_abort and should_abort():
        raise RuntimeError("⏹ Đã hủy bởi người dùng")
    deadline = time.monotonic() + total_timeout
    pool_key = f"{host}:{port}"
    conn = _get_thread_conn(pool_key, host, port, use_ssl, timeout, ssl_context)

    body_bytes = json.dumps(payload).encode("utf-8")
    headers["Content-Length"] = str(len(body_bytes))

    rate_delay = get_rate_limit_delay()
    if rate_delay > 0:
        if progress_callback:
            progress_callback(f"⏳ Đang chờ {rate_delay:.1f}s (tránh rate limit)...")
        abortable_wait(rate_delay, should_abort)

    last_error = None
    max_retries = 5
    for attempt in range(max_retries + 1):
        try:
            if should_abort and should_abort():
                raise RuntimeError("⏹ Đã hủy bởi người dùng")
            if time.monotonic() >= deadline:
                raise RuntimeError("⏱ Đã hết thời gian chờ tổng cho yêu cầu AI")
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

            conn.request("POST", path, body=body_bytes, headers=headers)
            resp = conn.getresponse()

            if resp.status == 429:
                retry_after = resp.getheader("Retry-After")
                err_body = resp.read().decode("utf-8", errors="replace")[:300]
                _bump_rate_limit_delay()
                if retry_after:
                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = 30.0
                else:
                    wait = 30.0
                if progress_callback:
                    progress_callback(
                        f"⚠️ Rate limit (429) — chờ {wait:.0f}s rồi thử lại...\n"
                        "💡 OpenRouter free giới hạn ~20 req/phút. Đang tự chậm lại."
                    )
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

            chunks = []
            total_read = 0
            content_length = int(resp.getheader("Content-Length", 0))
            while True:
                if should_abort and should_abort():
                    conn.close()
                    raise RuntimeError("⏹ Đã hủy bởi người dùng")
                chunk = resp.read(8192)
                if not chunk:
                    break
                chunks.append(chunk)
                total_read += len(chunk)
                if (
                    progress_callback
                    and content_length > 0
                    and total_read % 65536 < 8192
                ):
                    pct = min(99, total_read * 100 // content_length)
                    progress_callback(f"⏳ Đang nhận dữ liệu... {pct}%")

            body = b"".join(chunks).decode("utf-8")
            _reset_rate_limit_delay()
            return body

        except (http.client.HTTPException, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < max_retries:
                delay = 2.0 * (2 ** attempt)
                if progress_callback:
                    progress_callback(
                        f"🔄 Retry {attempt + 1}/{max_retries} sau {delay:.0f}s..."
                    )
                abortable_wait(
                    min(delay, max(0.0, deadline - time.monotonic())),
                    should_abort,
                )
                continue
            raise RuntimeError(
                f"❌ Lỗi kết nối sau {max_retries + 1} lần thử: {last_error}"
            )

    raise RuntimeError(f"❌ Không thể kết nối: {last_error}")
