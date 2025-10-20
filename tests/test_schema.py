# ensure schema generation works.

from pathlib import Path
import subprocess
import yaml

def test_generate_schema():
    # Run the CLI target to generate schema
    res = subprocess.run(["python", "scripts/generate_schema.py"], check=True, capture_output=True, text=True)
    assert "Schema generated" in res.stdout

    schema_path = Path("docs/schema_v1.yaml")
    assert schema_path.exists()

    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    assert "schema_version" in schema
    assert "fields" in schema
    assert isinstance(schema["fields"], list)
    # Must include core fields declared in data_dictionary.csv
    names = [f["name"] for f in schema["fields"]]
    for key in ["timestamp", "lat", "lon", "speed", "accel", "heading"]:
        assert key in names, f"missing {key} in schema fields"
