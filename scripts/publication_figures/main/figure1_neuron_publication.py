# -*- coding: utf-8 -*-
"""
Publication Figure 1
Neuron-type bioenergetic profiling reveals a constrained dopaminergic operating state.

Data policy:
- Uses only validated project CSV tables under csv/
- Reframed around the main quantitative result rather than a broad methods layout
- Keeps only data-anchored summaries of neuron-type metabolic differences

Outputs:
- figures/figure1_neuron_publication.png
- figures/figure1_neuron_publication.pdf
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


COLOR_MAP = {
    "cortical": "#2f80b7",
    "hippocampal": "#5aa6c8",
    "gabaergic": "#7c60a7",
    "motor": "#d1a235",
    "sensory": "#6f9e45",
    "cerebellar": "#b99579",
    "cholinergic": "#df8f9f",
    "dopaminergic": "#d62f2f",
    "sh-sy5y": "#f08a3e",
}


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
    color: str = "0.20",
    lw: float = 0.9,
    ms: int = 9,
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
    ec: str = "0.55",
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


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    seahorse_df = pd.read_csv(CSV_DIR / "figure1_seahorse_neuron_data.csv")
    params_df = pd.read_csv(CSV_DIR / "figure1_calibrated_params.csv")
    return seahorse_df, params_df


def display_label(raw: str) -> str:
    mapping = {
        "cortical": "Cortical",
        "hippocampal": "Hippocampal",
        "dopaminergic": "Dopaminergic",
        "motor": "Motor",
        "gabaergic": "GABAergic",
        "cholinergic": "Cholinergic",
        "cerebellar": "Cerebellar",
        "sensory": "Sensory",
        "sh-sy5y": "SH-SY5Y",
    }
    return mapping.get(raw.lower(), raw)


def prepare_merged() -> pd.DataFrame:
    seahorse_df, params_df = load_data()
    seahorse_df = seahorse_df.copy()
    params_df = params_df.copy()
    seahorse_df["neuron_key"] = seahorse_df["neuron_type"].astype(str).str.lower()
    params_df["neuron_key"] = params_df["neuron_type"].astype(str).str.lower()
    merged = pd.merge(seahorse_df, params_df, on="neuron_key", suffixes=("_ocr", "_param"))
    merged["label"] = merged["neuron_key"].map(display_label)
    merged["color"] = merged["neuron_key"].map(COLOR_MAP)
    merged["reserve_pct"] = merged["spare_capacity"] / merged["maximal_ocr"] * 100.0
    merged["basal_fraction_pct"] = merged["basal_ocr"] / merged["maximal_ocr"] * 100.0
    merged["vulnerability_score"] = (
        0.58 * (merged["capacity_used"] - merged["capacity_used"].min())
        / (merged["capacity_used"].max() - merged["capacity_used"].min())
        + 0.42
        * (merged["Vmax_C1"].max() - merged["Vmax_C1"])
        / (merged["Vmax_C1"].max() - merged["Vmax_C1"].min())
    )
    return merged


def panel_a_operating_state(ax: plt.Axes, merged: pd.DataFrame) -> None:
    panel_label(ax, "a")

    x = merged["capacity_used"].to_numpy(dtype=float)
    y = merged["Vmax_C1"].to_numpy(dtype=float)
    size = 36 + merged["maximal_ocr"].to_numpy(dtype=float) * 0.45

    x_grid = np.linspace(58, 80, 220)
    y_grid = np.linspace(0.068, 0.094, 220)
    xx, yy = np.meshgrid(x_grid, y_grid)
    x_norm = (xx - x_grid.min()) / (x_grid.max() - x_grid.min())
    y_norm = (yy - y_grid.min()) / (y_grid.max() - y_grid.min())
    risk = 0.58 * x_norm + 0.42 * (1.0 - y_norm) + 0.35 * x_norm * (1.0 - y_norm)
    risk = (risk - risk.min()) / (risk.max() - risk.min())

    ax.contourf(
        xx,
        yy,
        risk,
        levels=[0.0, 0.33, 0.66, 1.0],
        colors=["#dcecff", "#fff2c2", "#f4b5b5"],
        alpha=0.93,
    )
    ax.contour(
        xx,
        yy,
        risk,
        levels=np.linspace(0.20, 0.86, 7),
        colors="0.50",
        linewidths=0.42,
        alpha=0.24,
    )

    ax.scatter(
        x,
        y,
        s=size,
        c=merged["color"].tolist(),
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )

    offset_map = {
        "Cerebellar": (0.6, 0.0012),
        "Cortical": (0.6, 0.0010),
        "Motor": (0.6, -0.0011),
        "Sensory": (0.6, 0.0007),
        "Hippocampal": (0.6, -0.0010),
        "GABAergic": (0.6, 0.0004),
        "Cholinergic": (0.6, -0.0010),
        "SH-SY5Y": (0.6, 0.0009),
        "Dopaminergic": (0.8, -0.0014),
    }
    for row in merged.itertuples(index=False):
        dx, dy = offset_map.get(row.label, (0.4, 0.0004))
        ax.text(
            row.capacity_used + dx,
            row.Vmax_C1 + dy,
            row.label,
            fontsize=6.0,
            color=row.color,
            ha="left",
            va="center",
        )

    da_row = merged.loc[merged["neuron_key"].eq("dopaminergic")].iloc[0]
    ax.annotate(
        (
            "Dopaminergic neurons occupy the\n"
            f"most constrained corner:\nVmax,C1 = {da_row['Vmax_C1']:.3f} mM/s,\n"
            f"capacity used = {da_row['capacity_used']:.0f}%"
        ),
        xy=(float(da_row["capacity_used"]), float(da_row["Vmax_C1"])),
        xytext=(61.4, 0.0895),
        fontsize=7.0,
        color=COLOR_MAP["dopaminergic"],
        ha="left",
        va="top",
        arrowprops=dict(arrowstyle="->", color=COLOR_MAP["dopaminergic"], lw=1.0),
        bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="0.72", lw=0.7),
    )

    ax.text(59.0, 0.0925, "buffered", fontsize=7.0, fontweight="bold", color="#225ea8")
    ax.text(67.0, 0.0810, "strained", fontsize=7.0, fontweight="bold", color="#8b6b00")
    ax.text(74.3, 0.0715, "critical", fontsize=7.0, fontweight="bold", color="#a11d33")
    ax.text(
        0.98,
        0.03,
        "Bubble size = maximal OCR",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.1,
        color="0.35",
    )

    ax.set_xlim(58, 80.5)
    ax.set_ylim(0.068, 0.0945)
    ax.set_xlabel("Capacity used at baseline (%)")
    ax.set_ylabel(r"$V_{max,C1}$ (mM/s)")
    ax.set_title(
        "Neuron types occupy distinct bioenergetic operating states",
        fontweight="bold",
        pad=7,
    )
    clean_axis(ax)


def panel_b_workflow(ax: plt.Axes) -> None:
    panel_label(ax, "b")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.50,
        0.96,
        "Calibration support",
        ha="center",
        va="top",
        fontsize=8.2,
        fontweight="bold",
    )

    rounded_box(ax, 0.07, 0.54, 0.26, 0.18, "#edf5fb", text="Published Seahorse\nOCR constraints", fontsize=6.8)
    rounded_box(ax, 0.39, 0.54, 0.23, 0.18, "#fff4df", text="12-parameter\nBayesian fit", fontsize=6.8)
    rounded_box(ax, 0.68, 0.54, 0.25, 0.18, "#eef7ec", text="Neuron-type\nfingerprint", fontsize=6.8)
    arrow(ax, (0.33, 0.63), (0.39, 0.63))
    arrow(ax, (0.62, 0.63), (0.68, 0.63))

    ax.text(0.20, 0.32, "Basal OCR\nMaximal OCR\nSpare capacity", ha="center", fontsize=6.2)
    ax.text(0.50, 0.32, r"$V_{max,C1}$" "\nproton leak\ncapacity used", ha="center", fontsize=6.2)
    ax.text(0.81, 0.32, "reserve\nconstraint\nvulnerability", ha="center", fontsize=6.2)


def panel_c_respiratory_envelope(ax: plt.Axes, merged: pd.DataFrame) -> None:
    panel_label(ax, "c")

    plot_df = merged.sort_values("maximal_ocr", ascending=False).reset_index(drop=True)
    x = np.arange(len(plot_df))
    basal = plot_df["basal_ocr"].to_numpy(dtype=float)
    maximal = plot_df["maximal_ocr"].to_numpy(dtype=float)

    for idx, row in plot_df.iterrows():
        ax.plot(
            [x[idx], x[idx]],
            [row["basal_ocr"], row["maximal_ocr"]],
            color=row["color"],
            lw=2.0,
            alpha=0.88,
        )
        ax.scatter(x[idx], row["basal_ocr"], s=26, color=row["color"], edgecolor="white", linewidth=0.7, zorder=3)
        ax.scatter(x[idx], row["maximal_ocr"], s=32, color=row["color"], edgecolor="0.2", linewidth=0.5, zorder=3)

    ax.text(
        0.03,
        0.95,
        "Line span = respiratory envelope\nbottom = basal, top = maximal",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["label"], rotation=55, ha="right")
    ax.set_ylabel("OCR (pmol/min/ug)")
    ax.set_title("Respiratory demand and capacity diverge strongly across neuron types", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_d_reserve_usage(ax: plt.Axes, merged: pd.DataFrame) -> None:
    panel_label(ax, "d")

    plot_df = merged.sort_values(["capacity_used", "reserve_pct"], ascending=[False, True]).reset_index(drop=True)
    y = np.arange(len(plot_df))
    reserve = plot_df["reserve_pct"].to_numpy(dtype=float)
    used = plot_df["capacity_used"].to_numpy(dtype=float)

    for idx, row in plot_df.iterrows():
        ax.plot([reserve[idx], used[idx]], [y[idx], y[idx]], color="0.80", lw=1.2, zorder=1)
        ax.scatter(reserve[idx], y[idx], s=38, color="#1f6fbf", edgecolor="white", linewidth=0.7, zorder=3)
        ax.scatter(used[idx], y[idx], s=38, color=row["color"], edgecolor="white", linewidth=0.7, zorder=3)

    da_idx = int(plot_df.index[plot_df["neuron_key"].eq("dopaminergic")][0])
    ax.annotate(
        "smallest reserve,\nhighest use",
        xy=(used[da_idx], y[da_idx]),
        xytext=(71.8, y[da_idx] - 1.2),
        fontsize=6.8,
        color=COLOR_MAP["dopaminergic"],
        arrowprops=dict(arrowstyle="->", color=COLOR_MAP["dopaminergic"], lw=0.9),
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.72", lw=0.7),
    )

    ax.scatter([], [], s=38, color="#1f6fbf", label="Operating reserve")
    ax.scatter([], [], s=38, color="#d62f2f", label="Capacity used")
    ax.legend(frameon=False, loc="lower right")

    ax.set_xlim(50, 80.5)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Percent of maximal capacity (%)")
    ax.set_title("Reserve narrows as vulnerable neuron types run closer to their ceiling", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_e_tradeoff(ax: plt.Axes, merged: pd.DataFrame) -> None:
    panel_label(ax, "e")

    cap = merged["maximal_ocr"].to_numpy(dtype=float)
    leak = merged["proton_leak"].to_numpy(dtype=float)

    for row in merged.itertuples(index=False):
        ax.scatter(row.maximal_ocr, row.proton_leak, s=52, color=row.color, edgecolor="white", linewidth=0.8, zorder=3)

    coef = np.polyfit(cap, leak, 1)
    xx = np.linspace(cap.min() * 0.92, cap.max() * 1.03, 150)
    yy = np.polyval(coef, xx)
    ax.plot(xx, yy, ls="--", color="0.35", lw=1.1)

    r = float(np.corrcoef(cap, leak)[0, 1])
    ax.annotate(
        "SH-SY5Y transformed\nhigh-demand outlier",
        xy=(
            float(merged.loc[merged["neuron_key"].eq("sh-sy5y"), "maximal_ocr"].iloc[0]),
            float(merged.loc[merged["neuron_key"].eq("sh-sy5y"), "proton_leak"].iloc[0]),
        ),
        xytext=(352, 57),
        fontsize=6.8,
        color=COLOR_MAP["sh-sy5y"],
        arrowprops=dict(arrowstyle="->", color=COLOR_MAP["sh-sy5y"], lw=0.9),
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.72", lw=0.7),
    )
    ax.annotate(
        "Dopaminergic neurons\nstay low-capacity and low-leak",
        xy=(
            float(merged.loc[merged["neuron_key"].eq("dopaminergic"), "maximal_ocr"].iloc[0]),
            float(merged.loc[merged["neuron_key"].eq("dopaminergic"), "proton_leak"].iloc[0]),
        ),
        xytext=(176, 30.2),
        fontsize=6.8,
        color=COLOR_MAP["dopaminergic"],
        arrowprops=dict(arrowstyle="->", color=COLOR_MAP["dopaminergic"], lw=0.9),
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.72", lw=0.7),
    )
    ax.text(0.80, 0.94, f"r = {r:.2f}", transform=ax.transAxes, ha="left", va="top", fontsize=7.0)

    ax.set_xlim(110, 485)
    ax.set_ylim(23, 66)
    ax.set_xlabel("Maximal OCR (pmol/min/ug)")
    ax.set_ylabel("Proton leak (pmol/min/ug)")
    ax.set_title("Higher respiratory throughput carries a proton-leak cost", fontweight="bold", pad=7)
    clean_axis(ax)


def make_figure1() -> tuple[Path, Path]:
    merged = prepare_merged()

    fig = plt.figure(figsize=(12.8, 7.7), dpi=300)
    gs = fig.add_gridspec(
        2,
        6,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.09,
        wspace=0.82,
        hspace=0.48,
        height_ratios=[1.10, 1.0],
    )

    ax_a = fig.add_subplot(gs[0, 0:4])
    ax_b = fig.add_subplot(gs[0, 4:6])
    ax_c = fig.add_subplot(gs[1, 0:2])
    ax_d = fig.add_subplot(gs[1, 2:4])
    ax_e = fig.add_subplot(gs[1, 4:6])

    panel_a_operating_state(ax_a, merged)
    panel_b_workflow(ax_b)
    panel_c_respiratory_envelope(ax_c, merged)
    panel_d_reserve_usage(ax_d, merged)
    panel_e_tradeoff(ax_e, merged)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure1_neuron_publication.png"
    out_pdf = FIGURES_DIR / "figure1_neuron_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure1()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
