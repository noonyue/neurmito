# -*- coding: utf-8 -*-
"""
Publication Supplementary Figure S3
Global sensitivity analysis and multi-output parameter importance.

Data policy:
- Uses only validated project CSV tables under csv/
- Keeps the publication-oriented multi-panel composition
- Replaces synthetic neuron-level perturbation maps with direct parameter/output summaries

Outputs:
- figures/sfigure_s3_publication.png
- figures/sfigure_s3_publication.pdf
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
    "blue": "#2f5aa8",
    "red": "#c51f2f",
    "green": "#3c8c3c",
    "orange": "#d95f02",
    "purple": "#6a3d9a",
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


def panel_a_first_order(ax: plt.Axes, sens_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    plot_df = sens_df.sort_values("Sobol_first_order", ascending=True).copy()
    colors = [COLORS["red"] if p == "Vmax_C1" else COLORS["blue"] if "Vmax" in p else COLORS["green"] if "Km" in p or "Ki" in p else COLORS["purple"] for p in plot_df["parameter"]]
    ax.barh(plot_df["parameter"], plot_df["Sobol_first_order"], color=colors, edgecolor="white", height=0.68)
    ax.set_xlim(0, 0.75)
    ax.set_xlabel("First-order Sobol index")
    ax.set_title("First-order parameter sensitivity", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_b_total_order(ax: plt.Axes, sens_df: pd.DataFrame) -> None:
    panel_label(ax, "b")
    plot_df = sens_df.sort_values("Sobol_total_order", ascending=True).copy()
    y = np.arange(len(plot_df))
    ax.barh(y + 0.16, plot_df["Sobol_first_order"], height=0.30, color=COLORS["blue"], label="First-order")
    ax.barh(y - 0.16, plot_df["Sobol_total_order"], height=0.30, color=COLORS["orange"], label="Total-order")
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["parameter"])
    ax.set_xlim(0, 0.95)
    ax.set_xlabel("Sobol index")
    ax.set_title("First-order vs total-order sensitivity", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="lower right")
    clean_axis(ax)


def panel_c_heatmap(ax: plt.Axes, multi_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    value_cols = [c for c in multi_df.columns if c != "output"]
    mat = multi_df[value_cols].to_numpy(dtype=float)
    im = ax.imshow(mat, cmap="YlOrRd", aspect="auto", vmin=0, vmax=max(0.9, mat.max()))
    ax.set_yticks(np.arange(len(multi_df)))
    ax.set_yticklabels(multi_df["output"])
    ax.set_xticks(np.arange(len(value_cols)))
    ax.set_xticklabels(value_cols, rotation=35, ha="right")
    ax.set_title("Multi-output sensitivity matrix", fontweight="bold", pad=7)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=5.6, color="black")
    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Sensitivity")


def panel_d_interactions(ax: plt.Axes, sens_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    plot_df = sens_df.sort_values("interaction_effect", ascending=False).copy()
    colors = [COLORS["orange"] if v >= 0.15 else COLORS["purple"] for v in plot_df["interaction_effect"]]
    x = np.arange(len(plot_df))
    ax.bar(x, plot_df["interaction_effect"], color=colors, edgecolor="0.3", linewidth=0.6, alpha=0.82)
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["parameter"], rotation=35, ha="right")
    ax.set_ylabel("Interaction effect")
    ax.set_title("Higher-order interaction contribution", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_e_top(ax_axes: list[plt.Axes], sens_df: pd.DataFrame) -> None:
    top = sens_df.sort_values("ranking").head(5).copy()
    titles = ["Local", "S1", "ST", "Interaction", "Rank"]
    columns = ["local_sensitivity", "Sobol_first_order", "Sobol_total_order", "interaction_effect", "ranking"]
    for ax, title, column in zip(ax_axes, titles, columns):
        vals = top[column].to_numpy(dtype=float)
        if column == "ranking":
            vals = vals[::-1]
            labels = top["parameter"].iloc[::-1]
        else:
            labels = top["parameter"]
        ax.barh(labels, vals, color=COLORS["purple"], alpha=0.78)
        ax.set_title(title, fontsize=7, pad=4)
        ax.tick_params(axis="y", labelsize=5.8)
        clean_axis(ax)


def make_s3() -> tuple[Path, Path]:
    sens_df = load_csv("sfigure_s3_sensitivity_parameters.csv")
    multi_df = load_csv("sfigure_s3_multioutput_sensitivity.csv")

    fig = plt.figure(figsize=(13.5, 9.0), dpi=300)
    ax_a = fig.add_axes([0.070, 0.610, 0.395, 0.320])
    ax_b = fig.add_axes([0.585, 0.610, 0.365, 0.320])
    ax_c = fig.add_axes([0.070, 0.305, 0.410, 0.235])
    ax_d = fig.add_axes([0.580, 0.305, 0.370, 0.235])
    e_axes = [fig.add_axes([0.165 + i * 0.155, 0.145, 0.115, 0.105]) for i in range(5)]
    ax_cap = fig.add_axes([0.035, 0.035, 0.930, 0.080])

    panel_a_first_order(ax_a, sens_df)
    panel_b_total_order(ax_b, sens_df)
    panel_c_heatmap(ax_c, multi_df)
    panel_d_interactions(ax_d, sens_df)
    panel_e_top(e_axes, sens_df)

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S3\ |}$ Global sensitivity analysis and multi-output parameter importance. "
        "a, First-order Sobol indices from sfigure_s3_sensitivity_parameters.csv. "
        "b, Comparison of first-order and total-order sensitivity for the same ranked parameter set. "
        "c, Output-specific sensitivity matrix from sfigure_s3_multioutput_sensitivity.csv across OCR, ATP production, and ROS levels. "
        "d, Higher-order interaction effects computed as total-order minus first-order contribution. "
        "e, Compact view of the top-ranked parameters across local sensitivity, Sobol indices, interaction effect, and global ranking."
    )
    ax_cap.text(
        0.015,
        0.96,
        textwrap.fill(caption, width=188),
        ha="left",
        va="top",
        fontsize=6.9,
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="0.55", lw=0.8),
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "sfigure_s3_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s3_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s3()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
