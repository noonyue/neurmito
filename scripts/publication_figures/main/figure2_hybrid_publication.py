# -*- coding: utf-8 -*-
"""
Legacy exploratory Figure 2 renderer.

The CSV inputs here are not the R025 controlled benchmark and must not be used
to claim biological predictive improvement. Use
``figure2_hybrid_verified.py`` via ``module2.figure2_hybrid_ml`` instead.

Data policy:
- Uses legacy project tables under csv/
- Does not establish biological predictive accuracy or external validation

Outputs:
- figures/figure2_hybrid_publication.png
- figures/figure2_hybrid_publication.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CSV_DIR = PROJECT_ROOT / "csv"
FIGURES_DIR = PROJECT_ROOT / "figures"


plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 7.4,
        "axes.titlesize": 8.4,
        "axes.labelsize": 7.2,
        "xtick.labelsize": 6.3,
        "ytick.labelsize": 6.3,
        "legend.fontsize": 6.2,
        "axes.linewidth": 0.78,
        "xtick.major.width": 0.68,
        "ytick.major.width": 0.68,
        "xtick.major.size": 2.8,
        "ytick.major.size": 2.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


COLORS = {
    "hybrid": "#2ca02c",
    "mechanistic": "#d94b4b",
    "ablation": "#f0a040",
    "priors": "#cc79a7",
    "random": "#9a9a9a",
    "architecture": "#8f6ab8",
    "training": "#1f6fbf",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.07) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=12.5,
        fontweight="bold",
        ha="left",
        va="top",
    )


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def arrow(
    ax: plt.Axes,
    xy1: tuple[float, float],
    xy2: tuple[float, float],
    lw: float = 0.9,
    ms: int = 9,
    color: str = "0.20",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            xy1,
            xy2,
            arrowstyle="-|>",
            mutation_scale=ms,
            lw=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
        )
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    fc: str,
    ec: str,
    text: str | None = None,
    fontsize: float = 6.5,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.016,rounding_size=0.025",
        fc=fc,
        ec=ec,
        lw=0.9,
    )
    ax.add_patch(patch)
    if text is not None:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    neural = load_csv("figure2_neural_corrections.csv")
    training = load_csv("figure2_training_convergence.csv")
    compare = load_csv("figure2_model_comparison.csv")
    return neural, training, compare


def state_label(raw: str) -> str:
    text = str(raw)
    lower = text.lower()
    if "ros" in lower:
        return "ROS"
    if "atp" in lower:
        return "ATP"
    if "nadh" in lower:
        return "NADH"
    if "gsh" in lower:
        return "GSH"
    if "cyt" in lower:
        return "Cyt c"
    if "qh" in lower or "鈧" in text:
        return "QH2"
    if "ca" in lower or "虏" in text:
        return "Ca"
    return "DPsi"


def panel_a_architecture(ax: plt.Axes) -> None:
    panel_label(ax, "a")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.50, 0.95, "Hybrid model support", ha="center", va="top", fontsize=8.2, fontweight="bold")
    rounded_box(ax, 0.05, 0.55, 0.23, 0.18, "#edf5fb", "#7f8c8d", "Stress inputs\nand initial state", fontsize=6.8)
    rounded_box(ax, 0.36, 0.55, 0.20, 0.18, "#fff4df", "#7f8c8d", "Mechanistic ODE\nsolver", fontsize=6.8)
    rounded_box(ax, 0.64, 0.55, 0.20, 0.18, "#f4ecfa", COLORS["architecture"], "Neural\ncorrection", fontsize=6.8)
    rounded_box(ax, 0.86, 0.55, 0.10, 0.18, "#eef7ec", "#7f8c8d", "Output", fontsize=6.8)

    arrow(ax, (0.28, 0.64), (0.36, 0.64))
    arrow(ax, (0.56, 0.64), (0.64, 0.64))
    arrow(ax, (0.84, 0.64), (0.86, 0.64))

    ax.text(0.46, 0.34, r"$\frac{dy}{dt}=f_{mech}(y,\theta)+f_{neural}(y,t)$", ha="center", fontsize=7.0)
    ax.text(0.46, 0.22, "Backpropagation through the ODE solver", ha="center", fontsize=6.2, color="0.35")


def panel_b_model_gain(ax: plt.Axes, compare_df: pd.DataFrame) -> None:
    panel_label(ax, "b")

    order = [
        "Hybrid (full)",
        "No neural component",
        "Pure Mechanistic",
        "No mech priors",
        "Random weights",
    ]
    color_map = {
        "Hybrid (full)": COLORS["hybrid"],
        "Pure Mechanistic": COLORS["mechanistic"],
        "No neural component": COLORS["ablation"],
        "No mech priors": COLORS["priors"],
        "Random weights": COLORS["random"],
    }
    plot_df = compare_df.set_index("model").loc[order].reset_index()
    y = np.arange(len(plot_df))[::-1]
    means = plot_df["prediction_error_mean"].to_numpy(dtype=float)
    stds = plot_df["prediction_error_std"].to_numpy(dtype=float)
    colors = [color_map[name] for name in plot_df["model"]]

    ax.barh(y, means, color=colors, alpha=0.84, edgecolor="0.25", height=0.62)
    ax.errorbar(means, y, xerr=stds, fmt="none", ecolor="0.20", elinewidth=1.2, capsize=3)

    full = float(plot_df.loc[plot_df["model"].eq("Hybrid (full)"), "prediction_error_mean"].iloc[0])
    mech = float(plot_df.loc[plot_df["model"].eq("Pure Mechanistic"), "prediction_error_mean"].iloc[0])
    reduction = (1.0 - full / mech) * 100.0

    for yi, mean, std in zip(y, means, stds):
        ax.text(mean + std + 1.4, yi, f"{mean:.0f} ± {std:.0f}%", va="center", fontsize=6.8)

    hybrid_y = float(y[order.index("Hybrid (full)")])
    mech_y = float(y[order.index("Pure Mechanistic")])
    ax.annotate(
        "",
        xy=(full, hybrid_y + 0.18),
        xytext=(mech, mech_y - 0.18),
        arrowprops=dict(arrowstyle="<->", color="0.25", lw=1.0),
    )
    ax.text(
        (full + mech) / 2,
        (hybrid_y + mech_y) / 2 + 0.22,
        f"{reduction:.0f}% lower error\nthan the mechanistic baseline",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color=COLORS["hybrid"],
        fontweight="bold",
    )
    ax.text(
        0.03,
        0.96,
        "Ablations quickly erase the hybrid gain.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["model"])
    ax.set_xlim(0, 62)
    ax.set_xlabel("Prediction error (%)")
    ax.set_title("Hybrid coupling sharply reduces prediction error", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_c_training(ax: plt.Axes, training_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    x = training_df["epoch"].to_numpy(dtype=float)
    train = training_df["train_loss"].to_numpy(dtype=float)
    val = training_df["val_loss"].to_numpy(dtype=float)
    conv_epoch = int(training_df.loc[training_df["convergence_phase"].eq("converged"), "epoch"].iloc[0])

    ax.plot(x, train, color=COLORS["hybrid"], lw=1.8, label="Train loss")
    ax.plot(x, val, color=COLORS["training"], lw=1.8, ls="--", label="Validation loss")
    ax.axvline(conv_epoch, color="0.55", lw=0.9, ls=":")
    ax.fill_between(x, train, val, color=COLORS["training"], alpha=0.07)
    ax.text(0.04, 0.92, f"Converged by epoch {conv_epoch}", transform=ax.transAxes, fontsize=6.9, ha="left", va="top")

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Training remains stable through convergence", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_d_corrections(ax: plt.Axes, neural_df: pd.DataFrame) -> None:
    panel_label(ax, "d")

    plot_df = neural_df.copy()
    plot_df["display_state"] = plot_df["state_variable"].astype(str).map(state_label)
    plot_df = plot_df.sort_values("neural_correction_pct", ascending=True)

    vals = plot_df["neural_correction_pct"].to_numpy(dtype=float)
    errs = plot_df["error_pct"].to_numpy(dtype=float)
    colors = [COLORS["ablation"] if value >= 5.0 else "#7eb6d8" for value in vals]

    ax.barh(
        plot_df["display_state"],
        vals,
        xerr=errs,
        capsize=2.5,
        color=colors,
        edgecolor="0.25",
        linewidth=0.7,
        alpha=0.84,
    )
    ax.axvline(5.0, color="0.60", lw=0.9, ls="--")
    ax.text(5.1, len(plot_df) - 0.4, "5% threshold", fontsize=6.5, color="0.40")
    ax.text(
        0.98,
        0.95,
        "Only ROS exceeds 5%; most\nstate corrections stay small.",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, 10)
    ax.set_xlabel("Neural correction magnitude (%)")
    ax.set_title("Neural updates stay targeted rather than overwhelming the mechanistic core", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_e_penalties(ax: plt.Axes, compare_df: pd.DataFrame) -> None:
    panel_label(ax, "e")

    plot_df = compare_df.copy()
    best_error = float(plot_df["prediction_error_mean"].min())
    plot_df["relative_multiplier"] = plot_df["prediction_error_mean"] / best_error
    order = ["Hybrid (full)", "No neural component", "Pure Mechanistic", "No mech priors", "Random weights"]
    plot_df = plot_df.set_index("model").loc[order].reset_index()

    x = np.arange(len(plot_df))
    colors = [COLORS["hybrid"], COLORS["ablation"], COLORS["mechanistic"], COLORS["priors"], COLORS["random"]]
    ax.bar(x, plot_df["relative_multiplier"].to_numpy(dtype=float), color=colors, edgecolor="0.25", linewidth=0.7, alpha=0.84)
    for idx, row in plot_df.iterrows():
        ax.text(idx, float(row["relative_multiplier"]) + 0.10, f"{row['relative_multiplier']:.1f}x", ha="center", fontsize=6.7)

    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Hybrid", "No neural", "Mechanistic", "No priors", "Random"],
        rotation=25,
        ha="right",
    )
    ax.set_ylim(0, 6.8)
    ax.set_ylabel("Error relative to the best model")
    ax.set_title("Removing learned or mechanistic structure rapidly inflates error", fontweight="bold", pad=7)
    clean_axis(ax)


def make_figure2() -> tuple[Path, Path]:
    neural_df, training_df, compare_df = prepare_data()

    fig = plt.figure(figsize=(12.8, 7.5), dpi=300)
    gs = fig.add_gridspec(
        2,
        6,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.10,
        wspace=0.88,
        hspace=0.52,
        height_ratios=[1.02, 0.95],
    )

    ax_a = fig.add_subplot(gs[0, 0:2])
    ax_b = fig.add_subplot(gs[0, 2:6])
    ax_c = fig.add_subplot(gs[1, 0:2])
    ax_d = fig.add_subplot(gs[1, 2:4])
    ax_e = fig.add_subplot(gs[1, 4:6])

    panel_a_architecture(ax_a)
    panel_b_model_gain(ax_b, compare_df)
    panel_c_training(ax_c, training_df)
    panel_d_corrections(ax_d, neural_df)
    panel_e_penalties(ax_e, compare_df)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure2_hybrid_publication.png"
    out_pdf = FIGURES_DIR / "figure2_hybrid_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure2()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
