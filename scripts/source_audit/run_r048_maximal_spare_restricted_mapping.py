"""R048 maximal/spare-only restricted mapping.

R047 freezes the common observation contract to two source-local ratios:
``maximal_to_basal`` and ``spare_to_basal``. This script re-ranks the
prequalified R041 16-point ``Vmax_CV``/``g_H`` grid under that narrower
contract and propagates the R042 digitization intervals for those two
endpoints only.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
R041 = ROOT / "refine-logs" / "runs" / "R041" / "restricted_identifiability_screen.json"
R042 = ROOT / "refine-logs" / "runs" / "R042" / "digitization_uncertainty_propagation.json"
R047 = ROOT / "refine-logs" / "runs" / "R047" / "cross_source_formula_coordination.json"
OUT = (
    ROOT
    / "refine-logs"
    / "runs"
    / "R048"
    / "maximal_spare_restricted_mapping.json"
)
ENDPOINTS = ("maximal_to_basal", "spare_to_basal")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _subset(mapping, endpoints=ENDPOINTS):
    return {endpoint: float(mapping[endpoint]) for endpoint in endpoints}


def _log_ratio_residual(predicted, observed, endpoints=ENDPOINTS):
    residuals = {}
    for endpoint in endpoints:
        pred = float(predicted[endpoint])
        obs = float(observed[endpoint])
        if pred <= 0 or obs <= 0:
            raise ValueError(f"{endpoint} must be positive")
        residuals[endpoint] = math.log(pred) - math.log(obs)
    return residuals


def _loss(predicted, observed, endpoints=ENDPOINTS):
    residuals = _log_ratio_residual(predicted, observed, endpoints)
    return sum(value * value for value in residuals.values()) / len(residuals)


def _valid_grid_points(r041):
    return [
        row
        for row in r041["grid_results"]
        if row["status"] == "ok" and row.get("stationary")
    ]


def _rank(grid_points, train_ratios, reserve_ratios):
    ranked = []
    for row in grid_points:
        predicted = _subset(row["relative_constraints"])
        train_loss = _loss(predicted, train_ratios)
        reserve_loss = _loss(predicted, reserve_ratios)
        ranked.append({
            "multipliers": row["multipliers"],
            "train_loss": train_loss,
            "reserve_loss": reserve_loss,
            "train_log_ratio_residual": _log_ratio_residual(
                predicted, train_ratios
            ),
            "reserve_log_ratio_residual": _log_ratio_residual(
                predicted, reserve_ratios
            ),
            "predicted_relative_constraints": predicted,
            "max_stage_derivative": row["max_stage_derivative"],
        })
    ranked.sort(key=lambda item: item["train_loss"])
    return ranked


def _near_best_summary(ranked):
    best = ranked[0]["train_loss"]
    threshold = best + max(0.01, 0.25 * abs(best))
    near = [row for row in ranked if row["train_loss"] <= threshold]
    return {
        "best_train_loss": best,
        "near_best_threshold": threshold,
        "near_best_count": len(near),
        "near_best_multipliers": [row["multipliers"] for row in near],
        "single_winner": len(near) == 1,
    }


def _interval_corners(intervals):
    values = [
        (endpoint, float(intervals[endpoint]["low"]), float(intervals[endpoint]["high"]))
        for endpoint in ENDPOINTS
    ]
    for picks in itertools.product((0, 1), repeat=len(values)):
        yield {
            endpoint: low if pick == 0 else high
            for pick, (endpoint, low, high) in zip(picks, values)
        }


def _rank_stability(grid_points, train_intervals, reserve_intervals):
    winner_counts = {}
    top_train_losses = []
    winner_reserve_losses = []
    reserve_corners = list(_interval_corners(reserve_intervals))
    for train_corner in _interval_corners(train_intervals):
        ranked = _rank(grid_points, train_corner, reserve_corners[0])
        winner = ranked[0]
        key = json.dumps(winner["multipliers"], sort_keys=True)
        winner_counts[key] = winner_counts.get(key, 0) + 1
        top_train_losses.append(winner["train_loss"])
        winner_reserve_losses.extend(
            _loss(winner["predicted_relative_constraints"], reserve_corner)
            for reserve_corner in reserve_corners
        )
    return {
        "stable_single_winner": len(winner_counts) == 1,
        "unique_winners": len(winner_counts),
        "winner_counts": winner_counts,
        "top_train_loss_interval": {
            "low": min(top_train_losses),
            "high": max(top_train_losses),
        },
        "winner_reserve_loss_interval": {
            "low": min(winner_reserve_losses),
            "high": max(winner_reserve_losses),
        },
    }


def _between_source_overlap(r042):
    overlap = {}
    for endpoint in ENDPOINTS:
        overlap[endpoint] = r042["between_source_interval_overlap"][endpoint]
    return overlap


def run_mapping():
    r041 = _read_json(R041)
    r042 = _read_json(R042)
    r047 = _read_json(R047)
    contract = r047["minimum_common_observation_contract"]
    if contract["fit_or_holdout_endpoints"] != list(ENDPOINTS):
        raise ValueError("R047 contract no longer matches the R048 endpoint set.")

    grid_points = _valid_grid_points(r041)
    source_ratios = {
        source: _subset(ratios)
        for source, ratios in r041["source_ratios"].items()
    }
    source_intervals = r042["source_ratio_intervals"]

    directions = {
        "fit_R039_reserve_R033": {
            "train_source": "PMID:24056030",
            "reserve_source": "PMID:31931869",
        },
        "fit_R033_reserve_R039": {
            "train_source": "PMID:31931869",
            "reserve_source": "PMID:24056030",
        },
    }
    fit_directions = {}
    for name, spec in directions.items():
        train_source = spec["train_source"]
        reserve_source = spec["reserve_source"]
        ranked = _rank(
            grid_points,
            source_ratios[train_source],
            source_ratios[reserve_source],
        )
        fit_directions[name] = {
            "train_source": train_source,
            "reserve_source": reserve_source,
            "top_ranked": ranked[:5],
            "near_best_summary": _near_best_summary(ranked),
            "digitization_interval_rank_stability": _rank_stability(
                grid_points,
                source_intervals[train_source],
                source_intervals[reserve_source],
            ),
        }

    output = {
        "run_id": "R048",
        "screen_status": "complete_maximal_spare_restricted_mapping",
        "contract_source": str(R047.relative_to(ROOT)).replace("\\", "/"),
        "grid_source": str(R041.relative_to(ROOT)).replace("\\", "/"),
        "uncertainty_source": str(R042.relative_to(ROOT)).replace("\\", "/"),
        "used_endpoints": list(ENDPOINTS),
        "excluded_endpoints": [
            "atp_linked_to_basal",
            "proton_leak_to_basal",
            "independent_oligomycin_to_basal",
            "absolute_ocr",
        ],
        "parameter_families": r041["parameter_families"],
        "grid": r041["grid"],
        "protocol": r041["protocol"],
        "source_ratios": source_ratios,
        "between_source_interval_overlap": _between_source_overlap(r042),
        "fit_directions": fit_directions,
        "qc": {
            "stationary_grid_points_used": len(grid_points),
            "failed_points": r041["qc"]["failed_points"],
            "nonstationary_points_excluded": r041["qc"]["nonstationary_points"],
        },
        "claim_gate": {
            "maximal_spare_contract_used": True,
            "atp_linked_used": False,
            "proton_leak_fit_target_used": False,
            "source_values_pooled": False,
            "rank_stable_under_digitization": all(
                direction["digitization_interval_rank_stability"][
                    "stable_single_winner"
                ]
                for direction in fit_directions.values()
            ),
            "absolute_calibration_allowed": False,
            "figure1_mcmc_allowed": False,
            "external_validation_claim_allowed": False,
        },
        "interpretation": (
            "The reduced endpoint contract removes the ATP-linked mismatch from "
            "the objective, but the result remains a source-holdout diagnostic. "
            "It is not an absolute calibration or external validation because "
            "normalization/protocol differences and weak biological mapping "
            "remain unresolved."
        ),
    }
    return output


def main():
    output = run_mapping()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

