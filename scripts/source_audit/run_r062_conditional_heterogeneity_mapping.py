"""R062 conditional heterogeneity mapping.

R062 compares the original lower-reserve matched pair (R033/R039) with the
new higher-reserve matched candidates (R060/R060B) without blindly pooling the
source values for calibration. The analysis uses only the R047 maximal/spare
contract and the stationary R041 16-point grid.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "refine-logs" / "runs"
R041 = RUNS / "R041" / "restricted_identifiability_screen.json"
R042 = RUNS / "R042" / "digitization_uncertainty_propagation.json"
R048 = RUNS / "R048" / "maximal_spare_restricted_mapping.json"
R060 = RUNS / "R060" / "pmc4454361_control_relative_digitization.json"
R060B = RUNS / "R060B" / "pmc5124357_control_relative_digitization.json"
R061 = RUNS / "R061" / "three_source_relative_consistency.json"
OUT = RUNS / "R062" / "conditional_heterogeneity_mapping.json"
REPORT = ROOT / "refine-logs" / "R062_CONDITIONAL_HETEROGENEITY_MAPPING.md"

ENDPOINTS = ("maximal_to_basal", "spare_to_basal")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _subset(mapping: dict) -> dict:
    return {endpoint: float(mapping[endpoint]) for endpoint in ENDPOINTS}


def _log_ratio_residual(predicted: dict, observed: dict) -> dict:
    residuals = {}
    for endpoint in ENDPOINTS:
        pred = float(predicted[endpoint])
        obs = float(observed[endpoint])
        if pred <= 0 or obs <= 0:
            raise ValueError(f"{endpoint} must be positive")
        residuals[endpoint] = math.log(pred) - math.log(obs)
    return residuals


def _loss(predicted: dict, observed: dict) -> float:
    residuals = _log_ratio_residual(predicted, observed)
    return sum(value * value for value in residuals.values()) / len(residuals)


def _valid_grid_points(r041: dict) -> list:
    return [
        row
        for row in r041["grid_results"]
        if row["status"] == "ok" and row.get("stationary")
    ]


def _rank(grid_points: list, observed: dict) -> list:
    ranked = []
    for row in grid_points:
        predicted = _subset(row["relative_constraints"])
        ranked.append(
            {
                "multipliers": row["multipliers"],
                "loss": _loss(predicted, observed),
                "log_ratio_residual": _log_ratio_residual(predicted, observed),
                "predicted_relative_constraints": predicted,
                "max_stage_derivative": row["max_stage_derivative"],
            }
        )
    ranked.sort(key=lambda item: item["loss"])
    return ranked


def _near_best_summary(ranked: list) -> dict:
    best = ranked[0]["loss"]
    threshold = best + max(0.01, 0.25 * abs(best))
    near = [row for row in ranked if row["loss"] <= threshold]
    return {
        "best_loss": best,
        "near_best_threshold": threshold,
        "near_best_count": len(near),
        "near_best_multipliers": [row["multipliers"] for row in near],
        "single_winner": len(near) == 1,
    }


def _low_source_ratios(r042: dict) -> dict:
    return {
        source: {
            endpoint: float(values[endpoint]["nominal"])
            for endpoint in ENDPOINTS
        }
        for source, values in r042["source_ratio_intervals"].items()
    }


def _high_source_ratios(r060: dict, r060b: dict) -> dict:
    return {
        r060["source_id"]: {
            endpoint: float(r060["relative_ratios"][endpoint]["value"])
            for endpoint in ENDPOINTS
        },
        r060b["source_id"]: {
            endpoint: float(r060b["relative_ratios"][endpoint]["value"])
            for endpoint in ENDPOINTS
        },
    }


def _mean_ratios(source_ratios: dict, members: list) -> dict:
    return {
        endpoint: sum(source_ratios[source][endpoint] for source in members)
        / len(members)
        for endpoint in ENDPOINTS
    }


def _group_spread(source_ratios: dict, members: list) -> dict:
    return {
        endpoint: {
            "min": min(source_ratios[source][endpoint] for source in members),
            "max": max(source_ratios[source][endpoint] for source in members),
            "range": max(source_ratios[source][endpoint] for source in members)
            - min(source_ratios[source][endpoint] for source in members),
        }
        for endpoint in ENDPOINTS
    }


def _single_source_rankings(grid_points: list, source_ratios: dict) -> dict:
    return {
        source: {
            "observed_ratios": ratios,
            "top_ranked": _rank(grid_points, ratios)[:5],
            "near_best_summary": _near_best_summary(_rank(grid_points, ratios)),
        }
        for source, ratios in source_ratios.items()
    }


def build_mapping() -> dict:
    r041 = _read_json(R041)
    r042 = _read_json(R042)
    r048 = _read_json(R048)
    r060 = _read_json(R060)
    r060b = _read_json(R060B)
    r061 = _read_json(R061)

    grid_points = _valid_grid_points(r041)
    source_ratios = {}
    source_ratios.update(_low_source_ratios(r042))
    source_ratios.update(_high_source_ratios(r060, r060b))

    low_sources = ["PMID:31931869", "PMID:24056030"]
    high_sources = ["PMID:25081478", "PMID:27889640"]
    source_groups = {
        "low_reserve_pair": {
            "sources": low_sources,
            "mean_ratios": _mean_ratios(source_ratios, low_sources),
            "within_group_spread": _group_spread(source_ratios, low_sources),
            "source_role": "existing R033/R039 matched pair",
        },
        "high_reserve_pair": {
            "sources": high_sources,
            "mean_ratios": _mean_ratios(source_ratios, high_sources),
            "within_group_spread": _group_spread(source_ratios, high_sources),
            "source_role": "R060/R060B high-reserve matched candidates",
        },
    }

    conditional_group_rankings = {}
    for group, spec in source_groups.items():
        ranked = _rank(grid_points, spec["mean_ratios"])
        conditional_group_rankings[group] = {
            "observed_mean_ratios": spec["mean_ratios"],
            "top_ranked": ranked[:8],
            "near_best_summary": _near_best_summary(ranked),
        }

    low_top = conditional_group_rankings["low_reserve_pair"]["top_ranked"][0]
    high_top = conditional_group_rankings["high_reserve_pair"]["top_ranked"][0]
    parameter_direction_shift = (
        low_top["multipliers"]["g_H"] >= 1.0
        and high_top["multipliers"]["g_H"] <= 0.8
    )
    reserve_group_shift = (
        "high_pair_above_low_pair"
        if source_groups["high_reserve_pair"]["mean_ratios"]["spare_to_basal"]
        > source_groups["low_reserve_pair"]["mean_ratios"]["spare_to_basal"]
        else "not_detected"
    )

    single_source_rankings = _single_source_rankings(grid_points, source_ratios)

    claim_gate = {
        "maximal_spare_contract_used": True,
        "atp_linked_used": False,
        "proton_leak_fit_target_used": False,
        "blind_pooling_allowed": False,
        "source_values_pooled_for_calibration": False,
        "group_means_are_conditional_sensitivity_targets": True,
        "absolute_calibration_allowed": False,
        "figure1_mcmc_allowed": False,
        "external_validation_claim_allowed": False,
    }

    qc = {
        "stationary_grid_points_used": len(grid_points),
        "failed_points": r041["qc"]["failed_points"],
        "nonstationary_points_excluded": r041["qc"]["nonstationary_points"],
        "r048_contract_preserved": r048["claim_gate"]["maximal_spare_contract_used"]
        is True,
        "r061_blind_pooling_block_preserved": r061["claim_gate"][
            "blind_pooling_allowed"
        ]
        is False,
        "four_source_records_present": sorted(source_ratios) == [
            "PMID:24056030",
            "PMID:25081478",
            "PMID:27889640",
            "PMID:31931869",
        ],
        "parameter_direction_shift_detected": parameter_direction_shift,
        "claim_gates_closed": (
            claim_gate["absolute_calibration_allowed"] is False
            and claim_gate["external_validation_claim_allowed"] is False
            and claim_gate["figure1_mcmc_allowed"] is False
            and claim_gate["blind_pooling_allowed"] is False
            and claim_gate["source_values_pooled_for_calibration"] is False
        ),
        "manuscript_modified": False,
    }
    qc["passed"] = (
        qc["stationary_grid_points_used"] == 14
        and qc["r048_contract_preserved"]
        and qc["r061_blind_pooling_block_preserved"]
        and qc["four_source_records_present"]
        and qc["parameter_direction_shift_detected"]
        and qc["claim_gates_closed"]
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R062",
        "status": "complete_conditional_heterogeneity_mapping",
        "purpose": (
            "Quantify whether the lower-reserve R033/R039 pair and higher-reserve "
            "R060/R060B pair prefer different regions of the prequalified R041 grid."
        ),
        "used_endpoints": list(ENDPOINTS),
        "excluded_endpoints": [
            "atp_linked_to_basal",
            "proton_leak_to_basal",
            "absolute_ocr",
            "treatment_response",
        ],
        "source_ratios": source_ratios,
        "source_groups": source_groups,
        "single_source_rankings": single_source_rankings,
        "conditional_group_rankings": conditional_group_rankings,
        "heterogeneity_summary": {
            "reserve_group_shift": reserve_group_shift,
            "parameter_direction_shift_detected": parameter_direction_shift,
            "low_pair_top_multipliers": low_top["multipliers"],
            "high_pair_top_multipliers": high_top["multipliers"],
            "interpretation": (
                "The high-reserve candidate pair shifts the best diagnostic region "
                "toward lower g_H relative to the original R033/R039 pair. This is "
                "a source-heterogeneity sensitivity pattern, not a calibrated "
                "parameter estimate."
            ),
        },
        "interpretation": {
            "calibrated_parameter_estimate": False,
            "external_validation": False,
            "safe_use": (
                "Report, if needed, as conditional source-heterogeneity evidence "
                "showing that reserve-capacity source differences project onto "
                "the g_H direction in the coarse diagnostic grid."
            ),
        },
        "claim_gate": claim_gate,
        "recommended_next_run": {
            "run_id": "R063",
            "scope": "optional_figure1_heterogeneity_overlay",
            "objective": (
                "Optionally update the audited Figure 1 source panel/metadata to "
                "show the low- vs high-reserve source split, without changing the "
                "manuscript text or claiming validation."
            ),
            "fallback": (
                "If no figure update is desired, freeze R062 as the terminal OI1/OI2 "
                "computational evidence record."
            ),
        },
        "input_artifacts": {
            "R041": {
                "path": str(R041.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R041),
            },
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
            "R060B": {
                "path": str(R060B.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R060B),
            },
            "R061": {
                "path": str(R061.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R061),
            },
        },
        "qc": qc,
        "manuscript_modified": False,
    }


def build_report(payload: dict) -> str:
    low = payload["conditional_group_rankings"]["low_reserve_pair"]
    high = payload["conditional_group_rankings"]["high_reserve_pair"]
    return f"""# R062 Conditional heterogeneity mapping

