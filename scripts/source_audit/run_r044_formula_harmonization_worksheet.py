"""R044 source-local formula harmonization worksheet.

The worksheet separates direct observations, digitized bars, stated formulas,
inferred intermediate stages, and unavailable terms. It never fills a missing
term with zero and never creates a pooled ATP-linked target.
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


OUT = ROOT / "refine-logs" / "runs" / "R044" / "formula_harmonization_worksheet.json"


def main():
    r033 = build_r033()
    r039 = build_r039()
    r039_qc = r039["derived_qc"]
    output = {
        "run_id": "R044",
        "status": "complete_source_local_formula_worksheet",
        "notation": {
            "B": "basal OCR",
            "O": "oligomycin-stage OCR / oligomycin-insensitive OCR",
            "F": "FCCP maximal OCR",
            "N": "non-mitochondrial OCR",
            "A": "ATP-linked or ATP-production endpoint",
            "P": "proton-leak endpoint",
        },
        "records": {
            "PMID:31931869": {
                "source_record": "R033",
                "normalization": r033["normalization_basis"],
                "direct_or_digitized_terms": {
                    "B": "digitized Figure 2 control basal bar",
                    "A": "digitized Figure 2 ATP Prod. bar",
                    "P": "digitized Figure 2 Proton Leak bar",
                    "F": "digitized Figure 2 Max Resp. bar",
                    "O": "unavailable as an independent digitized stage",
                    "N": "unavailable in the archived four-bar control crop",
                },
                "source_stated_formulas": {
                    "A": "B - oligomycin-insensitive OCR",
                    "P": "O - N",
                },
                "inferred_terms": {
                    "O": "not inferred because N and independent O are unavailable",
                },
                "status": {
                    "maximal_spare": "usable as source-local ratios",
                    "proton_leak": "retain with formula metadata",
                    "atp_linked": "do not pool before formula harmonization",
                },
            },
            "PMID:24056030": {
                "source_record": "R039",
                "normalization": r039["normalization_basis"],
                "direct_or_digitized_terms": {
                    "B": "digitized Figure 2B control basal bar",
                    "A": "digitized Figure 2B control ATP-linked bar",
                    "P": "digitized Figure 2B control proton-leak bar",
                    "F": "digitized Figure 2B control maximal bar",
                    "N": "digitized Figure 2B control non-mitochondrial bar",
                    "O": "unavailable as an independent digitized stage",
                },
                "source_stated_formulas": {
                    "A": "oligomycin-inhibitable OCR component",
                    "P": (
                        "remaining OCR after oligomycin attributed to proton "
                        "leak or other proton-gradient processes"
                    ),
                },
                "inferred_terms": {
                    "O_from_A": float(r039_qc["oligomycin_from_atp_linked"]),
                    "O_from_P_plus_N": float(
                        r039_qc["oligomycin_from_proton_leak"]
                    ),
                },
                "inference_conflict": {
                    "gap": float(r039_qc["oligomycin_identity_gap"]),
                    "interpretation": (
                        "The two reconstructions disagree; this is retained as "
                        "source endpoint/protocol uncertainty, not corrected."
                    ),
                },
                "status": {
                    "maximal_spare": "usable as source-local ratios",
                    "proton_leak": "retain with formula metadata",
                    "atp_linked": "do not pool before formula harmonization",
                },
            },
        },
        "common_observation_contract": {
            "maximal_to_basal": "retain source-local only",
            "spare_to_basal": "retain source-local only",
            "proton_leak_to_basal": "retain source-local with formula tag",
            "atp_linked_to_basal": "blocked_until_formula_equivalence",
        },
        "claim_gate": {
            "missing_terms_filled_with_zero": False,
            "pooled_atp_target_created": False,
            "eligible_for_external_validation": False,
            "absolute_calibration_allowed": False,
            "figure1_mcmc_allowed": False,
        },
        "next_decision": (
            "Do not fit the reduced ODE to ATP-linked ratios. If a common "
            "observable is needed, use only maximal/spare with source-local "
            "metadata, or obtain raw stage traces that expose O and N."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

