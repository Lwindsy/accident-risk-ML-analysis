#!/usr/bin/env python3
import hashlib
import sys
from pathlib import Path
import yaml
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONTRACT_YAML = DOCS / "data_contract.yaml"
LOCK_FILE = DOCS / "data_contract.lock"

REQUIRED_COLS = ["timestamp","lat","lon","speed","accel","heading"]

def sha256_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def verify_lock():
    if not CONTRACT_YAML.exists() or not LOCK_FILE.exists():
        print("[ERROR] Contract yaml or lock file missing.", file=sys.stderr)
        sys.exit(1)
    content = load_text(CONTRACT_YAML)
    lock = load_text(LOCK_FILE).strip()
    digest = sha256_text(content)
    if digest != lock:
        print(f"[ERROR] Lock mismatch. expected={lock}, actual={digest}", file=sys.stderr)
        sys.exit(2)
    print("[OK] Lock matches contract yaml.")

def verify_required_columns(sample_paths):
    for p in sample_paths:
        df = pd.read_csv(p)
        miss = [c for c in REQUIRED_COLS if c not in df.columns]
        if miss:
            print(f"[ERROR] {p} missing columns: {miss}", file=sys.stderr)
            sys.exit(3)
    print("[OK] Sample files conform to required columns.")

def main():
    verify_lock()
    # Opportunistic sample check: clean and standardized folders if present
    candidates = []
    for gl in ["data/clean/*.csv", "data/standardized/*.csv"]:
        for p in ROOT.glob(gl):
            candidates.append(p)
    if candidates:
        verify_required_columns(candidates)
    else:
        print("[INFO] No sample files found for column check. Lock verified only.")

if __name__ == "__main__":
    main()
