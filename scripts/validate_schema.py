# This script validates the consistency between a schema YAML file and a CSV dataset.
# It compares the defined fields in the schema with the columns present in the CSV.
# If some fields are missing, it prints a warning instead of failing, allowing early testing on partial data.


from pathlib import Path
import sys
import yaml
import pandas as pd

SCHEMA_PATH = Path("docs/schema_v1.yaml")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_schema.py <csv_path>", file=sys.stderr)
        sys.exit(2)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(3)

    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(4)

    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    required = [f["name"] for f in schema.get("fields", [])]
    df = pd.read_csv(csv_path)

    missing = [c for c in required if c not in df.columns]
    present = [c for c in required if c in df.columns]

    print("Schema fields:", len(required))
    print("Present in CSV:", len(present))
    print("Missing in CSV:", len(missing))

    if missing:
        print("WARNING: The following schema fields are missing in the CSV:")
        for c in missing:
            print(f" - {c}")

    # Phase 1 policy: do not fail the build for demo gaps.
    print("Phase 1 validation completed.")
    sys.exit(0)

if __name__ == "__main__":
    main()