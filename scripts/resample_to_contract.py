#!/usr/bin/env python3
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def unwrap_deg(a):
    """Unwrap degrees to a continuous series for interpolation."""
    rad = np.deg2rad(a.to_numpy())
    unwrapped = np.unwrap(rad)
    return pd.Series(np.rad2deg(unwrapped), index=a.index)

def wrap_deg(a):
    """Wrap degrees back to [0, 360)."""
    wrapped = np.mod(a, 360.0)
    return wrapped

def resample_to_rate(df, rate_hz: int):
    # Assume timestamp is seconds_since_epoch float
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Build uniform time index
    t0, t1 = df["timestamp"].iloc[0], df["timestamp"].iloc[-1]
    if t1 <= t0:
        return df.iloc[0:0].copy()
    dt = 1.0 / rate_hz
    new_t = np.arange(t0, t1 + 1e-9, dt)
    out = pd.DataFrame({"timestamp": new_t})
    # Merge-asof for numeric fields
    # Interpolate speed, accel; special handling for heading
    for col in ["speed","accel"]:
        out[col] = np.interp(new_t, df["timestamp"], df[col])

    if "heading" in df.columns:
        h_unwrap = unwrap_deg(df["heading"])
        h_interp = np.interp(new_t, df["timestamp"], h_unwrap)
        out["heading"] = wrap_deg(h_interp)
    # Forward-fill categorical columns if any (not specified here)
    # Lat/lon: linear interpolation is acceptable over small gaps
    for col in ["lat","lon"]:
        out[col] = np.interp(new_t, df["timestamp"], df[col])
    return out

def main():
    ap = argparse.ArgumentParser(description="Standardize CSVs to contract sampling rate.")
    ap.add_argument("--input-glob", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--rate-hz", type=int, default=10)
    args = ap.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    paths = list(Path(".").glob(args.input_glob))
    if not paths:
        print(f"[INFO] No input files matched: {args.input_glob}")
        return

    for p in paths:
        df = pd.read_csv(p)
        missing = [c for c in ["timestamp","lat","lon","speed","accel","heading"] if c not in df.columns]
        if missing:
            print(f"[WARN] Skip {p} due to missing cols: {missing}")
            continue
        # Drop windows with long gaps if needed (policy threshold = 2s)
        df = df.dropna(subset=["timestamp","lat","lon","speed","accel","heading"])
        out = resample_to_rate(df, args.rate_hz)
        # Here we could implement gap invalidation; left to Phase 3 windowing.
        outpath = outdir / p.name
        out.to_csv(outpath, index=False)
        print(f"[OK] Wrote standardized: {outpath}")

if __name__ == "__main__":
    main()
