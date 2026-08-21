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
ANKI_RANGE = re.compile(
    r"Anki\s+(\d+\.\d+(?:\.\d+)?)\s+(?:through|to)\s+(\d+\.\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _manifest():
    return json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_matches_current_compatibility_matrix():
    manifest = _manifest()
    version = manifest["version"]
    minimum = manifest["anki"]["min_version"]
    maximum = manifest["anki"]["max_version"]
    compatibility = (ROOT / "COMPATIBILITY.md").read_text(encoding="utf-8")

    assert (minimum, maximum) == ("2.1.50", "26.5")
    assert manifest["package"] == "bento_forge"
    assert manifest["human_version"] == version
    assert manifest["min_point_version"] == 50
    assert manifest["max_point_version"] == 260500
    assert manifest["dependencies"]["python"] == ">=3.9"
    assert f"For {version} it declares Anki {minimum} through {maximum}" in compatibility
    assert f"| {minimum} | 3.9 | Legacy compatibility target |" in compatibility
    assert f"| {maximum} | 3.13.5 | Validated compatibility target |" in compatibility


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


def test_unreleased_changelog_uses_dated_version_snapshots():
    """Keep unreleased work attributable to the day and manifest version it used."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = changelog.split("## [V", maxsplit=1)[0]

    assert "cập nhật đến" not in unreleased.lower()
    assert re.search(
        r"^### \d{4}-\d{2}-\d{2} — Phiên bản: `\d+\.\d+\.\d+` → `\d+\.\d+\.\d+`$",
        unreleased,
        re.MULTILINE,
    )
    expected_backfill = {
        "2026-08-15": ("17.1.0", "17.2.0"),
        "2026-08-16": ("17.2.0", "17.2.0"),
        "2026-08-20": ("17.2.0", "18.1.0"),
        "2026-08-21": ("18.1.0", "18.1.0"),
    }
    for day, (opening_version, closing_version) in expected_backfill.items():
        assert (
            f"### {day} — Phiên bản: `{opening_version}` → `{closing_version}`"
            in unreleased
        )


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
        ["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.splitlines()
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", *tracked_python],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
