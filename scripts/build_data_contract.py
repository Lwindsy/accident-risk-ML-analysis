#!/usr/bin/env python3
import hashlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SCHEMA_FILE = DOCS / "schema_v1.yaml"
CONTRACT_YAML = DOCS / "data_contract.yaml"
CONTRACT_MD = DOCS / "data_contract.md"  # not modified here, only validated if present
LOCK_FILE = DOCS / "data_contract.lock"

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def dump_yaml(obj: dict) -> str:
    # Stable dump for reproducible hash
    return yaml.safe_dump(obj, sort_keys=True, allow_unicode=True)

def enforce_contract_from_schema(schema: dict) -> dict:
    """Produce a frozen contract dict from schema_v1 with enforced policies."""
    contract = {
        "contract_version": "1.0",
        "frozen_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "global_meta": {
            "coordinate_reference_system": "EPSG:4326",
            "time_basis": "UTC",
            "sampling_rate_hz": 10,
            "window_definition": {
                "history_seconds": 10,
                "prediction_horizon_seconds": 10,
            },
        },
        "standardization_policy": {
            "resample": {
                "method": "time_index_uniform",
                "target_rate_hz": 10,
                "interpolation": {
                    "numeric": "linear",
                    "categorical": "ffill",
                },
                "fill": {
                    "max_gap_seconds": 2
                }
            },
            "coordinates": {
                "crs_mandatory": "EPSG:4326",
                "lat_range": [-90.0, 90.0],
                "lon_range": [-180.0, 180.0],
            },
            "units": {
                "speed": "m/s",
                "accel": "m/s^2",
                "heading": "degrees",
            }
        },
        "fields": [],
        "conformance": {
            "file_requirements": {
                "must_have_columns": ["timestamp", "lat", "lon", "speed", "accel", "heading"]
            },
            "dataset_quality_gates": {
                "valid_rows_ratio_min": 0.95,
                "no_future_leakage": True
            },
            "privacy": {
                "pii_allowed_in_standardized": False,
                "geo_precision": ">= 4 decimals after de-identification as defined in privacy policy"
            }
        }
    }
    # Map schema fields → contract fields with constraints
    field_index = {f["name"]: f for f in schema.get("fields", [])}
    def base_field(name, unit, desc, extra_constraints=None):
        constraints = {"finite": True}
        if extra_constraints:
            constraints.update(extra_constraints)
        return {
            "name": name,
            "type": "float",
            "unit": unit,
            "description": desc,
            "constraints": constraints
        }

    contract["fields"] = [
        base_field("timestamp", "seconds_since_epoch",
                   "Monotonic vehicle timestamp in UTC seconds.",
                   {"monotonic_non_decreasing": True}),
        base_field("lat", "degrees",
                   "WGS-84 latitude.",
                   {"range": [-90.0, 90.0]}),
        base_field("lon", "degrees",
                   "WGS-84 longitude.",
                   {"range": [-180.0, 180.0]}),
        base_field("speed", "m/s",
                   "Instantaneous vehicle speed.",
                   {"min": 0.0}),
        base_field("accel", "m/s^2",
                   "Longitudinal acceleration (forward positive)."),
        base_field("heading", "degrees",
                   "Vehicle heading angle in [0, 360).",
                   {"range": [0.0, 360.0], "wrap_behavior": "mod_360"}),
    ]
    # Sanity: warn if schema is missing expected columns
    required = set(["timestamp","lat","lon","speed","accel","heading"])
    missing = [c for c in required if c not in field_index]
    if missing:
        print(f"[WARN] schema_v1.yaml missing expected fields: {missing}", file=sys.stderr)
    return contract

def write_lock_for_text(text: str, lock_path: Path) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lock_path.write_text(digest + "\n", encoding="utf-8")
    return digest

def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    if not SCHEMA_FILE.exists():
        print(f"[ERROR] Missing schema file: {SCHEMA_FILE}", file=sys.stderr)
        sys.exit(1)
    schema = load_yaml(SCHEMA_FILE)
    contract = enforce_contract_from_schema(schema)
    dumped = dump_yaml(contract)
    CONTRACT_YAML.write_text(dumped, encoding="utf-8")
    digest = write_lock_for_text(dumped, LOCK_FILE)
    print(f"[OK] Wrote {CONTRACT_YAML}")
    print(f"[OK] Wrote lock {LOCK_FILE} with SHA-256: {digest}")

if __name__ == "__main__":
    main()
