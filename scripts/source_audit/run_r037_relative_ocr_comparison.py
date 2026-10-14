"""Run the R037 relative OCR comparison with an explicit compatibility gate."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.relative_ocr_constraints import (  # noqa: E402
    RelativeOCRRecord,
    derive_relative_constraints,
    log_ratio_residual,
)


MODEL_PATH = ROOT / "refine-logs" / "runs" / "R034" / "mito_stress_observables.json"
SOURCE_PATHS = (
    ROOT / "refine-logs" / "runs" / "R032"
    / "pmc5247568_ht22_control_digitization.json",
    ROOT / "refine-logs" / "runs" / "R033"
    / "pmc6958642_primary_cortical_control_digitization.json",
)
OUT = ROOT / "refine-logs" / "runs" / "R037" / "relative_ocr_comparison.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source_ratios(payload):
    record = RelativeOCRRecord(
        source_id=payload["source_id"],
        preparation=payload["preparation"],
        normalization_basis=payload["normalization_basis"],
        metrics=payload["metrics"],
        provenance_status=payload["provenance_status"],
    )
    return derive_relative_constraints(record)


def main():
    model = _read(MODEL_PATH)
    predicted = model["relative_constraints"]
    comparisons = []
    for path in SOURCE_PATHS:
        source = _read(path)
        observed = _source_ratios(source)
        comparisons.append(
            {
                "source_id": source["source_id"],
                "preparation": source["preparation"],
                "observed_relative_constraints": observed,
                "descriptive_log_ratio_residual": log_ratio_residual(
                    predicted, observed
                ),
                "eligible_for_external_validation": False,
                "eligibility_reason": (
                    "Reduced ODE output has no source-matched neuronal preparation "
                    "or cell-type-specific parameter mapping."
                ),
            }
        )

    result = {
        "run_id": "R037",
        "model_context": "reduced_ODE_default_no_cell_type_mapping",
        "model_relative_constraints": predicted,
        "comparison_status": "descriptive_only_withheld_external_validation",
        "comparisons": comparisons,
        "claim_boundary": (
            "Residuals document the interface and cannot be reported as "
            "external biological validation."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

