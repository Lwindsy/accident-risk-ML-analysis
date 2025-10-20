import numpy as np
import pandas as pd
from scripts.resample_to_contract import resample_to_rate, wrap_deg

def test_linear_resample_to_10hz_basic():
    t = np.arange(0.0, 1.0 + 1e-9, 0.2)  # 5 Hz
    df = pd.DataFrame({
        "timestamp": t,
        "lat": np.linspace(0.0, 1.0, len(t)),
        "lon": np.linspace(1.0, 2.0, len(t)),
        "speed": np.linspace(0.0, 10.0, len(t)),
        "accel": np.linspace(0.0, 1.0, len(t)),
        "heading": np.linspace(350.0, 10.0, len(t)),  # crossing 360 wrap
    })
    out = resample_to_rate(df, rate_hz=10)
    assert np.isclose(out["timestamp"].diff().dropna().unique(), 0.1).all()
    # Check monotonic and bounds
    assert (out["speed"] >= -1e-6).all()
    assert ((out["lat"] >= -1e9) & (out["lon"] <= 1e12)).all()
    # Heading must be wrapped to [0,360)
    assert ((out["heading"] >= 0.0) & (out["heading"] < 360.0)).all()
