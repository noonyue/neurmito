"""Run R009 mechanism ablations on the endpoint-qualified stress grid.

R009 asks whether the R008B endpoint transition is driven by declared feedback
mechanisms or by simpler additive stress effects.  It reuses the frozen R008
endpoint classifier and does not define a collapse threshold.
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
    ATP_SLOPE_TOL,
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
from scripts.source_audit.run_r008b_formal_endpoint_grid import (
    add_baseline_normalized_metrics,
    class_counts,
    load_all_r007_conditions,
    matrix_rows,
)


def variant_params():
    variants = {}

    full = DEFAULT_PARAMS.copy()
    variants["full_model"] = full

    no_leak = DEFAULT_PARAMS.copy()
    no_leak["ROS_leak_gain"] = 0.0
    variants["no_ros_induced_leak"] = no_leak

    no_c1_feedback = DEFAULT_PARAMS.copy()
    no_c1_feedback["Ki_H2O2"] = 1e9
    variants["no_h2o2_c1_feedback"] = no_c1_feedback

    no_both = DEFAULT_PARAMS.copy()
    no_both["ROS_leak_gain"] = 0.0
    no_both["Ki_H2O2"] = 1e9
    variants["no_ros_leak_no_h2o2_c1_feedback"] = no_both

    return variants


def baseline_lookup(rows):
    return {
        (row["model_variant"], row["rotenone_inhibition"], row["paraquat_index"]): row
        for row in rows
    }


def transition_summary(rows, variant):
    variant_rows = [row for row in rows if row["model_variant"] == variant]
    rot_08 = [row for row in variant_rows if row["rotenone_inhibition"] == 0.8]
    rot_09 = [row for row in variant_rows if row["rotenone_inhibition"] == 0.9]
    dpsi_08 = np.array([row["final_dpsi_mv"] for row in rot_08], dtype=float)
    dpsi_09 = np.array([row["final_dpsi_mv"] for row in rot_09], dtype=float)
    atp_08 = np.array([row["final_atp_m_mm"] for row in rot_08], dtype=float)
    atp_09 = np.array([row["final_atp_m_mm"] for row in rot_09], dtype=float)
    return {
        "model_variant": variant,
        "n_conditions": len(variant_rows),
        "solver_success_count": sum(bool(row["solver_success"]) for row in variant_rows),
        "endpoint_class_counts": json.dumps(class_counts(variant_rows), sort_keys=True),
        "depolarized_endpoint_count": sum(
            row["endpoint_class"] == "near_fixed_depolarized_endpoint"
            for row in variant_rows
        ),
        "mean_dpsi_rotenone_0_8": float(np.mean(dpsi_08)),
        "mean_dpsi_rotenone_0_9": float(np.mean(dpsi_09)),
        "mean_dpsi_drop_0_8_to_0_9": float(np.mean(dpsi_08) - np.mean(dpsi_09)),
        "mean_atp_rotenone_0_8": float(np.mean(atp_08)),
        "mean_atp_rotenone_0_9": float(np.mean(atp_09)),
        "mean_atp_drop_0_8_to_0_9": float(np.mean(atp_08) - np.mean(atp_09)),
    }


def additive_proxy_rows(full_rows):
    lookup = {
        (row["rotenone_inhibition"], row["paraquat_index"]): row
        for row in full_rows
    }
    baseline = lookup[(0.0, 0.0)]
    rows = []
    for row in full_rows:
        rotenone = row["rotenone_inhibition"]
        paraquat = row["paraquat_index"]
        rot_only = lookup[(rotenone, 0.0)]
        pq_only = lookup[(0.0, paraquat)]

        additive_dpsi = (
            rot_only["final_dpsi_mv"]
            + pq_only["final_dpsi_mv"]
            - baseline["final_dpsi_mv"]
        )
        additive_atp = (
            rot_only["final_atp_m_mm"]
            + pq_only["final_atp_m_mm"]
            - baseline["final_atp_m_mm"]
        )

        rows.append({
            "rotenone_inhibition": rotenone,
            "paraquat_index": paraquat,
            "observed_final_dpsi_mv": row["final_dpsi_mv"],
            "additive_expected_final_dpsi_mv": additive_dpsi,
            "dpsi_synergy_residual_mv": row["final_dpsi_mv"] - additive_dpsi,
            "observed_final_atp_m_mm": row["final_atp_m_mm"],
            "additive_expected_final_atp_m_mm": additive_atp,
            "atp_synergy_residual_mm": row["final_atp_m_mm"] - additive_atp,
            "observed_endpoint_class": row["endpoint_class"],
        })
    return rows


def run_ablation(output_dir, r007_csv, duration=5000.0, n_points=1001):
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = load_all_r007_conditions(r007_csv)
    variants = variant_params()
    rows = []

    for variant_index, (variant, params) in enumerate(variants.items(), start=1):
        for condition_index, condition in enumerate(conditions, start=1):
            rows.append(
                simulate_endpoint(
                    condition,
                    duration,
                    n_points,
                    params=params,
                    model_variant=variant,
                )
            )
            print(
                f"completed variant {variant_index}/{len(variants)} "
                f"{variant} condition {condition_index}/{len(conditions)}",
                flush=True,
            )

    for variant in variants:
        add_baseline_normalized_metrics([
            row for row in rows if row["model_variant"] == variant
        ])

    full_rows = [row for row in rows if row["model_variant"] == "full_model"]
    additive_rows = additive_proxy_rows(full_rows)
    summary_rows = [transition_summary(rows, variant) for variant in variants]

    endpoint_csv = output_dir / "mechanism_ablation_grid.csv"
    summary_csv = output_dir / "mechanism_ablation_summary.csv"
    additive_csv = output_dir / "additive_proxy_residuals.csv"
    dpsi_matrix_csv = output_dir / "final_dpsi_by_variant_matrix.csv"
    metadata_path = output_dir / "metadata.json"

    write_csv(endpoint_csv, rows)
    write_csv(summary_csv, summary_rows)
    write_csv(additive_csv, additive_rows)

    matrix = []
    for variant in variants:
        for row in matrix_rows(
            [item for item in rows if item["model_variant"] == variant],
            "final_dpsi_mv",
        ):
            row["model_variant"] = variant
            matrix.append(row)
    write_csv(dpsi_matrix_csv, matrix)

    metadata = {
        "run_id": "R009",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "mechanism ablation under frozen endpoint protocol",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "base_parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "input_r007_csv": str(r007_csv),
        "duration_s": duration,
        "n_output_points": n_points,
        "n_conditions_per_variant": len(conditions),
        "variants": {
            "full_model": "default reduced model",
            "no_ros_induced_leak": "ROS_leak_gain = 0",
            "no_h2o2_c1_feedback": "Ki_H2O2 = 1e9",
            "no_ros_leak_no_h2o2_c1_feedback": (
                "ROS_leak_gain = 0 and Ki_H2O2 = 1e9"
            ),
        },
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
        "summary_csv": summary_csv.name,
        "additive_proxy_csv": additive_csv.name,
        "dpsi_matrix_csv": dpsi_matrix_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, summary_csv, additive_csv, metadata_path, rows


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
        default=Path("inputs/audit_runs/R009"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    _endpoint_csv, summary_csv, additive_csv, metadata_path, rows = run_ablation(
        args.output_dir,
        args.r007_csv,
        duration=args.duration,
        n_points=args.n_points,
    )
    variants = sorted({row["model_variant"] for row in rows})
    print("conditions:", len(rows))
    print("variants:", variants)
    print("summary_csv:", summary_csv)
    print("additive_csv:", additive_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

