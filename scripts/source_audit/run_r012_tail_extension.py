"""Run R012 tail extension for the uncertain R011 transition band.

R012 extends only the R011 non-converged transition-band conditions to a longer
time horizon.  It reuses the frozen R008 endpoint protocol and does not define a
collapse threshold.
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


UNCERTAIN_CLASSES = {"continuing_depletion", "slow_drift_not_converged"}


def load_uncertain_conditions(csv_path):
    selected = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("endpoint_class") not in UNCERTAIN_CLASSES:
                continue
            selected.append({
                "rotenone_inhibition": parse_float(row, "rotenone_inhibition"),
                "paraquat_index": parse_float(row, "paraquat_index"),
                "previous_endpoint_class": row.get("endpoint_class"),
                "previous_duration_s": parse_float(row, "duration_s"),
                "previous_final_dpsi_mv": parse_float(row, "final_dpsi_mv"),
                "previous_final_atp_m_mm": parse_float(row, "final_atp_m_mm"),
                "selection_reason": "r011_uncertain_endpoint",
            })
    selected.sort(key=lambda item: (item["rotenone_inhibition"], item["paraquat_index"]))
    return selected


def class_counts(rows):
    counts = {}
    for row in rows:
        endpoint = row["endpoint_class"]
        counts[endpoint] = counts.get(endpoint, 0) + 1
    return counts


def transition_changes(rows):
    counts = {}
    for row in rows:
        key = (row["previous_endpoint_class"], row["endpoint_class"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {
            "previous_endpoint_class": prev,
            "new_endpoint_class": new,
            "count": count,
        }
        for (prev, new), count in sorted(counts.items())
    ]


def transition_band_summary(rows):
    rows_by_paraquat = {}
    for row in rows:
        rows_by_paraquat.setdefault(row["paraquat_index"], []).append(row)

    summary_rows = []
    for paraquat, group in sorted(rows_by_paraquat.items()):
        group = sorted(group, key=lambda item: item["rotenone_inhibition"])
        summary_rows.append({
            "paraquat_index": paraquat,
            "n_conditions": len(group),
            "n_reclassified": sum(
                row["previous_endpoint_class"] != row["endpoint_class"]
                for row in group
            ),
            "final_depolarized": sum(
                row["endpoint_class"] == "near_fixed_depolarized_endpoint"
                for row in group
            ),
            "final_physiological": sum(
                row["endpoint_class"] == "near_fixed_physiological_endpoint"
                for row in group
            ),
            "final_continuing": sum(
                row["endpoint_class"] == "continuing_depletion"
                for row in group
            ),
            "final_slow_drift": sum(
                row["endpoint_class"] == "slow_drift_not_converged"
                for row in group
            ),
            "max_previous_rotenone": max(row["rotenone_inhibition"] for row in group),
            "min_previous_rotenone": min(row["rotenone_inhibition"] for row in group),
        })
    return summary_rows


def run_tail_extension(output_dir, r011_csv, duration=10000.0, n_points=1001):
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = load_uncertain_conditions(r011_csv)
    rows = [
        simulate_endpoint(
            condition,
            duration,
            n_points,
            params=DEFAULT_PARAMS.copy(),
            model_variant="tail_extension_10000s",
        )
        for condition in conditions
    ]

    endpoint_csv = output_dir / "tail_extension_grid.csv"
    summary_csv = output_dir / "tail_extension_summary.csv"
    changes_csv = output_dir / "class_transition_changes.csv"
    metadata_path = output_dir / "metadata.json"

    write_csv(endpoint_csv, rows)
    write_csv(summary_csv, transition_band_summary(rows))
    write_csv(changes_csv, transition_changes(rows))

    metadata = {
        "run_id": "R012",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "extended-horizon resolution of uncertain transition-band conditions",
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "parameter_sha256": parameter_hash(DEFAULT_PARAMS),
        "input_r011_csv": str(r011_csv),
        "duration_s": duration,
        "n_output_points": n_points,
        "n_conditions": len(rows),
        "source_selection_classes": sorted(UNCERTAIN_CLASSES),
        "endpoint_class_counts": class_counts(rows),
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
        "changes_csv": changes_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return endpoint_csv, summary_csv, changes_csv, metadata_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--r011-csv",
        type=Path,
        default=Path("inputs/audit_runs/R011/transition_refinement_grid.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inputs/audit_runs/R012"),
    )
    parser.add_argument("--duration", type=float, default=10000.0)
    parser.add_argument("--n-points", type=int, default=1001)
    args = parser.parse_args()

    endpoint_csv, summary_csv, changes_csv, metadata_path, rows = run_tail_extension(
        args.output_dir,
        args.r011_csv,
        duration=args.duration,
        n_points=args.n_points,
    )
    print("conditions:", len(rows))
    print("class_counts:", class_counts(rows))
    print("endpoint_csv:", endpoint_csv)
    print("summary_csv:", summary_csv)
    print("changes_csv:", changes_csv)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()

