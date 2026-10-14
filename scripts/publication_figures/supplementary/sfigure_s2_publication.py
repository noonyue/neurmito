# -*- coding: utf-8 -*-
"""
Publication Supplementary Figure S2
Cell culture protocols and drug-treatment validation.

Data policy:
- Uses only validated project CSV tables under csv/
- Keeps the publication-oriented multi-panel composition
- Leaves protocol timeline panels explicitly schematic while anchoring quantitative panels to real CSVs

Outputs:
- figures/sfigure_s2_publication.png
- figures/sfigure_s2_publication.pdf
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


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
    "gray": "0.45",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.06) -> None:
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


def note_tag(
    ax: plt.Axes,
    text: str,
    x: float = 0.02,
    y: float = 0.96,
    fc: str = "#fff7dd",
    ec: str = "0.70",
) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=5.8,
        color="0.30",
        bbox=dict(boxstyle="round,pad=0.25", fc=fc, ec=ec, lw=0.7),
    )


def arrow(ax: plt.Axes, xy1: tuple[float, float], xy2: tuple[float, float], color: str = "k", lw: float = 0.8, ms: int = 8) -> None:
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


def rounded_box(ax: plt.Axes, x: float, y: float, w: float, h: float, fc: str, ec: str, text: str | None = None, fontsize: float = 6.4) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.08,rounding_size=0.15",
        fc=fc,
        ec=ec,
        lw=1.0,
    )
    ax.add_patch(patch)
    if text is not None:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, fontweight="bold")
    return patch


def panel_a_timeline(ax: plt.Axes) -> None:
    panel_label(ax, "a")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.text(5, 6.7, "Primary neuron culture timeline", ha="center", va="top", fontsize=8, fontweight="bold")
    note_tag(ax, "Context schematic only", x=0.03, y=0.93)

    stages = [
        (0.6, 4.2, 1.8, 1.2, "Embryonic\n(E18)", "#dae8f7", COLORS["blue"], "Dissociation"),
        (2.6, 4.2, 1.6, 1.2, "Plating\n(DIV 0)", "#dae8f7", COLORS["blue"], "Coating"),
        (4.4, 4.2, 1.6, 1.2, "DIV 1-3\nGrowth", "#e8f4e8", COLORS["green"], "Media change"),
        (6.2, 4.2, 1.6, 1.2, "DIV 7-14\nMature", "#fff4e0", COLORS["orange"], "Experiments"),
        (8.0, 4.2, 1.6, 1.2, "Treatment\nDIV 14+", "#f7e0e8", COLORS["red"], "Drug exposure"),
    ]
    for x0, y0, w, h, label, fc, ec, sub in stages:
        rounded_box(ax, x0, y0, w, h, fc, ec)
        ax.text(x0 + w / 2, y0 + h / 2 + 0.10, label, ha="center", va="center", fontsize=6.3, fontweight="bold")
        ax.text(x0 + w / 2, y0 + 0.22, sub, ha="center", va="center", fontsize=5.5, color=COLORS["gray"])

    for i, (x0, y0, w, h, *_rest) in enumerate(stages[:-1]):
        arrow(ax, (x0 + w, y0 + h / 2), (stages[i + 1][0], y0 + h / 2), lw=0.7, ms=6)

    ax.axhline(3.9, xmin=0.06, xmax=0.95, color="0.6", lw=0.5, ls="--")
    for xi, div in [(2.0, "DIV 0"), (4.8, "DIV 3"), (7.0, "DIV 7"), (8.8, "DIV 14")]:
        ax.plot([xi, xi], [3.75, 4.05], color="0.6", lw=0.8)
        ax.text(xi, 3.55, div, ha="center", va="top", fontsize=5.5)

    steps = [
        "1. Dissect cortex and remove meninges",
        "2. Papain digestion (10 min, 37C)",
        "3. Triturate and count viable cells",
        "4. Plate on poly-D-lysine substrate",
    ]
    for idx, text in enumerate(steps):
        ax.text(0.7, 1.6 - idx * 0.45, text, fontsize=5.7, color="0.25")


def panel_b_seeding(ax: plt.Axes, cell_df: pd.DataFrame) -> None:
    panel_label(ax, "b")
    plot_df = cell_df.copy()
    plot_df["short_label"] = [
        "Rat CTX", "Mouse CTX", "Rat HIP", "Mouse STR", "Rat CB", "Human MOT", "Mouse DA", "Rat GABA", "Human CHOL"
    ]
    colors = ["#2f80b7", "#5aa6c8", "#5aa6c8", "#f2a33a", "#b99579", "#9b59b6", "#d62f2f", "#7c60a7", "#9b59b6"]
    x = np.arange(len(plot_df))
    bars = ax.bar(x, plot_df["seeding_density"].to_numpy(dtype=float), color=colors, edgecolor="white", width=0.62)
    for bar, val in zip(bars, plot_df["seeding_density"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.3, f"{int(val)}", ha="center", va="bottom", fontsize=5.8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["short_label"], rotation=35, ha="right")
    ax.set_ylabel("Seeding density")
    ax.set_title("Cell-type-specific seeding density", fontweight="bold", pad=7)
    handles = [
        Line2D([0], [0], color="#2f80b7", lw=0, marker="s", markersize=7, label="Rat"),
        Line2D([0], [0], color="#5aa6c8", lw=0, marker="s", markersize=7, label="Mouse"),
        Line2D([0], [0], color="#9b59b6", lw=0, marker="s", markersize=7, label="Human iPSC"),
    ]
    leg = ax.legend(handles=handles, loc="upper right", frameon=True, framealpha=0.85, fontsize=6.0)
    leg.get_frame().set_edgecolor("0.55")
    clean_axis(ax)


def panel_c_drug(ax: plt.Axes, drug_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    concentrations = np.array([0.1, 1, 10, 100, 1000], dtype=float)
    col_map = {
        "Rotenone": COLORS["red"],
        "Paraquat": COLORS["blue"],
        "Antimycin A": COLORS["green"],
    }
    for _, row in drug_df.iterrows():
        survival = row[["conc_0.1nM", "conc_1nM", "conc_10nM", "conc_100nM", "conc_1000nM"]].to_numpy(dtype=float)
        ax.plot(concentrations, survival, marker="o", ms=4.0, lw=1.5, color=col_map.get(row["drug"], "0.35"), label=row["drug"])
    ax.set_xscale("log")
    ax.set_ylim(0, 105)
    ax.set_xlabel("Concentration (nM)")
    ax.set_ylabel("Relative viability (%)")
    ax.set_title("Drug dose-response validation", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_d_validation(ax: plt.Axes, val_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    x = val_df["experimental_OCR"].to_numpy(dtype=float)
    y = val_df["model_OCR"].to_numpy(dtype=float)
    xerr = val_df["experimental_std"].to_numpy(dtype=float)
    yerr = val_df["model_std"].to_numpy(dtype=float)
    ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o", color=COLORS["blue"], mec="white", mew=0.5, elinewidth=0.8, capsize=2.5)
    xx = np.linspace(0, max(x.max(), y.max()) * 1.05, 150)
    ax.plot(xx, xx, color="0.35", lw=1.0, ls="--")
    corr = np.corrcoef(x, y)[0, 1]
    ax.text(0.05, 0.94, f"r = {corr:.2f}\n(n = {len(x)})", transform=ax.transAxes, ha="left", va="top", fontsize=6.6, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.7", lw=0.7))
    note_tag(ax, "Quantitative agreement panel", x=0.62, y=0.94, fc="#edf7ed")
    ax.set_xlabel("Experimental OCR")
    ax.set_ylabel("Model OCR")
    ax.set_title("Independent OCR validation series", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_e_protocol_table(ax: plt.Axes, cell_df: pd.DataFrame) -> None:
    panel_label(ax, "e")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.50, 0.92, "Protocol summary from the curated culture table", ha="center", va="top", fontsize=7.6, fontweight="bold")
    note_tag(ax, "Curated metadata summary", x=0.04, y=0.80)
    highlight = cell_df.loc[cell_df["seeding_density"].idxmax()]
    low = cell_df.loc[cell_df["seeding_density"].idxmin()]
    text = (
        f"Highest density: {highlight['neuron_type']} ({int(highlight['seeding_density'])})\n"
        f"Lowest density: {low['neuron_type']} ({int(low['seeding_density'])})\n"
        f"Typical maturation window: DIV {cell_df['DIV'].mode().iloc[0]}"
    )
    ax.text(0.04, 0.52, text, fontsize=6.5, va="center")


def panel_f_rotenone(ax: plt.Axes, val_df: pd.DataFrame) -> None:
    panel_label(ax, "f")
    x = val_df["rotenone_uM"].to_numpy(dtype=float)
    model = val_df["model_OCR"].to_numpy(dtype=float)
    exp = val_df["experimental_OCR"].to_numpy(dtype=float)
    ax.plot(x, model, color=COLORS["red"], lw=1.5, marker="o", ms=3.5, label="Model")
    ax.plot(x, exp, color=COLORS["blue"], lw=1.5, marker="s", ms=3.5, label="Experiment")
    ax.fill_between(x, exp - val_df["experimental_std"].to_numpy(dtype=float), exp + val_df["experimental_std"].to_numpy(dtype=float), color=COLORS["blue"], alpha=0.12)
    ax.set_xscale("log")
    ax.set_xlabel("Rotenone (uM)")
    ax.set_ylabel("OCR")
    ax.set_title("Rotenone-response agreement", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def make_s2() -> tuple[Path, Path]:
    cell_df = load_csv("sfigure_s2_cell_culture_protocols.csv")
    drug_df = load_csv("sfigure_s2_drug_treatments.csv")
    val_df = load_csv("sfigure_s2_validation_results.csv")

    fig = plt.figure(figsize=(13.5, 9.0), dpi=300)
    ax_a = fig.add_axes([0.050, 0.605, 0.360, 0.340])
    ax_b = fig.add_axes([0.455, 0.605, 0.490, 0.340])
    ax_c = fig.add_axes([0.050, 0.305, 0.440, 0.250])
    ax_d = fig.add_axes([0.535, 0.305, 0.420, 0.250])
    ax_e = fig.add_axes([0.050, 0.150, 0.405, 0.110])
    ax_f = fig.add_axes([0.520, 0.150, 0.435, 0.110])
    ax_cap = fig.add_axes([0.035, 0.040, 0.930, 0.090])

    panel_a_timeline(ax_a)
    panel_b_seeding(ax_b, cell_df)
    panel_c_drug(ax_c, drug_df)
    panel_d_validation(ax_d, val_df)
    panel_e_protocol_table(ax_e, cell_df)
    panel_f_rotenone(ax_f, val_df)

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S2\ |}$ Cell-culture context and quantitative calibration inputs. "
        "a, Schematic timeline of the primary neuron culture workflow used only to contextualize the quantitative panels. "
        "b, Seeding density values across the curated neuron-culture table. "
        "c, Dose-response behavior for rotenone, paraquat, and antimycin A from the project treatment table. "
        "d, Direct comparison between model and experimental OCR values across the independent validation series. "
        "e, Compact protocol summary derived from the curated cell-culture metadata. "
        "f, Rotenone-specific OCR agreement shown as a direct model-versus-experiment response curve. "
        "Panels a and e are contextual schematics/metadata summaries, whereas panels b-d and f are quantitative tables anchored to project CSV files."
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
    out_png = FIGURES_DIR / "sfigure_s2_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s2_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s2()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
