"""
Tests for the environment bootstrap script.

These tests exercise the decision flow without performing side effects by using
the --dry-run flag. They verify user-facing messages and argument handling.
"""
from pathlib import Path
import sys
import types

import importlib.util
import runpy

SCRIPT_PATH = Path("scripts") / "setup_env.py"


def _import_script_module():
    """Dynamically import the setup script as a module to access helpers."""
    spec = importlib.util.spec_from_file_location("setup_env", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader, "Failed to load setup_env.py"
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_script_file_exists():
    assert SCRIPT_PATH.exists(), "scripts/setup_env.py is missing"


def test_dry_run_basic_execution(capsys, monkeypatch, tmp_path):
    """
    Running the script in --dry-run mode should print the planned actions and exit with code 0.
    It should not attempt to create or remove any directories.
    """
    module = _import_script_module()
    venv_dir = tmp_path / ".venv-test"

    # Ensure requirements files exist for the test context.
    # If the repo already has them, keep existing; otherwise create minimal ones.
    rt = Path("requirements.txt")
    rd = Path("requirements-dev.txt")
    created_rt = created_rd = False
    if not rt.exists():
        rt.write_text("pandas\n", encoding="utf-8")
        created_rt = True
    if not rd.exists():
        rd.write_text("pytest\n", encoding="utf-8")
        created_rd = True

    try:
        # Execute main in dry-run mode.
        exit_code = module.main([
            "--venv-path", str(venv_dir),
            "--force-recreate",
            "--dry-run",
        ])
        captured = capsys.readouterr().out

        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
        assert "Dry-run mode: True" in captured
        assert str(venv_dir) in captured
        assert "$ " in captured  # commands echoed
        assert "Environment ready." in captured
        # venv should not really be created in dry-run
        assert not venv_dir.exists(), "venv directory should not be created in dry-run"
    finally:
        if created_rt:
            rt.unlink(missing_ok=True)
        if created_rd:
            rd.unlink(missing_ok=True)


def test_version_check_exposes_clear_error(monkeypatch, capsys):
    """
    Simulate an older Python version to ensure a clear error is emitted.
    """
    module = _import_script_module()

    class FakeVersion:
        major = 3
        minor = 10

        def __lt__(self, other):
            return (self.major, self.minor) < other

    # Patch version_info check path by calling the internal function under a patched sys.version_info
    # We call _check_python_version() directly for a narrowly scoped failure signal.
    monkeypatch.setattr(module.sys, "version_info", (3, 10, 0), raising=True)

    # Call via a wrapper to capture the message
    try:
        module._check_python_version()
        assert False, "Expected SetupError for insufficient Python version"
    except module.SetupError as e:
        msg = str(e)
        assert "Python 3.11+ is required" in msg
