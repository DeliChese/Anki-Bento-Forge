"""Regression tests for the release artifact built by build_addon.ps1."""

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
    assert packaged_manifest["package"] == "bento_forge_test"
    assert packaged_manifest["min_point_version"] == 50
    assert packaged_manifest["max_point_version"] == 260500
    assert cache_sentinel.is_file()
    assert loose_bytecode.is_file()
    assert optimized_bytecode.is_file()
