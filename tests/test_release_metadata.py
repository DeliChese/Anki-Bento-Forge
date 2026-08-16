"""Release metadata must derive compatibility and status from evidence."""

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RELEASE_DOCS = (
    "README.md",
    "COMPATIBILITY.md",
    "CHANGELOG.md",
    "RELEASE_CHECKLIST.md",
    "REFACTOR_PLAN.md",
)
ANKI_RANGE = re.compile(r"(?<!\d)(2\.\d+\.\d+)\s*[–—-]\s*(2\.\d+\.\d+)(?!\d)")


def _manifest():
    return json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_matches_current_compatibility_matrix():
    manifest = _manifest()
    version = manifest["version"]
    minimum = manifest["anki"]["min_version"]
    maximum = manifest["anki"]["max_version"]
    compatibility = (ROOT / "COMPATIBILITY.md").read_text(encoding="utf-8")

    assert minimum == maximum
    assert manifest["dependencies"]["python"] == ">=3.9"
    assert f"For {version} it declares exactly Anki {minimum}" in compatibility
    supported_rows = [
        line for line in compatibility.splitlines() if "Supported release target" in line
    ]
    assert len(supported_rows) == 1
    assert supported_rows[0].startswith(
        f"| {minimum} | 3.9 | Supported release target |"
    )


def test_release_docs_do_not_claim_a_conflicting_anki_range():
    manifest = _manifest()
    expected = (manifest["anki"]["min_version"], manifest["anki"]["max_version"])

    for relative_path in RELEASE_DOCS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for claimed_range in ANKI_RANGE.findall(text):
            assert claimed_range == expected, (
                f"{relative_path} claims Anki range {claimed_range}; manifest declares {expected}"
            )


def test_current_version_is_not_recorded_as_released_without_ci_and_smoke():
    version = _manifest()["version"]
    checklist = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    record = next(line for line in checklist.splitlines() if line.startswith(f"| {version} |"))
    cells = [cell.strip() for cell in record.strip("|").split("|")]

    assert cells[1] in {"Chưa phát hành", "Chưa phát hành lại"}
    assert cells[2] != "Đạt" or cells[3] != "Đạt"
    assert cells[4] == "—"
    assert f"## [V{version}]" not in changelog


def test_ci_uses_the_same_two_round_isolated_harness():
    harness = (ROOT / "scripts" / "test_isolated.ps1").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "foreach ($round in 1..2)" in harness
    assert "BENTO_FORGE_TEST_TMP" in harness
    assert "Remove-Item -LiteralPath $runRoot -Recurse -Force -ErrorAction Stop" in harness
    assert "./scripts/test_isolated.ps1 -Python python" in workflow


def test_every_tracked_python_file_compiles():
    """Keep auxiliary scripts inside the syntax gate, not just add-on modules."""
    tracked_python = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", *tracked_python],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
