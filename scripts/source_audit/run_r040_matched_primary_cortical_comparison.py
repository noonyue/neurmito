"""Compare the two matched-preparation primary cortical relative OCR records.

This run checks only source-to-source consistency after within-source ratio
transformation. It deliberately withholds model external-validation eligibility:
the reduced ODE still has no source-specific neuronal parameter mapping.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.relative_ocr_constraints import (
    RelativeOCRRecord,
    derive_relative_constraints,
    log_ratio_residual,
)
from scripts.extract_r033_pmc6958642_fig2 import build_record as build_r033_record
from scripts.extract_r039_pmc3859859_fig2 import build_record as build_r039_record

OUT = ROOT / "refine-logs" / "runs" / "R040" / "matched_primary_cortical_comparison.json"


def _relative_record(payload):
    return RelativeOCRRecord(
        source_id=payload["source_id"],
        preparation=payload["preparation"],
        normalization_basis=payload["normalization_basis"],
        metrics=payload["metrics"],
        provenance_status=payload["provenance_status"],
        absolute_calibration_eligible=payload.get(
            "absolute_calibration_eligible", False
        ),
    )


def main():
    r033 = build_r033_record()
    r039 = build_r039_record()
    r033_ratios = derive_relative_constraints(_relative_record(r033))
    r039_ratios = derive_relative_constraints(_relative_record(r039))
    output = {
        "run_id": "R040",
        "comparison_status": "matched_preparation_source_contract_only",
        "matched_preparation_contract": {
            "species": "rat",
            "tissue": "cortex",
            "cell_type": "primary neurons",
            "embryonic_day": "E18",
            "culture_day": "DIV7",
            "condition": "untreated control",
        },
        "protocol_differences_retained_as_source_metadata": [
            "Seahorse XFe24 versus XF24 platform",
            "Janus Green cell-number normalization versus protein normalization",
            "source-specific inhibitor concentrations and timing",
        ],
        "relative_constraints": {
            "PMID:31931869": r033_ratios,
            "PMID:24056030": r039_ratios,
        },
        "log_ratio_residual_r039_vs_r033": log_ratio_residual(
            r039_ratios, r033_ratios
        ),
        "eligible_for_source_matched_holdout_design": True,
        "eligible_for_model_external_validation": False,
        "model_validation_withheld_reason": (
            "The reduced ODE has no source-specific neuronal preparation "
            "or cell-type parameter mapping."
        ),
        "absolute_calibration_allowed": False,
        "claim_boundary": (
            "This is a source-contract and descriptive consistency check, "
            "not external biological validation or Figure 1 calibration."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

