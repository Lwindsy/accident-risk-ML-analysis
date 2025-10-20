"""
Extended tests for scripts/setup_env.py.
Simulate failure cases and dry-run logic without touching the real environment.
"""
from pathlib import Path
import importlib.util
import sys


def _import_setup_env():
    spec = importlib.util.spec_from_file_location("setup_env", "scripts/setup_env.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_version_check_fails(monkeypatch):
    """If Python version is below required, should raise SetupError."""
    module = _import_setup_env()
    monkeypatch.setattr(module.sys, "version_info", (3, 10, 0))
    try:
        module._check_python_version()
    except module.SetupError as e:
        assert "Python 3.11+" in str(e)
    else:
        raise AssertionError("Expected SetupError due to old Python version")


def test_missing_requirements_raises(tmp_path, monkeypatch):
    """Missing requirements.txt should raise SetupError."""
    module = _import_setup_env()
    venv_dir = tmp_path / ".venv"
    monkeypatch.chdir(tmp_path)
    try:
        module._install_requirements(
            venv_path=venv_dir,
            req_runtime=Path("requirements.txt"),
            req_dev=Path("requirements-dev.txt"),
            include_dev=False,
            dry_run=True,
        )
    except module.SetupError as e:
        assert "Missing requirements file" in str(e)
    else:
        raise AssertionError("Expected SetupError for missing requirements")


def test_create_or_reuse_dry_run(monkeypatch, tmp_path, capsys):
    """Dry-run creation should only echo commands, not create directories."""
    module = _import_setup_env()
    venv_dir = tmp_path / ".venv"
    module._create_or_reuse_venv(venv_dir, force_recreate=False, dry_run=True)
    out = capsys.readouterr().out
    assert "$ " in out and "Creating virtual environment" in out


def test_full_main_dry_run(tmp_path, monkeypatch, capsys):
    """Full dry-run main() should complete successfully."""
    module = _import_setup_env()
    rt = tmp_path / "requirements.txt"
    rd = tmp_path / "requirements-dev.txt"
    rt.write_text("numpy\n")
    rd.write_text("pytest\n")
    monkeypatch.chdir(tmp_path)
    code = module.main(["--dry-run", "--venv-path", ".venv"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Dry-run mode: True" in out
    assert "Environment ready." in out
