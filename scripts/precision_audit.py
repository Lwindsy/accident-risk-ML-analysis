# scripts/precision_audit.py
import glob
from pathlib import Path
from typing import List, Optional

import pandas as pd
import matplotlib.pyplot as plt

CLEAN_GLOB = "data/clean/*.csv"
REPORT_MD = Path("docs/precision_audit_report.md")
OUTDIR = Path("reports/precision")
LAT_COL, LON_COL, TS_COL = "lat", "lon", "timestamp"

def load_clean_files(pattern: str) -> List[pd.DataFrame]:
    dfs = []
    for fp in sorted(glob.glob(pattern)):
        try:
            dfs.append(pd.read_csv(fp))
        except Exception:
            pass
    return dfs

def avg_decimals(series: pd.Series) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: 
        return None
    def decs(x: float) -> int:
        s = f"{x:.12f}".rstrip("0").split(".")
        return len(s[1]) if len(s) == 2 else 0
    sample = s.sample(min(len(s), 500), random_state=42)
    vals = [decs(float(x)) for x in sample]
    return sum(vals) / len(vals) if vals else None

def timestamp_scale(series: pd.Series) -> Optional[str]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: 
        return None
    med = float(s.median())
    if med > 1e11: return "milliseconds"
    if med > 1e8:  return "seconds"
    return "unknown"

def plot_hist(series: pd.Series, title: str, outfile: Path, bins: int = 50):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return
    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.hist(s, bins=bins)
    plt.title(title)
    plt.xlabel(title)
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()

def main():
    dfs = load_clean_files(CLEAN_GLOB)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_MD.open("w", encoding="utf-8") as f:
        f.write("# Precision Audit Report (Clean Data)\n\n")
        if not dfs:
            f.write("No clean CSV files found.\n")
            return
        all_df = pd.concat(dfs, axis=0, ignore_index=True)

        # lat/lon
        if LAT_COL in all_df.columns:
            adp = avg_decimals(all_df[LAT_COL])
            f.write(f"- Average decimal places for `{LAT_COL}`: {adp if adp is not None else 'N/A'}\n")
            plot_hist(all_df[LAT_COL], "lat", OUTDIR / "lat_hist.png")
        else:
            f.write(f"- Column `{LAT_COL}` not present.\n")

        if LON_COL in all_df.columns:
            adp = avg_decimals(all_df[LON_COL])
            f.write(f"- Average decimal places for `{LON_COL}`: {adp if adp is not None else 'N/A'}\n")
            plot_hist(all_df[LON_COL], "lon", OUTDIR / "lon_hist.png")
        else:
            f.write(f"- Column `{LON_COL}` not present.\n")

        # timestamp
        if TS_COL in all_df.columns:
            scale = timestamp_scale(all_df[TS_COL])
            f.write(f"- Timestamp scale: {scale if scale else 'N/A'}\n")
            plot_hist(all_df[TS_COL], "timestamp", OUTDIR / "timestamp_hist.png", bins=60)
        else:
            f.write(f"- Column `{TS_COL}` not present.\n")

        # Policy conformance checks（简单门槛）
        f.write("\n## Policy Checks\n\n")
        ok_geo = True
        if LAT_COL in all_df.columns:
            adp_lat = avg_decimals(all_df[LAT_COL]) or 0.0
            ok_geo = ok_geo and adp_lat <= 4.1
            f.write(f"- `{LAT_COL}` avg decimals ≤ 4.1: {'OK' if adp_lat <= 4.1 else 'FAIL'}\n")
        if LON_COL in all_df.columns:
            adp_lon = avg_decimals(all_df[LON_COL]) or 0.0
            ok_geo = ok_geo and adp_lon <= 4.1
            f.write(f"- `{LON_COL}` avg decimals ≤ 4.1: {'OK' if adp_lon <= 4.1 else 'FAIL'}\n")

        ok_time = True
        if TS_COL in all_df.columns:
            scale = timestamp_scale(all_df[TS_COL])
            ok_time = (scale == "seconds")
            f.write(f"- `timestamp` in seconds: {'OK' if ok_time else 'FAIL'}\n")

        f.write("\n## Result\n\n")
        f.write("PASS\n" if (ok_geo and ok_time) else "CHECK REQUIRED\n")

if __name__ == "__main__":
    main()
