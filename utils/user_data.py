"""Safe, profile-scoped persistence for Bento Forge.

No user-generated data belongs in the add-on directory: Anki can replace that
directory during an update, and running the test suite used to modify it.  This
module keeps data below the active Anki profile and provides the small set of
file operations needed by the add-on without importing ``aqt`` at module load.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Optional

from .logger import get_logger

logger = get_logger()

_DATA_DIR_ENV = "BENTO_FORGE_DATA_DIR"
_DATA_DIR_NAME = "bento_forge"
_MAX_JSON_BYTES = 2 * 1024 * 1024


def get_user_data_dir() -> str:
    """Return Bento Forge's profile-scoped data directory.

    ``BENTO_FORGE_DATA_DIR`` is deliberately supported for isolated tests.
    Outside Anki (for example unit tests), use a process-local temp directory
    rather than silently falling back to the source tree.
    """
    override = os.environ.get(_DATA_DIR_ENV)
    if override:
        path = Path(override)
    else:
        profile_folder = None
        try:
            from aqt import mw  # Imported lazily: utils are testable offline.

            manager = getattr(mw, "pm", None)
            candidate = getattr(manager, "profileFolder", None)
            if callable(candidate):
                value = candidate()
                if isinstance(value, str) and value:
                    profile_folder = value
        except Exception:
            profile_folder = None

        if profile_folder:
            path = Path(profile_folder) / _DATA_DIR_NAME
        else:
            path = Path(tempfile.gettempdir()) / f"{_DATA_DIR_NAME}-{os.getpid()}"

    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_user_data_path(name: str) -> str:
    """Build a path below the Bento Forge data directory.

    Only relative file names are accepted so a caller cannot accidentally
    write outside profile data.
    """
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("User-data path must be relative")
    path = Path(get_user_data_dir()) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def atomic_write_json(path: str, value: Any) -> None:
    """Durably replace a JSON document, leaving no partial file on a crash."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def read_json(
    path: str,
    default: Any,
    validator: Optional[Callable[[Any], bool]] = None,
    *,
    max_bytes: int = _MAX_JSON_BYTES,
) -> Any:
    """Read JSON only when it has the expected shape and a safe size."""
    try:
        if os.path.getsize(path) > max_bytes:
            raise ValueError(f"file exceeds {max_bytes} byte limit")
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        if validator is not None and not validator(value):
            raise ValueError("JSON schema validation failed")
        return value
    except FileNotFoundError:
        return default
    except Exception as error:
        logger.warning("Ignoring invalid Bento Forge data file %s: %s", path, error)
        return default


def migrate_legacy_json(
    legacy_path: str,
    destination_path: str,
    validator: Optional[Callable[[Any], bool]] = None,
) -> bool:
    """Migrate one legacy add-on-local JSON file exactly once.

    A copy of the validated legacy document is retained beside the new file as
    ``.legacy-backup`` before the original is removed.  The backup makes the
    migration recoverable while avoiding user data in an updateable add-on
    directory.
    """
    if os.path.exists(destination_path) or not os.path.exists(legacy_path):
        return False
    data = read_json(legacy_path, None, validator)
    if data is None:
        logger.warning("Legacy data was not migrated because it is invalid: %s", legacy_path)
        return False

    backup_path = destination_path + ".legacy-backup"
    try:
        atomic_write_json(backup_path, data)
        atomic_write_json(destination_path, data)
        os.unlink(legacy_path)
        logger.info("Migrated Bento Forge user data from legacy path")
        return True
    except Exception as error:
        logger.warning("Could not migrate legacy Bento Forge data %s: %s", legacy_path, error)
        return False


def rollback_migration(destination_path: str) -> bool:
    """Restore a migration backup to its profile-data destination for recovery."""
    backup_path = destination_path + ".legacy-backup"
    data = read_json(backup_path, None)
    if data is None:
        return False
    try:
        atomic_write_json(destination_path, data)
        return True
    except Exception as error:
        logger.warning("Could not restore Bento Forge migration backup %s: %s", backup_path, error)
        return False


def migrate_legacy_directory(legacy_path: str, destination_path: str) -> bool:
    """Move a legacy cache directory into profile data when no target exists."""
    if os.path.exists(destination_path) or not os.path.isdir(legacy_path):
        return False
    try:
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(legacy_path, destination_path)
        logger.info("Migrated Bento Forge cache directory from legacy path")
        return True
    except Exception as error:
        logger.warning("Could not migrate legacy Bento Forge cache directory %s: %s", legacy_path, error)
        return False


def prune_cache_dir(path: str, *, max_age_seconds: int, max_bytes: int, max_files: int) -> None:
    """Bound cache lifetime and size, deleting expired entries before oldest ones."""
    directory = Path(path)
    if not directory.exists():
        return
    now = time.time()
    files = []
    for item in directory.iterdir():
        if not item.is_file():
            continue
        try:
            stat = item.stat()
            if now - stat.st_mtime > max_age_seconds:
                item.unlink()
            else:
                files.append((item, stat.st_mtime, stat.st_size))
        except OSError:
            continue

    total = sum(size for _, _, size in files)
    remaining = len(files)
    for item, _, size in sorted(files, key=lambda entry: entry[1]):
        if remaining <= max_files and total <= max_bytes:
            break
        try:
            item.unlink()
            total -= size
            remaining -= 1
        except OSError:
            continue


def clear_cache_dir(path: str) -> None:
    """Remove a cache directory only; persistent profile data is untouched."""
    if os.path.isdir(path):
        shutil.rmtree(path)