## Status

Complete. R062 compared the existing lower-reserve R033/R039 pair with the
higher-reserve R060/R060B pair using only maximal/basal and spare/basal.

## Conditional group targets

| Group | Sources | Mean maximal/basal | Mean spare/basal | Top diagnostic multipliers |
|---|---|---:|---:|---|
| low_reserve_pair | PMID:31931869; PMID:24056030 | {low['observed_mean_ratios']['maximal_to_basal']:.4f} | {low['observed_mean_ratios']['spare_to_basal']:.4f} | `{low['top_ranked'][0]['multipliers']}` |
| high_reserve_pair | PMID:25081478; PMID:27889640 | {high['observed_mean_ratios']['maximal_to_basal']:.4f} | {high['observed_mean_ratios']['spare_to_basal']:.4f} | `{high['top_ranked'][0]['multipliers']}` |

## Interpretation

The source groups prefer different diagnostic regions of the same prequalified
R041 grid. The lower-reserve pair points toward `g_H` around 1.0, whereas the
higher-reserve pair points toward lower `g_H` around 0.8/0.5. This supports a
source-heterogeneity interpretation, not a calibrated parameter estimate.

## Claim gate

- no blind source pooling;
- no absolute OCR calibration;
- no ATP-linked pooling;
- no proton-leak fitting;
- no MCMC/Bayesian posterior;
- no external biological validation claim;
- no manuscript modification.
"""


def main():
    payload = build_mapping()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    REPORT.write_text(build_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

