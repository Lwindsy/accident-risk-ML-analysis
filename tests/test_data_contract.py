import hashlib
from pathlib import Path
import yaml

DOCS = Path("docs")
CONTRACT_YAML = DOCS / "data_contract.yaml"
LOCK_FILE = DOCS / "data_contract.lock"

def test_contract_exists_and_fields():
    assert CONTRACT_YAML.exists()
    with CONTRACT_YAML.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    gm = doc["global_meta"]
    assert gm["coordinate_reference_system"] == "EPSG:4326"
    assert gm["time_basis"] == "UTC"
    assert gm["sampling_rate_hz"] == 10
    names = [f["name"] for f in doc["fields"]]
    for k in ["timestamp","lat","lon","speed","accel","heading"]:
        assert k in names

def test_lock_matches():
    txt = CONTRACT_YAML.read_text(encoding="utf-8")
    want = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    got = LOCK_FILE.read_text(encoding="utf-8").strip()
    assert want == got
