"""R052 audited supplementary figure rebuild.

This run creates a minimal supplementary set from already-audited computational
outputs. It deliberately does not reuse or overwrite the legacy
``sfigure_s*_publication`` assets, because several of those carry unsupported
wet-lab, MCMC, spatial-validation, disease-quantification, or ROC claims.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "refine-logs" / "runs"
OUT_DIR = ROOT / "figures"
R052_DIR = RUNS / "R052"
MANIFEST = R052_DIR / "audited_supplementary_manifest.json"

INPUTS = {
    "R009_mechanism_ablation": RUNS / "R009" / "mechanism_ablation_summary.csv",
    "R014B_transition_band": RUNS / "R014B" / "transition_band_summary.csv",
    "R014B_transition_grid": RUNS / "R014B" / "resolved_transition_grid.csv",
    "R021_qc": RUNS / "R021" / "qc_summary.json",
    "R022_development": RUNS / "R022" / "development_metrics.csv",
    "R023_locked_test": RUNS / "R023" / "locked_test_metrics.json",
    "R023_negative_controls": RUNS / "R023" / "negative_controls.json",
    "R025_summary": RUNS / "R025" / "summary.csv",
    "R025_metrics": RUNS / "R025" / "metrics.csv",
    "R047_contract": RUNS / "R047" / "cross_source_formula_coordination.json",
    "R049_claim_boundary": RUNS / "R049" / "computational_claim_boundary.json",
    "R051_figure1": RUNS / "R051" / "figure1_metadata.json",
}

OUTPUTS = {
    "audited_sfigure_s1_source_contract": {
        "label": "Audited Supplementary Figure S1",
        "stem": "audited_sfigure_s1_source_contract",
        "scope": "R047/R049 source-contract and claim-boundary provenance",
    },
    "audited_sfigure_s2_hybrid_benchmark": {
        "label": "Audited Supplementary Figure S2",
        "stem": "audited_sfigure_s2_hybrid_benchmark",
        "scope": "R025 controlled hidden-residual in-silico benchmark",
    },
    "audited_sfigure_s3_phase_robustness": {
        "label": "Audited Supplementary Figure S3",
        "stem": "audited_sfigure_s3_phase_robustness",
        "scope": "R009/R014B reduced-ODE endpoint and transition robustness",
    },
    "audited_sfigure_s4_ews_locked_test": {
        "label": "Audited Supplementary Figure S4",
        "stem": "audited_sfigure_s4_ews_locked_test",
        "scope": "R021-R023 locked EWS test and negative controls",
    },
}

COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "gray": "#777777",
    "light": "#F2F2F2",
}

plt.rcParams.update({
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value):
    if value in ("", "nan", "NaN", None):
        return float("nan")
    return float(value)


def _save(fig, key: str) -> dict:
    info = OUTPUTS[key]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / f"{info['stem']}.png"
    pdf = OUT_DIR / f"{info['stem']}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return {
        "label": info["label"],
        "scope": info["scope"],
        "png": str(png.relative_to(ROOT)).replace("\\", "/"),
        "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        "png_sha256": _sha256(png),
        "pdf_sha256": _sha256(pdf),
        "status": "active_audited_computational_supplement",
    }


def _plot_source_contract() -> dict:
    r047 = _read_json(INPUTS["R047_contract"])
    r049 = _read_json(INPUTS["R049_claim_boundary"])
    r051 = _read_json(INPUTS["R051_figure1"])

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.25), constrained_layout=True)

    terms = ["B", "O", "F", "N", "A", "P"]
    records = ["R033", "R039", "R046"]
    status_code = {
        "reported": 4,
        "digitized": 4,
        "inferred": 3,
        "inferred_conflicting": 2,
        "unavailable": 1,
    }
    matrix = np.asarray([
        [status_code[r047["records"][record]["terms"][term]] for term in terms]
        for record in records
    ])
    cmap = matplotlib.colors.ListedColormap(
        ["white", "#DDDDDD", COLORS["purple"], COLORS["orange"], COLORS["green"]]
    )
    axes[0].imshow(matrix, cmap=cmap, vmin=0, vmax=4, aspect="auto")
    short = {
        "reported": "reported",
        "digitized": "digitized",
        "inferred": "inferred",
        "inferred_conflicting": "conflict",
        "unavailable": "missing",
    }
    for row, record in enumerate(records):
        for col, term in enumerate(terms):
            status = r047["records"][record]["terms"][term]
            axes[0].text(
                col,
                row,
                short[status],
                ha="center",
                va="center",
                fontsize=6.3,
                color="white" if status_code[status] in (2, 4) else "black",
            )
    axes[0].set_xticks(np.arange(len(terms)), terms)
    axes[0].set_yticks(np.arange(len(records)), records)
    axes[0].set_title("a  Source-stage status", loc="left", fontweight="bold")
    axes[0].tick_params(length=0)
    for spine in axes[0].spines.values():
        spine.set_visible(False)

    endpoint_items = [
        ("maximal", "F", "fit/holdout"),
        ("spare", "F-B", "fit/holdout"),
        ("proton leak", "P", "diagnostic only"),
        ("ATP-linked", "A", "blocked"),
        ("absolute OCR", "units", "blocked"),
    ]
    decision_color = {
        "fit/holdout": COLORS["green"],
        "diagnostic only": COLORS["orange"],
        "blocked": COLORS["purple"],
    }
    y = np.arange(len(endpoint_items))
    axes[1].barh(
        y,
        [1] * len(endpoint_items),
        color=[decision_color[item[2]] for item in endpoint_items],
        alpha=0.85,
    )
    axes[1].set_yticks(y, [item[0] for item in endpoint_items])
    axes[1].set_xticks([])
    axes[1].invert_yaxis()
    for yi, (_, formula, decision) in zip(y, endpoint_items):
        axes[1].text(0.03, yi, formula, va="center", ha="left", color="white", fontweight="bold")
        axes[1].text(0.98, yi, decision, va="center", ha="right", color="white")
    axes[1].set_title("b  Observation contract", loc="left", fontweight="bold")

    supported = len(r049["supported_claims"])
    blocked = len(r049["blocked_claims"])
    axes[2].bar(["supported\nscoped", "blocked"], [supported, blocked],
                color=[COLORS["green"], COLORS["purple"]])
    axes[2].set_ylabel("Claim count")
    axes[2].set_title("c  Claim boundary", loc="left", fontweight="bold")
    axes[2].text(
        0.5,
        0.92,
        "Figure 1 gate:\nno absolute OCR\nno MCMC\nno validation",
        transform=axes[2].transAxes,
        ha="center",
        va="top",
        fontsize=7,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": COLORS["light"], "edgecolor": COLORS["gray"]},
    )
    assert r051["claim_gate"]["absolute_ocr_displayed"] is False
    return _save(fig, "audited_sfigure_s1_source_contract")


def _r025_stats():
    rows = _read_csv(INPUTS["R025_metrics"])
    grouped = defaultdict(lambda: {"trajectory_rmse": [], "endpoint_rmse": []})
    for row in rows:
        grouped[row["model"]]["trajectory_rmse"].append(_float(row["trajectory_rmse"]))
        grouped[row["model"]]["endpoint_rmse"].append(_float(row["endpoint_rmse"]))
    stats = {}
    for model, values in grouped.items():
        stats[model] = {}
        for metric, items in values.items():
            stats[model][f"{metric}_mean"] = mean(items)
            stats[model][f"{metric}_sd"] = stdev(items) if len(items) > 1 else 0.0
    return stats


def _plot_hybrid_benchmark() -> dict:
    stats = _r025_stats()
    models = ["ode", "neural", "hybrid"]
    labels = ["ODE", "Neural", "Hybrid"]
    fig, axes = plt.subplots(1, 3, figsize=(11.3, 3.25), constrained_layout=True)

    for ax, metric, title in (
        (axes[0], "trajectory_rmse", "a  Trajectory RMSE"),
        (axes[1], "endpoint_rmse", "b  Endpoint RMSE"),
    ):
        vals = [stats[m][f"{metric}_mean"] for m in models]
        errs = [stats[m][f"{metric}_sd"] for m in models]
        ax.bar(labels, vals, yerr=errs, capsize=3,
               color=[COLORS["gray"], COLORS["blue"], COLORS["green"]])
        ax.set_ylabel("RMSE")
        ax.set_title(title, loc="left", fontweight="bold")

    ode_traj = stats["ode"]["trajectory_rmse_mean"]
    ode_end = stats["ode"]["endpoint_rmse_mean"]
    improvements = {
        "Neural\ntrajectory": 100 * (ode_traj - stats["neural"]["trajectory_rmse_mean"]) / ode_traj,
        "Hybrid\ntrajectory": 100 * (ode_traj - stats["hybrid"]["trajectory_rmse_mean"]) / ode_traj,
        "Neural\nendpoint": 100 * (ode_end - stats["neural"]["endpoint_rmse_mean"]) / ode_end,
        "Hybrid\nendpoint": 100 * (ode_end - stats["hybrid"]["endpoint_rmse_mean"]) / ode_end,
    }
    axes[2].bar(
        list(improvements.keys()),
        list(improvements.values()),
        color=[COLORS["blue"], COLORS["green"], COLORS["blue"], COLORS["green"]],
    )
    axes[2].set_ylabel("% lower RMSE than ODE")
    axes[2].set_title("c  Controlled benchmark only", loc="left", fontweight="bold")
    axes[2].tick_params(axis="x", rotation=25)
    axes[2].axhline(0, color="black", lw=0.8)
    return _save(fig, "audited_sfigure_s2_hybrid_benchmark")


def _plot_phase_robustness() -> dict:
    band = _read_csv(INPUTS["R014B_transition_band"])
    ablation = _read_csv(INPUTS["R009_mechanism_ablation"])
    grid = _read_csv(INPUTS["R014B_transition_grid"])

    fig, axes = plt.subplots(1, 3, figsize=(11.6, 3.25), constrained_layout=True)

    pq = [_float(row["paraquat_index"]) for row in band]
    highest = [_float(row["highest_physiological_rotenone"]) for row in band]
    lowest = [_float(row["lowest_depolarized_rotenone"]) for row in band]
    axes[0].plot(pq, highest, "o-", color=COLORS["green"], label="highest physiological")
    axes[0].plot(pq, lowest, "o-", color=COLORS["red"], label="lowest depolarized")
    axes[0].fill_between(pq, highest, lowest, color=COLORS["orange"], alpha=0.25)
    axes[0].set_xlabel("Paraquat index")
    axes[0].set_ylabel("Rotenone inhibition")
    axes[0].set_title("a  Resolved transition band", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)

    short_variant = {
        "full_model": "full",
        "no_ros_induced_leak": "no ROS\nleak",
        "no_h2o2_c1_feedback": "no H2O2\nCI feedback",
        "no_ros_leak_no_h2o2_c1_feedback": "no ROS leak\nor CI feedback",
    }
    names = [short_variant.get(row["model_variant"], row["model_variant"]) for row in ablation]
    drops = [_float(row["mean_dpsi_drop_0_8_to_0_9"]) for row in ablation]
    axes[1].bar(np.arange(len(names)), drops, color=COLORS["blue"])
    axes[1].set_xticks(np.arange(len(names)), names)
    axes[1].set_ylabel("Mean DPsi drop, 0.8 to 0.9")
    axes[1].set_title("b  Mechanism ablation", loc="left", fontweight="bold")
    axes[1].tick_params(axis="x", labelsize=6)

    class_counts = defaultdict(int)
    for row in grid:
        if row["resolved_endpoint_eligible_for_phase_diagram"] == "True":
            class_counts[row["resolved_endpoint_class"]] += 1
    classes = list(class_counts)
    counts = [class_counts[item] for item in classes]
    axes[2].bar(
        [item.replace("near_fixed_", "").replace("_endpoint", "").replace("_", "\n") for item in classes],
        counts,
        color=[COLORS["green"] if "physiological" in item else COLORS["red"] for item in classes],
    )
    axes[2].set_ylabel("Qualified endpoints")
    axes[2].set_title("c  Endpoint classes", loc="left", fontweight="bold")
    return _save(fig, "audited_sfigure_s3_phase_robustness")


def _plot_ews_locked_test() -> dict:
    qc = _read_json(INPUTS["R021_qc"])
    locked = _read_json(INPUTS["R023_locked_test"])
    negative = _read_json(INPUTS["R023_negative_controls"])

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.25), constrained_layout=True)

    class_counts = qc["endpoint_class_counts"]
    classes = sorted(
        class_counts,
        key=lambda item: 0 if "physiological" in item else 1,
    )
    axes[0].bar(
        [c.replace("near_fixed_", "").replace("_endpoint", "").replace("_", "\n") for c in classes],
        [class_counts[c] for c in classes],
        color=[COLORS["red"] if "depolarized" in c else COLORS["green"] for c in classes],
    )
    axes[0].set_ylabel("Trajectory groups")
    axes[0].set_title("a  R021 cohort balance", loc="left", fontweight="bold")

    models = [item["model"] for item in locked]
    aurocs = [item["auroc"] for item in locked]
    lows = [item["bootstrap"]["auroc_ci_low"] for item in locked]
    highs = [item["bootstrap"]["auroc_ci_high"] for item in locked]
    x = np.arange(len(models))
    axes[1].bar(x, aurocs, color=[COLORS["green"], COLORS["orange"], COLORS["blue"], COLORS["gray"]])
    axes[1].errorbar(
        x,
        aurocs,
        yerr=[np.asarray(aurocs) - np.asarray(lows), np.asarray(highs) - np.asarray(aurocs)],
        fmt="none",
        ecolor="black",
        capsize=3,
        lw=1,
    )
    axes[1].set_xticks(x, [m.replace("best_", "").replace("locked_", "locked\n") for m in models])
    axes[1].set_ylim(0.75, 1.02)
    axes[1].set_ylabel("AUROC")
    axes[1].set_title("b  Locked test metrics", loc="left", fontweight="bold")

    neg_labels = ["label\npermutation", "time\nshuffle", "future-window\ncheck"]
    neg_values = [
        negative["group_label_permutation"]["auroc_median"],
        negative["within_trajectory_time_shuffle"]["auroc"],
        negative["future_window_removal"]["future_window_max_abs_feature_difference"],
    ]
    axes[2].bar(neg_labels, neg_values, color=[COLORS["purple"], COLORS["orange"], COLORS["gray"]])
    axes[2].axhline(0.5, color="black", ls=":", lw=1)
    axes[2].set_ylabel("Diagnostic value")
    axes[2].set_title("c  Leakage and chance controls", loc="left", fontweight="bold")
    axes[2].text(
        0.98,
        0.92,
        "No independent\nEWS-gain claim",
        transform=axes[2].transAxes,
        ha="right",
        va="top",
        fontsize=7,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": COLORS["light"], "edgecolor": COLORS["gray"]},
    )
    return _save(fig, "audited_sfigure_s4_ews_locked_test")


def build_manifest(outputs: dict) -> dict:
    return {
        "run_id": "R052",
        "status": "complete_audited_supplementary_rebuild",
        "input_artifacts": {
            name: {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(path),
            }
            for name, path in INPUTS.items()
        },
        "active_supplementary_figures": outputs,
        "inactive_legacy_supplementary_pattern": "figures/sfigure_s*_publication.(png|pdf)",
        "claim_gate": {
            "wet_lab_or_experimental_validation_claim": False,
            "mcmc_or_bayesian_posterior_claim": False,
            "spatial_external_validation_claim": False,
            "disease_treatment_or_clinical_claim": False,
            "independent_ews_gain_claim": False,
            "absolute_ocr_calibration_claim": False,
        },
        "blocked_legacy_groups_remain_inactive": [
            "S2 experimental-validation label",
            "S5/S16 Bayesian or posterior diagnostics",
            "S9 spatial validation",
            "S10-S15 disease quantification or treatment/progression",
            "S18 unsupported anomaly ROC/AUC",
        ],
        "manuscript_modified": False,
    }


def generate() -> dict:
    outputs = {
        "S1": _plot_source_contract(),
        "S2": _plot_hybrid_benchmark(),
        "S3": _plot_phase_robustness(),
        "S4": _plot_ews_locked_test(),
    }
    manifest = build_manifest(outputs)
    R052_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main():
    payload = generate()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

