"""Run the R008 endpoint-protocol experiment.

R008 extends the stress-grid conditions that were not endpoint-qualified at
1000 s.  It deliberately does not define a collapse threshold.  The output is
an endpoint eligibility table for downstream phase-diagram analysis.
"""

import argparse
import csv
import hashlib
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
from module1.neurmito_system import IDX, odes, simulate


R007_DERIVATIVE_TOL = 1e-3
CONVERGENCE_DERIVATIVE_TOL = 1e-3
DPSI_SLOPE_TOL = 1e-4
ATP_SLOPE_TOL = 1e-5
MIN_STATE_TOL = -1e-7
PHYSIO_DPSI_FLOOR = 140.0
PHYSIO_DPSI_CEILING = 200.0
RECOVERY_DPSI_GAIN = 5.0
LAST_WINDOW_FRACTION = 0.10


def parameter_hash(params):
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def parse_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def parse_float(row, key, default=np.nan):
    value = row.get(key, "")
    if value == "":
        return default
    return float(value)


def select_conditions_from_r007(csv_path):
    """Select conditions needing endpoint extension from R007."""
    selected = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rotenone = parse_float(row, "rotenone_inhibition")
            paraquat = parse_float(row, "paraquat_index")
            is_baseline = rotenone == 0.0 and paraquat == 0.0
            derivative_high = (
                parse_float(row, "final_derivative_max_abs")
                > R007_DERIVATIVE_TOL
            )
            dpsi_low = parse_float(row, "final_dpsi_mv") < PHYSIO_DPSI_FLOOR
            if is_baseline or (parse_bool(row["solver_success"]) and (derivative_high or dpsi_low)):
                selected.append({
                    "rotenone_inhibition": rotenone,
                    "paraquat_index": paraquat,
                    "r007_final_dpsi_mv": parse_float(row, "final_dpsi_mv"),
                    "r007_final_atp_m_mm": parse_float(row, "final_atp_m_mm"),
                    "r007_final_derivative_max_abs": parse_float(
                        row, "final_derivative_max_abs"
                    ),
                    "selection_reason": (
                        "baseline" if is_baseline
                        else "r007_not_endpoint_qualified"
                    ),
                })
    return selected


def last_window_slope(t, values, fraction=LAST_WINDOW_FRACTION):
    """Return a least-squares slope over the final fraction of a trajectory."""
    n_points = len(t)
    start = max(0, int(np.floor(n_points * (1.0 - fraction))))
    if n_points - start < 2:
        return np.nan
    centered_t = t[start:] - t[start]
    slope, _intercept = np.polyfit(centered_t, values[start:], 1)
    return float(slope)


def endpoint_class(row):
    """Classify endpoint eligibility without assigning collapse labels."""
    if not row["solver_success"]:
        return "solver_failed"
    if row["minimum_state_value"] < MIN_STATE_TOL:
        return "invalid_negative_state"

    near_fixed = (
        row["final_derivative_max_abs"] <= CONVERGENCE_DERIVATIVE_TOL
        and abs(row["dpsi_slope_last_window"]) <= DPSI_SLOPE_TOL
        and abs(row["atp_slope_last_window"]) <= ATP_SLOPE_TOL
    )
    if near_fixed:
        if row["final_dpsi_mv"] < PHYSIO_DPSI_FLOOR:
            return "near_fixed_depolarized_endpoint"
        if row["final_dpsi_mv"] > PHYSIO_DPSI_CEILING:
            return "near_fixed_hyperpolarized_endpoint"
        return "near_fixed_physiological_endpoint"

    continuing_down = (
        row["dpsi_slope_last_window"] < -DPSI_SLOPE_TOL
        or row["atp_slope_last_window"] < -ATP_SLOPE_TOL
    )
    if continuing_down:
        return "continuing_depletion"

    recovering = (
        row["dpsi_slope_last_window"] > DPSI_SLOPE_TOL
        and row["final_dpsi_mv"] - row["min_dpsi_mv"] >= RECOVERY_DPSI_GAIN
    )
    if recovering:
        return "recovery_not_converged"

    return "slow_drift_not_converged"


def simulate_endpoint(condition, duration, n_points, params=None, model_variant="default"):
    if params is None:
        params = DEFAULT_PARAMS.copy()
    rotenone = condition["rotenone_inhibition"]
    paraquat = condition["paraquat_index"]
    stress = {"rotenone": rotenone, "paraquat": paraquat}
    t_eval = np.linspace(0.0, duration, n_points)
    sol = simulate(
        (0.0, duration),
        t_eval,
        params=params.copy(),
        stress=stress,
    )

    row = dict(condition)
    row.update({
        "duration_s": duration,
        "n_output_points": n_points,
        "model_variant": model_variant,
        "solver_success": bool(sol.success),
        "solver_message": str(sol.message),
    })
    if not sol.success or sol.y.shape[1] == 0:
        row["endpoint_class"] = "solver_failed"
        row["endpoint_eligible_for_phase_diagram"] = False
        row["physiology_qualified_endpoint"] = False
        return row

    final = sol.y[:, -1]
    final_derivative = odes(duration, final, params.copy(), stress=stress)
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


def write_csv(path, rows):
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_protocol(
    output_dir,
    r007_csv,
    duration=5000.0,
    n_points=1001,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = select_conditions_from_r007(r007_csv)
    rows = [simulate_endpoint(condition, duration, n_points) for condition in selected]

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

    selected_csv = output_dir / "selected_conditions.csv"
    endpoint_csv = output_dir / "endpoint_protocol.csv"
    metadata_path = output_dir / "metadata.json"
    write_csv(selected_csv, selected)
    write_csv(endpoint_csv, rows)

    class_counts = {}
    for row in rows:
        class_counts[row["endpoint_class"]] = class_counts.get(row["endpoint_class"], 0) + 1

    metadata = {
        "run_id": "R008",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "endpoint eligibility protocol for high-stress trajectories",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "input_r007_csv": str(r007_csv),
        "duration_s": duration,
        "n_output_points": n_points,
        "selection_rule": (
            "baseline plus R007 conditions with final_derivative_max_abs > "
            f"{R007_DERIVATIVE_TOL:g} or final_dpsi_mv < {PHYSIO_DPSI_FLOOR:g}"
        ),
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
        "endpoint_protocol_frozen": True,
        "class_counts": class_counts,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "selected_conditions_csv": selected_csv.name,
        "endpoint_csv": endpoint_csv.name,
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
        default=Path("inputs/audit_runs/R008"),
    )
    parser.add_argument("--duration", type=float, default=5000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    endpoint_csv, metadata_path, rows = run_protocol(
        args.output_dir,
        args.r007_csv,
        duration=args.duration,
        n_points=args.n_points,
    )
    class_counts = {}
    for row in rows:
        class_counts[row["endpoint_class"]] = class_counts.get(row["endpoint_class"], 0) + 1

    print("conditions:", len(rows))
    print("class_counts:", class_counts)
    print("endpoint_csv:", endpoint_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

