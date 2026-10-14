"""Run R010 initial-condition and solver robustness checks.

R010 tests whether the R008B rotenone 0.8->0.9 endpoint transition is stable
to physiologically bounded initial-condition perturbations and independent ODE
solvers.  It reuses the frozen R008 endpoint classifier and still does not
define a collapse threshold.
"""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from module1.bazil2016_ode import DEFAULT_PARAMS, MODEL_NAME, MODEL_REFERENCE
from module1.neurmito_system import CARDIAC_IC, IDX, odes
from scripts.source_audit.run_r008_endpoint_protocol import (
    ATP_SLOPE_TOL,
    CONVERGENCE_DERIVATIVE_TOL,
    DPSI_SLOPE_TOL,
    LAST_WINDOW_FRACTION,
    MIN_STATE_TOL,
    PHYSIO_DPSI_CEILING,
    PHYSIO_DPSI_FLOOR,
    endpoint_class,
    last_window_slope,
    parameter_hash,
    write_csv,
)
from scripts.source_audit.run_r008b_formal_endpoint_grid import (
    add_baseline_normalized_metrics,
    class_counts,
    load_all_r007_conditions,
)


SOLVER_METHODS = ("LSODA", "BDF", "Radau")


def initial_condition_variants():
    """Return bounded initial-condition perturbations."""
    variants = {"default_ic": CARDIAC_IC.copy()}

    low_energy = CARDIAC_IC.copy()
    low_energy[IDX["DPsi"]] = 160.0
    low_energy[IDX["ATP_m"]] = 7.5
    low_energy[IDX["ADP_m"]] = 2.4
    low_energy[IDX["ATP_c"]] = 6.8
    low_energy[IDX["ADP_c"]] = 2.0
    low_energy[IDX["NADH"]] = 0.50
    low_energy[IDX["QH2"]] = 0.90
    low_energy[IDX["Cred"]] = 1.60
    low_energy[IDX["H2O2_m"]] = 2.0e-4
    variants["low_energy_reduced_ic"] = low_energy

    high_energy = CARDIAC_IC.copy()
    high_energy[IDX["DPsi"]] = 190.0
    high_energy[IDX["ATP_m"]] = 9.5
    high_energy[IDX["ADP_m"]] = 0.4
    high_energy[IDX["ATP_c"]] = 8.5
    high_energy[IDX["ADP_c"]] = 0.3
    high_energy[IDX["NADH"]] = 0.20
    high_energy[IDX["QH2"]] = 0.50
    high_energy[IDX["Cred"]] = 1.10
    high_energy[IDX["H2O2_m"]] = 5.0e-5
    variants["high_energy_oxidized_ic"] = high_energy

    return variants


def simulate_robust_endpoint(
    condition,
    duration,
    n_points,
    y0,
    method,
    robustness_axis,
    variant,
):
    rotenone = condition["rotenone_inhibition"]
    paraquat = condition["paraquat_index"]
    stress = {"rotenone": rotenone, "paraquat": paraquat}
    t_eval = np.linspace(0.0, duration, n_points)
    params = DEFAULT_PARAMS.copy()
    sol = solve_ivp(
        lambda t, y: odes(t, y, params, stress=stress),
        (0.0, duration),
        y0.copy(),
        t_eval=t_eval,
        method=method,
        rtol=1e-6,
        atol=1e-9,
        max_step=1.0,
    )

    row = dict(condition)
    row.update({
        "run_axis": robustness_axis,
        "variant": variant,
        "solver_method": method,
        "duration_s": duration,
        "n_output_points": n_points,
        "solver_success": bool(sol.success),
        "solver_message": str(sol.message),
    })
    if not sol.success or sol.y.shape[1] == 0:
        row["endpoint_class"] = "solver_failed"
        row["endpoint_eligible_for_phase_diagram"] = False
        row["physiology_qualified_endpoint"] = False
        return row

    final = sol.y[:, -1]
    final_derivative = odes(duration, final, params, stress=stress)
    row.update({
        "final_dpsi_mv": float(final[IDX["DPsi"]]),
        "min_dpsi_mv": float(np.min(sol.y[IDX["DPsi"]])),
        "max_dpsi_mv": float(np.max(sol.y[IDX["DPsi"]])),
        "final_atp_m_mm": float(final[IDX["ATP_m"]]),
        "min_atp_m_mm": float(np.min(sol.y[IDX["ATP_m"]])),
        "final_adp_m_mm": float(final[IDX["ADP_m"]]),
        "final_h2o2_m_mm": float(final[IDX["H2O2_m"]]),
        "max_h2o2_m_mm": float(np.max(sol.y[IDX["H2O2_m"]])),
        "minimum_state_value": float(np.min(sol.y)),
        "final_derivative_max_abs": float(np.max(np.abs(final_derivative))),
        "dpsi_slope_last_window": last_window_slope(t_eval, sol.y[IDX["DPsi"]]),
        "atp_slope_last_window": last_window_slope(t_eval, sol.y[IDX["ATP_m"]]),
        "n_function_evaluations": int(sol.nfev),
    })
    row["endpoint_class"] = endpoint_class(row)
    row["endpoint_eligible_for_phase_diagram"] = row["endpoint_class"].startswith(
        "near_fixed_"
    )
    row["physiology_qualified_endpoint"] = (
        row["endpoint_class"] == "near_fixed_physiological_endpoint"
    )
    return row


