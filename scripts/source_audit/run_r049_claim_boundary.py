"""Freeze the post-R048 computational claim and provenance boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "R047": ROOT
    / "refine-logs"
    / "runs"
    / "R047"
    / "cross_source_formula_coordination.json",
    "R048": ROOT
    / "refine-logs"
    / "runs"
    / "R048"
    / "maximal_spare_restricted_mapping.json",
}
OUT = (
    ROOT
    / "refine-logs"
    / "runs"
    / "R049"
    / "computational_claim_boundary.json"
)


def _artifact_metadata(path):
    payload = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def build_boundary():
    r047 = json.loads(INPUTS["R047"].read_text(encoding="utf-8"))
    r048 = json.loads(INPUTS["R048"].read_text(encoding="utf-8"))
    return {
        "run_id": "R049",
        "status": "complete_computational_claim_boundary",
        "as_of": "2026-08-11",
        "input_artifacts": {
            name: _artifact_metadata(path) for name, path in INPUTS.items()
        },
        "supported_claims": [
            {
                "claim_id": "C1",
                "statement": (
                    "The qualified reduced ODE can generate unit-invariant "
                    "source-local Mito Stress proxy ratios."
                ),
                "evidence": [
                    "R036 qualified observable protocol",
                    "R041 stationary-grid diagnostics",
                ],
                "scope": "computational mechanism/proxy behavior",
            },
            {
                "claim_id": "C2",
                "statement": (
                    "Matched E18/DIV7 primary cortical source records support "
                    "descriptive source-contract comparison for maximal/basal "
                    "and spare/basal ratios."
                ),
                "evidence": [
                    "R039 matched source recovery",
                    "R040 matched source-contract comparison",
                    "R047 maximal/spare-only contract",
                ],
                "scope": "source-local descriptive comparison; not validation",
            },
            {
                "claim_id": "C3",
                "statement": (
                    "A restricted Vmax_CV/g_H grid can be used for diagnostic "
                    "source-holdout mapping under the maximal/spare-only contract."
                ),
                "evidence": [
                    "R048 two-direction holdout mapping",
                    "R048 digitization-corner rank analysis",
                ],
                "scope": "diagnostic parameter sensitivity only",
            },
        ],
        "blocked_claims": [
            {
                "claim_id": "B1",
                "statement": "Absolute OCR calibration in pmol/min/ug protein.",
                "reason": "No source-specific unit bridge and rank instability.",
            },
            {
                "claim_id": "B2",
                "statement": "Figure 1 Bayesian/MCMC posterior calibration.",
                "reason": "Absolute calibration gate remains closed.",
            },
            {
                "claim_id": "B3",
                "statement": "ATP-linked cross-source pooled target.",
                "reason": "R039 O reconstruction conflict and mixed endpoint status.",
            },
            {
                "claim_id": "B4",
                "statement": "Proton-leak cross-source fit target.",
                "reason": "Formula/protocol equivalence is not established.",
            },
            {
                "claim_id": "B5",
                "statement": "Independent biological external validation.",
                "reason": "No source-specific neuronal parameter mapping.",
            },
            {
                "claim_id": "B6",
                "statement": "Clinical efficacy, intervention success, or wet-lab validation.",
                "reason": "The current work is computational only.",
            },
        ],
        "minimum_figure_data_provenance_checklist": [
            "source DOI/PMID/PMCID and figure/table identifier",
            "archived source image or table with SHA256",
            "preparation, species, culture day, and treatment condition",
            "normalization basis and units",
            "directly reported, digitized, inferred, and unavailable fields",
            "explicit endpoint formulas and stage definitions",
            "pixel uncertainty and interval propagation",
            "reproducible extraction script and unit test",
            "claim gate stating whether pooling, calibration, or validation is allowed",
        ],
        "future_update_gates": {
            "new_source": (
                "Do not add it to a pooled target until preparation, formula, "
                "normalization, and endpoint equivalence are audited."
            ),
            "new_figure": (
                "Attach panel-level provenance and regenerate only after the "
                "corresponding claim gate is true."
            ),
            "absolute_calibration": (
                "Requires a verified source-specific unit bridge, not merely "
                "a protein-normalized single record."
            ),
            "external_validation": (
                "Requires an independently mapped preparation and a frozen "
                "parameter protocol before holdout scoring."
            ),
        },
        "current_decision": (
            "Keep the project positioned as a provenance-audited, source-local "
            "computational framework. Any future figure update must preserve "
            "the maximal/spare-only boundary unless a new formula-equivalent "
            "source is independently recovered."
        ),
        "claim_gate_snapshot": {
            "r047_minimal_contract": r047["claim_gate"][
                "minimal_maximal_spare_contract_established"
            ],
            "r048_rank_stable_under_digitization": r048["claim_gate"][
                "rank_stable_under_digitization"
            ],
            "absolute_calibration_allowed": False,
            "figure1_mcmc_allowed": False,
            "external_validation_claim_allowed": False,
        },
    }


def main():
    payload = build_boundary()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

