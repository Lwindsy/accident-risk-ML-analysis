"""
Sanity checks for dependency manifests.

These tests do not install packages. They only parse the requirement
files to ensure essential packages are declared and that the syntax
is sound for automated tooling and CI pipelines.
"""
from pathlib import Path

ESSENTIAL_RUNTIME = {"pandas", "numpy", "pyyaml", "matplotlib"}
ESSENTIAL_DEV = {"pytest", "flake8", "black"}

def _parse_pkgs(path: Path):
    """Extract top-level package names from a pip requirement file."""
    pkgs = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Allow common version specifiers and extras.
        token = (
            line.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("~=")[0]
                .strip()
        )
        name = token.split("[")[0].strip().lower()
        if name:
            pkgs.add(name)
    return pkgs

def test_runtime_requirements_contains_essentials():
    path = Path("requirements.txt")
    assert path.exists(), "requirements.txt is missing"
    pkgs = _parse_pkgs(path)
    missing = sorted(p for p in ESSENTIAL_RUNTIME if p not in pkgs)
    assert not missing, f"Missing runtime packages: {missing}"

def test_dev_requirements_contains_essentials():
    path = Path("requirements-dev.txt")
    assert path.exists(), "requirements-dev.txt is missing"
    pkgs = _parse_pkgs(path)
    missing = sorted(p for p in ESSENTIAL_DEV if p not in pkgs)
    assert not missing, f"Missing dev packages: {missing}"
