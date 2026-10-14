# -*- coding: utf-8 -*-
"""
Publication Supplementary Figure S1
Framework organization, evidence boundaries, and software architecture.

Data policy:
- Uses curated framework inventory tables under csv/
- Produces an organizational supplementary figure rather than a quantitative result plot
- Explicitly separates literature constraints, calibration-derived quantities, and model predictions

Outputs:
- figures/sfigure_s1_publication.png
- figures/sfigure_s1_publication.pdf
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
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
    "Input": "#dcecff",
    "Mechanistic": "#fff2c2",
    "Inference": "#eadcf6",
    "ML": "#dff0de",
    "Analysis": "#ffe0c6",
    "Monitoring": "#f7d5d5",
    "Clinical": "#f3dfb4",
    "Data Layer": "#2f6fb0",
    "Model Layer": "#4d8b31",
    "Calibration": "#8b62c5",
    "Prediction": "#d77c2b",
    "Output": "#c73b46",
    "line": "0.30",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    if name == "sfigure_s1_software_architecture.csv":
        rows: list[dict[str, str]] = []
        with path.open("r", encoding="utf-8") as handle:
            header = handle.readline().strip().split(",")
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                parts = [part.strip() for part in raw.split(",")]
                if len(parts) < 3:
                    continue
                layer = parts[0]
                component = parts[1]
                description = ", ".join(parts[2:])
                rows.append(
                    {
                        header[0]: layer,
                        header[1]: component,
                        header[2]: description,
                    }
                )
        return pd.DataFrame(rows, columns=header)
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


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    fc: str,
    ec: str = "0.55",
    lw: float = 0.9,
    text: str | None = None,
    fontsize: float = 6.4,
    fontweight: str = "bold",
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.03",
        fc=fc,
        ec=ec,
        lw=lw,
    )
    ax.add_patch(patch)
    if text is not None:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, fontweight=fontweight)
    return patch


def arrow(
    ax: plt.Axes,
    xy1: tuple[float, float],
    xy2: tuple[float, float],
    color: str = COLORS["line"],
    lw: float = 0.9,
    ms: int = 8,
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


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_a_framework(ax: plt.Axes, comp_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.50, 0.97, "Framework layers and information flow", ha="center", va="top", fontsize=8.2, fontweight="bold")

    layer_y = {
        "Data Layer": 0.80,
        "Model Layer": 0.62,
        "Calibration": 0.44,
        "Prediction": 0.26,
        "Output": 0.08,
    }
    x_positions = [0.06, 0.27, 0.48, 0.69]

    output_offsets = {
        "Early Warning System": 0.48,
        "Disease Applications": 0.69,
    }
    custom_x = {
        "Seahorse Data": 0.06,
        "ODE Model": 0.27,
        "Bayesian Calibration": 0.48,
        "Hybrid Neural-ODE": 0.69,
        "Multi-Stress Analysis": 0.27,
    }
    box_centers: dict[str, tuple[float, float]] = {}

    for idx, row in enumerate(comp_df.itertuples(index=False)):
        y = layer_y.get(row.layer, 0.08)
        x = custom_x.get(row.component, output_offsets.get(row.component, x_positions[idx % len(x_positions)]))
        fc = COLORS.get(row.category, "#efefef")
        rounded_box(
            ax,
            x,
            y,
            0.22,
            0.10,
            fc=fc,
            ec="0.50",
            text=str(row.component).replace(" ", "\n", 1),
            fontsize=6.2,
        )
        box_centers[str(row.component)] = (x + 0.11, y + 0.05)
        ax.text(x + 0.11, y - 0.02, row.layer, ha="center", va="top", fontsize=5.6, color="0.35")

    connections = [
        ("Seahorse Data", "Bayesian Calibration"),
        ("ODE Model", "Bayesian Calibration"),
        ("Bayesian Calibration", "Hybrid Neural-ODE"),
        ("Hybrid Neural-ODE", "Multi-Stress Analysis"),
        ("Multi-Stress Analysis", "Early Warning System"),
        ("Multi-Stress Analysis", "Disease Applications"),
    ]
    for start, end in connections:
        xy1 = box_centers[start]
        xy2 = box_centers[end]
        arrow(ax, (xy1[0], xy1[1] - 0.055), (xy2[0], xy2[1] + 0.055))

    ax.text(
        0.02,
        0.01,
        "Organizational view only: the boxes summarize framework components rather than experimental measurements.",
        ha="left",
        va="bottom",
        fontsize=5.8,
        color="0.35",
    )


def panel_b_evidence_boundary(ax: plt.Axes) -> None:
    panel_label(ax, "b")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.50, 0.97, "Evidence classes carried through the manuscript", ha="center", va="top", fontsize=8.2, fontweight="bold")

    boxes = [
        (
            0.03,
            0.18,
            0.28,
            0.62,
            "#e3f0fb",
            "Literature-constrained inputs",
            "Seahorse OCR tables\nCell-culture metadata\nPublished neuron-type priors\n\nMain use:\nFigure 1\nSupplementary Fig. S2\nSupplementary Table S5",
        ),
        (
            0.36,
            0.18,
            0.28,
            0.62,
            "#f7eed6",
            "Calibration and derived quantities",
            "Bayesian fit summaries\nSensitivity rankings\nConvergence diagnostics\nUncertainty decomposition\n\nMain use:\nFigure 1 context\nSupplementary Figs. S3-S6, S16-S17",
        ),
        (
            0.69,
            0.18,
            0.28,
            0.62,
            "#f9dedd",
            "Model predictions and simulations",
            "Stress-state inference\nCollapse boundaries\nEarly-warning trajectories\nSpatial and disease extensions\n\nMain use:\nFigures 2-6\nSupplementary Figs. S7-S15, S18-S20",
        ),
    ]

    for x, y, w, h, fc, title, body in boxes:
        rounded_box(ax, x, y, w, h, fc=fc, ec="0.55", text=None)
        ax.text(x + 0.02, y + h - 0.05, title, ha="left", va="top", fontsize=7.0, fontweight="bold")
        ax.text(x + 0.02, y + h - 0.12, body, ha="left", va="top", fontsize=6.2)

    arrow(ax, (0.31, 0.49), (0.36, 0.49))
    arrow(ax, (0.64, 0.49), (0.69, 0.49))
    ax.text(0.50, 0.08, "This separation is used to prevent model predictions from being presented as direct experimental observations.", ha="center", va="center", fontsize=6.0, color="0.35")


def panel_c_inventory(ax: plt.Axes, comp_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.50, 0.97, "Component inventory from the curated framework table", ha="center", va="top", fontsize=8.2, fontweight="bold")

    headers = ["Component", "Category", "Layer", "Role"]
    x_cols = [0.02, 0.34, 0.54, 0.72]
    widths = [0.30, 0.18, 0.16, 0.26]
    y_top = 0.86
    row_h = 0.095

    for x, w, head in zip(x_cols, widths, headers):
        ax.add_patch(Rectangle((x, y_top), w, 0.08, fc="#ececec", ec="0.55", lw=0.8))
        ax.text(x + 0.01, y_top + 0.04, head, ha="left", va="center", fontsize=6.5, fontweight="bold")

    role_map = {
        "Input": "Constrain biological baselines",
        "Mechanistic": "Carry interpretable state dynamics",
        "Inference": "Estimate calibrated parameter ranges",
        "ML": "Correct residual stress dynamics",
        "Analysis": "Map collapse under combined stress",
        "Monitoring": "Quantify pre-collapse warnings",
        "Clinical": "Generalize to disease contexts",
    }

    for idx, row in enumerate(comp_df.itertuples(index=False)):
        y = y_top - (idx + 1) * row_h
        bg = "#fbfbfb" if idx % 2 == 0 else "#f1f5f9"
        for x, w in zip(x_cols, widths):
            ax.add_patch(Rectangle((x, y), w, row_h, fc=bg, ec="0.82", lw=0.6))
        ax.text(x_cols[0] + 0.01, y + row_h / 2, str(row.component), ha="left", va="center", fontsize=6.0, fontweight="bold")
        ax.text(x_cols[1] + 0.01, y + row_h / 2, str(row.category), ha="left", va="center", fontsize=6.0)
        ax.text(x_cols[2] + 0.01, y + row_h / 2, str(row.layer), ha="left", va="center", fontsize=6.0)
        ax.text(x_cols[3] + 0.01, y + row_h / 2, textwrap.fill(role_map.get(str(row.category), str(row.description)), width=22), ha="left", va="center", fontsize=5.8)


def panel_d_software(ax: plt.Axes, arch_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.50, 0.97, "Software stack used to operationalize the framework", ha="center", va="top", fontsize=8.2, fontweight="bold")

    y_positions = [0.78, 0.60, 0.42, 0.24, 0.06]
    layer_colors = ["#e7f0fc", "#eef4e8", "#f7e9d9", "#f4e7f9", "#f8dddd"]
    for (row, y, fc) in zip(arch_df.itertuples(index=False), y_positions, layer_colors):
        rounded_box(ax, 0.12, y, 0.28, 0.11, fc=fc, ec="0.55", text=str(row.layer), fontsize=6.5)
        rounded_box(ax, 0.48, y, 0.18, 0.11, fc="white", ec="0.65", text=str(row.component), fontsize=6.2, fontweight="normal")
        rounded_box(ax, 0.71, y, 0.22, 0.11, fc="white", ec="0.65", text=textwrap.fill(str(row.description), width=16), fontsize=5.8, fontweight="normal")
        arrow(ax, (0.40, y + 0.055), (0.48, y + 0.055))
        arrow(ax, (0.66, y + 0.055), (0.71, y + 0.055))

    for upper, lower in zip(y_positions[:-1], y_positions[1:]):
        arrow(ax, (0.26, upper), (0.26, lower + 0.11))


def panel_e_routing(ax: plt.Axes) -> None:
    panel_label(ax, "e")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.50, 0.97, "Routing from computational modules to the manuscript figure set", ha="center", va="top", fontsize=8.2, fontweight="bold")

    routes = [
        ("Baseline reserve landscape", "Figure 1", "Supp. S2-S5"),
        ("Hybrid stress-state inference", "Figure 2", "Supp. S6"),
        ("Nonlinear collapse boundaries", "Figure 3", "Supp. S7"),
        ("Early-warning behavior", "Figure 4", "Supp. S8, S18"),
        ("Spatial vulnerability extension", "Figure 5", "Supp. S9"),
        ("Disease-context extension", "Figure 6", "Supp. S10-S15"),
        ("Uncertainty and implementation", "Methods / Discussion", "Supp. S16-S20"),
    ]

    y0 = 0.82
    for idx, (module, main_fig, support) in enumerate(routes):
        y = y0 - idx * 0.105
        rounded_box(ax, 0.03, y, 0.34, 0.075, fc="#edf3fb", ec="0.65", text=module, fontsize=6.2)
        rounded_box(ax, 0.45, y, 0.16, 0.075, fc="#fff4df", ec="0.65", text=main_fig, fontsize=6.2)
        rounded_box(ax, 0.69, y, 0.26, 0.075, fc="#f7e7ef", ec="0.65", text=support, fontsize=6.2)
        arrow(ax, (0.37, y + 0.0375), (0.45, y + 0.0375))
        arrow(ax, (0.61, y + 0.0375), (0.69, y + 0.0375))

    ax.text(0.50, 0.06, "Supplementary figures are intended to support specific claims rather than serve as a stand-alone project dashboard.", ha="center", va="center", fontsize=6.0, color="0.35")


def make_s1() -> tuple[Path, Path]:
    comp_df = load_csv("sfigure_s1_framework_components.csv")
    arch_df = load_csv("sfigure_s1_software_architecture.csv")

    fig = plt.figure(figsize=(13.5, 8.9), dpi=300)
    ax_a = fig.add_axes([0.045, 0.565, 0.430, 0.345])
    ax_b = fig.add_axes([0.525, 0.565, 0.430, 0.345])
    ax_c = fig.add_axes([0.045, 0.165, 0.430, 0.325])
    ax_d = fig.add_axes([0.525, 0.165, 0.215, 0.325])
    ax_e = fig.add_axes([0.760, 0.165, 0.195, 0.325])
    ax_cap = fig.add_axes([0.035, 0.035, 0.930, 0.090])

    panel_a_framework(ax_a, comp_df)
    panel_b_evidence_boundary(ax_b)
    panel_c_inventory(ax_c, comp_df)
    panel_d_software(ax_d, arch_df)
    panel_e_routing(ax_e)

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S1\ |}$ Framework organization, evidence boundaries, and software architecture. "
        "a, Layered workflow reconstructed from sfigure_s1_framework_components.csv, linking data inputs, mechanistic modeling, calibration, prediction, and output modules. "
        "b, Organizational evidence map that separates literature-constrained inputs, calibration-derived quantities, and model predictions across the manuscript figure set. "
        "c, Component inventory from the curated framework table, summarizing the role of each major module. "
        "d, Software stack assembled from sfigure_s1_software_architecture.csv. "
        "e, Routing map connecting framework modules to the main figures and supporting supplementary figures. "
        "Panels b and e are manuscript-organization schematics rather than quantitative result plots."
    )
    ax_cap.text(
        0.015,
        0.96,
        textwrap.fill(caption, width=188),
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.42", fc="white", ec="0.55", lw=0.8),
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "sfigure_s1_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s1_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s1()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
