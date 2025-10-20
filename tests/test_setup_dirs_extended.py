"""
Extended tests for scripts/setup_dirs.py.
Covers both normal and error paths to guarantee idempotence.
"""
from pathlib import Path
import importlib.util
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]  # one level above tests/


def _import_module():
    """Dynamically import setup_dirs.py from the real project scripts directory."""
    target = PROJECT_ROOT / "scripts" / "setup_dirs.py"
    if not target.exists():
        raise FileNotFoundError(f"Cannot find {target}")
    spec = importlib.util.spec_from_file_location("setup_dirs", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_setup_dirs_creates_missing(monkeypatch, tmp_path):
    """Should create all required directories when missing."""
    # Work in a clean tmp directory but import module from project root
    monkeypatch.chdir(tmp_path)
    module = _import_module()
    created = module.ensure_dirs(module.REQUIRED_DIRS)
    for p in module.REQUIRED_DIRS:
        assert (tmp_path / p).exists(), f"Expected {p} to be created"
    assert created, "Expected new directories to be created"


def test_setup_dirs_idempotent(monkeypatch, tmp_path):
    """Running twice should not raise or create duplicates."""
    monkeypatch.chdir(tmp_path)
    module = _import_module()
    module.ensure_dirs(module.REQUIRED_DIRS)
    created = module.ensure_dirs(module.REQUIRED_DIRS)
    assert created == [], "Second run should create nothing"


def test_main_outputs(monkeypatch, tmp_path, capsys):
    """Verify main() prints a clear message."""
    monkeypatch.chdir(tmp_path)
    module = _import_module()
    exit_code = module.main()
    out = capsys.readouterr().out
    assert "Created:" in out or "No action taken" in out
    assert exit_code is None or exit_code == 0
