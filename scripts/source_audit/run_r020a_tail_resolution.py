"""Resolve unresolved R020A parameter-envelope trajectories with long tails."""

import argparse
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from module1.bazil2016_ode import DEFAULT_PARAMS
from scripts.source_audit.run_r008_endpoint_protocol import (
    parameter_hash,
    simulate_endpoint,
    write_csv,
)
from scripts.source_audit.run_r020a_parameter_envelope import (
    class_counts,
    transition_band_summary,
    variant_params,
)


UNRESOLVED_CLASSES = {
    "continuing_depletion",
    "slow_drift_not_converged",
    "recovery_not_converged",
}


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _tail_task(task):
    row, duration, n_points = task
    condition = {
        "rotenone_inhibition": float(row["rotenone_inhibition"]),
        "paraquat_index": float(row["paraquat_index"]),
        "selection_reason": "r020a_unresolved_tail",
    }
    params = variant_params(
        row["parameter_name"],
        float(row["perturbation_factor"]),
    )
    resolved = simulate_endpoint(
        condition,
        duration,
        n_points,
        params=params,
        model_variant=f"R020A_tail_{row['variant_id']}",
    )
    resolved.update(
        {
            "variant_id": row["variant_id"],
            "parameter_name": row["parameter_name"],
            "perturbation_factor": row["perturbation_factor"],
        }
    )
    return resolved


def resolve_tails(
    input_csv,
    output_dir,
    durations=(10000.0, 30000.0, 60000.0, 120000.0),
    n_points=1001,
    workers=1,
):
    rows = read_csv(input_csv)
    initial_rows = [dict(row) for row in rows]
    for row in rows:
        row["initial_endpoint_class"] = row["endpoint_class"]
        row["initial_duration_s"] = row["duration_s"]
        row["final_endpoint_class"] = row["endpoint_class"]
        row["resolved_from_tail"] = "False"

    stage_counts = []
    for duration in durations:
        unresolved = [
            row for row in rows if row["final_endpoint_class"] in UNRESOLVED_CLASSES
        ]
        if not unresolved:
            break
        tasks = [(row, duration, n_points) for row in unresolved]
        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                tail_rows = list(executor.map(_tail_task, tasks))
        else:
            tail_rows = [_tail_task(task) for task in tasks]
        by_key = {
            (
                row["variant_id"],
                float(row["rotenone_inhibition"]),
                float(row["paraquat_index"]),
            ): row
            for row in tail_rows
        }
        for row in rows:
            key = (
                row["variant_id"],
                float(row["rotenone_inhibition"]),
                float(row["paraquat_index"]),
            )
            tail = by_key.get(key)
            if tail is None:
                continue
            for field, value in tail.items():
                if field in {"rotenone_inhibition", "paraquat_index", "selection_reason"}:
                    continue
                row[f"resolved_{field}"] = value
            row["resolved_duration_s"] = duration
            row["resolved_from_tail"] = "True"
            row["final_endpoint_class"] = tail["endpoint_class"]
        stage_counts.append(
            {
                "duration_s": duration,
                "n_input_unresolved": len(unresolved),
                "n_remaining_unresolved": sum(
                    row["final_endpoint_class"] in UNRESOLVED_CLASSES for row in rows
                ),
            }
        )
        checkpoint = Path(output_dir) / f"tail_checkpoint_{int(duration)}s.csv"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        write_csv(checkpoint, rows)

    # Summaries use the final class and final values, while retaining the
    # initial rows for auditability.
    summary_input = []
    for row in rows:
        final = dict(row)
        final["endpoint_class"] = row["final_endpoint_class"]
        if row["resolved_from_tail"] == "True":
            final["final_dpsi_mv"] = row.get(
                "resolved_final_dpsi_mv", row["final_dpsi_mv"]
            )
        summary_input.append(final)
    summary_rows = []
    for variant_id in sorted({row["variant_id"] for row in summary_input}):
        variant_rows = [
            row for row in summary_input if row["variant_id"] == variant_id
        ]
        summary_rows.extend(
            dict({"variant_id": variant_id}, **summary)
            for summary in transition_band_summary(variant_rows)
        )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_csv = output_dir / "resolved_parameter_envelope_grid.csv"
    summary_csv = output_dir / "resolved_transition_band_summary.csv"
    metadata_path = output_dir / "tail_resolution_metadata.json"
    write_csv(resolved_csv, rows)
    write_csv(summary_csv, summary_rows)
    metadata = {
        "run_id": "R020A_tail",
        "input_csv": str(input_csv),
        "durations_s": list(durations),
        "n_output_points": n_points,
        "n_initial_rows": len(initial_rows),
        "n_unresolved_initial": sum(
            row["endpoint_class"] in UNRESOLVED_CLASSES for row in initial_rows
        ),
        "stage_counts": stage_counts,
        "final_class_counts": class_counts(
            [{"endpoint_class": row["final_endpoint_class"]} for row in rows]
        ),
        "endpoint_protocol_reused": "R008",
        "collapse_threshold_defined": False,
        "formal_phase_boundary_defined": False,
        "resolved_csv": resolved_csv.name,
        "summary_csv": summary_csv.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return resolved_csv, summary_csv, metadata_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("inputs/audit_runs/R020A/parameter_envelope_grid.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inputs/audit_runs/R020A"),
    )
    parser.add_argument(
        "--durations",
        default="10000,30000,60000,120000",
        help="comma-separated staged tail durations in seconds",
    )
    parser.add_argument("--n-points", type=int, default=1001)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    outputs = resolve_tails(
        args.input_csv,
        args.output_dir,
        durations=tuple(float(value) for value in args.durations.split(",")),
        n_points=args.n_points,
        workers=args.workers,
    )
    print("rows:", len(outputs[-1]))
    print("resolved_csv:", outputs[0])
    print("summary_csv:", outputs[1])
    print("metadata:", outputs[2])


if __name__ == "__main__":
    main()

