#!/usr/bin/env python3
"""
Initialize the unified logging configuration for the project.

The logging configuration is read from config/logging.conf and dynamically
adjusted to create the log file under logs/ with the current timestamp.
This ensures reproducible file naming and traceable runtime diagnostics.

Key design points:
- English-only output for uniform logs across teams.
- The log file path is auto-created if missing.
- All modules should import `get_logger(__name__)` instead of using root loggers.
"""

import logging
import logging.config
from pathlib import Path
from datetime import datetime


CONFIG_PATH = Path("config/logging.conf")
LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = LOG_DIR / "project.log"


def ensure_log_dir() -> None:
    """Create the logs directory if it does not exist."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_timestamped_logfile() -> Path:
    """Generate a timestamped log file name under logs/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"project_{timestamp}.log"


def init_logging() -> logging.Logger:
    """
    Initialize logging configuration from file.
    Returns a preconfigured 'project' logger ready for use.
    """
    ensure_log_dir()

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Logging configuration not found: {CONFIG_PATH}")

    # Create a copy of the configuration file to override file path dynamically
    from configparser import ConfigParser
    parser = ConfigParser()
    parser.read(CONFIG_PATH, encoding="utf-8")

    # Override file path argument for the file handler
    new_log_path = get_timestamped_logfile()
    parser.set("handler_fileHandler", "args", f"('{new_log_path}', 'a', 'utf-8')")

    # Write to a temporary config in memory
    import io
    temp = io.StringIO()
    parser.write(temp)
    temp.seek(0)

    # Apply configuration
    logging.config.fileConfig(temp)
    logger = logging.getLogger("project")
    logger.debug("Logging initialized successfully.")
    logger.debug(f"Active log file: {new_log_path}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a child logger with the given name.
    Automatically initializes logging if not configured yet.
    """
    if not logging.getLogger().handlers:
        init_logging()
    return logging.getLogger(f"project.{name}")


if __name__ == "__main__":
    # Manual run: verify log creation and output format
    logger = init_logging()
    logger.info("Logger initialized.")
    logger.debug("Debug message for verification.")
    print(f"Active log file written to: {DEFAULT_LOG_FILE.parent.resolve()}")
