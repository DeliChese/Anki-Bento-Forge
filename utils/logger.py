"""
📋 Logger Module — Hệ thống logging tập trung cho AnkiTool

Thay thế tất cả print() statements bằng logging.
Log đồng thời ra file và console (Anki debug window).
"""

import logging
import os
import re
import sys
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Singleton logger
_logger: Optional[logging.Logger] = None
_initialized: bool = False

# Đường dẫn file log
_LOG_FILENAME = "anki_tool.log"
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_LOG_BACKUP_COUNT = 3  # Giữ 3 file log cũ

_AUTHORIZATION_RE = re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)\S+")
_API_KEY_FIELD_RE = re.compile(r"(?i)([\"']?api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\s,}\"']+")
_COMMON_SECRET_RE = re.compile(r"\b(?:sk|rk|pk)_[A-Za-z0-9_\-]{8,}\b")
_EVENT_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


def redact_sensitive(value):
    """Mask credentials before any handler can write them to a log sink."""
    if isinstance(value, BaseException):
        # Exception messages can contain remote responses or user-provided input.
        return type(value).__name__
    if isinstance(value, str):
        value = _AUTHORIZATION_RE.sub(r"\1[REDACTED]", value)
        value = _API_KEY_FIELD_RE.sub(r"\1[REDACTED]", value)
        return _COMMON_SECRET_RE.sub("[REDACTED]", value)
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in {"api_key", "authorization"} else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def format_event(code: str, action: str, **context) -> str:
    """Build a privacy-safe, searchable log event.

    ``code`` is a stable, uppercase identifier (for example ``TTS_EDGE_FAILED``).
    Callers should pass only operational metadata such as counts, provider names,
    or exception *types*; never card text, prompts, responses, API keys, or URLs.
    """
    if not _EVENT_CODE_RE.fullmatch(code):
        raise ValueError("Log event code must be an uppercase identifier")
    fields = [f"action={action}"]
    for key in sorted(context):
        fields.append(f"{key}={redact_sensitive(context[key])}")
    return f"{code}: " + "; ".join(fields)


def log_event(code: str, action: str, *, level: int = logging.WARNING, **context) -> None:
    """Emit a standardized event without serializing private learning content."""
    get_logger().log(level, format_event(code, action, **context))


class _SensitiveDataFilter(logging.Filter):
    """Last-line defense for logger calls that accidentally include secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive(record.msg)
        record.args = redact_sensitive(record.args)
        return True


def _get_log_dir() -> str:
    """Return the profile-scoped directory used for diagnostic logs."""
    override = os.environ.get("BENTO_FORGE_DATA_DIR")
    if override:
        directory = Path(override)
    else:
        profile_folder = None
        try:
            from aqt import mw

            profile_manager = getattr(mw, "pm", None)
            profile_path = getattr(profile_manager, "profileFolder", None)
            if callable(profile_path):
                value = profile_path()
                if isinstance(value, str) and value:
                    profile_folder = value
        except Exception:
            profile_folder = None
        directory = (
            Path(profile_folder) / "bento_forge"
            if profile_folder else Path(tempfile.gettempdir()) / f"bento_forge-{os.getpid()}"
        )
    directory = directory / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


def setup_logging(level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True) -> logging.Logger:
    """
    Khởi tạo logger cho toàn bộ add-on.
    Chỉ cần gọi 1 lần khi add-on khởi động.

    Args:
        level: Mức log ("DEBUG", "INFO", "WARNING", "ERROR")
        log_to_file: Ghi log ra file
        log_to_console: Ghi log ra console (Anki stdout)

    Returns:
        Logger instance
    """
    global _logger, _initialized

    if _initialized and _logger is not None:
        return _logger

    _logger = logging.getLogger("AnkiTool")
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    _logger.handlers.clear()
    _logger.filters.clear()
    _logger.addFilter(_SensitiveDataFilter())

    # Format
    fmt = logging.Formatter(
        "[AnkiTool] %(asctime)s [%(levelname)-7s] %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (có rotation)
    if log_to_file:
        try:
            file_handler = RotatingFileHandler(
                os.path.join(_get_log_dir(), _LOG_FILENAME),
                maxBytes=_LOG_MAX_BYTES,
                backupCount=_LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            _logger.addHandler(file_handler)
        except Exception:
            pass  # Fallback: không ghi file cũng được

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        # Format ngắn hơn cho console
        console_fmt = logging.Formatter(
            "[AnkiTool] %(levelname)-7s | %(message)s"
        )
        console_handler.setFormatter(console_fmt)
        _logger.addHandler(console_handler)

    _initialized = True
    _logger.info("Logger initialized (level=%s)", level)
    return _logger


def get_logger() -> logging.Logger:
    """Lấy logger instance. Tự động gọi setup_logging() nếu chưa khởi tạo."""
    global _logger
    if _logger is None:
        return setup_logging()
    return _logger


# Convenience functions
def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """Log error + traceback"""
    get_logger().exception(msg, *args, **kwargs)
