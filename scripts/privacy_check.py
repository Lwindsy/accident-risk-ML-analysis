# scripts/privacy_check.py
import argparse
import glob
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import yaml
except ImportError:
    yaml = None  # Optional; script will continue without schema checks.

REPORT_PATH = Path("docs/privacy_audit_report.md")
SCHEMA_PATH = Path("docs/schema_v1.yaml")
DATA_GLOB = "data/raw/*.csv"

# Heuristics for likely PII fields by column name (case-insensitive).
PII_NAME_PATTERNS = [
    r"driver[_\- ]?id",
    r"person[_\- ]?id",
    r"plate|license[_\- ]?plate",
    r"vin\b",
    r"phone|mobile|tel",
    r"email",
    r"address|street|house|postcode|zip",
    r"name|surname|firstname|lastname",
    r"device[_\- ]?id|imei|imsi|mac",
    r"ip[_\- ]?addr|ipaddress",
    r"ssn|national[_\- ]?id|passport",
]

# Heuristics for PII by value shape (sampled).
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d[\d\-\s]{6,}$", re.ASCII)

# Columns that are expected in the PRD scope but still need precision audit.
COORD_COLS = ["lat", "lon"]
TIME_COLS = ["timestamp"]

@dataclass
class Finding:
    file: str
    column: str
    reason: str
    sample: Optional[str] = None

def load_schema_fields() -> Optional[List[str]]:
    """Load allowed fields from YAML schema if present."""
    if not SCHEMA_PATH.exists() or yaml is None:
        return None
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        obj = yaml.safe_load(f)
    fields = obj.get("fields", [])
    names = []
    for fdesc in fields:
        name = str(fdesc.get("name", "")).strip()
        if name:
            names.append(name)
    return names or None

def looks_like_pii_name(col: str) -> bool:
    c = col.lower()
    return any(re.search(pat, c) for pat in PII_NAME_PATTERNS)

def value_based_pii_signals(series: pd.Series, sample_size: int = 30) -> List[str]:
    """Return list of reasons if values look like PII (email/phone)."""
    reasons = []
    sample = series.dropna().astype(str).head(sample_size).tolist()
    if any(EMAIL_RE.match(s) for s in sample):
        reasons.append("contains email-like values")
    if any(PHONE_RE.match(s) for s in sample):
        reasons.append("contains phone-like values")
    return reasons

def coord_precision(series: pd.Series) -> Optional[float]:
    """Estimate average decimal places for floats (lat/lon)."""
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    # Estimate average decimal digits by formatting with high precision.
    def dec_places(x: float) -> int:
        s = f"{x:.12f}".rstrip("0").split(".")
        return len(s[1]) if len(s) == 2 else 0
    decs = [dec_places(x) for x in clean.sample(min(200, len(clean)), random_state=42)]
    return sum(decs) / len(decs)

def timestamp_granularity(series: pd.Series) -> Optional[str]:
    """Guess timestamp granularity (seconds vs milliseconds)."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None
    # If values are around 1e12, likely milliseconds since epoch; ~1e9 for seconds.
    median_val = float(numeric.median())
    if median_val > 1e11:
        return "milliseconds"
    if median_val > 1e9 / 10:  # crude boundary
        return "seconds"
    return "unknown"

def scan_file(path: str, allowed_fields: Optional[List[str]]) -> Tuple[List[Finding], Dict[str, str]]:
    df = pd.read_csv(path, nrows=2000)  # sample file head; enough for signals
    findings: List[Finding] = []
    metrics: Dict[str, str] = {}

    # Name/Schema checks
    for col in df.columns:
        # Schema deviation
        if allowed_fields is not None and col not in allowed_fields:
            if looks_like_pii_name(col):
                findings.append(Finding(path, col, "column not in schema and name looks PII"))
        # Name heuristics
        if looks_like_pii_name(col):
            reasons = ["column name matches PII heuristic"]
            # Value-based signals
            extra = value_based_pii_signals(df[col])
            reasons.extend(extra)
            findings.append(Finding(path, col, "; ".join(reasons)))

    # Coordinate precision audit
    for c in COORD_COLS:
        if c in df.columns:
            avg_dp = coord_precision(df[c])
            if avg_dp is not None:
                metrics[f"{c}_avg_decimal_places"] = f"{avg_dp:.2f}"
                if avg_dp >= 6:
                    findings.append(Finding(path, c, "lat/lon precision appears high; consider rounding to 4 dp"))

    # Timestamp granularity audit
    for c in TIME_COLS:
        if c in df.columns:
            gran = timestamp_granularity(df[c])
            if gran:
                metrics[f"{c}_granularity"] = gran
                if gran == "milliseconds":
                    findings.append(Finding(path, c, "timestamp appears to be in milliseconds; consider converting to seconds"))

    # Value-based PII in non-PII-named columns (defense in depth)
    for col in df.columns:
        extra = value_based_pii_signals(df[col])
        if extra:
            findings.append(Finding(path, col, "; ".join(extra)))

    return findings, metrics

def write_report(report_path: Path, results: List[Finding], metrics_all: Dict[str, Dict[str, str]]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Privacy Audit Report\n\n")
        f.write("This report summarizes potential PII signals and precision audits over `data/raw/*.csv`.\n\n")
        if results:
            f.write("## Potential PII Findings\n\n")
            f.write("| File | Column | Reason | Sample |\n")
            f.write("|------|--------|--------|--------|\n")
            for r in results:
                sample = (r.sample or "")[:60]
                f.write(f"| {r.file} | {r.column} | {r.reason} | {sample} |\n")
            f.write("\n")
        else:
            f.write("## Potential PII Findings\n\n")
            f.write("No PII-like columns detected by current heuristics.\n\n")

        f.write("## Precision & Granularity Metrics\n\n")
        if metrics_all:
            f.write("| File | Metric | Value |\n")
            f.write("|------|--------|-------|\n")
            for file, m in metrics_all.items():
                for k, v in m.items():
                    f.write(f"| {file} | {k} | {v} |\n")
        else:
            f.write("No metrics collected.\n")

def main():
    parser = argparse.ArgumentParser(description="Privacy audit for raw CSV telemetry files.")
    parser.add_argument("--allow-pii", action="store_true", help="Do not fail the process if findings exist.")
    parser.add_argument("--glob", default="data/raw/*.csv", help="Glob for CSV files to audit.")
    args = parser.parse_args()


    allowed_fields = load_schema_fields()
    results: List[Finding] = []
    metrics_all: Dict[str, Dict[str, str]] = {}

    files = sorted(glob.glob(parser.parse_args().glob))
    if not files:
        print("No CSV files found under data/raw/")
    for fp in files:
        fs, metrics = scan_file(fp, allowed_fields)
        results.extend(fs)
        if metrics:
            metrics_all[fp] = metrics

    write_report(REPORT_PATH, results, metrics_all)
    print(f"Privacy audit report written to: {REPORT_PATH}")

    if results and not args.allow_pii:
        print("PII-like findings detected. Failing the process (use --allow-pii to override).")
        raise SystemExit(2)

if __name__ == "__main__":
    main()
