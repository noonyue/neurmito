"""Validate that the public source records and declarations are present."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [ROOT / "inputs" / "source_records", ROOT / "inputs" / "input_manifest.json", ROOT / "inputs" / "parameter_manifest.json"]

def main() -> int:
    missing = [str(p) for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit("Missing public inputs: " + ", ".join(missing))
    print(json.dumps({"status": "ok", "source_records": str(REQUIRED[0]), "manifests": [str(p) for p in REQUIRED[1:]]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
