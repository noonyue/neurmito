"""Run the reduced-model, unit-free Mito Stress observable audit."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from module1.mito_stress_observables import run_mito_stress_protocol


OUT = ROOT / "refine-logs" / "runs" / "R034" / "mito_stress_observables.json"


def main():
    result = run_mito_stress_protocol()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

