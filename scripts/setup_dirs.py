#!/usr/bin/env python3
"""
Create or verify the canonical directory structure for the project.

This script is intentionally idempotent: running it multiple times is safe.
It does not delete or rename any existing path to avoid breaking earlier phases.
"""
from pathlib import Path

# Root is the current working directory where the repository is checked out.
ROOT = Path(".")

# Directories that should exist by convention.
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

def ensure_dirs(paths):
    created = []
    for p in paths:
        path = ROOT / p
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    return created

def main():
    created = ensure_dirs(REQUIRED_DIRS)
    if created:
        print("Created:", *created, sep="\n - ")
    else:
        print("All required directories already exist. No action taken.")

if __name__ == "__main__":
    main()
