"""API-key storage backed by the operating system credential store.

The optional ``keyring`` package is deliberately never installed at runtime.
Without a working credential backend, Bento Forge refuses to persist an API key
instead of disguising reversible obfuscation as encryption.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
from ctypes import wintypes
from typing import Dict, Optional

from .logger import get_logger
from .user_data import get_user_data_dir

logger = get_logger()

_SERVICE_NAME = "Bento Forge"
_KEYRING_REQUIREMENT = "keyring==25.6.0"
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168


class _CredentialAttributeW(ctypes.Structure):
    pass


class _CredentialW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CredentialAttributeW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class _WindowsCredentialStore:
    """Small dependency-free adapter for Windows Credential Manager.

    Targets match python-keyring's Windows backend, so an API key remains
    readable if an Anki update removes the optional keyring package.
    """

    def __init__(self):
        self._api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._api.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(_CredentialW)),
        ]
        self._api.CredReadW.restype = wintypes.BOOL
        self._api.CredWriteW.argtypes = [ctypes.POINTER(_CredentialW), wintypes.DWORD]
        self._api.CredWriteW.restype = wintypes.BOOL
        self._api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._api.CredDeleteW.restype = wintypes.BOOL
        self._api.CredFree.argtypes = [ctypes.c_void_p]
        self._api.CredFree.restype = None

    @staticmethod
    def _compound_name(username: str, service: str) -> str:
        return f"{username}@{service}"

    def _read(self, target: str) -> Optional[Dict[str, str]]:
        pointer = ctypes.POINTER(_CredentialW)()
        if not self._api.CredReadW(
            target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            error = ctypes.get_last_error()
            if error == _ERROR_NOT_FOUND:
                return None
            raise OSError(error, "Windows Credential Manager read failed")
        try:
            credential = pointer.contents
            blob = ctypes.string_at(
                credential.CredentialBlob, credential.CredentialBlobSize
            )
            try:
                password = blob.decode("utf-16-le")
            except UnicodeDecodeError:
                # python-keyring historically accepted UTF-8 credentials too.
                password = blob.decode("utf-8")
            return {
                "username": credential.UserName or "",
                "password": password,
            }
        finally:
            self._api.CredFree(pointer)

    def _write(self, target: str, username: str, password: str) -> None:
        encoded = str(password).encode("utf-16-le")
        blob = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
        credential = _CredentialW()
        credential.Type = _CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.Comment = "Stored by Bento Forge"
        credential.CredentialBlobSize = len(encoded)
        credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = username
        if not self._api.CredWriteW(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()
            raise OSError(error, "Windows Credential Manager write failed")

    def _delete(self, target: str) -> None:
        if self._api.CredDeleteW(target, _CRED_TYPE_GENERIC, 0):
            return
        error = ctypes.get_last_error()
        if error != _ERROR_NOT_FOUND:
            raise OSError(error, "Windows Credential Manager delete failed")

    def get_password(self, service: str, username: str) -> Optional[str]:
        credential = self._read(service)
        if credential and credential["username"] == username:
            return credential["password"]
        credential = self._read(self._compound_name(username, service))
        if credential and credential["username"] == username:
            return credential["password"]
        return None

    def set_password(self, service: str, username: str, password: str) -> None:
        existing = self._read(service)
        if existing and existing["username"] != username:
            self._write(
                self._compound_name(existing["username"], service),
                existing["username"],
                existing["password"],
            )
        self._write(service, username, password)

    def delete_password(self, service: str, username: str) -> None:
        existing = self._read(service)
        if existing and existing["username"] == username:
            self._delete(service)
        self._delete(self._compound_name(username, service))


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


def _get_windows_credential_store():
    if os.name != "nt":
        return None
    try:
        return _WindowsCredentialStore()
    except Exception:
        return None


def _get_secret_store():
    """Prefer the OS-native backend, then the optional cross-platform package."""
    return _get_windows_credential_store() or _get_keyring()


def get_secret_store_status() -> Dict[str, object]:
    """Describe whether this environment can safely persist API keys."""
    store = _get_secret_store()
    return {
        "available": store is not None,
        "install_command": get_secret_store_install_command(),
    }


def load_api_key(provider: Optional[str] = None) -> Optional[str]:
    """Read one profile/provider API key, returning ``None`` on safe failure."""
    store = _get_secret_store()
    if store is None:
        return None
    try:
        return store.get_password(_SERVICE_NAME, _account_name(provider)) or ""
    except Exception:
        logger.warning("OS credential store could not read the Bento Forge API key")
        return None


def save_api_key(api_key: str, provider: Optional[str] = None) -> bool:
    """Persist one provider API key only through the OS credential store."""
    store = _get_secret_store()
    if store is None:
        logger.warning("No OS credential store is available; API key was not persisted")
        return False
    try:
        store.set_password(_SERVICE_NAME, _account_name(provider), api_key)
        return True
    except Exception:
        logger.warning("OS credential store could not save the Bento Forge API key")
        return False


def delete_api_key(provider: Optional[str] = None) -> bool:
    """Delete one provider key; an absent key is already a success."""
    store = _get_secret_store()
    if store is None:
        return False
    try:
        store.delete_password(_SERVICE_NAME, _account_name(provider))
    except Exception:
        # Keyring backends do not share a portable "not found" exception type.
        return True
    return True
