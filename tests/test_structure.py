"""
Tests that validate the repository's canonical structure for Phase 3.1.

These checks are purposely simple. They ensure the presence of directories
required by later steps (logger config, reports, standardized data, etc.).
"""
from pathlib import Path

REQUIRED_DIRS = [
    "data",
    "data/raw",
    "data/clean",
    "data/processed",
    "data/standardized",
    "docs",
    "scripts",
    "tests",
    "notebooks",
    "reports",
    "logs",
    "tmp",
    "config",
]

def test_required_directories_exist():
    root = Path(".")
    missing = [d for d in REQUIRED_DIRS if not (root / d).exists()]
    assert not missing, f"Missing directories: {missing}. Run: python scripts/setup_dirs.py"
