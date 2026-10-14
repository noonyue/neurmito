# -*- coding: utf-8 -*-
"""
Publication Supplementary Figure S4
Cross-validation, model comparison, and robustness diagnostics.

Data policy:
- Uses only validated project CSV tables under csv/
- Replaces synthetic MCMC-style placeholders with direct evaluation diagnostics from the available result tables

Outputs:
- figures/sfigure_s4_publication.png
- figures/sfigure_s4_publication.pdf
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CSV_DIR = PROJECT_ROOT / "csv"
FIGURES_DIR = PROJECT_ROOT / "figures"


plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 7,
        "axes.titlesize": 8,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.linewidth": 0.75,
        "xtick.major.width": 0.65,
        "ytick.major.width": 0.65,
        "xtick.major.size": 2.6,
        "ytick.major.size": 2.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


COLORS = {
    "hybrid": "#1f77b4",
    "ode": "#d62728",
    "ml": "#2ca02c",
    "baseline": "#7f7f7f",
    "accent": "#9467bd",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="top",
    )


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_a_cv(ax: plt.Axes, cv_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    long_df = cv_df.melt(id_vars="neuron_type", var_name="cell_class", value_name="cv_score")
    long_df["method"] = long_df["neuron_type"].str.replace("_cv", "", regex=False)
    order = ["Hybrid", "ODE", "ML"]
    class_order = ["Dopaminergic", "Glutamatergic", "GABAergic", "Cholinergic", "Serotonergic", "Motor"]
    pivot = long_df.pivot(index="cell_class", columns="method", values="cv_score").reindex(class_order)
    x = np.arange(len(class_order))
    width = 0.24
    ax.bar(x - width, pivot["Hybrid"], width=width, color=COLORS["hybrid"], alpha=0.82, label="Hybrid")
    ax.bar(x, pivot["ODE"], width=width, color=COLORS["ode"], alpha=0.82, label="ODE")
    ax.bar(x + width, pivot["ML"], width=width, color=COLORS["ml"], alpha=0.82, label="ML")
    ax.set_xticks(x)
    ax.set_xticklabels(class_order, rotation=30, ha="right")
    ax.set_ylim(0.75, 0.95)
    ax.set_ylabel("Cross-validation score")
    ax.set_title("Cross-validation across neuron classes", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="lower right")
    clean_axis(ax)


def panel_b_rmse(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "b")
    x = np.arange(len(mc_df))
    width = 0.22
    ax.bar(x - width, mc_df["OCR_RMSE"], width=width, color=COLORS["hybrid"], alpha=0.75, label="OCR RMSE")
    ax.bar(x, mc_df["ATP_RMSE"], width=width, color=COLORS["accent"], alpha=0.75, label="ATP RMSE")
    ax.bar(x + width, mc_df["ROS_RMSE"], width=width, color=COLORS["ode"], alpha=0.75, label="ROS RMSE")
    ax.set_xticks(x)
    ax.set_xticklabels(mc_df["model"], rotation=25, ha="right")
    ax.set_ylabel("RMSE")
    ax.set_title("Per-output prediction error", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_c_timing(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    x = np.arange(len(mc_df))
    ax.plot(x, mc_df["Fit_time_s"], color=COLORS["ode"], lw=1.6, marker="o", ms=4, label="Fit time (s)")
    ax2 = ax.twinx()
    ax2.plot(x, mc_df["Prediction_time_s"], color=COLORS["hybrid"], lw=1.6, marker="s", ms=4, label="Prediction time (s)")
    ax.set_xticks(x)
    ax.set_xticklabels(mc_df["model"], rotation=25, ha="right")
    ax.set_ylabel("Fit time (s)", color=COLORS["ode"])
    ax2.set_ylabel("Prediction time (s)", color=COLORS["hybrid"])
    ax.tick_params(axis="y", colors=COLORS["ode"])
    ax2.tick_params(axis="y", colors=COLORS["hybrid"])
    ax.set_title("Training vs inference cost", fontweight="bold", pad=7)
    ax2.spines["top"].set_visible(False)
    clean_axis(ax)


def panel_d_noise(ax: plt.Axes, rb_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    x = rb_df["noise_level"].to_numpy(dtype=float)
    ax.plot(x, rb_df["Hybrid_R2"], color=COLORS["hybrid"], lw=1.6, marker="o", ms=4, label="Hybrid")
    ax.plot(x, rb_df["ODE_R2"], color=COLORS["ode"], lw=1.6, marker="s", ms=4, label="ODE")
    ax.plot(x, rb_df["ML_R2"], color=COLORS["ml"], lw=1.6, marker="^", ms=4, label="ML")
    ax.set_xlabel("Noise level")
    ax.set_ylabel(r"$R^2$")
    ax.set_title("Noise robustness", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="lower left")
    clean_axis(ax)


def panel_e_memory(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "e")
    ax.barh(mc_df["model"], mc_df["Memory_GB"], color=[COLORS["hybrid"], COLORS["ode"], COLORS["ml"], COLORS["baseline"]], alpha=0.80)
    for i, value in enumerate(mc_df["Memory_GB"]):
        ax.text(value + 0.05, i, f"{value:.1f} GB", va="center", fontsize=6.2)
    ax.set_xlabel("Memory footprint (GB)")
    ax.set_title("Memory requirement by model", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_f_robustness(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "f")
    order = mc_df.sort_values("Robustness_R2", ascending=True)
    ax.barh(order["model"], order["Robustness_R2"], color=[COLORS["baseline"], COLORS["ode"], COLORS["ml"], COLORS["hybrid"]], alpha=0.82)
    for i, value in enumerate(order["Robustness_R2"]):
        ax.text(value + 0.01, i, f"{value:.2f}", va="center", fontsize=6.2)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Robustness R2")
    ax.set_title("Global robustness ranking", fontweight="bold", pad=7)
    clean_axis(ax)


def make_s4() -> tuple[Path, Path]:
    cv_df = load_csv("sfigure_s4_cross_validation.csv")
    mc_df = load_csv("sfigure_s4_model_comparison.csv")
    rb_df = load_csv("sfigure_s4_robustness.csv")

    fig = plt.figure(figsize=(13.5, 9.0), dpi=300)
    ax_a = fig.add_axes([0.060, 0.610, 0.430, 0.270])
    ax_b = fig.add_axes([0.545, 0.610, 0.400, 0.270])
    ax_c = fig.add_axes([0.060, 0.315, 0.280, 0.220])
    ax_d = fig.add_axes([0.390, 0.315, 0.280, 0.220])
    ax_e = fig.add_axes([0.720, 0.315, 0.225, 0.220])
    ax_f = fig.add_axes([0.175, 0.090, 0.650, 0.150])
    ax_cap = fig.add_axes([0.035, 0.020, 0.930, 0.055])

    panel_a_cv(ax_a, cv_df)
    panel_b_rmse(ax_b, mc_df)
    panel_c_timing(ax_c, mc_df)
    panel_d_noise(ax_d, rb_df)
    panel_e_memory(ax_e, mc_df)
    panel_f_robustness(ax_f, mc_df)

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S4\ |}$ Cross-validation, model comparison, and robustness diagnostics. "
        "a, Cross-validation performance across six neuron classes from sfigure_s4_cross_validation.csv. "
        "b, Model-comparison RMSE values for OCR, ATP, and ROS predictions from sfigure_s4_model_comparison.csv. "
        "c, Training and inference cost comparison using fit time and prediction time. "
        "d, Noise robustness trends from sfigure_s4_robustness.csv. "
        "e, Memory requirement across model classes. "
        "f, Summary robustness ranking from the global Robustness R2 metric."
    )
    ax_cap.text(
        0.015,
        0.96,
        textwrap.fill(caption, width=188),
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.38", fc="white", ec="0.55", lw=0.8),
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "sfigure_s4_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s4_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s4()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
