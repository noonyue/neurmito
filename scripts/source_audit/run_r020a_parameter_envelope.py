"""Run R020A local parameter-envelope robustness experiments.

R020A perturbs one parameter at a time by +/-10% while reusing the audited
R011 refined rotenone/paraquat grid and the frozen R008 endpoint protocol.
This is a local numerical robustness check for the qualified reduced ODE;
it is not a biological uncertainty or posterior-sampling analysis.
"""

import argparse
import csv
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
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
from scripts.source_audit.run_r011_transition_refinement import (
    PARAQUAT_GRID,
    REFINED_ROTENONE_GRID,
)


PERTURBED_PARAMETERS = (
    "Vmax_C1",
    "Vmax_CV",
    "Vmax_ATPase",
    "ROS_leak_gain",
    "k_ROS_C1",
)
PERTURBATION_FACTORS = (0.9, 1.1)


def build_conditions():
    return [
        {
            "rotenone_inhibition": rotenone,
            "paraquat_index": paraquat,
            "selection_reason": "r011_refined_grid",
        }
        for rotenone in REFINED_ROTENONE_GRID
        for paraquat in PARAQUAT_GRID
    ]


def build_variants():
    variants = [{"variant_id": "default", "parameter_name": "", "factor": 1.0}]
    for parameter_name in PERTURBED_PARAMETERS:
        for factor in PERTURBATION_FACTORS:
            variants.append(
                {
                    "variant_id": f"{parameter_name}_{factor:.1f}x",
                    "parameter_name": parameter_name,
                    "factor": factor,
                }
            )
    return variants


def variant_params(parameter_name, factor):
    params = DEFAULT_PARAMS.copy()
    if parameter_name:
        params[parameter_name] *= factor
    return params


def class_counts(rows):
    counts = {}
    for row in rows:
        label = row["endpoint_class"]
        counts[label] = counts.get(label, 0) + 1
    return counts


def transition_band_summary(rows):
    summaries = []
    for paraquat in PARAQUAT_GRID:
        group = [
            row for row in rows
            if float(row["paraquat_index"]) == float(paraquat)
        ]
        physiological = [
            float(row["rotenone_inhibition"])
            for row in group
            if row["endpoint_class"] == "near_fixed_physiological_endpoint"
        ]
        depolarized = [
            float(row["rotenone_inhibition"])
            for row in group
            if row["endpoint_class"] == "near_fixed_depolarized_endpoint"
        ]
        highest_phys = max(physiological) if physiological else np.nan
        lowest_depol = min(depolarized) if depolarized else np.nan
        summaries.append(
            {
                "paraquat_index": paraquat,
                "n_conditions": len(group),
                "n_physiological": len(physiological),
                "n_depolarized": len(depolarized),
                "highest_physiological_rotenone": highest_phys,
                "lowest_depolarized_rotenone": lowest_depol,
                "observed_transition_gap": (
                    lowest_depol - highest_phys
                    if physiological and depolarized
                    else np.nan
                ),
            }
        )
    return summaries


def _simulate_task(task):
    """Process-pool worker kept at module scope for Windows spawn support."""
    condition, variant, duration, n_points = task
    params = variant_params(variant["parameter_name"], variant["factor"])
    row = simulate_endpoint(
        condition,
        duration,
        n_points,
        params=params,
        model_variant=f"R020A_{variant['variant_id']}",
    )
    row.update(
        {
            "variant_id": variant["variant_id"],
            "parameter_name": variant["parameter_name"],
            "perturbation_factor": variant["factor"],
            "parameter_sha256": parameter_hash(params),
        }
    )
    return row


def run_parameter_envelope(
    output_dir,
    duration=5000.0,
    n_points=1001,
    workers=1,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = build_conditions()
    variants = build_variants()
    all_rows = []
    summary_rows = []

    tasks = [
        (condition, variant, duration, n_points)
        for variant in variants
        for condition in conditions
    ]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            all_rows = list(executor.map(_simulate_task, tasks))
    else:
        all_rows = [_simulate_task(task) for task in tasks]

    for variant in variants:
        rows = [
            row for row in all_rows
            if row["variant_id"] == variant["variant_id"]
        ]

        counts = class_counts(rows)
        bands = transition_band_summary(rows)
        for band in bands:
            summary_rows.append(
                {
                    **variant,
                    **band,
                    "n_solver_failed": counts.get("solver_failed", 0),
                    "n_invalid_negative_state": counts.get(
                        "invalid_negative_state", 0
                    ),
                    "n_unresolved": sum(
                        counts.get(label, 0)
                        for label in (
                            "continuing_depletion",
                            "slow_drift_not_converged",
                            "recovery_not_converged",
                        )
                    ),
                }
            )

    endpoint_csv = output_dir / "parameter_envelope_grid.csv"
    summary_csv = output_dir / "transition_band_summary.csv"
    manifest_csv = output_dir / "parameter_manifest.csv"
    metadata_path = output_dir / "metadata.json"
    write_csv(endpoint_csv, all_rows)
    write_csv(summary_csv, summary_rows)
    write_csv(manifest_csv, variants)

    metadata = {
        "run_id": "R020A",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "local +/-10% one-at-a-time parameter envelope for C1 "
            "transition robustness"
        ),
        "scope_statement": (
            "Numerical local robustness only; not biological uncertainty, "
            "posterior inference, or wet-lab validation."
        ),
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "default_parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "duration_s": duration,
        "n_output_points": n_points,
        "rotenone_grid": REFINED_ROTENONE_GRID,
        "paraquat_grid": PARAQUAT_GRID,
        "n_variants": len(variants),
        "n_conditions_per_variant": len(conditions),
        "n_total_conditions": len(all_rows),
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
        "summary_csv": summary_csv.name,
        "manifest_csv": manifest_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, summary_csv, manifest_csv, metadata_path, all_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inputs/audit_runs/R020A"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    outputs = run_parameter_envelope(
        args.output_dir,
        duration=args.duration,
        n_points=args.n_points,
        workers=args.workers,
    )
    print("rows:", len(outputs[-1]))
    print("endpoint_csv:", outputs[0])
    print("summary_csv:", outputs[1])
    print("manifest_csv:", outputs[2])
    print("metadata:", outputs[3])


if __name__ == "__main__":
    main()

