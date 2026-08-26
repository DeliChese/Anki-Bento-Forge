"""Regression tests for the release artifact built by build_addon.ps1."""

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIRECTORIES = ("Language", "audio", "hooks", "mode", "ui", "workers")


def test_build_artifact_includes_workers_and_excludes_python_bytecode(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "dist"
    source.mkdir()

    for directory in PACKAGE_DIRECTORIES + ("utils",):
        package = source / directory
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
    (source / "workers" / "import_worker.py").write_text("", encoding="utf-8")

    (source / "__init__.py").write_text("", encoding="utf-8")
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "name": "Bento Forge package test",
                "package": "bento_forge_test",
                "version": "0.0.0",
                "human_version": "0.0.0",
                "min_point_version": 50,
                "max_point_version": 260500,
                "dependencies": {"packages": []},
            }
        ),
        encoding="utf-8",
    )

    cache_sentinel = source / "workers" / "__pycache__" / "worker.cpython-311.pyc"
    cache_sentinel.parent.mkdir()
    cache_sentinel.write_bytes(b"cached worker bytecode")
    loose_bytecode = source / "ui" / "legacy.pyc"
    loose_bytecode.write_bytes(b"loose bytecode")
    optimized_bytecode = source / "mode" / "legacy.pyo"
    optimized_bytecode.write_bytes(b"legacy optimized bytecode")
    local_state_files = (
        source / "utils" / "ai_config.json",
        source / "utils" / "ai_prompts.json",
        source / "utils" / "factory_state.json",
        source / "utils" / "import_history.json",
        source / "ui" / "debug.log",
    )
    for local_state in local_state_files:
        local_state.write_text("local-only", encoding="utf-8")
    (source / "utils" / "ai_config.example.json").write_text(
        '{"provider": "example"}', encoding="utf-8",
    )
    (source / "utils" / "ui_theme.json").write_text(
        '{"preset": "default"}', encoding="utf-8",
    )

    powershell = shutil.which("pwsh") or shutil.which("powershell")
    assert powershell is not None, "PowerShell is required to verify the package artifact"
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-File",
            str(ROOT / "scripts" / "build_addon.ps1"),
            "-OutputDirectory",
            str(output),
            "-SourceDirectory",
            str(source),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    artifact = output / "bento-forge.ankiaddon"
    assert artifact.is_file()
    with zipfile.ZipFile(artifact) as archive:
        members = {
            PurePosixPath(name.replace("\\", "/")) for name in archive.namelist()
        }
        packaged_manifest = json.loads(archive.read("manifest.json"))

    assert PurePosixPath("workers/__init__.py") in members
    assert PurePosixPath("workers/import_worker.py") in members
    assert all("__pycache__" not in member.parts for member in members)
    assert all(member.suffix.lower() not in {".pyc", ".pyo"} for member in members)
    assert PurePosixPath("utils/ai_config.example.json") in members
    assert PurePosixPath("utils/ui_theme.json") in members
    assert all(
        PurePosixPath(path.relative_to(source).as_posix()) not in members
        for path in local_state_files
    )
    assert packaged_manifest["package"] == "bento_forge_test"
    assert packaged_manifest["min_point_version"] == 50
    assert packaged_manifest["max_point_version"] == 260500
    expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert (output / "bento-forge.ankiaddon.sha256").read_text(encoding="utf-8") == (
        f"{expected_hash}  bento-forge.ankiaddon"
    )
    sbom = json.loads((output / "bento-forge.sbom.json").read_text(encoding="utf-8-sig"))
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["component"] == {
        "type": "application",
        "name": "Bento Forge package test",
        "version": "0.0.0",
    }
    assert sbom["components"] == []
    assert cache_sentinel.is_file()
    assert loose_bytecode.is_file()
    assert optimized_bytecode.is_file()
    assert all(path.is_file() for path in local_state_files)
