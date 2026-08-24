"""Pure checks for the local MeloTTS bridge; no Anki or model download required."""

import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def _load_melo_module():
    spec = importlib.util.spec_from_file_location("bento_melo_local", _ROOT / "audio" / "melo.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_rate_to_speed_is_bounded_and_tolerates_invalid_rates():
    melo = _load_melo_module()

    assert melo._rate_to_speed("+25%") == 1.25
    assert melo._rate_to_speed("-50%") == 0.5
    assert melo._rate_to_speed("+900%") == 4.0
    assert melo._rate_to_speed("not-a-rate") == 1.0


def test_melo_runtime_is_only_available_with_python_and_service(tmp_path, monkeypatch):
    melo = _load_melo_module()
    python = tmp_path / "python.exe"
    service = tmp_path / "melo_service.py"
    monkeypatch.setattr(melo, "_runtime_python", lambda: str(python))
    monkeypatch.setattr(melo, "_service_script", lambda: str(service))

    assert melo.is_melo_available() is False
    python.touch()
    service.touch()
    assert melo.is_melo_available() is True
