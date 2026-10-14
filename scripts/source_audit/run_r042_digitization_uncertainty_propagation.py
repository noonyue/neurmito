"""R042 digitization/protocol uncertainty propagation.

The calculation propagates each source's recorded pixel uncertainty through
source-local OCR ratios, then checks whether the R041 restricted-grid ranking
is stable under the resulting interval corners.

Protocol differences are not assigned fabricated numeric priors. They are
retained as a qualitative claim gate: if digitization intervals do not explain
between-source disagreement, the disagreement is attributed to unresolved
source/protocol/model-mapping uncertainty rather than to calibration evidence.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.relative_ocr_constraints import (  # noqa: E402
    RelativeOCRRecord,
    derive_relative_constraints,
    source_local_constraint_loss,
)
from scripts.extract_r033_pmc6958642_fig2 import build_record as build_r033  # noqa: E402
from scripts.extract_r039_pmc3859859_fig2 import build_record as build_r039  # noqa: E402


R041_PATH = ROOT / "refine-logs" / "runs" / "R041" / "restricted_identifiability_screen.json"
OUT = ROOT / "refine-logs" / "runs" / "R042" / "digitization_uncertainty_propagation.json"
RATIO_KEYS = (
    "maximal_to_basal",
    "spare_to_basal",
    "atp_linked_to_basal",
    "proton_leak_to_basal",
)
METRIC_MAP = {
    "basal_ocr": "basal_ocr",
    "maximal_ocr": "maximal_ocr",
    "atp_linked": "atp_linked",
    "proton_leak": "proton_leak",
}


def _digitize_value(axis_zero_y: float, axis_top_y: float,
                    axis_top_value: float, bar_top_y: float) -> float:
    return (axis_zero_y - bar_top_y) * axis_top_value / (axis_zero_y - axis_top_y)


def metric_intervals(payload: Mapping[str, object]) -> Dict[str, Dict[str, float]]:
    digitization = payload["digitization"]  # type: ignore[index]
    axis_zero_y = float(digitization["axis_zero_y"])  # type: ignore[index]
    axis_top_y = float(digitization["axis_top_y"])  # type: ignore[index]
    axis_top_value = float(digitization["axis_top_value"])  # type: ignore[index]
    pixel_uncertainty = float(digitization["pixel_uncertainty"])  # type: ignore[index]
    bar_top_y = digitization["bar_top_y"]  # type: ignore[index]
    intervals = {}
    for metric in METRIC_MAP:
        center = float(bar_top_y[metric])  # type: ignore[index]
        values = [
            _digitize_value(axis_zero_y, axis_top_y, axis_top_value, center - pixel_uncertainty),
            _digitize_value(axis_zero_y, axis_top_y, axis_top_value, center + pixel_uncertainty),
        ]
        intervals[metric] = {
            "low": min(values),
            "high": max(values),
            "nominal": float(payload["metrics"][metric]),  # type: ignore[index]
        }
    return intervals


def _record_from_metrics(payload: Mapping[str, object],
                         metrics: Mapping[str, float]) -> RelativeOCRRecord:
    return RelativeOCRRecord(
        source_id=str(payload["source_id"]),
        preparation=str(payload["preparation"]),
        normalization_basis=str(payload["normalization_basis"]),
        metrics=metrics,
        provenance_status=str(payload["provenance_status"]),
        absolute_calibration_eligible=bool(
            payload.get("absolute_calibration_eligible", False)
        ),
    )


def ratio_corners(payload: Mapping[str, object]) -> Iterable[Dict[str, float]]:
    intervals = metric_intervals(payload)
    for corner in itertools.product(("low", "high"), repeat=len(METRIC_MAP)):
        metrics = {
            metric: intervals[metric][choice]
            for metric, choice in zip(METRIC_MAP, corner)
        }
        try:
            yield derive_relative_constraints(_record_from_metrics(payload, metrics))
        except ValueError:
            continue


def ratio_intervals(payload: Mapping[str, object]) -> Dict[str, Dict[str, float]]:
    nominal = derive_relative_constraints(
        _record_from_metrics(payload, payload["metrics"])  # type: ignore[arg-type]
    )
    corners = list(ratio_corners(payload))
    return {
        key: {
            "low": min(float(row[key]) for row in corners),
            "high": max(float(row[key]) for row in corners),
            "nominal": float(nominal[key]),
        }
        for key in RATIO_KEYS
    }


def interval_overlap(left: Mapping[str, Mapping[str, float]],
                     right: Mapping[str, Mapping[str, float]]):
    overlap = {}
    for key in RATIO_KEYS:
        low = max(float(left[key]["low"]), float(right[key]["low"]))
        high = min(float(left[key]["high"]), float(right[key]["high"]))
        overlap[key] = {
            "overlaps": low <= high,
            "intersection_low": low if low <= high else None,
            "intersection_high": high if low <= high else None,
            "gap": 0.0 if low <= high else low - high,
        }
    return overlap


def _stationary_grid(r041: Mapping[str, object]):
    return [
        row for row in r041["grid_results"]  # type: ignore[index]
        if row["status"] == "ok" and row.get("stationary")
    ]


def rank_stability(grid_results, train_corners: Iterable[Mapping[str, float]],
                   reserve_nominal: Mapping[str, float]):
    winners = {}
    top_losses = []
    reserve_losses_for_winner = []
    for target in train_corners:
        ranked = []
        for row in grid_results:
            predicted = row["relative_constraints"]
            train_loss = source_local_constraint_loss(predicted, target)
            reserve_loss = source_local_constraint_loss(predicted, reserve_nominal)
            ranked.append((train_loss, reserve_loss, row))
        ranked.sort(key=lambda item: item[0])
        train_loss, reserve_loss, winner = ranked[0]
        key = json.dumps(winner["multipliers"], sort_keys=True)
        winners[key] = winners.get(key, 0) + 1
        top_losses.append(train_loss)
        reserve_losses_for_winner.append(reserve_loss)
    return {
        "winner_counts": winners,
        "unique_winners": len(winners),
        "top_train_loss_interval": {
            "low": min(top_losses),
            "high": max(top_losses),
        },
        "winner_reserve_loss_interval": {
            "low": min(reserve_losses_for_winner),
            "high": max(reserve_losses_for_winner),
        },
        "stable_single_winner": len(winners) == 1,
    }


def main():
    r033 = build_r033()
    r039 = build_r039()
    r041 = json.loads(R041_PATH.read_text(encoding="utf-8"))
    grid = _stationary_grid(r041)
    r033_intervals = ratio_intervals(r033)
    r039_intervals = ratio_intervals(r039)
    r033_nominal = derive_relative_constraints(
        _record_from_metrics(r033, r033["metrics"])
    )
    r039_nominal = derive_relative_constraints(
        _record_from_metrics(r039, r039["metrics"])
    )
    output = {
        "run_id": "R042",
        "screen_status": "complete_digitization_uncertainty_diagnostic",
        "source_ratio_intervals": {
            "PMID:31931869": r033_intervals,
            "PMID:24056030": r039_intervals,
        },
        "between_source_interval_overlap": interval_overlap(
            r033_intervals, r039_intervals
        ),
        "r041_rank_stability_under_digitization_corners": {
            "fit_R039_reserve_R033": rank_stability(
                grid, list(ratio_corners(r039)), r033_nominal
            ),
            "fit_R033_reserve_R039": rank_stability(
                grid, list(ratio_corners(r033)), r039_nominal
            ),
        },
        "protocol_uncertainty": {
            "quantified": False,
            "reason": (
                "Platform, normalization, inhibitor timing/concentration, and "
                "laboratory protocol differences are retained as source metadata; "
                "no empirical protocol-error prior is available."
            ),
        },
        "claim_gate": {
            "weak_identifiability_stable": True,
            "eligible_for_external_validation": False,
            "absolute_calibration_allowed": False,
            "decision": (
                "Digitization uncertainty is not enough to convert R041 into a "
                "calibrated or externally validated result. Protocol uncertainty "
                "remains unresolved."
            ),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


