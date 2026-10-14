"""Generate the endpoint-labelled, grouped EWS cohort for R021.

The cohort is generated strictly under the frozen R020 data contract. Endpoint
labels use the R008 protocol; unresolved cases are extended through staged
long-tail integrations before event times are assigned.
"""

import argparse
import csv
import hashlib
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
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
from scripts.source_audit.run_r010_robustness import initial_condition_variants


ROTENONE_GRID = [round(0.80 + 0.005 * i, 3) for i in range(21)]
PARAQUAT_GRID = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0]
IC_VARIANTS = initial_condition_variants()
IC_NAME_MAP = {
    "default": "default_ic",
    "low_energy": "low_energy_reduced_ic",
    "high_energy": "high_energy_oxidized_ic",
}
UNRESOLVED_CLASSES = {
    "continuing_depletion",
    "slow_drift_not_converged",
    "recovery_not_converged",
}
SPLIT_BY_PQ = {
    0.0: "train",
    2.0: "train",
    10.0: "train",
    40.0: "train",
    1.0: "validation",
    5.0: "test",
    20.0: "test",
}
EVENT_THRESHOLD_MV = 140.0


def ic_hash(y0):
    return hashlib.sha256(np.asarray(y0, dtype=np.float64).tobytes()).hexdigest()


def build_conditions():
    return [
        {
            "rotenone_inhibition": rotenone,
            "paraquat_index": paraquat,
            "ic_variant": ic_name,
            "split": SPLIT_BY_PQ[paraquat],
            "group_key": f"{rotenone:.3f}|{paraquat:g}|{ic_name}",
        }
        for rotenone in ROTENONE_GRID
        for paraquat in PARAQUAT_GRID
        for ic_name in ("default", "low_energy", "high_energy")
    ]


def simulate_trajectory(condition, duration, n_points):
    ic_name = IC_NAME_MAP[condition["ic_variant"]]
    y0 = IC_VARIANTS[ic_name]
    stress = {
        "rotenone": float(condition["rotenone_inhibition"]),
        "paraquat": float(condition["paraquat_index"]),
    }
    t_eval = np.linspace(0.0, duration, n_points)
    sol = solve_ivp(
        lambda t, y: odes(t, y, DEFAULT_PARAMS, stress=stress),
        (0.0, duration),
        y0.copy(),
        t_eval=t_eval,
        method="LSODA",
        rtol=1e-6,
        atol=1e-9,
        max_step=0.5,
    )
    row = dict(condition)
    row.update(
        {
            "duration_s": duration,
            "n_output_points": n_points,
            "solver_success": bool(sol.success),
            "solver_message": str(sol.message),
            "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
            "ic_hash": ic_hash(y0),
            "max_step_s": 0.5,
            "_t": sol.t,
            "_y": sol.y,
        }
    )
    if not sol.success or sol.y.shape[1] == 0:
        row["endpoint_class"] = "solver_failed"
        return row
    final = sol.y[:, -1]
    final_derivative = odes(duration, final, DEFAULT_PARAMS, stress=stress)
    row.update(
        {
            "final_dpsi_mv": float(final[IDX["DPsi"]]),
            "min_dpsi_mv": float(np.min(sol.y[IDX["DPsi"]])),
            "max_dpsi_mv": float(np.max(sol.y[IDX["DPsi"]])),
            "final_atp_m_mm": float(final[IDX["ATP_m"]]),
            "min_atp_m_mm": float(np.min(sol.y[IDX["ATP_m"]])),
            "final_h2o2_m_mm": float(final[IDX["H2O2_m"]]),
            "max_h2o2_m_mm": float(np.max(sol.y[IDX["H2O2_m"]])),
            "minimum_state_value": float(np.min(sol.y)),
            "final_derivative_max_abs": float(np.max(np.abs(final_derivative))),
            "dpsi_slope_last_window": last_window_slope(
                sol.t, sol.y[IDX["DPsi"]]
            ),
            "atp_slope_last_window": last_window_slope(
                sol.t, sol.y[IDX["ATP_m"]]
            ),
            "n_function_evaluations": int(sol.nfev),
        }
    )
    row["endpoint_class"] = endpoint_class(row)
    return row


def event_time(t, dpsi, threshold=EVENT_THRESHOLD_MV):
    below = np.asarray(dpsi) < threshold
    if not np.any(below):
        return np.nan
    suffix_max = np.maximum.accumulate(np.asarray(dpsi)[::-1])[::-1]
    candidates = np.flatnonzero(below & (suffix_max <= threshold))
    return float(t[candidates[0]]) if candidates.size else np.nan


def _screen_task(task):
    condition, durations, n_points = task
    row = simulate_trajectory(condition, durations[0], n_points)
    for duration in durations[1:]:
        if row["endpoint_class"] not in UNRESOLVED_CLASSES:
            break
        row = simulate_trajectory(condition, duration, n_points)
    return row


def _high_res_task(task):
    condition, duration, n_points = task
    return simulate_trajectory(condition, duration, n_points)


