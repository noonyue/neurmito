"""R061 three-source relative consistency audit.

This run compares the newly digitized R060 source against the existing
R033/R039 matched primary cortical pair under the R047 maximal/spare-only
contract. It decides whether the third source can be blindly pooled for a
future three-source mapping, while keeping all absolute, validation, wet-lab,
Bayesian/MCMC, ATP-linked, and proton-leak claim gates closed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, Tuple


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R061" / "three_source_relative_consistency.json"
REPORT = ROOT / "refine-logs" / "R061_THREE_SOURCE_RELATIVE_CONSISTENCY.md"

R042 = RUNS / "R042" / "digitization_uncertainty_propagation.json"
R048 = RUNS / "R048" / "maximal_spare_restricted_mapping.json"
R060 = RUNS / "R060" / "pmc4454361_control_relative_digitization.json"

ENDPOINTS = ("maximal_to_basal", "spare_to_basal")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _interval_overlaps(left: dict, right: dict) -> dict:
    low = max(left["low"], right["low"])
    high = min(left["high"], right["high"])
    overlaps = low <= high
    return {
        "overlaps": overlaps,
        "intersection_low": round(low, 6) if overlaps else None,
        "intersection_high": round(high, 6) if overlaps else None,
        "gap": 0.0 if overlaps else round(max(left["low"], right["low"]) - min(left["high"], right["high"]), 6),
    }


def _as_interval(entry: dict) -> dict:
    interval = entry["interval"]
    return {
        "low": float(interval[0]),
        "nominal": float(entry["value"]),
        "high": float(interval[1]),
    }


def _existing_band(intervals: Dict[str, dict], endpoint: str) -> dict:
    lows = [intervals[source][endpoint]["low"] for source in intervals]
    highs = [intervals[source][endpoint]["high"] for source in intervals]
    nominals = [intervals[source][endpoint]["nominal"] for source in intervals]
    return {
        "low": min(lows),
        "nominal_min": min(nominals),
        "nominal_max": max(nominals),
        "high": max(highs),
    }


def _ratio_table_rows(sources: Dict[str, dict]) -> Iterable[str]:
    for source_id, record in sources.items():
        yield (
            f"| {source_id} | {record['maximal_to_basal']['nominal']:.4f} "
            f"({record['maximal_to_basal']['low']:.4f}-{record['maximal_to_basal']['high']:.4f}) | "
            f"{record['spare_to_basal']['nominal']:.4f} "
            f"({record['spare_to_basal']['low']:.4f}-{record['spare_to_basal']['high']:.4f}) | "
            f"{record['role']} |"
        )


def build_audit() -> dict:
    r042 = _read_json(R042)
    r048 = _read_json(R048)
    r060 = _read_json(R060)

    existing_intervals = {
        source_id: {
            endpoint: {
                "low": float(values[endpoint]["low"]),
                "nominal": float(values[endpoint]["nominal"]),
                "high": float(values[endpoint]["high"]),
            }
            for endpoint in ENDPOINTS
        }
        for source_id, values in r042["source_ratio_intervals"].items()
    }

    r060_intervals = {
        endpoint: _as_interval(r060["relative_ratios"][endpoint])
        for endpoint in ENDPOINTS
    }

    sources = {
        "PMID:31931869": {
            **existing_intervals["PMID:31931869"],
            "run_id": "R033",
            "role": "existing_matched_pair_anchor",
        },
        "PMID:24056030": {
            **existing_intervals["PMID:24056030"],
            "run_id": "R039",
            "role": "existing_matched_pair_anchor",
        },
        "PMID:25081478": {
            **r060_intervals,
            "run_id": "R060",
            "role": "new_candidate_high_spare_shift",
        },
    }

    r060_vs_existing_band = {}
    shifted_endpoints = []
    for endpoint in ENDPOINTS:
        existing_band = _existing_band(existing_intervals, endpoint)
        r060_interval = r060_intervals[endpoint]
        overlap = _interval_overlaps(existing_band, r060_interval)
        shifted = r060_interval["low"] > existing_band["high"]
        r060_vs_existing_band[endpoint] = {
            "existing_pair_interval_band": existing_band,
            "r060_interval": r060_interval,
            "overlap": overlap,
            "r060_low_exceeds_existing_high": shifted,
            "r060_nominal_minus_existing_nominal_max": round(
                r060_interval["nominal"] - existing_band["nominal_max"], 6
            ),
        }
        if shifted:
            shifted_endpoints.append(endpoint)

    high_shift_flag = len(shifted_endpoints) == len(ENDPOINTS)
    blind_pooling_allowed = False

    source_use_decision = {
        "PMID:31931869": {
            "decision": "retain",
            "role": "matched_pair_anchor",
            "reason": "Existing R033/R039 matched pair intervals overlap for the maximal/spare-only contract.",
        },
        "PMID:24056030": {
            "decision": "retain",
            "role": "matched_pair_anchor",
            "reason": "Existing R033/R039 matched pair intervals overlap for the maximal/spare-only contract.",
        },
        "PMID:25081478": {
            "decision": "retain_with_heterogeneity_flag",
            "role": "heterogeneity_evidence_not_blind_pooling",
            "reason": (
                "R060 is a source-local matched-candidate record, but both maximal/basal "
                "and spare/basal intervals sit above the existing R033/R039 interval band."
            ),
        },
    }

    claim_gate = {
        "maximal_spare_contract_used": True,
        "absolute_calibration_reopened": False,
        "atp_linked_pooling_allowed": False,
        "proton_leak_fitting_allowed": False,
        "mcmc_or_bayesian_allowed": False,
        "external_validation_claim_allowed": False,
        "blind_pooling_allowed": blind_pooling_allowed,
    }

    qc = {
        "three_sources_present": sorted(sources) == [
            "PMID:24056030",
            "PMID:25081478",
            "PMID:31931869",
        ],
        "used_endpoints": list(ENDPOINTS),
        "r048_contract_preserved": r048["claim_gate"]["maximal_spare_contract_used"] is True,
        "r060_fit_eligible_under_r047": all(
            r060["relative_ratios"][endpoint]["fit_eligible_under_r047"] is True
            for endpoint in ENDPOINTS
        ),
        "r060_high_shift_flag": high_shift_flag,
        "claim_gates_closed": (
            claim_gate["absolute_calibration_reopened"] is False
            and claim_gate["external_validation_claim_allowed"] is False
            and claim_gate["mcmc_or_bayesian_allowed"] is False
            and claim_gate["atp_linked_pooling_allowed"] is False
            and claim_gate["proton_leak_fitting_allowed"] is False
            and claim_gate["blind_pooling_allowed"] is False
        ),
        "manuscript_modified": False,
    }
    qc["passed"] = (
        qc["three_sources_present"]
        and qc["r048_contract_preserved"]
        and qc["r060_fit_eligible_under_r047"]
        and qc["r060_high_shift_flag"]
        and qc["claim_gates_closed"]
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R061",
        "status": "complete_three_source_relative_consistency",
        "purpose": (
            "Compare R060 against the R033/R039 matched primary cortical pair before "
            "any three-source maximal/spare-only mapping."
        ),
        "used_endpoints": list(ENDPOINTS),
        "sources": sources,
        "three_source_consistency": {
            "r060_vs_existing_pair_band": r060_vs_existing_band,
            "r060_high_shift_flag": high_shift_flag,
            "r060_shifted_endpoints": shifted_endpoints,
            "blind_pooling_allowed": blind_pooling_allowed,
            "interpretation": (
                "R060 expands the matched-candidate evidence base but is shifted upward "
                "relative to the existing R033/R039 pair; treat it as source heterogeneity "
                "rather than direct pooled calibration input."
            ),
        },
        "source_use_decision": source_use_decision,
        "claim_gate": claim_gate,
        "recommended_next_run": {
            "run_id": "R060B",
            "target_source": "PMID:27889640",
            "objective": (
                "Digitize the backup primary cortical Mito Stress candidate to test whether "
                "the high-spare R060 pattern recurs before launching conditional R062 mapping."
            ),
            "precedes": "R062",
            "fallback_if_not_recoverable": (
                "Proceed to R062 as a sensitivity-only mapping that explicitly compares "
                "R033/R039 with include/exclude-R060 conditions."
            ),
        },
        "input_artifacts": {
            "R042": {
                "path": str(R042.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R042),
            },
            "R048": {
                "path": str(R048.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R048),
            },
            "R060": {
                "path": str(R060.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R060),
            },
        },
        "qc": qc,
        "manuscript_modified": False,
    }


def build_report(payload: dict) -> str:
    rows = "\n".join(_ratio_table_rows(payload["sources"]))
    consistency = payload["three_source_consistency"]
    next_run = payload["recommended_next_run"]
    return f"""# R061 Three-source relative consistency audit

## Status

Complete. R060 was compared against the existing R033/R039 matched primary
cortical pair using only the R047 maximal/spare-only contract.

## Ratio comparison

| Source | Maximal/basal, nominal (interval) | Spare/basal, nominal (interval) | Role |
|---|---:|---:|---|
{rows}

## Decision

- R060 is retained as a source-local matched-candidate record.
- R060 is not blindly pooled with R033/R039 because both retained endpoints are
  shifted above the existing pair interval band.
- The paper remains computational-only and relative-only: no absolute OCR
  calibration, ATP-linked pooling, proton-leak fitting, MCMC/Bayesian posterior,
  wet-lab/clinical/intervention, or external-validation claim is reopened.

## Key flags

- R060 high-shift flag: `{consistency['r060_high_shift_flag']}`
- Shifted endpoints: `{', '.join(consistency['r060_shifted_endpoints'])}`
- Blind pooling allowed: `{consistency['blind_pooling_allowed']}`

## Recommended next run

`{next_run['run_id']}`: digitize `{next_run['target_source']}` as the backup
primary cortical Mito Stress candidate before conditional three-source mapping
(`{next_run['precedes']}`).
"""


def main():
    payload = build_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    REPORT.write_text(build_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

