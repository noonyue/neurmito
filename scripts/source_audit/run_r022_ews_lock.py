"""Select EWS features and thresholds on train/validation groups only (R022)."""

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.source_audit.run_r008_endpoint_protocol import write_csv


WINDOW_SECONDS = (5.0, 10.0, 20.0, 30.0)
LEAD_SECONDS = (10.0, 20.0, 30.0, 50.0)
MODEL_NAMES = (
    "ews_logistic_variance_ac",
    "baseline_dpsi",
    "baseline_dpsi_slope",
    "baseline_dpsi_atp_logistic",
)


def read_conditions(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return {
            row["group_key"]: row
            for row in csv.DictReader(handle)
            if row["split"] in {"train", "validation"}
        }


def load_trajectories(path, allowed_groups):
    groups = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = row["group_key"]
            if key not in allowed_groups:
                continue
            item = groups.setdefault(
                key,
                {"time": [], "dpsi": [], "atp": []},
            )
            item["time"].append(float(row["time_s"]))
            item["dpsi"].append(float(row["dpsi_mv"]))
            item["atp"].append(float(row["atp_m_mm"]))
    for item in groups.values():
        for key in item:
            item[key] = np.asarray(item[key], dtype=float)
    return groups


def _target_time(condition, lead_seconds, reference_time):
    if condition["label"] == "1":
        return float(condition["event_time_s"]) - lead_seconds
    return reference_time


def _window_values(arr, time, target_time, window_seconds):
    end = int(np.searchsorted(time, target_time, side="right"))
    if end < 2:
        return None
    start = int(np.searchsorted(time, target_time - window_seconds, side="left"))
    if end - start < 3:
        return None
    return arr[start:end]


def extract_landmark(condition, trajectory, window_seconds, lead_seconds, reference_time):
    target = _target_time(condition, lead_seconds, reference_time)
    if target < window_seconds:
        return None
    time = trajectory["time"]
    end = int(np.searchsorted(time, target, side="right"))
    if end < 3:
        return None
    dpsi_window = _window_values(
        trajectory["dpsi"], time, target, window_seconds
    )
    atp_window = _window_values(trajectory["atp"], time, target, window_seconds)
    if dpsi_window is None or atp_window is None:
        return None
    slope = float(np.polyfit(np.arange(dpsi_window.size), dpsi_window, 1)[0])
    variance = float(np.var(dpsi_window, ddof=1))
    x0 = dpsi_window[:-1]
    x1 = dpsi_window[1:]
    if np.std(x0) == 0.0 or np.std(x1) == 0.0:
        autocorr = 0.0
    else:
        autocorr = float(np.corrcoef(x0, x1)[0, 1])
    return {
        "group_key": condition["group_key"],
        "split": condition["split"],
        "label": int(condition["label"]),
        "target_time_s": target,
        "event_time_s": condition["event_time_s"],
        "dpsi": float(trajectory["dpsi"][end - 1]),
        "atp": float(trajectory["atp"][end - 1]),
        "dpsi_slope": slope,
        "rolling_variance": variance,
        "lag1_ac": autocorr,
        "window_seconds": window_seconds,
        "lead_seconds": lead_seconds,
    }


def build_landmarks(conditions, trajectories, window_seconds, lead_seconds):
    positive_events = [
        float(row["event_time_s"])
        for row in conditions.values()
        if row["split"] == "train" and row["label"] == "1"
    ]
    reference_time = float(np.median(positive_events)) - lead_seconds
    rows = []
    for condition in conditions.values():
        trajectory = trajectories.get(condition["group_key"])
        if trajectory is None:
            continue
        landmark = extract_landmark(
            condition,
            trajectory,
            window_seconds,
            lead_seconds,
            reference_time,
        )
        if landmark is not None:
            rows.append(landmark)
    return rows, reference_time


def _sigmoid(z):
    z = np.clip(z, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-z))


def standardize_fit(x):
    mean = np.nanmean(x, axis=0)
    scale = np.nanstd(x, axis=0)
    scale[scale < 1e-12] = 1.0
    return mean, scale


def fit_logistic(x, y, l2=1e-3, iterations=80):
    x = np.column_stack([np.ones(x.shape[0]), x])
    weights = np.zeros(x.shape[1], dtype=float)
    for _ in range(iterations):
        p = _sigmoid(x @ weights)
        grad = x.T @ (p - y)
        grad[1:] += l2 * weights[1:]
        hessian = (x.T * (p * (1.0 - p))) @ x
        hessian[1:, 1:] += l2 * np.eye(x.shape[1] - 1)
        try:
            step = np.linalg.solve(hessian, grad)
        except np.linalg.LinAlgError:
            break
        weights -= step
        if np.max(np.abs(step)) < 1e-7:
            break
    return weights


def predict_logistic(x, weights):
    return _sigmoid(
        np.column_stack([np.ones(x.shape[0]), x]) @ weights
    )


def auroc(y, score):
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    positives = y == 1
    negatives = y == 0
    if not positives.any() or not negatives.any():
        return np.nan
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(score) + 1)
    return float(
        (ranks[positives].sum() - positives.sum() * (positives.sum() + 1) / 2)
        / (positives.sum() * negatives.sum())
    )


def auprc(y, score):
    order = np.argsort(-np.asarray(score), kind="mergesort")
    y = np.asarray(y, dtype=int)[order]
    tp = np.cumsum(y == 1)
    fp = np.cumsum(y == 0)
    if tp[-1] == 0:
        return np.nan
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / tp[-1]
    previous_recall = np.concatenate(([0.0], recall[:-1]))
    return float(np.sum((recall - previous_recall) * precision))


def brier(y, probability):
    return float(np.mean((np.asarray(probability) - np.asarray(y)) ** 2))


