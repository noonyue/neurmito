"""R059 matched-source candidate recovery audit.

R059 advances OI1 from R058 by reconciling the prior R038 conditional source
screen with PubMed/PMC metadata and full-text method snippets. It does not
digitize new bars or reopen calibration; it only determines which remaining
matched primary cortical neuron sources should proceed to source-image
archiving and relative-only digitization.
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
OUT = RUNS / "R059" / "matched_source_candidate_recovery.json"
R038 = RUNS / "R038" / "source_matched_candidate_screen.json"
R058 = RUNS / "R058" / "open_issue_resolution_plan.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit() -> dict:
    r038 = _read_json(R038)
    r058 = _read_json(R058)

    candidate_ledger = [
        {
            "source_id": "PMID:24056030",
            "pmcid": "PMC3859859",
            "doi": "10.1016/j.freeradbiomed.2013.09.006",
            "title": (
                "Inhibition of autophagy and glycolysis by nitric oxide during "
                "hypoxia-reoxygenation impairs cellular bioenergetics and "
                "promotes cell death in primary neurons."
            ),
            "preparation_evidence": [
                "primary cortical neurons from embryonic day 18 embryos",
                "DIV7 untreated/normoxia control record recovered in R039",
                "Seahorse XF24 Mito Stress workflow",
            ],
            "endpoint_evidence": [
                "basal/maximal/reserve/ATP-linked/proton-leak/non-mito OCR bars recovered",
                "R039 source-local digitization complete",
            ],
            "decision": "already_extracted_matched_source",
            "eligible_for_calibration": False,
            "eligible_for_oi1_digitization": False,
            "rationale": (
                "This source is already the R039 member of the current R033/R039 "
                "matched descriptive pair; it is not a new additional source."
            ),
        },
        {
            "source_id": "PMID:25081478",
            "pmcid": "PMC4454361",
            "doi": "10.1111/jnc.12844",
            "title": "Bioenergetic adaptation in response to autophagy regulators during rotenone exposure.",
            "preparation_evidence": [
                "primary rat cortical neurons isolated from embryonic day 18 rats",
                "DIV7 cultures are explicitly reported",
                "80,000 cells/well plated on XF24 plates",
            ],
            "endpoint_evidence": [
                "Seahorse XF24 extracellular flux analyzer",
                "sequential oligomycin, FCCP, and antimycin A injections",
                "0 nM rotenone control condition in Figure 1 OCR/Mito Stress workflow",
                "protein-normalized OCR; relative-only use required",
            ],
            "decision": "pass_to_digitization",
            "eligible_for_calibration": False,
            "eligible_for_oi1_digitization": True,
            "rationale": (
                "The full-text method and figure legend satisfy the preparation and "
                "Mito Stress protocol screen. The next step is source-image archive "
                "and control-bar digitization, not calibration."
            ),
        },
        {
            "source_id": "PMID:27889640",
            "pmcid": "PMC5124357",
            "doi": "10.1016/j.redox.2016.11.004",
            "title": (
                "Inhibition of autophagy with bafilomycin and chloroquine decreases "
                "mitochondrial quality and bioenergetic function in primary neurons."
            ),
            "preparation_evidence": [
                "primary cortical rat neurons isolated at embryonic day E18",
                "experiments performed on DIV7",
                "Seahorse XF96 analyzer",
            ],
            "endpoint_evidence": [
                "Figure 2 includes control, bafilomycin, and chloroquine groups",
                "mitochondrial stress test with oligomycin, FCCP, and antimycin A",
                "basal, maximal, reserve capacity, ATP-linked, proton leak, and non-mito OCR calculated",
                "protein-normalized OCR; relative-only use required",
            ],
            "decision": "pass_to_digitization_secondary",
            "eligible_for_calibration": False,
            "eligible_for_oi1_digitization": True,
            "rationale": (
                "This is a plausible secondary source, but treatment-focused design "
                "and XF96 platform difference make it second priority after PMID:25081478."
            ),
        },
    ]

    pass_to_digitization = [
        item["source_id"]
        for item in candidate_ledger
        if item["eligible_for_oi1_digitization"]
    ]
    recommended_next_run = {
        "run_id": "R060",
        "objective": (
            "Archive and digitize PMID:25081478 Figure 1 control Mito Stress bars "
            "as source-local relative ratios."
        ),
        "target_source": "PMID:25081478",
        "backup_source": "PMID:27889640",
        "allowed_outputs": [
            "source image archive with SHA256",
            "axis calibration",
            "basal/maximal/spare source-local ratios if recoverable",
            "negative audit if control bars are not digitizable",
        ],
        "blocked_targets": [
            "absolute OCR",
            "ATP-linked pooling",
            "proton-leak fitting",
            "external validation claim",
        ],
    }

    qc = {
        "prior_oi1_open": any(
            issue["issue_id"] == "OI1" and issue["status"] == "open"
            for issue in r058["canonical_open_issues"]
        ),
        "digitization_candidates_available": len(pass_to_digitization) >= 1,
        "absolute_calibration_reopened": False,
        "mcmc_reopened": False,
        "manuscript_modified": False,
    }
    qc["passed"] = (
        qc["prior_oi1_open"]
        and qc["digitization_candidates_available"]
        and qc["absolute_calibration_reopened"] is False
        and qc["mcmc_reopened"] is False
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R059",
        "status": "complete_matched_source_candidate_recovery",
        "oi1_status": "open_digitization_pending",
        "candidate_ledger": candidate_ledger,
        "pass_to_digitization": pass_to_digitization,
        "recommended_next_run": recommended_next_run,
        "input_artifacts": {
            "R038": {
                "path": str(R038.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R038),
                "status": r038["status"],
            },
            "R058": {
                "path": str(R058.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R058),
            },
        },
        "qc": qc,
        "manuscript_modified": False,
    }


def main():
    payload = build_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