def transition_summary(rows, axis, variant):
    selected = [row for row in rows if row["run_axis"] == axis and row["variant"] == variant]
    rot_08 = [row for row in selected if row["rotenone_inhibition"] == 0.8]
    rot_09 = [row for row in selected if row["rotenone_inhibition"] == 0.9]
    dpsi_08 = np.array([row["final_dpsi_mv"] for row in rot_08], dtype=float)
    dpsi_09 = np.array([row["final_dpsi_mv"] for row in rot_09], dtype=float)
    atp_08 = np.array([row["final_atp_m_mm"] for row in rot_08], dtype=float)
    atp_09 = np.array([row["final_atp_m_mm"] for row in rot_09], dtype=float)
    return {
        "run_axis": axis,
        "variant": variant,
        "n_conditions": len(selected),
        "solver_success_count": sum(bool(row["solver_success"]) for row in selected),
        "endpoint_class_counts": json.dumps(class_counts(selected), sort_keys=True),
        "depolarized_endpoint_count": sum(
            row["endpoint_class"] == "near_fixed_depolarized_endpoint"
            for row in selected
        ),
        "mean_dpsi_rotenone_0_8": float(np.mean(dpsi_08)),
        "mean_dpsi_rotenone_0_9": float(np.mean(dpsi_09)),
        "mean_dpsi_drop_0_8_to_0_9": float(np.mean(dpsi_08) - np.mean(dpsi_09)),
        "mean_atp_rotenone_0_8": float(np.mean(atp_08)),
        "mean_atp_rotenone_0_9": float(np.mean(atp_09)),
        "mean_atp_drop_0_8_to_0_9": float(np.mean(atp_08) - np.mean(atp_09)),
    }


def add_reference_deltas(rows):
    reference = {
        (row["rotenone_inhibition"], row["paraquat_index"]): row
        for row in rows
        if row["run_axis"] == "initial_condition"
        and row["variant"] == "default_ic"
    }
    for row in rows:
        ref = reference.get((row["rotenone_inhibition"], row["paraquat_index"]))
        if ref is None or not row.get("solver_success"):
            continue
        row["dpsi_delta_vs_default_lsoda"] = (
            row["final_dpsi_mv"] - ref["final_dpsi_mv"]
        )
        row["atp_delta_vs_default_lsoda"] = (
            row["final_atp_m_mm"] - ref["final_atp_m_mm"]
        )
        row["same_endpoint_class_as_default_lsoda"] = (
            row["endpoint_class"] == ref["endpoint_class"]
        )


def axis_rows(rows, axis, variant):
    return [
        row for row in rows
        if row["run_axis"] == axis and row["variant"] == variant
    ]


def run_robustness(output_dir, r007_csv, duration=5000.0, n_points=1001):
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = load_all_r007_conditions(r007_csv)
    ic_variants = initial_condition_variants()
    rows = []

    for variant_index, (variant, y0) in enumerate(ic_variants.items(), start=1):
        for condition_index, condition in enumerate(conditions, start=1):
            rows.append(
                simulate_robust_endpoint(
                    condition,
                    duration,
                    n_points,
                    y0,
                    "LSODA",
                    "initial_condition",
                    variant,
                )
            )
            print(
                f"completed ic {variant_index}/{len(ic_variants)} "
                f"{variant} condition {condition_index}/{len(conditions)}",
                flush=True,
            )

    for method_index, method in enumerate(SOLVER_METHODS, start=1):
        for condition_index, condition in enumerate(conditions, start=1):
            rows.append(
                simulate_robust_endpoint(
                    condition,
                    duration,
                    n_points,
                    CARDIAC_IC.copy(),
                    method,
                    "solver",
                    method,
                )
            )
            print(
                f"completed solver {method_index}/{len(SOLVER_METHODS)} "
                f"{method} condition {condition_index}/{len(conditions)}",
                flush=True,
            )

    for axis, variants in (
        ("initial_condition", ic_variants),
        ("solver", {method: method for method in SOLVER_METHODS}),
    ):
        for variant in variants:
            add_baseline_normalized_metrics(axis_rows(rows, axis, variant))
    add_reference_deltas(rows)

    summary_rows = []
    for variant in ic_variants:
        summary_rows.append(transition_summary(rows, "initial_condition", variant))
    for method in SOLVER_METHODS:
        summary_rows.append(transition_summary(rows, "solver", method))

    endpoint_csv = output_dir / "robustness_grid.csv"
    summary_csv = output_dir / "robustness_summary.csv"
    metadata_path = output_dir / "metadata.json"
    write_csv(endpoint_csv, rows)
    write_csv(summary_csv, summary_rows)

    metadata = {
        "run_id": "R010",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "initial-condition and solver robustness under frozen endpoint protocol",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "input_r007_csv": str(r007_csv),
        "duration_s": duration,
        "n_output_points": n_points,
        "n_conditions_per_variant": len(conditions),
        "initial_condition_variants": list(ic_variants.keys()),
        "solver_methods": list(SOLVER_METHODS),
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
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, summary_csv, metadata_path, rows


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
        default=Path("inputs/audit_runs/R010"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    _endpoint_csv, summary_csv, metadata_path, rows = run_robustness(
        args.output_dir,
        args.r007_csv,
        duration=args.duration,
        n_points=args.n_points,
    )
    print("conditions:", len(rows))
    print("summary_csv:", summary_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