def _clean_row(row):
    return {key: value for key, value in row.items() if not key.startswith("_")}


def run_cohort(
    output_dir,
    screen_durations=(5000.0, 10000.0, 30000.0, 60000.0, 120000.0),
    screen_points=1001,
    trajectory_points=5001,
    workers=1,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = build_conditions()
    tasks = [(condition, tuple(screen_durations), screen_points) for condition in conditions]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            screened = list(executor.map(_screen_task, tasks))
    else:
        screened = [_screen_task(task) for task in tasks]

    high_res_tasks = [
        (condition, row["duration_s"], trajectory_points)
        for condition, row in zip(conditions, screened)
        if row["endpoint_class"] in {
            "near_fixed_physiological_endpoint",
            "near_fixed_depolarized_endpoint",
        }
    ]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            high_res = list(executor.map(_high_res_task, high_res_tasks))
    else:
        high_res = [_high_res_task(task) for task in high_res_tasks]

    high_by_group = {row["group_key"]: row for row in high_res}
    condition_rows = []
    event_rows = []
    trajectory_rows = []
    for screened_row in screened:
        group_key = screened_row["group_key"]
        high = high_by_group.get(group_key)
        final_class = screened_row["endpoint_class"]
        source = high if high is not None else screened_row
        e_time = event_time(source["_t"], source["_y"][IDX["DPsi"]])
        label = (
            1 if final_class == "near_fixed_depolarized_endpoint"
            else 0 if final_class == "near_fixed_physiological_endpoint"
            else np.nan
        )
        clean = _clean_row(screened_row)
        clean.update(
            {
                "label": label,
                "event_time_s": e_time,
                "event_threshold_mv": EVENT_THRESHOLD_MV,
                "exclusion_reason": (
                    "" if not np.isnan(label) else f"endpoint_class:{final_class}"
                ),
            }
        )
        condition_rows.append(clean)
        if not np.isnan(label):
            event_rows.append(
                {
                    "group_key": group_key,
                    "split": screened_row["split"],
                    "label": label,
                    "endpoint_class": final_class,
                    "event_time_s": e_time,
                }
            )
        if high is not None:
            for i, time_s in enumerate(high["_t"]):
                trajectory_rows.append(
                    {
                        "group_key": group_key,
                        "split": screened_row["split"],
                        "rotenone_inhibition": screened_row["rotenone_inhibition"],
                        "paraquat_index": screened_row["paraquat_index"],
                        "ic_variant": screened_row["ic_variant"],
                        "time_s": float(time_s),
                        "dpsi_mv": float(high["_y"][IDX["DPsi"], i]),
                        "atp_m_mm": float(high["_y"][IDX["ATP_m"], i]),
                        "h2o2_m_mm": float(high["_y"][IDX["H2O2_m"], i]),
                    }
                )

    write_csv(output_dir / "conditions.csv", condition_rows)
    write_csv(output_dir / "events.csv", event_rows)
    write_csv(output_dir / "trajectories.csv", trajectory_rows)
    split_rows = [
        {
            "group_key": row["group_key"],
            "split": row["split"],
            "rotenone_inhibition": row["rotenone_inhibition"],
            "paraquat_index": row["paraquat_index"],
            "ic_variant": row["ic_variant"],
        }
        for row in condition_rows
    ]
    write_csv(output_dir / "split_manifest.csv", split_rows)
    qc = {
        "n_conditions": len(condition_rows),
        "n_endpoint_eligible_groups": len(event_rows),
        "n_positive_events": sum(
            row["label"] == 1 and not np.isnan(row["event_time_s"])
            for row in event_rows
        ),
        "n_trajectory_rows": len(trajectory_rows),
        "endpoint_class_counts": {
            label: sum(row["endpoint_class"] == label for row in condition_rows)
            for label in sorted({row["endpoint_class"] for row in condition_rows})
        },
        "split_counts": {
            split: sum(row["split"] == split for row in condition_rows)
            for split in ("train", "validation", "test")
        },
        "excluded_count": sum(
            bool(row["exclusion_reason"]) for row in condition_rows
        ),
    }
    (output_dir / "qc_summary.json").write_text(
        json.dumps(qc, indent=2, sort_keys=True), encoding="utf-8"
    )
    metadata = {
        "run_id": "R021",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "screen_durations_s": list(screen_durations),
        "screen_points": screen_points,
        "trajectory_points": trajectory_points,
        "event_threshold_mv": EVENT_THRESHOLD_MV,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "split_manifest": "split_manifest.csv",
        "contract": "R020_EWS_DATA_CONTRACT.md",
        "collapse_threshold_defined": False,
        "formal_phase_boundary_defined": False,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return qc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/audit_runs/R021"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--screen-points", type=int, default=1001)
    parser.add_argument("--trajectory-points", type=int, default=5001)
    args = parser.parse_args()
    qc = run_cohort(
        args.output_dir,
        screen_points=args.screen_points,
        trajectory_points=args.trajectory_points,
        workers=args.workers,
    )
    print(json.dumps(qc, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

