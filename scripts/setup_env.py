#!/usr/bin/env python3
"""
Automate Python environment bootstrapping for this repository.

Design goals:
- Be idempotent: safe to run multiple times.
- Work cross-platform where possible (Linux, macOS, Windows).
- Keep user-facing strings in English.
- Provide a --dry-run mode for CI/testing (no side effects).

Responsibilities:
1) Validate Python version (>= 3.11).
2) Create or reuse a virtual environment at the requested path (default: .venv).
3) Install runtime requirements (requirements.txt).
4) Optionally install development requirements (requirements-dev.txt).
5) Print clear diagnostics and exit codes.

This script assumes requirements files live at repository root.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


MIN_PY_MAJOR = 3
MIN_PY_MINOR = 11


class SetupError(RuntimeError):
    """Raised for recoverable setup errors with a clear message."""


def _echo(msg: str) -> None:
    """Standard console output with a uniform prefix for easier grepping."""
    print(f"[env-setup] {msg}")


def _check_python_version() -> None:
    """Ensure the interpreter is recent enough for the stack."""
    if sys.version_info < (MIN_PY_MAJOR, MIN_PY_MINOR):
        raise SetupError(
            f"Python {MIN_PY_MAJOR}.{MIN_PY_MINOR}+ is required; "
            f"found {platform.python_version()} at {sys.executable}"
        )


def _run(cmd: list[str], dry_run: bool) -> int:
    """Run a command. In dry-run mode, only echo the command."""
    _echo(f"$ {' '.join(cmd)}")
    if dry_run:
        return 0
    try:
        return subprocess.call(cmd)
    except FileNotFoundError as e:
        raise SetupError(f"Command not found: {cmd[0]} ({e})")


def _venv_python(venv_path: Path) -> Path:
    """Return the platform-specific path to the venv's python executable."""
    if platform.system().lower().startswith("win"):
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def _venv_pip(venv_path: Path) -> Path:
    """Return the platform-specific path to the venv's pip executable."""
    if platform.system().lower().startswith("win"):
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


def _system_python() -> str:
    """
    Return a system Python executable to bootstrap a new venv.

    This avoids self-referencing .venv/bin/python when the venv is deleted
    under --force-recreate. Falls back to current sys.executable if detection fails.
    """
    import sysconfig
    from shutil import which
    # Try common names first
    for candidate in ("python3.11", "python3", "python"):
        p = which(candidate)
        if p:
            return p
    # Fallback: same executable
    return sys.executable


def _create_or_reuse_venv(venv_path: Path, force_recreate: bool, dry_run: bool) -> None:
    """Create a virtual environment, or reuse an existing one if allowed."""
    if venv_path.exists() and force_recreate:
        _echo(f"Removing existing venv at: {venv_path}")
        if not dry_run:
            shutil.rmtree(venv_path)

    if not venv_path.exists():
        _echo(f"Creating virtual environment at: {venv_path}")
        python_exec = _system_python()
        rc = _run([python_exec, "-m", "venv", str(venv_path)], dry_run=dry_run)
        if rc != 0:
            raise SetupError(f"Failed to create venv (exit code {rc})")
    else:
        _echo(f"Reusing existing virtual environment at: {venv_path}")

    pip = _venv_pip(venv_path)
    rc = _run([str(pip), "install", "--upgrade", "pip", "setuptools", "wheel"], dry_run=dry_run)
    if rc != 0:
        raise SetupError(f"Failed to upgrade pip/setuptools/wheel (exit code {rc})")


def _install_requirements(
    venv_path: Path,
    req_runtime: Path,
    req_dev: Path | None,
    include_dev: bool,
    dry_run: bool,
) -> None:
    """Install runtime and, optionally, development requirements into the venv."""
    pip = _venv_pip(venv_path)

    if not req_runtime.exists():
        raise SetupError(f"Missing requirements file: {req_runtime}")

    _echo(f"Installing runtime requirements from {req_runtime}")
    rc = _run([str(pip), "install", "-r", str(req_runtime)], dry_run=dry_run)
    if rc != 0:
        raise SetupError(f"Failed to install runtime requirements (exit code {rc})")

    if include_dev:
        if req_dev is None:
            raise SetupError("Development requirements requested but path is None")
        if not req_dev.exists():
            raise SetupError(f"Missing development requirements file: {req_dev}")
        _echo(f"Installing development requirements from {req_dev}")
        rc = _run([str(pip), "install", "-r", str(req_dev)], dry_run=dry_run)
        if rc != 0:
            raise SetupError(f"Failed to install development requirements (exit code {rc})")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a Python virtual environment and install project dependencies."
    )
    parser.add_argument(
        "--venv-path",
        default=".venv",
        help="Target directory for the virtual environment (default: .venv)",
    )
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Install only runtime requirements (skip development dependencies).",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Delete and recreate the virtual environment if it already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the actions and commands without performing changes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        _check_python_version()

        repo_root = Path(".").resolve()
        venv_path = (repo_root / args.venv_path).resolve()

        req_runtime = repo_root / "requirements.txt"
        req_dev = repo_root / "requirements-dev.txt"

        include_dev = not args.no_dev

        _echo(f"Repository: {repo_root}")
        _echo(f"Python: {platform.python_version()} ({sys.executable})")
        _echo(f"Venv path: {venv_path}")
        _echo(f"Include dev dependencies: {include_dev}")
        _echo(f"Dry-run mode: {args.dry_run}")

        _create_or_reuse_venv(venv_path=venv_path, force_recreate=args.force_recreate, dry_run=args.dry_run)
        _install_requirements(
            venv_path=venv_path,
            req_runtime=req_runtime,
            req_dev=req_dev,
            include_dev=include_dev,
            dry_run=args.dry_run,
        )

        py = _venv_python(venv_path)
        _echo("Environment ready.")
        _echo(f"Activate with: source {venv_path}/bin/activate" if os.name != "nt"
              else f"Activate with: {venv_path}\\Scripts\\activate")
        _echo(f"Python in venv: {py}")

        return 0
    except SetupError as e:
        _echo(f"ERROR: {e}")
        return 2
    except Exception as e:  # unexpected
        _echo(f"UNEXPECTED ERROR: {e.__class__.__name__}: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
