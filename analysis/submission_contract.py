"""Evidence-preserving analysis views for the corrected submission.

Locked inputs are never written here. Derived CSVs describe existing observations,
deterministic illustrations and previously plotted scenario coordinates.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "inputs" / "audit_runs"
DERIVED = ROOT / "results" / "submission_data"
TITLE = "NeurMito-DT: source-aware reserve analysis and nonlinear mitochondrial stress-state transitions"
STEMS = {
    1: "Figure_1_Reserve",
    2: "Figure_2_Transition",
    3: "Figure_3_Hybrid",
    4: "Figure_4_EWS",
    5: "Figure_5_Spatial",
    6: "Figure_6_Disease",
}
FIGURE_TITLES = {
    1: "Source-specific respiratory reserve and conditional mapping",
    2: "Resolved stress-transition scan, ablation and robustness",
    3: "Controlled hidden-residual benchmark",
    4: "Illustrative trajectory and configuration-specific locked diagnostics",
    5: "Prescribed spatial vulnerability scenario",
    6: "Prescribed disease-axis scenario and uncalibrated projections",
}
MAIN_TITLES = {
    1: ["Endpoint availability", "Retained observation definitions", "Maximal/basal ratios", "Source-specific spare/basal ratios", "Reserve coordinates", "Restricted loss", "Conditional parameter ranking", "Inference scope", "Group means"],
    2: ["Resolved endpoint class", "Final membrane potential", "Final ATP", "Transition profiles", "Discrete transition band", "Non-additive response residuals", "Mechanism ablation", "Endpoint robustness", "ATP-response robustness"],
    3: ["Benchmark x1", "Benchmark x2", "Trajectory RMSE", "Endpoint RMSE", "Seed-specific errors", "Residual correction", "Hidden gain and error", "Matched absolute errors", "Mean RMSE differences"],
    4: ["Illustrative trajectory", "Illustrative rolling variance", "Illustrative lag-1 autocorrelation", "Configuration-specific discrimination", "Brier score", "Bootstrap AUROC", "Event-aligned lead interval", "Locked-baseline label permutation", "EWS time shuffle", "Model-specific prediction distributions"],
    5: ["Health index", "Supply proxy", "Demand proxy", "ROS proxy", "Thresholded region", "Separately prescribed trajectories", "Distal/proximal index", "Position profiles", "Area fractions", "Demand-health projection"],
    6: ["Specified weights", "Separately prescribed trajectories", "Uncalibrated coordinates", "Mean mechanism weights", "Mean-weight priority score", "Weight deviations", "Weight radar", "Specified component coverage", "Prescribed score range"],
}
SUPP_TITLES = {
    1: ["Source-specific ratios", "Endpoint availability", "Digitization interval overlap", "Observation roles", "Reserve coordinates", "Evidence scope"],
    2: ["Restricted losses", "Compatible parameter combinations", "Near-best counts", "Digitization-corner winners", "Conditional means", "Inference scope"],
    3: ["Trajectory RMSE", "Endpoint RMSE", "Seed variability", "Benchmark x1", "Benchmark x2", "Matched errors"],
    4: ["Resolved endpoint class", "Membrane potential", "Discrete transition band", "Non-additive residual", "Ablation endpoint counts", "Robustness endpoint counts"],
    5: ["Split counts", "Endpoint counts", "Event times", "Configuration-specific discrimination", "Brier score", "Model-specific negative controls"],
    6: ["Rebuild chain", "Input footprint", "Evidence scope"],
}
SUPP_STEMS = {
    1: "r071_sfigure_s1_source_contract_audit",
    2: "r071_sfigure_s2_restricted_mapping_sensitivity",
    3: "r071_sfigure_s3_hybrid_benchmark_details",
    4: "r071_sfigure_s4_phase_robustness_details",
    5: "r071_sfigure_s5_ews_locked_test_details",
    6: "r071_sfigure_s6_reproducibility_map",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def reserve_observations() -> list[dict]:
    low = read_json(RUNS / "R042/digitization_uncertainty_propagation.json")["source_ratio_intervals"]
    records = []
    for record, pmid in [("R033", "31931869"), ("R039", "24056030")]:
        ratios = low[f"PMID:{pmid}"]
        records.append({
            "record": record, "pmid": pmid, "group": "lower-reserve source pair",
            "maximal_to_basal": ratios["maximal_to_basal"]["nominal"],
            "maximal_low": ratios["maximal_to_basal"]["low"], "maximal_high": ratios["maximal_to_basal"]["high"],
            "spare_to_basal": ratios["spare_to_basal"]["nominal"],
            "spare_low": ratios["spare_to_basal"]["low"], "spare_high": ratios["spare_to_basal"]["high"],
            "spare_definition": "(digitized maximal - digitized basal) / digitized basal",
            "evidence_type": "literature-derived digitization; algebraic spare",
            "source_file": "inputs/audit_runs/R042/digitization_uncertainty_propagation.json",
        })
    for record, filename in [("R060", "pmc4454361_control_relative_digitization.json"), ("R060B", "pmc5124357_control_relative_digitization.json")]:
        source = read_json(RUNS / record / filename)
        ratios = source["relative_ratios"]
        records.append({
            "record": record, "pmid": source["source_id"].split(":")[1],
            "group": "higher-reserve candidate pair",
            "maximal_to_basal": ratios["maximal_to_basal"]["value"],
            "maximal_low": ratios["maximal_to_basal"]["interval"][0], "maximal_high": ratios["maximal_to_basal"]["interval"][1],
            "spare_to_basal": ratios["spare_to_basal"]["value"],
            "spare_low": ratios["spare_to_basal"]["interval"][0], "spare_high": ratios["spare_to_basal"]["interval"][1],
            "spare_definition": "independently digitized source-reported spare / digitized basal",
            "evidence_type": "literature-derived digitization; source-reported spare",
            "source_file": f"inputs/audit_runs/{record}/{filename}",
        })
    for row in records:
        row["algebraic_maximal_minus_one"] = row["maximal_to_basal"] - 1.0
        row["definition_difference"] = row["spare_to_basal"] - row["algebraic_maximal_minus_one"]
        row["cross_source_equivalence"] = "not imposed; source protocol equivalence requires author confirmation"
    return records


def ews_configurations() -> tuple[list[dict], list[dict]]:
    conditions = read_csv(RUNS / "R021/conditions.csv")
    predictions = read_csv(RUNS / "R023/test_predictions.csv")
    metrics = read_json(RUNS / "R023/locked_test_metrics.json")
    configs, exclusions = [], []
    # R021's code uses 5001 equally spaced high-resolution points per group.
    # The conditions table retains the earlier 1001-point endpoint-screen field.
    points = 5001
    qc = read_json(RUNS / "R021/qc_summary.json")
    if qc["n_trajectory_rows"] != qc["n_conditions"] * points:
        raise ValueError("High-resolution point count is not supported by QC")
    for metric in metrics:
        name = metric["model"]
        kept = [row for row in predictions if row["model"] == name]
        kept_keys = {row["group_key"] for row in kept}
        if len(kept_keys) != len(kept):
            raise ValueError(f"Duplicate prediction group: {name}")
        training_events = [float(item["event_time_s"]) for item in conditions
                           if item["split"] == "train" and item["label"] == "1"]
        if not np.isclose(np.median(training_events) - metric["lead_seconds"], metric["reference_time_s"]):
            raise ValueError(f"Training reference time mismatch: {name}")
        kept_lookup = {item["group_key"]: item for item in kept}
        n_positive = sum(int(row["label"]) for row in kept)
        row = {key: value for key, value in metric.items() if key != "bootstrap"}
        row.update({"positive_count": n_positive, "negative_count": len(kept) - n_positive,
                    "test_split_n": 126, "excluded_count": 126 - len(kept),
                    "target_rule_positive": "observed event time - prescribed lead interval",
                    "target_rule_negative": "training-event median - prescribed lead interval",
                    "analysis_type": "retrospective event-aligned diagnostic, not prospective forecasting"})
        row.update(metric["bootstrap"])
        for condition in (item for item in conditions if item["split"] == "test"):
            target = (float(condition["event_time_s"]) - metric["lead_seconds"]
                      if condition["label"] == "1" else metric["reference_time_s"])
            time = np.linspace(0.0, float(condition["duration_s"]), points)
            start = int(np.searchsorted(time, target - metric["window_seconds"], side="left"))
            end = int(np.searchsorted(time, target, side="right"))
            reason = ("target precedes required history" if target < metric["window_seconds"] else
                      "fewer than three samples before target" if end < 3 else
                      "fewer than three samples in window" if end - start < 3 else "eligible")
            eligible = reason == "eligible"
            saved = condition["group_key"] in kept_keys
            if saved:
                prediction = kept_lookup[condition["group_key"]]
                if prediction["label"] != condition["label"] or not np.isclose(float(prediction["target_time_s"]), target):
                    raise ValueError(f"Prediction label/time mismatch: {name}, {condition['group_key']}")
            if eligible != saved:
                raise ValueError(f"Unexplained inclusion: {name}, {condition['group_key']}")
            exclusions.append({"model": name, "group_key": condition["group_key"],
                               "label": int(condition["label"]), "included": int(saved),
                               "reason": reason, "target_time_s": target,
                               "window_seconds": metric["window_seconds"],
                               "high_resolution_points": points, "window_sample_count": end - start,
                               "duration_s": condition["duration_s"]})
        if len(kept) != metric["n"] or not np.isclose(n_positive / len(kept), metric["positive_rate"]):
            raise ValueError(f"Metric sample counts disagree: {name}")
        configs.append(row)
    return configs, exclusions


def illustration() -> list[dict]:
    conditions = read_csv(RUNS / "R021/conditions.csv")
    events = [float(row["event_time_s"]) for row in conditions if row["split"] == "test" and row["label"] == "1"]
    event = min(events)
    time = np.linspace(0.0, 92.0, 185)
    y = 170 - 8 * np.log1p(time / 12) - 45 / (1 + np.exp(-(time - event) / 2.5))
    variance, ac = np.full_like(time, np.nan), np.full_like(time, np.nan)
    for i in range(24, len(time)):
        window = y[i - 24:i]
        variance[i] = np.var(window, ddof=1)
        ac[i] = np.corrcoef(window[:-1], window[1:])[0, 1]
    return [{"time_s": t, "illustrative_dpsi_mv": value, "rolling_variance_mv2": var,
             "lag1_ac": corr, "event_marker_s": event, "window_samples": 24,
             "evidence_type": "parameterized illustration; not an R021 ODE trajectory"}
            for t, value, var, corr in zip(time, y, variance, ac)]


def spatial_views() -> tuple[list[dict], list[dict]]:
    x, stress = np.linspace(0, 1, 100), np.linspace(0, 1, 80)
    grid = []
    for s in stress:
        for position in x:
            supply = 1 - 0.25 * position - 0.20 * s
            demand = 0.30 + 0.45 * position + 0.25 * s
            ros = s * (0.35 + 0.65 * position)
            health = 1 - 0.50 * s - 0.30 * position * s - 0.12 * demand + 0.08 * supply
            grid.append({"position": position, "stress": s, "supply": supply, "demand": demand,
                         "ros": ros, "health": health, "thresholded": int(health < 0.42)})
    trajectories = [{"position": position, "scenario_time": t,
                     "health": 1 - 0.60 * t - 0.28 * position * t ** 1.5}
                    for position in [0.1, 0.5, 0.9] for t in np.linspace(0, 1, 120)]
    return grid, trajectories


def disease_views() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    diseases = ["PD-like", "AD-like", "ALS-like", "HD-like", "FTD-like"]
    axes = ["Respiration", "ROS", "Calcium", "Demand", "Transport", "Proteostasis"]
    matrix = np.array([[0.9, 0.8, 0.4, 0.5, 0.3, 0.4], [0.5, 0.6, 0.8, 0.7, 0.4, 0.6],
                       [0.4, 0.8, 0.6, 0.7, 0.8, 0.5], [0.5, 0.7, 0.5, 0.8, 0.5, 0.8],
                       [0.4, 0.6, 0.6, 0.6, 0.7, 0.7]])
    weights = [{"disease": disease, "axis": axis, "weight": matrix[i, j],
                "evidence_type": "specified scenario weight"}
               for i, disease in enumerate(diseases) for j, axis in enumerate(axes)]
    projections = [{"disease": disease, "ros_weight": matrix[i, 1], "preset_offset": 0.08 * i,
                    "plotted_ros_coordinate": matrix[i, 1] + 0.08 * i,
                    "energy_coordinate": 1 - matrix[i, 0] * 0.45 - matrix[i, 3] * 0.25,
                    "priority_score": matrix[i].mean(), "prescribed_range": 0.08,
                    "offset_interpretation": "requires author confirmation; coordinate is uncalibrated",
                    "range_interpretation": "prescribed scenario range; not a confidence interval"}
                   for i, disease in enumerate(diseases)]
    trajectories = [{"disease": disease, "scenario_time": t,
                     "health": 1 - (0.35 + 0.12 * i) * t - 0.10 * i * t ** 2}
                    for i, disease in enumerate(diseases[:3]) for t in np.linspace(0, 1, 100)]
    checklist = np.array([[1, 1, 0, 0], [1, 0, 1, 0], [1, 1, 0, 1], [0, 1, 0, 1], [0, 1, 1, 0]])
    coverage = [{"disease": disease, "component": component, "included": int(checklist[i, j]),
                 "evidence_type": "prespecified coverage; not literature validation"}
                for i, disease in enumerate(diseases) for j, component in enumerate(["mito", "ROS", "Ca", "stress"])]
    return weights, projections, trajectories, coverage


def prepare() -> dict:
    DERIVED.mkdir(parents=True, exist_ok=True)
    before = {str(p.relative_to(ROOT)): sha256(p) for p in RUNS.rglob("*") if p.is_file()}
    protected = read_json(ROOT / "inputs/locked_audit_hashes.json")["files"]
    normalized = {name.replace("\\", "/"): digest for name, digest in before.items()}
    if normalized != protected:
        raise RuntimeError("Locked inputs differ from before_submission_fix checkpoint")
    configs, exclusions = ews_configurations()
    grid, trajectories = spatial_views()
    weights, projections, disease_trajectories, coverage = disease_views()
    views = {"Reserve_Observations": reserve_observations(), "EWS_Configurations": configs,
             "EWS_Eligibility": exclusions, "F4_Illustration": illustration(),
             "F5_Grid": grid, "F5_Trajectories": trajectories,
             "F6_Weights": weights, "F6_Projections": projections,
             "F6_Trajectories": disease_trajectories, "F6_Coverage": coverage}
    for name, rows in views.items():
        write_csv(DERIVED / f"{name}.csv", rows)
    phase = read_csv(RUNS / "R014B/resolved_transition_grid.csv")
    qc = read_json(RUNS / "R021/qc_summary.json")
    summary = {"title": TITLE, "main_panel_count": sum(map(len, MAIN_TITLES.values())),
               "supplementary_panel_count": sum(map(len, SUPP_TITLES.values())),
               "transition_scan_n": len(phase),
               "transition_scan_classes": dict(Counter(row["resolved_endpoint_class"] for row in phase)),
               "ews_cohort": qc, "ews_configurations": configs,
               "raw_input_hashes": before,
               "derived_files": {name: sha256(DERIVED / f"{name}.csv") for name in views},
               "limitations": ["source-reported spare is not forced to equal F/B-1",
                               "R025 is independent of the biological ODE",
                               "EWS anchors positive groups on observed future event times",
                               "R021 full trajectories and R022 locked development artifacts are absent",
                               "disease offsets/ranges/weights require author confirmation"]}
    if before != {str(p.relative_to(ROOT)): sha256(p) for p in RUNS.rglob("*") if p.is_file()}:
        raise RuntimeError("Locked inputs changed")
    (DERIVED / "analysis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({key: result[key] for key in ["transition_scan_n", "main_panel_count", "supplementary_panel_count"]}, indent=2))
