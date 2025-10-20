# This script converts the CSV-based data dictionary into a machine-readable YAML schema.
# It keeps the data dictionary as the single source of truth for non-engineers,
# while producing a structured YAML file for programmatic validation and downstream use.
# All human-facing strings are in English to ensure consistent documentation.


import csv
from pathlib import Path
import sys
import yaml

DICT_PATH = Path("docs/data_dictionary.csv")
SCHEMA_PATH = Path("docs/schema_v1.yaml")

# Global metadata included in Schema_v1 to be frozen at Gate A
GLOBAL_META = {
    "coordinate_reference_system": "WGS84",
    "time_basis": "UTC",
    "sampling_rate_hz": "TBD",  # Replace with actual value when the real dataset is selected
    "window_definition": {
        "history_seconds": 10,
        "prediction_horizon_seconds": 10
    },
    "notes": "Units and field names must remain stable after Gate A unless reviewed."
}

def infer_python_type(t: str) -> str:
    t = (t or "").strip().lower()
    if t in ("float", "double", "number"):
        return "float"
    if t in ("int", "integer", "long"):
        return "int"
    if t in ("string", "str", "text"):
        return "string"
    if t in ("bool", "boolean"):
        return "bool"
    # default to string to avoid breaking early
    return "string"

def main():
    if not DICT_PATH.exists():
        print(f"ERROR: {DICT_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    fields = []
    with DICT_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"field", "type", "unit", "example", "description"}
        if not required_cols.issubset(reader.fieldnames or []):
            print("ERROR: data_dictionary.csv missing required columns.", file=sys.stderr)
            sys.exit(2)

        for row in reader:
            fields.append({
                "name": row["field"].strip(),
                "type": infer_python_type(row["type"]),
                "unit": row["unit"].strip(),
                "example": row["example"].strip(),
                "description": row["description"].strip()
            })

    schema = {
        "schema_version": "1.0",
        "global_meta": GLOBAL_META,
        "fields": fields
    }

    SCHEMA_PATH.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    print(f"Schema generated at: {SCHEMA_PATH.resolve()}")

if __name__ == "__main__":
    main()