"""Figure 2 built only from the R025 controlled misspecification benchmark."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
R025 = ROOT / "refine-logs" / "runs" / "R025"
OUT = ROOT / "figures" / "figure2_hybrid_ml.png"
PDF = ROOT / "figures" / "figure2_hybrid_ml.pdf"

COLORS = {
    "ode": "#7F7F7F",
    "neural": "#D55E00",
    "hybrid": "#0072B2",
    "target": "#222222",
    "green": "#009E73",
    "light": "#F2F2F2",
}


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _panel_label(ax, label):
    ax.text(-0.08, 1.06, label, transform=ax.transAxes, fontsize=12,
            fontweight="bold", va="bottom")


def _clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _architecture(ax, metadata):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    boxes = [
        (0.06, 0.52, 0.22, 0.20, "Observed\nstate"),
        (0.39, 0.70, 0.22, 0.16, "Nominal ODE\nbackbone"),
        (0.39, 0.34, 0.22, 0.16, "Learned residual"),
        (0.72, 0.52, 0.22, 0.20, "Hybrid\nrollout"),
    ]
    for x, y, w, h, text in boxes:
        color = COLORS["hybrid"] if "Hybrid" in text else COLORS["light"]
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02",
            facecolor="#EAF2F8" if "Hybrid" in text else color,
            edgecolor=COLORS["hybrid"] if "Hybrid" in text else "#777777",
            lw=1.0,
        ))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=8.2, fontweight="bold" if "Hybrid" in text else None)
    for source, target in [
        ((0.28, 0.62), (0.39, 0.78)),
        ((0.28, 0.62), (0.39, 0.42)),
        ((0.61, 0.78), (0.72, 0.62)),
        ((0.61, 0.42), (0.72, 0.62)),
    ]:
        ax.add_patch(FancyArrowPatch(source, target, arrowstyle="->",
                                     mutation_scale=10, lw=1,
                                     color="#666666"))
    train = metadata["train_hidden_gain"]
    test = metadata["test_hidden_gain"]
    ax.text(
        0.5, 0.10,
        f"Train hidden gain: {train[0]:.2f}–{train[1]:.2f}   |   "
        f"Held-out gain: {test[0]:.2f}–{test[1]:.2f}",
        ha="center", fontsize=7.8, color="#555555",
    )
    ax.axis("off")


def _trajectory(ax, predictions):
    rows = [
        row for row in predictions
        if int(row["seed"]) == 0 and int(row["case_index"]) == 0
    ]
    target = sorted(
        [row for row in rows if row["model"] == "hybrid"],
        key=lambda row: float(row["time_s"]),
    )
    neural = sorted(
        [row for row in rows if row["model"] == "neural"],
        key=lambda row: float(row["time_s"]),
    )
    hybrid = sorted(
        [row for row in rows if row["model"] == "hybrid"],
        key=lambda row: float(row["time_s"]),
    )
    t = np.asarray([float(row["time_s"]) for row in target])
    ax.plot(t, [float(row["target_x1"]) for row in target], color=COLORS["target"],
            lw=1.7, label="Reference")
    ax.plot(t, [float(row["pred_x1"]) for row in neural], color=COLORS["neural"],
            lw=1.2, ls="--", label="Neural")
    ax.plot(t, [float(row["pred_x1"]) for row in hybrid], color=COLORS["hybrid"],
            lw=1.5, label="Hybrid")
    ax.set(xlabel="Time (benchmark units)", ylabel="$x_1$",
           title="Representative held-out rollout")
    ax.legend(frameon=False, fontsize=7)
    _clean(ax)


def _summary_maps(summary):
    return {row["model"]: row for row in summary}


def _trajectory_rmse(ax, summary):
    values = _summary_maps(summary)
    models = ["ode", "neural", "hybrid"]
    means = [float(values[model]["trajectory_rmse_mean"]) for model in models]
    sds = [float(values[model]["trajectory_rmse_sd"]) for model in models]
    ax.bar(range(3), means, yerr=sds,
           color=[COLORS[model] for model in models], capsize=3)
    ax.set_xticks(range(3), ["Nominal\nODE", "Neural", "Hybrid"])
    ax.set(ylabel="Trajectory RMSE", title="Held-out trajectory error")
    _clean(ax)


def _endpoint_rmse(ax, summary):
    values = _summary_maps(summary)
    models = ["ode", "neural", "hybrid"]
    means = [float(values[model]["endpoint_rmse_mean"]) for model in models]
    ax.bar(range(3), means, color=[COLORS[model] for model in models])
    ax.set_xticks(range(3), ["Nominal\nODE", "Neural", "Hybrid"])
    ax.set(ylabel="Endpoint RMSE", title="Held-out endpoint error")
    _clean(ax)


def _seedwise(ax, metrics):
    models = ["ode", "neural", "hybrid"]
    offsets = [-0.16, 0.0, 0.16]
    for offset, model in zip(offsets, models):
        rows = sorted(
            [row for row in metrics if row["model"] == model],
            key=lambda row: int(row["seed"]),
        )
        seeds = np.asarray([int(row["seed"]) for row in rows])
        values = np.asarray([float(row["trajectory_rmse"]) for row in rows])
        ax.plot(seeds + offset, values, marker="o", lw=1.2,
                color=COLORS[model], label=model.title())
    ax.set_xticks([0, 1, 2], ["Seed 0", "Seed 1", "Seed 2"])
    ax.set(ylabel="Trajectory RMSE", title="Seed-wise held-out error")
    ax.legend(frameon=False, fontsize=7)
    _clean(ax)


def _boundary(ax, metadata):
    ax.axis("off")
    ax.text(0.02, 0.94, "Claim boundary", fontsize=10, fontweight="bold",
            va="top")
    ax.add_patch(FancyBboxPatch(
        (0.04, 0.54), 0.90, 0.27, boxstyle="round,pad=0.03",
        facecolor="#E8F5EE", edgecolor=COLORS["green"], lw=1,
    ))
    ax.text(0.10, 0.72, "Supported", color=COLORS["green"],
            fontweight="bold", fontsize=8.5)
    ax.text(0.10, 0.61,
            "Controlled recovery under a specified\n"
            "hidden nonlinear residual.", fontsize=8.3, va="center")
    ax.add_patch(FancyBboxPatch(
        (0.04, 0.14), 0.90, 0.26, boxstyle="round,pad=0.03",
        facecolor="#FFF3D6", edgecolor="#E69F00", lw=1,
    ))
    ax.text(0.10, 0.32, "Not supported", color="#C97C00",
            fontweight="bold", fontsize=8.5)
    ax.text(0.10, 0.22,
            "Biological generalization, clinical prediction,\n"
            "or NeurMito endpoint-cohort improvement.", fontsize=8.3,
            va="center")


def generate():
    summary = _rows(R025 / "summary.csv")
    metrics = _rows(R025 / "metrics.csv")
    predictions = _rows(R025 / "predictions.csv")
    metadata = json.loads((R025 / "metadata.json").read_text(encoding="utf-8"))

    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.6), constrained_layout=True)
    _architecture(axes[0, 0], metadata)
    _trajectory(axes[0, 1], predictions)
    _trajectory_rmse(axes[0, 2], summary)
    _endpoint_rmse(axes[1, 0], summary)
    _seedwise(axes[1, 1], metrics)
    _boundary(axes[1, 2], metadata)
    for label, ax in zip(("a", "b", "c", "d", "e", "f"), axes.flat):
        _panel_label(ax, label)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=600, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)
    return OUT, PDF


if __name__ == "__main__":
    print(generate())