def threshold_from_train(y, score):
    candidates = np.unique(score)
    best = (float("-inf"), 0.5)
    for threshold in candidates:
        pred = score >= threshold
        tp = np.sum((pred == 1) & (y == 1))
        fn = np.sum((pred == 0) & (y == 1))
        fp = np.sum((pred == 1) & (y == 0))
        tn = np.sum((pred == 0) & (y == 0))
        tpr = tp / max(tp + fn, 1)
        fpr = fp / max(fp + tn, 1)
        youden = tpr - fpr
        if youden > best[0]:
            best = (youden, float(threshold))
    return best[1]


def evaluate(y, probability, threshold):
    return {
        "n": int(len(y)),
        "positive_rate": float(np.mean(y)),
        "auroc": auroc(y, probability),
        "auprc": auprc(y, probability),
        "brier": brier(y, probability),
        "threshold": threshold,
        "threshold_accuracy": float(
            np.mean((probability >= threshold) == (np.asarray(y) == 1))
        ),
    }


def fit_and_score(train_rows, validation_rows, model_name):
    feature_map = {
        "baseline_dpsi": ["dpsi"],
        "baseline_dpsi_slope": ["dpsi_slope"],
        "baseline_dpsi_atp_logistic": ["dpsi", "atp"],
        "ews_logistic_variance_ac": ["rolling_variance", "lag1_ac"],
    }
    features = feature_map[model_name]
    train_x = np.asarray([[row[key] for key in features] for row in train_rows])
    val_x = np.asarray([[row[key] for key in features] for row in validation_rows])
    y_train = np.asarray([row["label"] for row in train_rows], dtype=int)
    y_val = np.asarray([row["label"] for row in validation_rows], dtype=int)
    mean, scale = standardize_fit(train_x)
    weights = fit_logistic((train_x - mean) / scale, y_train)
    train_probability = predict_logistic((train_x - mean) / scale, weights)
    val_probability = predict_logistic((val_x - mean) / scale, weights)
    threshold = threshold_from_train(y_train, train_probability)
    train_metrics = evaluate(y_train, train_probability, threshold)
    val_metrics = evaluate(y_val, val_probability, threshold)
    return {
        "model_name": model_name,
        "features": features,
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "weights": weights.tolist(),
        "threshold": threshold,
        "train": train_metrics,
        "validation": val_metrics,
    }


def run_lock(output_dir, trajectories_csv, conditions_csv):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conditions = read_conditions(conditions_csv)
    trajectories = load_trajectories(trajectories_csv, set(conditions))
    candidate_rows = []
    model_results = []
    for window in WINDOW_SECONDS:
        for lead in LEAD_SECONDS:
            rows, reference_time = build_landmarks(
                conditions, trajectories, window, lead
            )
            train_rows = [row for row in rows if row["split"] == "train"]
            val_rows = [row for row in rows if row["split"] == "validation"]
            if len({row["label"] for row in train_rows}) < 2:
                continue
            if len({row["label"] for row in val_rows}) < 2:
                continue
            for model_name in MODEL_NAMES:
                result = fit_and_score(train_rows, val_rows, model_name)
                result.update(
                    {
                        "window_seconds": window,
                        "lead_seconds": lead,
                        "reference_time_s": reference_time,
                        "n_train": len(train_rows),
                        "n_validation": len(val_rows),
                    }
                )
                model_results.append(result)
                candidate_rows.append(
                    {
                        "model_name": model_name,
                        "window_seconds": window,
                        "lead_seconds": lead,
                        "n_train": len(train_rows),
                        "n_validation": len(val_rows),
                        "train_auroc": result["train"]["auroc"],
                        "validation_auroc": result["validation"]["auroc"],
                        "validation_auprc": result["validation"]["auprc"],
                        "validation_brier": result["validation"]["brier"],
                        "threshold": result["threshold"],
                    }
                )
    candidate_rows.sort(
        key=lambda row: (
            -row["validation_auroc"],
            -row["validation_auprc"],
            row["validation_brier"],
        )
    )
    selected = candidate_rows[0]
    selected_result = next(
        result
        for result in model_results
        if result["model_name"] == selected["model_name"]
        and result["window_seconds"] == selected["window_seconds"]
        and result["lead_seconds"] == selected["lead_seconds"]
    )
    config = {
        "run_id": "R022",
        "contract": "R020_EWS_DATA_CONTRACT.md",
        "selected": selected_result,
        "selection_rule": (
            "max validation AUROC, then validation AUPRC, then minimum "
            "validation Brier; all choices fit on train only"
        ),
        "candidate_windows_seconds": WINDOW_SECONDS,
        "candidate_leads_seconds": LEAD_SECONDS,
        "models": MODEL_NAMES,
        "test_groups_accessed": False,
        "locked": True,
    }
    (output_dir / "locked_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(output_dir / "development_metrics.csv", candidate_rows)
    (output_dir / "development_landmarks.json").write_text(
        json.dumps(
            {
                "n_development_groups": len(conditions),
                "n_trajectory_groups_loaded": len(trajectories),
                "train_groups": sum(row["split"] == "train" for row in conditions.values()),
                "validation_groups": sum(
                    row["split"] == "validation" for row in conditions.values()
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/audit_runs/R022"))
    parser.add_argument(
        "--trajectories-csv",
        type=Path,
        default=Path("inputs/audit_runs/R021/trajectories.csv"),
    )
    parser.add_argument(
        "--conditions-csv",
        type=Path,
        default=Path("inputs/audit_runs/R021/conditions.csv"),
    )
    args = parser.parse_args()
    config = run_lock(args.output_dir, args.trajectories_csv, args.conditions_csv)
    print(json.dumps(config["selected"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

