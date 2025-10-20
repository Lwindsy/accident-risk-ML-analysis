#!/usr/bin/env python3
"""
Reproducibility validator for a 10-minute setup and test rule.

This script measures how long it takes to:
  1) Create or reuse a virtual environment and install dependencies.
  2) Run the project's test suite.

Design principles:
  - English-only, interviewer-friendly comments.
  - No assumptions about shell; use Python to orchestrate commands.
  - Dry-run mode to integrate safely in CI without side effects.
  - JSON summary printed to stdout; non-zero exit when failing thresholds.

Exit codes:
  0  Success (within time threshold and tests passed)
  2  Validation failed (missing files, command failure, or time exceeded)
  3  Unexpected error
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import types
import time
from dataclasses import dataclass, asdict
from pathlib import Path

if __name__ not in sys.modules or sys.modules.get(__name__) is None:
    sys.modules[__name__] = sys.modules.get("__main__", sys)

# also ensure there's at least one fallback stable key for dataclass introspection
if "verify_reproducibility" not in sys.modules:
    sys.modules["verify_reproducibility"] = sys.modules[__name__]


MIN_PY_MAJOR = 3
MIN_PY_MINOR = 11

REQUIRED_FILES = [
    Path("requirements.txt"),
    Path("requirements-dev.txt"),
    Path("scripts") / "setup_env.py",
    Path("tests"),
]


@dataclass
class StepResult:
    name: str
    seconds: float
    exit_code: int
    note: str = ""


@dataclass
class Report:
    python: str
    repo: str
    max_minutes: float
    dry_run: bool
    steps: list[StepResult]
    passed_all: bool
    reason: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "python": self.python,
                "repo": self.repo,
                "max_minutes": self.max_minutes,
                "dry_run": self.dry_run,
                "steps": [asdict(s) for s in self.steps],
                "passed_all": self.passed_all,
                "reason": self.reason,
            },
            indent=2,
        )


class ValidationError(RuntimeError):
    """Raised for expected validation failures with clear messages."""


def _echo(msg: str) -> None:
    print(f"[repro] {msg}")


def _check_python_version() -> None:
    if sys.version_info < (MIN_PY_MAJOR, MIN_PY_MINOR):
        raise ValidationError(
            f"Python {MIN_PY_MAJOR}.{MIN_PY_MINOR}+ required; "
            f"found {platform.python_version()} at {sys.executable}"
        )


def _check_required_files() -> None:
    missing = [str(p) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        raise ValidationError(f"Missing required files/paths: {missing}")


def _run(cmd: list[str], dry_run: bool) -> int:
    _echo("$ " + " ".join(cmd))
    if dry_run:
        return 0
    try:
        return subprocess.call(cmd)
    except FileNotFoundError as e:
        raise ValidationError(f"Command not found: {cmd[0]} ({e})")


def _venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def run_step(name: str, func, *args, **kwargs) -> StepResult:
    start = time.perf_counter()
    exit_code = 0
    note = ""
    try:
        exit_code, note = func(*args, **kwargs)
    except ValidationError as e:
        exit_code = 2
        note = f"ValidationError: {e}"
    except Exception as e:
        exit_code = 3
        note = f"Unexpected: {e.__class__.__name__}: {e}"
    seconds = time.perf_counter() - start
    return StepResult(name=name, seconds=seconds, exit_code=exit_code, note=note)


def step_setup_env(venv_path: Path, dry_run: bool, force_recreate: bool) -> tuple[int, str]:
    """
    Use scripts/setup_env.py to build the environment.
    Returns (exit_code, note).
    """
    args = [sys.executable, "scripts/setup_env.py", "--venv-path", str(venv_path)]
    if force_recreate:
        args.append("--force-recreate")
    # install dev deps by default (no --no-dev)
    rc = _run(args, dry_run=dry_run)
    return rc, "setup_env executed"


def step_run_tests(venv_path: Path, dry_run: bool) -> tuple[int, str]:
    """
    Run pytest from the venv to ensure the test suite is green.
    Returns (exit_code, note).
    """
    py = _venv_python(venv_path)
    cmd = [str(py), "-m", "pytest", "-q"]
    rc = _run(cmd, dry_run=dry_run)
    return rc, "pytest executed"


def validate(max_minutes: float, venv_path: Path, dry_run: bool, force_recreate: bool) -> Report:
    _check_python_version()
    _check_required_files()

    steps: list[StepResult] = []
    steps.append(run_step("setup_env", step_setup_env, venv_path, dry_run, force_recreate))
    steps.append(run_step("tests", step_run_tests, venv_path, dry_run))

    total_sec = sum(s.seconds for s in steps)
    within_threshold = (total_sec <= max_minutes * 60.0) or dry_run
    all_ok = all(s.exit_code == 0 for s in steps)

    passed = within_threshold and all_ok
    reason = ""
    if not within_threshold:
        reason = f"Total time {total_sec:.2f}s exceeded {max_minutes*60:.2f}s"
    if not all_ok:
        failed = [s.name for s in steps if s.exit_code != 0]
        reason = (reason + "; " if reason else "") + f"Failed steps: {failed}"

    return Report(
        python=platform.python_version(),
        repo=str(Path(".").resolve()),
        max_minutes=max_minutes,
        dry_run=dry_run,
        steps=steps,
        passed_all=passed,
        reason=reason,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate that a newcomer can set up and test the project within a time budget."
    )
    p.add_argument("--max-minutes", type=float, default=10.0, help="Time budget in minutes (default: 10)")
    p.add_argument("--venv-path", default=".venv", help="Virtualenv path to create/reuse (default: .venv)")
    p.add_argument("--dry-run", action="store_true", help="Print plan and simulate success without side effects")
    p.add_argument("--force-recreate", action="store_true", help="Force venv recreation before timing")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = validate(
            max_minutes=args.max_minutes,
            venv_path=Path(args.venv_path),
            dry_run=args.dry_run,
            force_recreate=args.force_recreate,
        )
        _echo(report.to_json())
        return 0 if report.passed_all else 2
    except ValidationError as e:
        _echo(json.dumps({"error": str(e)}, indent=2))
        return 2
    except Exception as e:
        _echo(json.dumps({"unexpected": f"{e.__class__.__name__}: {e}"}))
        return 3


if __name__ == "__main__":
    sys.exit(main())
