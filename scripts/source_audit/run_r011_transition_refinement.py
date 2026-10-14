"""Run R011 transition refinement around the rotenone boundary.

R011 zooms into the R008B rotenone 0.8->0.9 transition with a denser rotenone
grid while keeping the paraquat axis unchanged.  It reuses the frozen R008
endpoint protocol and does not define a collapse threshold.
"""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from module1.bazil2016_ode import DEFAULT_PARAMS, MODEL_NAME, MODEL_REFERENCE
from scripts.source_audit.run_r008_endpoint_protocol import (
    CONVERGENCE_DERIVATIVE_TOL,
    DPSI_SLOPE_TOL,
    LAST_WINDOW_FRACTION,
    MIN_STATE_TOL,
    PHYSIO_DPSI_CEILING,
    PHYSIO_DPSI_FLOOR,
    parameter_hash,
    simulate_endpoint,
    write_csv,
)
from scripts.source_audit.run_r008b_formal_endpoint_grid import class_counts, matrix_rows


REFINED_ROTENONE_GRID = [
    0.80,
    0.82,
    0.83,
    0.84,
    0.85,
    0.86,
    0.87,
    0.88,
    0.89,
    0.90,
    0.91,
    0.92,
    0.95,
]
PARAQUAT_GRID = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0]


def build_refined_conditions():
    conditions = []
    for rotenone in REFINED_ROTENONE_GRID:
        for paraquat in PARAQUAT_GRID:
            conditions.append({
                "rotenone_inhibition": rotenone,
                "paraquat_index": paraquat,
                "selection_reason": "refined_transition_scan",
            })
    return conditions


def transition_band_summary(rows):
    rows_by_paraquat = {}
    for row in rows:
        rows_by_paraquat.setdefault(row["paraquat_index"], []).append(row)

    summary_rows = []
    for paraquat in PARAQUAT_GRID:
        group = sorted(
            rows_by_paraquat.get(paraquat, []),
            key=lambda item: item["rotenone_inhibition"],
        )
        physiological = [
            row for row in group
            if row["endpoint_class"] == "near_fixed_physiological_endpoint"
        ]
        depolarized = [
            row for row in group
            if row["endpoint_class"] == "near_fixed_depolarized_endpoint"
        ]
        highest_phys = max(
            (row["rotenone_inhibition"] for row in physiological),
            default=np.nan,
        )
        lowest_depol = min(
            (row["rotenone_inhibition"] for row in depolarized),
            default=np.nan,
        )
        band_width = (
            lowest_depol - highest_phys
            if not np.isnan(highest_phys) and not np.isnan(lowest_depol)
            else np.nan
        )
        summary_rows.append({
            "paraquat_index": paraquat,
            "n_conditions": len(group),
            "n_physiological": len(physiological),
            "n_depolarized": len(depolarized),
            "highest_physiological_rotenone": highest_phys,
            "lowest_depolarized_rotenone": lowest_depol,
            "observed_transition_gap": band_width,
        })
    return summary_rows


def run_refinement(output_dir, duration=5000.0, n_points=1001):
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = build_refined_conditions()
    rows = [
        simulate_endpoint(
            condition,
            duration,
            n_points,
            params=DEFAULT_PARAMS.copy(),
            model_variant="refined_transition_scan",
        )
        for condition in conditions
    ]

    endpoint_csv = output_dir / "transition_refinement_grid.csv"
    class_matrix_csv = output_dir / "endpoint_class_matrix.csv"
    dpsi_matrix_csv = output_dir / "final_dpsi_matrix.csv"
    band_csv = output_dir / "transition_band_summary.csv"
    metadata_path = output_dir / "metadata.json"

    write_csv(endpoint_csv, rows)
    write_csv(class_matrix_csv, matrix_rows(rows, "endpoint_class"))
    write_csv(dpsi_matrix_csv, matrix_rows(rows, "final_dpsi_mv"))
    band_rows = transition_band_summary(rows)
    write_csv(band_csv, band_rows)

    physiological_rotenones = [
        row["rotenone_inhibition"]
        for row in rows
        if row["endpoint_class"] == "near_fixed_physiological_endpoint"
    ]
    depolarized_rotenones = [
        row["rotenone_inhibition"]
        for row in rows
        if row["endpoint_class"] == "near_fixed_depolarized_endpoint"
    ]
    overall_band = {
        "highest_physiological_rotenone": max(physiological_rotenones)
        if physiological_rotenones
        else np.nan,
        "lowest_depolarized_rotenone": min(depolarized_rotenones)
        if depolarized_rotenones
        else np.nan,
    }
    if (
        not np.isnan(overall_band["highest_physiological_rotenone"])
        and not np.isnan(overall_band["lowest_depolarized_rotenone"])
    ):
        overall_band["observed_transition_gap"] = (
            overall_band["lowest_depolarized_rotenone"]
            - overall_band["highest_physiological_rotenone"]
        )
    else:
        overall_band["observed_transition_gap"] = np.nan

    metadata = {
        "run_id": "R011",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "transition-width refinement around the rotenone boundary",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "duration_s": duration,
        "n_output_points": n_points,
        "rotenone_grid": REFINED_ROTENONE_GRID,
        "paraquat_grid": PARAQUAT_GRID,
        "n_conditions": len(rows),
        "endpoint_class_counts": class_counts(rows),
        "overall_transition_band": overall_band,
        "endpoint_rules": {
            "convergence_derivative_tol": CONVERGENCE_DERIVATIVE_TOL,
            "dpsi_slope_tol_mv_per_s": DPSI_SLOPE_TOL,
            "last_window_fraction": LAST_WINDOW_FRACTION,
            "physiology_dpsi_floor_mv": PHYSIO_DPSI_FLOOR,
            "physiology_dpsi_ceiling_mv": PHYSIO_DPSI_CEILING,
            "minimum_state_tol": MIN_STATE_TOL,
        },
        "collapse_threshold_defined": False,
        "formal_phase_boundary_defined": False,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "endpoint_csv": endpoint_csv.name,
        "band_csv": band_csv.name,
        "class_matrix_csv": class_matrix_csv.name,
        "dpsi_matrix_csv": dpsi_matrix_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, band_csv, metadata_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inputs/audit_runs/R011"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    endpoint_csv, band_csv, metadata_path, rows = run_refinement(
        args.output_dir,
        duration=args.duration,
        n_points=args.n_points,
    )
    print("conditions:", len(rows))
    print("class_counts:", class_counts(rows))
    print("endpoint_csv:", endpoint_csv)
    print("band_csv:", band_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

