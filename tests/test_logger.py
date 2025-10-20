"""
Unit tests for the logging initialization module.

These tests verify that the logger configuration:
1) Creates the logs/ directory if missing.
2) Loads the config file correctly.
3) Generates a timestamped log file.
4) Writes entries in the expected format.
"""
from pathlib import Path
import re
import logging
from scripts import init_logger


def _write_minimal_config(config_dir: Path):
    """Write a minimal valid logging.conf for isolated tests."""
    text = """[loggers]
keys=root,project

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=fmt

[formatter_fmt]
format=%(asctime)s [%(levelname)s] %(name)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=fmt
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=fmt
args=('logs/project.log', 'a', 'utf-8')

[logger_root]
level=WARNING
handlers=consoleHandler

[logger_project]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=project
propagate=0
"""
    (config_dir / "logging.conf").write_text(text, encoding="utf-8")


def test_log_dir_is_created(tmp_path, monkeypatch):
    """Should create logs/ directory and timestamped log file."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _write_minimal_config(config_dir)

    logger = init_logger.init_logging()
    log_dir = tmp_path / "logs"
    assert log_dir.exists(), "logs directory should be created automatically"
    files = list(log_dir.glob("project_*.log"))
    assert files, "timestamped log file should be created"
    logger.info("Sample info message")
    logger.debug("Sample debug message")


def test_logger_retrieval_returns_child_logger(tmp_path, monkeypatch):
    """get_logger() should return a properly namespaced child logger."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _write_minimal_config(config_dir)

    logger = init_logger.get_logger("submodule")
    assert isinstance(logger, logging.Logger)
    assert logger.name.startswith("project.")


def test_log_format_and_content(tmp_path, monkeypatch):
    """The produced log lines should match expected timestamp + format."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _write_minimal_config(config_dir)

    logger = init_logger.init_logging()
    log_dir = tmp_path / "logs"
    log_file = list(log_dir.glob("project_*.log"))[0]
    logger.info("MessageFormatTest")

    content = log_file.read_text(encoding="utf-8")
    pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\] project - MessageFormatTest"
    assert re.search(pattern, content), f"Log format mismatch in {log_file}"
