"""Conceptual Figure 5 after R028 spatial-model audit.

This figure deliberately contains no quantitative spatial prediction.  The
current repository has no coupled spatial solver, boundary-condition definition,
or grid-convergence evidence.  It documents the admissible interpretation and
the computational work needed to enable a future spatial analysis.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "figures" / "figure5_spatial_heterogeneity.png"
PDF = ROOT / "figures" / "figure5_spatial_heterogeneity.pdf"

COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "gray": "#6C757D",
    "light_blue": "#E6F1F7",
    "light_orange": "#FFF3D6",
    "light_gray": "#F2F2F2",
}


def _panel_label(ax, label):
    ax.text(
        -0.05,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="bottom",
    )


def _scenario_panel(ax):
    x = np.linspace(0.08, 0.92, 180)
    y = 0.50 + 0.035 * np.sin(5 * np.pi * x)
    ax.plot(x, y, color=COLORS["gray"], lw=5, solid_capstyle="round")
    ax.add_patch(Circle((0.08, 0.50), 0.075, facecolor=COLORS["light_blue"],
                        edgecolor=COLORS["blue"], lw=1.4))
    ax.text(0.08, 0.50, "soma", ha="center", va="center", fontsize=8)

    positions = [0.24, 0.48, 0.73, 0.90]
    sizes = [0.041, 0.036, 0.031, 0.026]
    for xpos, radius in zip(positions, sizes):
        ax.add_patch(Circle((xpos, 0.50), radius, facecolor=COLORS["orange"],
                            edgecolor="white", lw=0.7))

    ax.annotate("proximal", (0.24, 0.34), ha="center", fontsize=8,
                color=COLORS["blue"])
    ax.annotate("distal", (0.83, 0.34), ha="center", fontsize=8,
                color=COLORS["orange"])
    ax.add_patch(FancyArrowPatch((0.19, 0.42), (0.86, 0.42),
                                 arrowstyle="->", mutation_scale=10,
                                 color=COLORS["gray"], lw=1))
    ax.text(
        0.50,
        0.79,
        "Position-indexed scenario only",
        ha="center",
        fontsize=10,
        fontweight="bold",
    )
    ax.text(
        0.50,
        0.68,
        "Relative proximal-to-distal vulnerability may be explored\n"
        "as an assumption, not inferred as a spatial prediction.",
        ha="center",
        va="center",
        fontsize=8,
    )
    ax.set(xlim=(0, 1), ylim=(0.18, 0.92))
    ax.axis("off")


def _missing_solver_panel(ax):
    items = [
        "Coupled transport / exchange equations",
        "Geometry, units, and boundary conditions",
        "Inter-compartment state coupling",
        "Grid-refinement and endpoint convergence",
    ]
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.04, 0.93, "Why no quantitative spatial result is shown",
            fontsize=10, fontweight="bold", va="top")
    for i, item in enumerate(items):
        y = 0.74 - i * 0.16
        ax.add_patch(FancyBboxPatch(
            (0.07, y - 0.065), 0.86, 0.10,
            boxstyle="round,pad=0.02",
            facecolor=COLORS["light_gray"],
            edgecolor=COLORS["gray"],
            lw=0.8,
        ))
        ax.text(0.11, y - 0.015, "Not implemented:", color=COLORS["orange"],
                fontsize=8, fontweight="bold", va="center")
        ax.text(0.43, y - 0.015, item, fontsize=8, va="center")
    ax.axis("off")


def _recovery_panel(ax):
    steps = [
        "Specify coupled spatial model",
        "Pre-register endpoint and tolerance",
        "Compare at three or more resolutions",
        "Benchmark against documented spatial data",
    ]
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.04, 0.93, "Gate for a future quantitative Figure 5",
            fontsize=10, fontweight="bold", va="top")
    y_values = [0.75, 0.57, 0.39, 0.21]
    for index, (step, y) in enumerate(zip(steps, y_values), start=1):
        ax.add_patch(Circle((0.12, y), 0.055, facecolor=COLORS["green"],
                            edgecolor="white", lw=1))
        ax.text(0.12, y, str(index), ha="center", va="center",
                color="white", fontsize=9, fontweight="bold")
        ax.text(0.22, y, step, va="center", fontsize=8.5)
        if index < len(steps):
            ax.add_patch(FancyArrowPatch((0.12, y - 0.07), (0.12, y - 0.13),
                                         arrowstyle="->", mutation_scale=9,
                                         color=COLORS["gray"], lw=0.9))
    ax.axis("off")


def generate():
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6), constrained_layout=True)
    _scenario_panel(axes[0])
    _missing_solver_panel(axes[1])
    _recovery_panel(axes[2])
    for label, ax in zip(("a", "b", "c"), axes):
        _panel_label(ax, label)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=600, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)
    return OUT, PDF


if __name__ == "__main__":
    print(generate())
