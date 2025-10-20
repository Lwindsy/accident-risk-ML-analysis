"""
Additional tests for scripts/init_logger.py to verify failure cases and format consistency.
"""
import pytest
from pathlib import Path
import importlib.util


def _import_logger():
    spec = importlib.util.spec_from_file_location("init_logger", "scripts/init_logger.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_missing_config_raises(tmp_path, monkeypatch):
    """If config/logging.conf is missing, init_logging() should raise FileNotFoundError."""
    module = _import_logger()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    with pytest.raises(FileNotFoundError):
        module.init_logging()


def test_timestamped_file_naming(monkeypatch, tmp_path):
    """Ensure timestamped log files follow naming convention."""
    module = _import_logger()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    file = module.get_timestamped_logfile()
    name = file.name
    assert name.startswith("project_") and name.endswith(".log")


def test_get_logger_auto_initializes(monkeypatch, tmp_path):
    """get_logger() should initialize logging when no handlers exist."""
    module = _import_logger()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "logs").mkdir()
    conf = tmp_path / "config" / "logging.conf"
    conf.write_text(
        "[loggers]\nkeys=root,project\n[handlers]\nkeys=consoleHandler\n"
        "[formatters]\nkeys=f\n[formatter_f]\nformat=%(message)s\n"
        "[handler_consoleHandler]\nclass=StreamHandler\nlevel=INFO\nformatter=f\nargs=(sys.stdout,)\n"
        "[logger_root]\nlevel=WARNING\nhandlers=consoleHandler\n"
        "[logger_project]\nlevel=DEBUG\nhandlers=consoleHandler\nqualname=project\npropagate=0\n",
        encoding="utf-8",
    )
    logger = module.get_logger("test")
    assert logger.name == "project.test"
