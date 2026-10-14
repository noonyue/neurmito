"""R043 source endpoint-definition and protocol metadata audit.

This is a source-semantic audit, not a model fit. The metadata below records
only definitions recovered from the archived PMC full texts and figure
captions. It explicitly distinguishes exact formulae from labels that are only
conceptually compatible.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "refine-logs" / "runs" / "R043" / "endpoint_definition_audit.json"


def main():
    sources = {
        "PMID:31931869": {
            "pmcid": "PMC6958642",
            "doi": "10.1186/s13195-019-0578-9",
            "preparation": "E18 primary rat cortical neurons, DIV7",
            "platform": "Seahorse XFe24",
            "control_record": "untreated primary-neuron control bars in Figure 2",
            "stage_protocol": {
                "baseline": "resting respiration",
                "oligomycin": "1 uM",
                "fccp": "2 uM",
                "antimycin_a": "0.5 uM",
                "rotenone": "0.5 uM",
            },
            "normalization": {
                "basis": "Janus Green whole-cell stain / total cell amount proxy",
                "protein_normalized": False,
            },
            "endpoint_semantics": {
                "basal": "resting/basal respiration",
                "maximal": "FCCP-stimulated maximal OCR",
                "proton_leak": (
                    "oligomycin OCR minus non-mitochondrial OCR"
                ),
                "atp_linked": {
                    "published_label": (
                        "ATP production through oxidative phosphorylation"
                    ),
                    "description": (
                        "difference between basal OCR and oligomycin-insensitive "
                        "OCR measurements"
                    ),
                    "exact_label_match_to_atp_linked": False,
                },
            },
            "harmonization_status": {
                "maximal_spare_proton_leak": "relative-only compatible",
                "atp_linked": "semantic review required before pooling",
            },
        },
        "PMID:24056030": {
            "pmcid": "PMC3859859",
            "doi": "10.1016/j.freeradbiomed.2013.09.006",
            "preparation": "E18 primary rat cortical neurons, DIV7-10",
            "platform": "Seahorse XF24",
            "control_record": "untreated normoxia control bars in Figure 2B",
            "stage_protocol": {
                "baseline": "baseline OCR before DetaNO injection / control",
                "oligomycin": "1 ug/mL",
                "fccp": "1 uM",
                "antimycin_a": "10 uM",
                "rotenone": (
                    "tested with antimycin; no additional effect reported"
                ),
            },
            "normalization": {
                "basis": "protein normalization in individual wells",
                "protein_normalized": True,
            },
            "endpoint_semantics": {
                "basal": "baseline respiration",
                "maximal": "FCCP-stimulated maximal OCR",
                "proton_leak": {
                    "published_description": (
                        "remaining proton leak or other processes utilizing "
                        "the mitochondrial proton gradient after oligomycin"
                    ),
                    "strict_non_mito_formula_explicit": False,
                },
                "atp_linked": {
                    "published_label": "ATP-linked respiration",
                    "description": (
                        "oligomycin-inhibitable OCR component"
                    ),
                    "exact_label_match_to_atp_production": False,
                },
            },
            "harmonization_status": {
                "maximal_spare_proton_leak": "relative-only compatible",
                "atp_linked": "semantic review required before pooling",
            },
        },
    }
    output = {
        "run_id": "R043",
        "status": "complete_endpoint_semantic_audit",
        "sources": sources,
        "decision": {
            "ratio_contract": {
                "maximal_to_basal": "retain",
                "spare_to_basal": "retain",
                "proton_leak_to_basal": "retain_with_source_formula_metadata",
                "atp_linked_to_basal": "do_not_pool_until_formula_harmonized",
            },
            "model_mapping": "withheld",
            "eligible_for_external_validation": False,
            "absolute_calibration_allowed": False,
            "figure1_mcmc_allowed": False,
        },
        "reasoning": [
            "The platforms and inhibitor doses differ across sources.",
            "The normalization bases differ across sources.",
            "R033 labels the endpoint as ATP production through oxidative phosphorylation, whereas R039 labels it ATP-linked respiration.",
            "R039 does not explicitly state a strict non-mitochondrial subtraction formula for proton leak in the reviewed text.",
            "The R042 ATP-linked interval gap therefore cannot be attributed to digitization error alone.",
        ],
        "next_gate": (
            "Do not pool ATP-linked ratios or fit ODE parameters until a "
            "source-local formula harmonization worksheet is archived."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


