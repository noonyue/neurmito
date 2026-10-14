"""Run locked grouped test and leakage audits for R023."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.source_audit.run_r022_ews_lock import (
    build_landmarks,
    evaluate,
    extract_landmark,
    fit_and_score,
    load_trajectories,
    read_conditions,
    standardize_fit,
    fit_logistic,
    predict_logistic,
)


def read_all_conditions(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return {row["group_key"]: row for row in csv.DictReader(handle)}


def best_development_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in (
            "window_seconds",
            "lead_seconds",
            "validation_auroc",
            "validation_auprc",
            "validation_brier",
        ):
            row[key] = float(row[key])
    selected = {}
    for model in sorted({row["model_name"] for row in rows}):
        candidates = [row for row in rows if row["model_name"] == model]
        selected[model] = sorted(
            candidates,
            key=lambda row: (
                -row["validation_auroc"],
                -row["validation_auprc"],
                row["validation_brier"],
            ),
        )[0]
    return selected


def grouped_bootstrap(y, score, n_boot=1000, seed=20260809):
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    score = np.asarray(score)
    values = []
    for _ in range(n_boot):
        indices = rng.integers(0, len(y), len(y))
        values.append(
            evaluate(y[indices], score[indices], 0.5)["auroc"]
        )
    values = np.asarray([value for value in values if np.isfinite(value)])
    return {
        "n_boot": int(len(values)),
        "auroc_median": float(np.median(values)),
        "auroc_ci_low": float(np.quantile(values, 0.025)),
        "auroc_ci_high": float(np.quantile(values, 0.975)),
    }


def predict_from_result(rows, result):
    features = result["features"]
    x = np.asarray([[row[key] for key in features] for row in rows])
    mean = np.asarray(result["mean"], dtype=float)
    scale = np.asarray(result["scale"], dtype=float)
    weights = np.asarray(result["weights"], dtype=float)
    probability = predict_logistic((x - mean) / scale, weights)
    y = np.asarray([row["label"] for row in rows], dtype=int)
    return y, probability


def run_test(output_dir, r021_dir, r022_dir, permutation_count=1000):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = read_all_conditions(Path(r021_dir) / "conditions.csv")
    all_groups = set(conditions)
    trajectories = load_trajectories(Path(r021_dir) / "trajectories.csv", all_groups)
    development = best_development_rows(Path(r022_dir) / "development_metrics.csv")
    locked = json.loads(
        (Path(r022_dir) / "locked_config.json").read_text(encoding="utf-8")
    )["selected"]

    results = []
    prediction_rows = []
    model_specs = {
        "locked_baseline": locked,
        "best_ews": development["ews_logistic_variance_ac"],
        "best_dpsi": development["baseline_dpsi"],
        "best_slope": development["baseline_dpsi_slope"],
    }
    fitted_results = {}
    for name, spec in model_specs.items():
        window = float(spec["window_seconds"])
        lead = float(spec["lead_seconds"])
        landmarks, reference_time = build_landmarks(
            conditions,
            trajectories,
            window,
            lead,
        )
        train_rows = [row for row in landmarks if row["split"] == "train"]
        test_rows = [row for row in landmarks if row["split"] == "test"]
        if name == "locked_baseline":
            result = locked
        else:
            result = fit_and_score(train_rows, [row for row in landmarks if row["split"] == "validation"], spec["model_name"])
        fitted_results[name] = result
        y, probability = predict_from_result(test_rows, result)
        for row, prob in zip(test_rows, probability):
            prediction_rows.append(
                {
                    "model": name,
                    "group_key": row["group_key"],
                    "label": row["label"],
                    "probability": float(prob),
                    "target_time_s": row["target_time_s"],
                    "event_time_s": row["event_time_s"],
                }
            )
        metrics = evaluate(y, probability, float(result["threshold"]))
        metrics.update(
            {
                "model": name,
                "window_seconds": window,
                "lead_seconds": lead,
                "reference_time_s": reference_time,
                "median_positive_lead_time_s": float(
                    np.nanmedian(
                        [
                            float(row["event_time_s"]) - float(row["target_time_s"])
                            for row in test_rows
                            if row["label"] == 1
                        ]
                    )
                ),
                "bootstrap": grouped_bootstrap(y, probability, permutation_count),
            }
        )
        results.append(metrics)

    # Group-level label permutation for the locked baseline.
    baseline = results[0]
    locked_spec = model_specs["locked_baseline"]
    landmarks, _ = build_landmarks(
        conditions,
        trajectories,
        float(locked_spec["window_seconds"]),
        float(locked_spec["lead_seconds"]),
    )
    test_rows = [row for row in landmarks if row["split"] == "test"]
    y, probability = predict_from_result(test_rows, locked_spec)
    rng = np.random.default_rng(20260809)
    permuted = []
    for _ in range(permutation_count):
        permuted.append(
            evaluate(rng.permutation(y), probability, 0.5)["auroc"]
        )
    permutation_summary = {
        "n": permutation_count,
        "auroc_median": float(np.nanmedian(permuted)),
        "auroc_ci_low": float(np.nanquantile(permuted, 0.025)),
        "auroc_ci_high": float(np.nanquantile(permuted, 0.975)),
        "observed_locked_auroc": baseline["auroc"],
    }

    # Future-window removal audit: landmark extraction is causal by construction.
    future_diffs = []
    for row in test_rows:
        group = trajectories[row["group_key"]]
        cutoff = float(row["target_time_s"])
        mask = group["time"] <= cutoff
        truncated = {key: values[mask] for key, values in group.items()}
        adjusted = dict(conditions[row["group_key"]])
        adjusted["label"] = "1"
        adjusted["event_time_s"] = str(
            cutoff + float(locked_spec["lead_seconds"])
        )
        rebuilt = extract_landmark(
            adjusted,
            truncated,
            float(locked_spec["window_seconds"]),
            float(locked_spec["lead_seconds"]),
            cutoff,
        )
        if rebuilt is not None:
            for key in ("dpsi", "atp", "dpsi_slope", "rolling_variance", "lag1_ac"):
                future_diffs.append(abs(float(rebuilt[key]) - float(row[key])))
    leakage = {
        "future_window_max_abs_feature_difference": float(max(future_diffs)),
        "future_window_n_checked": len(future_diffs),
        "test_groups_used": len(test_rows),
    }

    # Within-trajectory time-shuffle negative control for the best EWS model.
    ews_spec = fitted_results["best_ews"]
    ews_meta = model_specs["best_ews"]
    shuffled_rows = []
    rng = np.random.default_rng(20260810)
    for row in test_rows:
        group = trajectories[row["group_key"]]
        shuffled = {key: values.copy() for key, values in group.items()}
        rng.shuffle(shuffled["dpsi"])
        rng.shuffle(shuffled["atp"])
        adjusted = dict(conditions[row["group_key"]])
        adjusted["label"] = str(row["label"])
        adjusted["event_time_s"] = str(row["event_time_s"])
        feature_row = extract_landmark(
            adjusted,
            shuffled,
            float(ews_meta["window_seconds"]),
            float(ews_meta["lead_seconds"]),
            float(row["target_time_s"]),
        )
        if feature_row is not None:
            shuffled_rows.append(feature_row)
    shuffled_y, shuffled_probability = predict_from_result(
        shuffled_rows, ews_spec
    )
    shuffle_summary = {
        "model": "best_ews",
        "n_groups": len(shuffled_rows),
        "auroc": evaluate(shuffled_y, shuffled_probability, 0.5)["auroc"],
        "auprc": evaluate(shuffled_y, shuffled_probability, 0.5)["auprc"],
    }

    (output_dir / "locked_test_metrics.json").write_text(
        json.dumps(results, indent=2, sort_keys=True), encoding="utf-8"
    )
    from scripts.source_audit.run_r008_endpoint_protocol import write_csv
    write_csv(output_dir / "test_predictions.csv", prediction_rows)
    (output_dir / "negative_controls.json").write_text(
        json.dumps(
            {
                "group_label_permutation": permutation_summary,
                "future_window_removal": leakage,
                "within_trajectory_time_shuffle": shuffle_summary,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (output_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": "R023",
                "test_paraquat": [5, 20],
                "test_groups_accessed": len(test_rows),
                "locked_config": str(Path(r022_dir) / "locked_config.json"),
                "permutation_count": permutation_count,
                "performance_claim_status": "pending_review",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return results, permutation_summary, leakage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/audit_runs/R023"))
    parser.add_argument("--r021-dir", type=Path, default=Path("inputs/audit_runs/R021"))
    parser.add_argument("--r022-dir", type=Path, default=Path("inputs/audit_runs/R022"))
    parser.add_argument("--permutations", type=int, default=1000)
    args = parser.parse_args()
    results, permutation, leakage = run_test(
        args.output_dir,
        args.r021_dir,
        args.r022_dir,
        permutation_count=args.permutations,
    )
    print(json.dumps({"results": results, "permutation": permutation, "leakage": leakage}, indent=2))


if __name__ == "__main__":
    main()

