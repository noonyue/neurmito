"""R058 canonical open-issue resolution plan.

R058 converts the historical tracker state into a small canonical set of
remaining computational issues. It explicitly closes absolute OCR calibration
and Figure 1 Bayesian/MCMC calibration for the current paper, while preserving
only matched-source recovery/mapping as optional future computational work.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R058" / "open_issue_resolution_plan.json"
R049 = RUNS / "R049" / "computational_claim_boundary.json"
R057 = RUNS / "R057" / "active_claim_language_audit.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_plan() -> dict:
    r049 = _read_json(R049)
    r057 = _read_json(R057)

    closed_boundaries = {
        "absolute_ocr_calibration": {
            "status": "closed",
            "decision": "Do not pursue absolute OCR calibration for the current computational paper.",
            "reason": (
                "No verified source-specific unit bridge exists; protein-normalized "
                "single-source records do not establish cross-source absolute units."
            ),
            "allowed_replacement": "source-local maximal/basal and spare/basal ratios only",
            "evidence": ["R049:B1", "R051", "R057"],
        },
        "figure1_mcmc_or_bayesian": {
            "status": "closed",
            "decision": "Do not report Figure 1 MCMC/Bayesian posterior calibration.",
            "reason": "The absolute calibration gate remains closed.",
            "allowed_replacement": "restricted diagnostic Vmax_CV/g_H mapping from R048",
            "evidence": ["R049:B2", "R051", "R057"],
        },
        "wet_lab_or_clinical_claims": {
            "status": "closed",
            "decision": "Keep the paper computational-only.",
            "reason": "No wet-lab, clinical, intervention, or patient-outcome evidence is in scope.",
            "allowed_replacement": "mechanism-oriented computational hypotheses",
            "evidence": ["R049:B6", "R052", "R057"],
        },
    }

    canonical_open_issues = [
        {
            "issue_id": "OI1",
            "status": "open",
            "title": "Recover or document absence of a second matched primary cortical Mito Stress source.",
            "allowed_scope": (
                "Find an independently recoverable primary rat cortical neuron control "
                "source with source-local maximal/basal and spare/basal ratios."
            ),
            "blocked_actions": [
                "do not use HT22 as a matched biological holdout",
                "do not reopen absolute OCR calibration",
                "do not pool ATP-linked or proton-leak targets",
            ],
            "resolution_outputs": [
                "candidate ledger",
                "eligibility decisions",
                "negative audit if no matched source is recoverable",
            ],
            "depends_on": ["R033", "R039", "R047"],
        },
        {
            "issue_id": "OI2",
            "status": "open",
            "title": "If OI1 succeeds, perform maximal/spare-only matched-source mapping.",
            "allowed_scope": (
                "Run one-source fit / one-source reserve mapping using only source-local "
                "maximal/basal and spare/basal ratios."
            ),
            "blocked_actions": [
                "do not claim biological external validation",
                "do not report rank-stable calibration unless digitization-corner stability passes",
                "do not add ATP-linked, proton leak, or absolute OCR targets",
            ],
            "resolution_outputs": [
                "restricted mapping manifest",
                "rank-stability check",
                "claim-gate update",
            ],
            "depends_on": ["OI1", "R048"],
        },
    ]

    superseded_historical_todos = {
        "R030B": {
            "historical_task": "Figure 1 raw numeric recovery for absolute unit bridge",
            "replacement": "closed_boundary:absolute_ocr_calibration",
            "rationale": "Current evidence is insufficient and the paper is kept relative-only.",
        },
        "R034": {
            "historical_task": "relative OCR matched-preparation holdout check",
            "replacement": "canonical_open_issue:OI1",
            "rationale": "The next useful action is source recovery/negative audit, not calibration.",
        },
        "R038": {
            "historical_task": "source-matched neuronal preparation mapping",
            "replacement": "canonical_open_issue:OI2",
            "rationale": "Mapping is conditional on OI1 and remains maximal/spare-only.",
        },
    }

    qc = {
        "r049_gates_closed": (
            r049["claim_gate_snapshot"]["absolute_calibration_allowed"] is False
            and r049["claim_gate_snapshot"]["external_validation_claim_allowed"] is False
            and r049["claim_gate_snapshot"]["figure1_mcmc_allowed"] is False
        ),
        "r057_language_clean": r057["qc"]["passed"] is True,
        "open_issue_count": len(canonical_open_issues),
        "closed_boundary_count": len(closed_boundaries),
        "manuscript_modified": False,
    }
    qc["passed"] = (
        qc["r049_gates_closed"]
        and qc["r057_language_clean"]
        and qc["open_issue_count"] == 2
        and qc["closed_boundary_count"] == 3
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R058",
        "status": "complete_open_issue_resolution_plan",
        "closed_boundaries": closed_boundaries,
        "canonical_open_issues": canonical_open_issues,
        "superseded_historical_todos": superseded_historical_todos,
        "input_artifacts": {
            "R049": {
                "path": str(R049.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R049),
            },
            "R057": {
                "path": str(R057.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R057),
            },
        },
        "qc": qc,
        "manuscript_modified": False,
    }


def main():
    payload = build_plan()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

