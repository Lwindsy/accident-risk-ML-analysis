# tests/test_precision_audit.py
import pandas as pd
from scripts.precision_audit import avg_decimals, timestamp_scale

def test_avg_decimals():
    s = pd.Series([57.1234, 57.1001, 57.0])
    d = avg_decimals(s)
    assert d is not None and d >= 2

def test_timestamp_scale():
    assert timestamp_scale(pd.Series([1_700_000_000, 1_700_000_123])) == "seconds"
    assert timestamp_scale(pd.Series([1_700_000_000_000])) == "milliseconds"
