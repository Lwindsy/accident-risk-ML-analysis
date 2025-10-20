"""
Sanity tests for the Makefile.

These checks do not execute Make targets. They verify the presence
of required targets and basic portability assumptions.
"""
from pathlib import Path
import re

MAKEFILE = Path("Makefile")

REQUIRED_TARGETS = {
    "help",
    "setup",
    "env",
    "setup-structure",
    "init-logger",
    "test",
    "lint",
    "typecheck",
    "clean-venv",
    "ci",
}

def _parse_targets(text: str):
    targets = set()
    for line in text.splitlines():
        # Match lines like: "target:" but ignore pattern rules "%.o:" etc.
        m = re.match(r"^([A-Za-z0-9._-]+)\s*:\s*", line)
        if m:
            name = m.group(1)
            if not name.startswith("%"):
                targets.add(name)
    return targets

def test_makefile_exists():
    assert MAKEFILE.exists(), "Makefile is missing"

def test_required_targets_present():
    text = MAKEFILE.read_text(encoding="utf-8")
    targets = _parse_targets(text)
    missing = sorted(t for t in REQUIRED_TARGETS if t not in targets)
    assert not missing, f"Missing Make targets: {missing}"

def test_platform_sensitive_vars_declared():
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "ifeq ($(OS),Windows_NT)" in text, "OS detection block is required for cross-platform paths"
    for var in ("ACTIVATE", "PY", "PIP", "SEP"):
        assert var in text, f"Expected variable not defined: {var}"
