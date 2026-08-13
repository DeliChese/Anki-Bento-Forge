"""Release metadata must not overstate the tested compatibility scope."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_manifest_matches_current_compatibility_matrix():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["anki"] == {
        "min_version": "2.1.50",
        "max_version": "2.1.50",
    }
    assert manifest["dependencies"]["python"] == ">=3.9"
    assert (ROOT / "COMPATIBILITY.md").is_file()
