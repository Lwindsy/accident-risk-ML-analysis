# Accident Risk Prediction — Engineering Environment Setup (Phase 3)

This repository follows a frozen data contract (Phase 2.5) and prepares an engineering environment in Phase 3.
The goal is to let any new contributor reproduce a minimal path in **≤ 10 minutes**.

## What Phase 3.1 Adds
- Canonical structure validation (directories and ignore rules).
- A small idempotent script to create missing folders.
- A basic test to assert the structure is present.

## Directories (should exist)
- `data/` (with subfolders: `raw/`, `clean/`, `processed/`, `standardized/`)
- `docs/`
- `scripts/`
- `tests/`
- `notebooks/`
- `reports/`
- `logs/`
- `tmp/`
- `config/` (for `logging.conf` in 3.4)

> Nothing is removed or renamed; this preserves Phase 1 → 2.5 artifacts.

## Quick Start
```bash
# 1) Ensure Python 3.11+ is available
python --version

# 2) Apply Phase 3.1 structure (idempotent)
python scripts/setup_dirs.py

# 3) Run structure checks
pytest -q tests/test_structure.py
```

## Notes
- All comments in code are written for human reviewers, not for an AI tool. There are no "phase X" markers inside code.
- End-user facing strings are in English.
- No PII or license-sensitive data is included here.
