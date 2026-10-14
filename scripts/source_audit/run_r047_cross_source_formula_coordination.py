"""R047 cross-source formula coordination.

This run compares endpoint construction and availability across R033, R039,
and R046. It deliberately separates algebraic compatibility from biological
preparation matching and never pools source values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_r033_pmc6958642_fig2 import build_record as build_r033
from scripts.extract_r039_pmc3859859_fig2 import build_record as build_r039
from scripts.extract_r046_pmc5667543_fig2 import build_record as build_r046


OUT = (
    ROOT
    / "refine-logs"
    / "runs"
    / "R047"
    / "cross_source_formula_coordination.json"
)


def source_local_ratios(basal, maximal, atp, proton_leak, non_mito=None):
    ratios = {
        "maximal_to_basal": maximal / basal,
        "spare_to_basal": (maximal - basal) / basal,
        "atp_linked_to_basal": atp / basal,
        "proton_leak_to_basal": proton_leak / basal,
    }
    if non_mito is not None:
        ratios["non_mito_to_basal"] = non_mito / basal
    return {key: round(value, 6) for key, value in ratios.items()}


def build_coordination():
    r033 = build_r033()
    r039 = build_r039()
    r046 = build_r046()

    r033_metrics = r033["metrics"]
    r039_metrics = r039["metrics"]
    r046_stages = r046["stages"]
    r046_derived = r046["derived_observables"]

    records = {
        "R033": {
            "source_id": r033["source_id"],
            "preparation": (
                "E18 DIV7 primary rat cortical neurons, untreated control"
            ),
            "normalization": r033["normalization_basis"],
            "matched_e18_div7_contract": True,
            "terms": {
                "B": "digitized",
                "O": "unavailable",
                "F": "digitized",
                "N": "unavailable",
                "A": "digitized",
                "P": "digitized",
            },
            "formulas": {
                "A": "source-described as B - oligomycin-insensitive OCR",
                "P": "source-described as O - N",
                "spare": "F - B",
            },
            "ratios": source_local_ratios(
                r033_metrics["basal_ocr"],
                r033_metrics["maximal_ocr"],
                r033_metrics["atp_linked"],
                r033_metrics["proton_leak"],
            ),
        },
        "R039": {
            "source_id": r039["source_id"],
            "preparation": r039["preparation"],
            "normalization": r039["normalization_basis"],
            "matched_e18_div7_contract": True,
            "terms": {
                "B": "digitized",
                "O": "inferred_conflicting",
                "F": "digitized",
                "N": "digitized",
                "A": "digitized",
                "P": "digitized",
            },
            "formulas": {
                "A": "oligomycin-inhibitable OCR component",
                "P": (
                    "remaining OCR after oligomycin attributed to proton "
                    "leak/gradient processes"
                ),
                "O_from_A": "B - A",
                "O_from_P_and_N": "P + N",
                "spare": "F - B",
            },
            "formula_qc": {
                "O_from_A": round(
                    r039["derived_qc"]["oligomycin_from_atp_linked"], 6
                ),
                "O_from_P_and_N": round(
                    r039["derived_qc"]["oligomycin_from_proton_leak"], 6
                ),
                "O_identity_gap": round(
                    r039["derived_qc"]["oligomycin_identity_gap"], 6
                ),
            },
            "ratios": source_local_ratios(
                r039_metrics["basal_ocr"],
                r039_metrics["maximal_ocr"],
                r039_metrics["atp_linked"],
                r039_metrics["proton_leak"],
                r039_metrics["non_mito_ocr"],
            ),
        },
        "R046": {
            "source_id": r046["source_id"],
            "preparation": r046["preparation"],
            "normalization": r046["normalization_basis"],
            "matched_e18_div7_contract": False,
            "terms": {
                "B": "reported",
                "O": "digitized",
                "F": "digitized",
                "N": "digitized",
                "A": "inferred",
                "P": "inferred",
            },
            "formulas": {
                "A": "B - O",
                "P": "O - N",
                "spare": "F - B",
            },
            "ratios": source_local_ratios(
                r046_stages["B"]["value_percent_of_baseline"],
                r046_stages["F"]["value_percent_of_baseline"],
                r046_derived["A"]["value_percent_of_baseline"],
                r046_derived["P"]["value_percent_of_baseline"],
                r046_stages["N"]["value_percent_of_baseline"],
            ),
            "scientific_role": (
                "relative formula reference only; not a matched fit, "
                "calibration, or validation source"
            ),
        },
    }

    output = {
        "run_id": "R047",
        "status": "complete_minimum_common_contract",
        "records": records,
        "endpoint_equivalence_matrix": {
            "B": {
                "availability": "all_sources",
                "decision": "source_local_denominator_only",
                "reason": "normalization bases differ across sources",
            },
            "F": {
                "availability": "all_sources",
                "decision": "relative_ratio_compatible",
                "reason": (
                    "all sources expose maximal/FCCP relative to their own "
                    "basal stage"
                ),
            },
            "spare": {
                "availability": "all_sources",
                "decision": "relative_ratio_compatible",
                "formula": "F - B",
            },
            "A": {
                "availability": "all_sources_but_mixed_status",
                "decision": "blocked_for_cross_source_target",
                "reason": (
                    "R046 is inferred, R033 lacks independent O, and R039 "
                    "has conflicting O reconstructions"
                ),
            },
            "P": {
                "availability": "all_sources_but_mixed_status",
                "decision": "source_local_diagnostic_only",
                "reason": (
                    "R046 is inferred from independent stages while R033/R039 "
                    "are endpoint bars with non-equivalent formula evidence"
                ),
            },
            "O": {
                "availability": "independent_only_in_r046",
                "decision": "not_common",
            },
            "N": {
                "availability": "r039_and_r046_only",
                "decision": "not_common",
            },
        },
        "minimum_common_observation_contract": {
            "version": "relative_ocr_constraints_v2_maximal_spare_only",
            "fit_or_holdout_endpoints": [
                "maximal_to_basal",
                "spare_to_basal",
            ],
            "diagnostic_only_endpoints": [
                "proton_leak_to_basal_with_source_formula_tag",
            ],
            "blocked_endpoints": [
                "atp_linked_to_basal",
                "independent_oligomycin_to_basal",
                "absolute_ocr",
            ],
            "matched_sources_for_r048": ["R033", "R039"],
            "r046_role": "formula_reference_only",
            "pool_source_values": False,
        },
        "claim_gate": {
            "atp_formula_equivalence_established": False,
            "proton_leak_formula_equivalence_established": False,
            "minimal_maximal_spare_contract_established": True,
            "r048_restricted_mapping_allowed": True,
            "r048_may_use_atp_linked": False,
            "r048_may_use_proton_leak_as_fit_target": False,
            "absolute_calibration_allowed": False,
            "figure1_mcmc_allowed": False,
            "external_validation_claim_allowed": False,
        },
        "next_decision": (
            "Proceed conditionally to R048 using only maximal/basal and "
            "spare/basal for the matched R033/R039 source-holdout mapping. "
            "Keep R046 as a formula reference and do not add ATP-linked or "
            "proton-leak fit targets."
        ),
    }
    return output


def main():
    output = build_coordination()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

