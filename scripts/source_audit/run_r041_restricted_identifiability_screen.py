"""R041 restricted ODE-to-source identifiability screen.

This script uses a deliberately small two-parameter-family grid:

* ``Vmax_CV`` multiplier: ATP synthase capacity
* ``g_H`` multiplier: basal proton conductance

The grid is evaluated once and then used for two source-holdout directions:
fit R039 and reserve R033, then fit R033 and reserve R039.  The result is a
diagnostic identifiability screen only; it does not establish external
biological validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, Mapping, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.relative_ocr_constraints import (  # noqa: E402
    RelativeOCRRecord,
    derive_relative_constraints,
    log_ratio_residual,
    source_local_constraint_loss,
)
from module1.bazil2016_ode import DEFAULT_PARAMS  # noqa: E402
from module1.mito_stress_observables import run_mito_stress_protocol  # noqa: E402
from scripts.extract_r033_pmc6958642_fig2 import build_record as build_r033  # noqa: E402
from scripts.extract_r039_pmc3859859_fig2 import build_record as build_r039  # noqa: E402


OUT = ROOT / "refine-logs" / "runs" / "R041" / "restricted_identifiability_screen.json"
V_MAX_CV_GRID = (0.5, 0.8, 1.0, 1.5)
G_H_GRID = (0.5, 0.8, 1.0, 1.5)


def _as_relative_record(payload: Mapping[str, object]) -> RelativeOCRRecord:
    return RelativeOCRRecord(
        source_id=str(payload["source_id"]),
        preparation=str(payload["preparation"]),
        normalization_basis=str(payload["normalization_basis"]),
        metrics=payload["metrics"],  # type: ignore[arg-type]
        provenance_status=str(payload["provenance_status"]),
        absolute_calibration_eligible=bool(
            payload.get("absolute_calibration_eligible", False)
        ),
    )


def _evaluate_grid_point(multipliers: Tuple[float, float]) -> Dict[str, object]:
    vmax_cv_mult, g_h_mult = multipliers
    params = dict(DEFAULT_PARAMS)
    params["Vmax_CV"] *= vmax_cv_mult
    params["g_H"] *= g_h_mult
    try:
        protocol = run_mito_stress_protocol(
            params=params,
            duration_s=10000.0,
            sample_count=101,
            stationarity_tolerance=1e-6,
        )
        return {
            "status": "ok",
            "multipliers": {
                "Vmax_CV": float(vmax_cv_mult),
                "g_H": float(g_h_mult),
            },
            "relative_constraints": protocol["relative_constraints"],
            "stationary": bool(protocol["protocol"]["stationary"]),
            "max_stage_derivative": max(
                float(stage["max_abs_derivative"])
                for stage in protocol["stages"].values()
            ),
        }
    except Exception as exc:  # pragma: no cover - retained for audit output
        return {
            "status": "failed",
            "multipliers": {
                "Vmax_CV": float(vmax_cv_mult),
                "g_H": float(g_h_mult),
            },
            "error": f"{type(exc).__name__}: {exc}",
        }


def _rank_for_train_source(
    grid_results: Iterable[Mapping[str, object]],
    train_ratios: Mapping[str, float],
    reserve_ratios: Mapping[str, float],
):
    ranked = []
    for item in grid_results:
        if item["status"] != "ok" or not item.get("stationary"):
            continue
        predicted = item["relative_constraints"]  # type: ignore[assignment]
        train_loss = source_local_constraint_loss(predicted, train_ratios)
        reserve_loss = source_local_constraint_loss(predicted, reserve_ratios)
        ranked.append({
            "multipliers": item["multipliers"],
            "train_loss": train_loss,
            "reserve_loss": reserve_loss,
            "train_log_ratio_residual": log_ratio_residual(
                predicted, train_ratios
            ),
            "reserve_log_ratio_residual": log_ratio_residual(
                predicted, reserve_ratios
            ),
            "predicted_relative_constraints": predicted,
            "max_stage_derivative": item["max_stage_derivative"],
        })
    ranked.sort(key=lambda row: row["train_loss"])
    return ranked


def _summarize_nonidentifiability(ranked):
    if not ranked:
        return {"status": "no_stationary_grid_points"}
    best = ranked[0]["train_loss"]
    near = [
        row for row in ranked
        if row["train_loss"] <= best + max(0.05, 0.25 * abs(best))
    ]
    return {
        "status": "diagnostic_only",
        "best_train_loss": best,
        "near_best_count": len(near),
        "near_best_multipliers": [row["multipliers"] for row in near[:8]],
        "interpretation": (
            "Multiple near-best grid points indicate weak identifiability; "
            "a single coarse-grid optimum is not a calibrated parameter estimate."
        ),
    }


def run_screen(max_workers: int) -> Dict[str, object]:
    r033 = build_r033()
    r039 = build_r039()
    source_ratios = {
        r033["source_id"]: derive_relative_constraints(_as_relative_record(r033)),
        r039["source_id"]: derive_relative_constraints(_as_relative_record(r039)),
    }
    grid = [(cv, gh) for cv in V_MAX_CV_GRID for gh in G_H_GRID]
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_evaluate_grid_point, point) for point in grid]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: (
        row["multipliers"]["Vmax_CV"],  # type: ignore[index]
        row["multipliers"]["g_H"],  # type: ignore[index]
    ))

    r039_to_r033 = _rank_for_train_source(
        results,
        source_ratios["PMID:24056030"],
        source_ratios["PMID:31931869"],
    )
    r033_to_r039 = _rank_for_train_source(
        results,
        source_ratios["PMID:31931869"],
        source_ratios["PMID:24056030"],
    )
    failed = [row for row in results if row["status"] != "ok"]
    nonstationary = [
        row for row in results
        if row["status"] == "ok" and not row.get("stationary")
    ]
    output = {
        "run_id": "R041",
        "screen_status": "complete_restricted_diagnostic",
        "parameter_families": {
            "Vmax_CV": "ATP synthase capacity multiplier",
            "g_H": "basal proton conductance multiplier",
        },
        "grid": {
            "Vmax_CV": list(V_MAX_CV_GRID),
            "g_H": list(G_H_GRID),
            "n_points": len(grid),
        },
        "protocol": {
            "duration_s": 10000.0,
            "sample_count": 101,
            "stationarity_tolerance": 1e-6,
            "ocr_proxy": "Complex IV flux J_C4",
        },
        "source_ratios": source_ratios,
        "fit_directions": {
            "fit_R039_reserve_R033": {
                "train_source": "PMID:24056030",
                "reserve_source": "PMID:31931869",
                "top_ranked": r039_to_r033[:5],
                "nonidentifiability": _summarize_nonidentifiability(r039_to_r033),
            },
            "fit_R033_reserve_R039": {
                "train_source": "PMID:31931869",
                "reserve_source": "PMID:24056030",
                "top_ranked": r033_to_r039[:5],
                "nonidentifiability": _summarize_nonidentifiability(r033_to_r039),
            },
        },
        "qc": {
            "successful_points": sum(1 for row in results if row["status"] == "ok"),
            "failed_points": len(failed),
            "nonstationary_points": len(nonstationary),
            "failed_or_nonstationary_records": failed + nonstationary,
        },
        "grid_results": results,
        "claim_boundary": (
            "Restricted source-ratio identifiability screen only. Results do not "
            "constitute external biological validation, absolute OCR calibration, "
            "or neuron-specific ODE parameter inference."
        ),
        "eligible_for_external_validation": False,
        "absolute_calibration_allowed": False,
    }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    workers = max(1, min(int(args.workers), 4))
    result = run_screen(workers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

