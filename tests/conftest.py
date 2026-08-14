"""Profile-scoped temporary paths that remain usable in restricted Windows runs."""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def _bento_test_temp_root():
    configured_root = os.environ.get("BENTO_FORGE_TEST_TMP")
    if configured_root:
        root = Path(configured_root)
    else:
        root = Path(tempfile.gettempdir()) / f"bento-forge-pytest-{uuid.uuid4().hex}"

    # pathlib's normal directory mode stays accessible in the restricted Windows
    # sandbox where pytest/tempfile 0o700 directories can become unreadable.
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        if root.exists():
            shutil.rmtree(root)
        if root.exists():
            raise AssertionError(f"Test temp root was not removed: {root}")


@pytest.fixture
def tmp_path(_bento_test_temp_root):
    """Return an isolated path without relying on pytest's tmpdir plugin."""
    path = _bento_test_temp_root / uuid.uuid4().hex
    path.mkdir()
    try:
        yield path
    finally:
        if path.exists():
            shutil.rmtree(path)

