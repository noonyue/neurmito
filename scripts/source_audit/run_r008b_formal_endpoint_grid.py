"""Run the R008B formal endpoint-qualified stress grid.

R008B applies the frozen R008 endpoint protocol to every condition from the
R007 rotenone x paraquat grid.  It produces endpoint-eligible continuous
outputs for formal stress-map analysis, but it still does not define a collapse
threshold.
"""

import argparse
import csv
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
    ATP_SLOPE_TOL,
    CONVERGENCE_DERIVATIVE_TOL,
    DPSI_SLOPE_TOL,
    LAST_WINDOW_FRACTION,
    MIN_STATE_TOL,
    PHYSIO_DPSI_CEILING,
    PHYSIO_DPSI_FLOOR,
    parse_bool,
    parse_float,
    parameter_hash,
    simulate_endpoint,
    write_csv,
)


def load_all_r007_conditions(csv_path):
    conditions = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not parse_bool(row["solver_success"]):
                continue
            conditions.append({
                "rotenone_inhibition": parse_float(row, "rotenone_inhibition"),
                "paraquat_index": parse_float(row, "paraquat_index"),
                "r007_final_dpsi_mv": parse_float(row, "final_dpsi_mv"),
                "r007_final_atp_m_mm": parse_float(row, "final_atp_m_mm"),
                "r007_final_derivative_max_abs": parse_float(
                    row, "final_derivative_max_abs"
                ),
                "selection_reason": "formal_full_grid",
            })
    conditions.sort(key=lambda item: (item["rotenone_inhibition"], item["paraquat_index"]))
    return conditions


def class_counts(rows):
    counts = {}
    for row in rows:
        endpoint = row["endpoint_class"]
        counts[endpoint] = counts.get(endpoint, 0) + 1
    return counts


def add_baseline_normalized_metrics(rows):
    baseline = next(
        row for row in rows
        if row["rotenone_inhibition"] == 0.0 and row["paraquat_index"] == 0.0
    )
    for row in rows:
        if not row.get("solver_success"):
            continue
        row["dpsi_loss_fraction_vs_extended_baseline"] = (
            (baseline["final_dpsi_mv"] - row["final_dpsi_mv"])
            / baseline["final_dpsi_mv"]
        )
        row["atp_loss_fraction_vs_extended_baseline"] = (
            (baseline["final_atp_m_mm"] - row["final_atp_m_mm"])
            / baseline["final_atp_m_mm"]
        )
        row["h2o2_fold_change_vs_extended_baseline"] = (
            row["final_h2o2_m_mm"] / baseline["final_h2o2_m_mm"]
        )


def matrix_rows(rows, value_key):
    rotenone_values = sorted({row["rotenone_inhibition"] for row in rows})
    paraquat_values = sorted({row["paraquat_index"] for row in rows})
    lookup = {
        (row["rotenone_inhibition"], row["paraquat_index"]): row
        for row in rows
    }

    matrix = []
    for rotenone in rotenone_values:
        out = {"rotenone_inhibition": rotenone}
        for paraquat in paraquat_values:
            out[f"paraquat_{paraquat:g}"] = lookup[(rotenone, paraquat)][value_key]
        matrix.append(out)
    return matrix


def run_formal_grid(output_dir, r007_csv, duration=5000.0, n_points=1001):
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = load_all_r007_conditions(r007_csv)
    rows = []
    for index, condition in enumerate(conditions, start=1):
        rows.append(simulate_endpoint(condition, duration, n_points))
        print(f"completed {index}/{len(conditions)}", flush=True)

    add_baseline_normalized_metrics(rows)

    endpoint_csv = output_dir / "formal_endpoint_grid.csv"
    dpsi_matrix_csv = output_dir / "final_dpsi_matrix.csv"
    class_matrix_csv = output_dir / "endpoint_class_matrix.csv"
    metadata_path = output_dir / "metadata.json"

    write_csv(endpoint_csv, rows)
    write_csv(dpsi_matrix_csv, matrix_rows(rows, "final_dpsi_mv"))
    write_csv(class_matrix_csv, matrix_rows(rows, "endpoint_class"))

    counts = class_counts(rows)
    metadata = {
        "run_id": "R008B",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "formal endpoint-qualified full rotenone x paraquat grid",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "input_r007_csv": str(r007_csv),
        "duration_s": duration,
        "n_output_points": n_points,
        "n_conditions": len(rows),
        "solver_success_count": sum(bool(row["solver_success"]) for row in rows),
        "endpoint_class_counts": counts,
        "endpoint_rules": {
            "convergence_derivative_tol": CONVERGENCE_DERIVATIVE_TOL,
            "dpsi_slope_tol_mv_per_s": DPSI_SLOPE_TOL,
            "atp_slope_tol_mm_per_s": ATP_SLOPE_TOL,
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
        "dpsi_matrix_csv": dpsi_matrix_csv.name,
        "class_matrix_csv": class_matrix_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, metadata_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--r007-csv",
        type=Path,
        default=Path("inputs/audit_runs/R007/stress_grid.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inputs/audit_runs/R008B"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    endpoint_csv, metadata_path, rows = run_formal_grid(
        args.output_dir,
        args.r007_csv,
        duration=args.duration,
        n_points=args.n_points,
    )
    print("conditions:", len(rows))
    print("class_counts:", class_counts(rows))
    print("endpoint_csv:", endpoint_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

