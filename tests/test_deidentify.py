# tests/test_deidentify.py
import os
import pandas as pd
from scripts.deidentify import deidentify_dataframe, DEFAULT_POLICY
from scripts.deidentify import normalize_timestamp_series, round_float_series

def test_drop_name_and_hash_driver_id(monkeypatch):
    df = pd.DataFrame({
        "name": ["Alice", "Bob"],
        "driver_id": ["u1", "u2"],
        "lat": [57.700012, 57.700034],
        "lon": [11.970001, 11.970099],
        "timestamp": [1_700_000_000_123, 1_700_000_000_456],  # ms
    })
    # Provide salt to enable hashing
    monkeypatch.setenv("DEID_SALT", "unit-test-salt")
    stats = __import__("types").SimpleNamespace(
        files_processed=0, rows_processed=0,
        cols_dropped={}, cols_hashed={}, geo_rounded={}, ts_downsampled={}
    )
    out = deidentify_dataframe(df, DEFAULT_POLICY, os.getenv("DEID_SALT"), stats)
    # name removed
    assert "name" not in out.columns
    # driver_id hashed (not equal to original; 64 hex chars)
    assert out["driver_id"].str.len().eq(64).all()
    assert not out["driver_id"].isin(["u1","u2"]).any()
    # lat/lon rounded
    assert (out["lat"].astype(float).round(4) == out["lat"]).all()
    assert (out["lon"].astype(float).round(4) == out["lon"]).all()
    # timestamp normalized to seconds
    assert out["timestamp"].astype(str).str.len().between(9, 11).all()  # seconds magnitude

def test_round_float_series_precision():
    s = pd.Series([57.123456, 57.000099])
    r = round_float_series(s, 4)
    assert r.iloc[0] == 57.1235
    assert r.iloc[1] == 57.0001

def test_normalize_timestamp_series():
    s_ms = pd.Series([1_700_000_000_123, 1_700_000_000_999])
    s_sec = normalize_timestamp_series(s_ms)
    assert (s_sec == pd.Series([1_700_000_000, 1_700_000_000], dtype="Int64")).all()
