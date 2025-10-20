
# Engineering Environment Setup Guide — Accident Risk Prediction

**Goal:** Enable any new contributor to reproduce and validate a working environment within **10 minutes**.

---

## 1. Prerequisites

- **Python:** 3.11 or newer
- **Git:** Installed and configured with access to the repository
- **Operating System:** Linux, macOS, or Windows (WSL2 recommended)
- **Internet Connection:** Required for dependency installation

Check Python version:
```bash
python3 --version
```

---

## 2. Repository Structure Overview

```
accident-risk/
├── config/                # Configuration files (e.g., logging.conf)
├── data/                  # Data directories: raw/, clean/, processed/, standardized/
├── docs/                  # Documentation
├── logs/                  # Log outputs (auto-created)
├── notebooks/             # Jupyter notebooks (optional exploratory work)
├── reports/               # Generated analytical reports
├── scripts/               # Project scripts (setup, logging, validation)
│   ├── setup_dirs.py
│   ├── setup_env.py
│   ├── init_logger.py
│   └── verify_reproducibility.py
├── tests/                 # All pytest test cases
└── Makefile               # One-line automation targets
```

---

## 3. Quick Setup (≤10 Minutes)

### Step 1 — Clone the repository

```bash
git clone <your_repo_url> accident-risk
cd accident-risk
```

### Step 2 — Verify structure (idempotent check)

```bash
make setup-structure
```

### Step 3 — Create or reuse virtual environment

```bash
make setup
```

This automatically:
- Creates `.venv/` if missing
- Installs all dependencies from `requirements.txt` and `requirements-dev.txt`
- Upgrades `pip`, `setuptools`, and `wheel`

### Step 4 — Validate environment setup

```bash
make test
```

Expected output:
```
... [100%]
0 failed
```

### Step 5 — Initialize logging (optional check)

```bash
make init-logger
```
A timestamped log file (e.g., `logs/project_20251020_123000.log`) will be created.

---

## 4. Reproducibility Verification

You can verify the entire setup and test process fits within the **10-minute rule**:

```bash
python scripts/verify_reproducibility.py --force-recreate
```

Expected behavior:
- Creates or rebuilds `.venv/`
- Installs dependencies
- Executes pytest suite
- Prints a JSON report, e.g.:
```json
{
  "python": "3.11.14",
  "repo": "/home/user/accident-risk",
  "max_minutes": 10.0,
  "dry_run": false,
  "steps": [
    {"name": "setup_env", "seconds": 140.5, "exit_code": 0},
    {"name": "tests", "seconds": 23.8, "exit_code": 0}
  ],
  "passed_all": true,
  "reason": ""
}
```

If the total time exceeds the threshold, the script exits with code `2` and lists the failed step.

---

## 5. Automation Shortcuts (Makefile)

| Command | Description |
|----------|-------------|
| `make setup-structure` | Ensure directory tree consistency |
| `make setup` or `make env` | Create and install virtual environment |
| `make init-logger` | Initialize the unified logging system |
| `make lint` | Run flake8, black (check), and isort (check-only) |
| `make typecheck` | Run mypy static analysis |
| `make test` | Run pytest suite |
| `make ci` | Run structure + env + lint + typecheck + test chain |

---

## 6. Expected Outcomes

After successful setup:
- The command `pytest -q` returns **all tests passed**.
- Directory `logs/` exists and contains at least one timestamped file.
- Both runtime (`requirements.txt`) and dev (`requirements-dev.txt`) dependencies install cleanly.
- `verify_reproducibility.py` reports `passed_all: true` within the time limit.

---

## 7. Troubleshooting

| Symptom | Likely Cause | Resolution |
|----------|--------------|-------------|
| `bash: .venv/bin/python: No such file or directory` | PATH still points to a deleted venv | Run `deactivate && hash -r && exec bash` or reopen terminal |
| `pytest: command not found` | Dev dependencies not installed | Run `make setup` again |
| JSONDecodeError in tests | Partial or malformed JSON captured | Ensure latest tests and scripts are synced |
| `flake8` style warnings | Auto-format with `black .` or relax rules in `.flake8` |

---

## 8. Project Maintenance Checklist

1. **Keep dependencies updated:**  
   `pip install -U -r requirements.txt -r requirements-dev.txt`

2. **Run full CI validation before commits:**  
   `make ci`

3. **Generate logs for every run:**  
   `make init-logger`

4. **Ensure reproducibility:**  
   Run `python scripts/verify_reproducibility.py` monthly.

---

## 9. Time Expectation Summary

| Task | Typical Duration | Status |
|------|------------------|---------|
| Directory setup | < 1 min | ✅ |
| Environment creation | 2–5 min | ✅ |
| Dependency install | 3–4 min | ✅ |
| Tests | 1–2 min | ✅ |
| **Total (expected)** | **< 10 min** | ✅ |

---

**Document maintained by:** ML Engineering Team  
**Last updated:** 2025‑10‑20
