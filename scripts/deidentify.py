# scripts/deidentify.py
import argparse
import glob
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

INPUT_GLOB_DEFAULT = "data/raw/*.csv"
OUTPUT_DIR_DEFAULT = "data/clean"
SUMMARY_PATH = Path("docs/deidentify_summary.md")

# Default policy: remove human names, hash linkable IDs, round geo/time.
DEFAULT_POLICY = {
    "drop_columns": ["name"],  # remove direct identifiers from placeholder data
    "hash_columns": ["driver_id", "person_id"],  # linkable IDs if present
    "geo": {"lat": {"round": 4}, "lon": {"round": 4}},
    "time": {"timestamp": {"to": "seconds"}},  # downsample ms -> s if needed
}

@dataclass
class DeidStats:
    files_processed: int = 0
    rows_processed: int = 0
    cols_dropped: Dict[str, int] = field(default_factory=dict)
    cols_hashed: Dict[str, int] = field(default_factory=dict)
    geo_rounded: Dict[str, int] = field(default_factory=dict)
    ts_downsampled: Dict[str, int] = field(default_factory=dict)

def sha256_hash(value: str, salt: str) -> str:
    h = hashlib.sha256()
    h.update((salt + value).encode("utf-8"))
    return h.hexdigest()

def normalize_timestamp_series(series: pd.Series) -> pd.Series:
    # If median is ~1e12, assume milliseconds; convert to seconds.
    s_num = pd.to_numeric(series, errors="coerce")
    if s_num.dropna().empty:
        return series
    median_val = float(s_num.dropna().median())
    if median_val > 1e11:
        return (s_num // 1000).astype("Int64")
    return s_num.astype("Int64")

def round_float_series(series: pd.Series, ndigits: int) -> pd.Series:
    s_num = pd.to_numeric(series, errors="coerce")
    return s_num.round(ndigits)

def deidentify_dataframe(df: pd.DataFrame, policy: Dict, salt: Optional[str], stats: DeidStats) -> pd.DataFrame:
    out = df.copy()

    # Drop columns
    for col in policy.get("drop_columns", []):
        if col in out.columns:
            stats.cols_dropped[col] = stats.cols_dropped.get(col, 0) + 1
            out = out.drop(columns=[col])

    # Hash columns (requires salt)
    hash_cols = [c for c in policy.get("hash_columns", []) if c in out.columns]
    if hash_cols:
        if not salt:
            raise RuntimeError("Missing DEID_SALT for hashing linkable identifiers.")
        for col in hash_cols:
            stats.cols_hashed[col] = stats.cols_hashed.get(col, 0) + 1
            out[col] = out[col].astype(str).fillna("").apply(lambda v: sha256_hash(v, salt) if v != "" else "")

    # Geo precision
    for col, rule in policy.get("geo", {}).items():
        if col in out.columns and "round" in rule:
            ndigits = int(rule["round"])
            out[col] = round_float_series(out[col], ndigits)
            stats.geo_rounded[col] = stats.geo_rounded.get(col, 0) + 1

    # Time precision
    for col, rule in policy.get("time", {}).items():
        if col in out.columns and rule.get("to") == "seconds":
            out[col] = normalize_timestamp_series(out[col])
            stats.ts_downsampled[col] = stats.ts_downsampled.get(col, 0) + 1

    return out

def write_summary(summary_path: Path, stats: DeidStats, outputs: List[str]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# De-identification Summary\n\n")
        f.write(f"- Files processed: {stats.files_processed}\n")
        f.write(f"- Total rows processed (first 200k rows per file max): {stats.rows_processed}\n\n")
        def dict_block(title: str, d: Dict[str, int]):
            f.write(f"## {title}\n\n")
            if not d:
                f.write("None\n\n")
            else:
                for k, v in d.items():
                    f.write(f"- {k}: {v}\n")
                f.write("\n")
        dict_block("Dropped columns", stats.cols_dropped)
        dict_block("Hashed columns", stats.cols_hashed)
        dict_block("Geo precision applied", stats.geo_rounded)
        dict_block("Timestamp normalization", stats.ts_downsampled)
        f.write("## Outputs\n\n")
        for o in outputs:
            f.write(f"- {o}\n")

def main():
    parser = argparse.ArgumentParser(description="De-identify raw CSV files according to policy.")
    parser.add_argument("--input-glob", default=INPUT_GLOB_DEFAULT, help="Glob pattern for input CSV files.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR_DEFAULT, help="Directory to write de-identified CSV files.")
    parser.add_argument("--no-hash", action="store_true", help="Skip hashing even if policy requests it (for dry runs).")
    args = parser.parse_args()

    files = sorted(glob.glob(args.input_glob))
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    salt = os.getenv("DEID_SALT", "")
    if args.no_hash:
        salt = ""

    stats = DeidStats()
    outputs: List[str] = []

    for fp in files:
        df = pd.read_csv(fp)
        stats.files_processed += 1
        stats.rows_processed += min(len(df), 200000)

        processed = deidentify_dataframe(df, DEFAULT_POLICY, salt if not args.no_hash else None, stats)
        out_path = Path(args.output_dir) / Path(fp).name
        processed.to_csv(out_path, index=False)
        outputs.append(str(out_path))

    write_summary(SUMMARY_PATH, stats, outputs)
    print(f"De-identification completed. Summary written to {SUMMARY_PATH}")

if __name__ == "__main__":
    main()
