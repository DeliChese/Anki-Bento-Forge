"""API-key storage backed by the operating system credential store.

The optional ``keyring`` package is deliberately never installed at runtime.
Without a working credential backend, Bento Forge refuses to persist an API key
instead of disguising reversible obfuscation as encryption.
"""

from __future__ import annotations

import hashlib
from typing import Dict, Optional

from .logger import get_logger
from .user_data import get_user_data_dir

logger = get_logger()

_SERVICE_NAME = "Bento Forge"
_KEYRING_REQUIREMENT = "keyring==25.6.0"


def get_secret_store_install_command() -> str:
    """Return the explicit, pinned installation command for the optional backend."""
    return f"python -m pip install {_KEYRING_REQUIREMENT}"


def _account_name(provider: Optional[str] = None) -> str:
    """Keep credentials isolated by profile and provider without exposing either."""
    fingerprint = hashlib.sha256(get_user_data_dir().encode("utf-8")).hexdigest()
    account = f"api-key:{fingerprint[:24]}"
    # ``None`` deliberately retains the pre-V17.2 account name for one-time
    # migration. Every newly saved credential always gets a provider suffix.
    if provider is not None:
        provider_fingerprint = hashlib.sha256(str(provider).encode("utf-8")).hexdigest()
        account += f":{provider_fingerprint[:20]}"
    return account


def _get_keyring():
    try:
        import keyring

        backend = keyring.get_keyring()
        if backend.__class__.__module__.startswith("keyring.backends.fail"):
            return None
        return keyring
    except Exception:
        return None


def get_secret_store_status() -> Dict[str, object]:
    """Describe whether this environment can safely persist API keys."""
    keyring = _get_keyring()
    return {
        "available": keyring is not None,
        "install_command": get_secret_store_install_command(),
    }


def load_api_key(provider: Optional[str] = None) -> Optional[str]:
    """Read one profile/provider API key, returning ``None`` on safe failure."""
    keyring = _get_keyring()
    if keyring is None:
        return None
    try:
        return keyring.get_password(_SERVICE_NAME, _account_name(provider)) or ""
    except Exception:
        logger.warning("OS credential store could not read the Bento Forge API key")
        return None


def save_api_key(api_key: str, provider: Optional[str] = None) -> bool:
    """Persist one provider API key only through the OS credential store."""
    keyring = _get_keyring()
    if keyring is None:
        logger.warning("No OS credential store is available; API key was not persisted")
        return False
    try:
        keyring.set_password(_SERVICE_NAME, _account_name(provider), api_key)
        return True
    except Exception:
        logger.warning("OS credential store could not save the Bento Forge API key")
        return False


def delete_api_key(provider: Optional[str] = None) -> bool:
    """Delete one provider key; an absent key is already a success."""
    keyring = _get_keyring()
    if keyring is None:
        return False
    try:
        keyring.delete_password(_SERVICE_NAME, _account_name(provider))
    except Exception:
        # Keyring backends do not share a portable "not found" exception type.
        return True
    return True
