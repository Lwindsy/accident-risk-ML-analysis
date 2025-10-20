# tests/test_privacy_check.py
import pandas as pd
from scripts.privacy_check import looks_like_pii_name, value_based_pii_signals, coord_precision, timestamp_granularity

def test_pii_name_heuristics():
    assert looks_like_pii_name("driver_id")
    assert looks_like_pii_name("LicensePlate")
    assert not looks_like_pii_name("speed")
    assert not looks_like_pii_name("accel")

def test_value_based_email_phone():
    s_email = pd.Series(["a@b.com", "x@y.org"])
    s_phone = pd.Series(["+46 700-123-456", "0700 111 222"])
    s_none = pd.Series(["foo", "bar"])
    assert any("email" in r for r in value_based_pii_signals(s_email))
    assert any("phone" in r for r in value_based_pii_signals(s_phone))
    assert value_based_pii_signals(s_none) == []

def test_coord_precision():
    s = pd.Series([57.700012, 57.700034, 57.699998])
    dp = coord_precision(s)
    assert dp is not None and dp > 3  # more than ~3 decimals on average

def test_timestamp_granularity():
    s_sec = pd.Series([1_700_000_000, 1_700_000_123])
    s_ms  = pd.Series([1_700_000_000_000, 1_700_000_123_456])
    assert timestamp_granularity(s_sec) == "seconds"
    assert timestamp_granularity(s_ms) == "milliseconds"
