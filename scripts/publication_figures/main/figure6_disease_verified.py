"""Conceptual Figure 6 after R029 disease-scenario audit.

The repository has qualitative disease motivations but no source-audited mapping
from disease measurements to model parameters and no held-out external
benchmark.  This replacement is deliberately a hypothesis map rather than a
trajectory, efficacy, or clinical-window prediction.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "figures" / "figure6_disease_applications.png"
PDF = ROOT / "figures" / "figure6_disease_applications.pdf"

COLORS = {
    "pd": "#0072B2",
    "ad": "#CC79A7",
    "als": "#D55E00",
    "green": "#009E73",
    "orange": "#E69F00",
    "gray": "#6C757D",
    "light": "#F2F2F2",
}


def _panel_label(ax, label):
    ax.text(-0.05, 1.04, label, transform=ax.transAxes, fontsize=12,
            fontweight="bold", va="bottom")


def _rounded_text(ax, xy, text, facecolor, edgecolor, fontsize=8.2):
    patch = FancyBboxPatch(
        xy,
        0.76,
        0.15,
        boxstyle="round,pad=0.02",
        facecolor=facecolor,
        edgecolor=edgecolor,
        lw=0.9,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + 0.38, xy[1] + 0.075, text, ha="center", va="center",
            fontsize=fontsize)


def _mechanism_map(ax):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.04, 0.93, "Qualitative disease motivations retained",
            fontsize=10, fontweight="bold", va="top")
    disease_rows = [
        ("PD", "Respiratory / oxidative stress", COLORS["pd"], 0.71),
        ("AD", "Energy–calcium stress", COLORS["ad"], 0.47),
        ("ALS", "Transport / oxidative stress", COLORS["als"], 0.23),
    ]
    for disease, mechanism, color, y in disease_rows:
        ax.add_patch(Circle((0.13, y), 0.075, facecolor=color,
                            edgecolor="white", lw=1))
        ax.text(0.13, y, disease, color="white", ha="center", va="center",
                fontweight="bold", fontsize=9)
        ax.add_patch(FancyArrowPatch((0.21, y), (0.37, y), arrowstyle="->",
                                     mutation_scale=10, color=COLORS["gray"]))
        _rounded_text(ax, (0.39, y - 0.075), mechanism, "#FFFFFF", color)
    ax.text(
        0.50,
        0.06,
        "These mechanisms motivate scenarios; they do not yet determine\n"
        "disease-specific numerical parameter values.",
        ha="center",
        fontsize=7.7,
        color=COLORS["gray"],
    )
    ax.axis("off")


def _evidence_gate(ax):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.04, 0.93, "Missing evidence-to-model chain",
            fontsize=10, fontweight="bold", va="top")
    nodes = [
        "Primary\nmeasurement",
        "Source\nledger",
        "ODE\nmapping",
        "Parameter\nensemble",
        "Held-out\ncomparison",
    ]
    x_values = [0.10, 0.30, 0.50, 0.70, 0.90]
    for idx, (x, text) in enumerate(zip(x_values, nodes)):
        ax.add_patch(Circle((x, 0.54), 0.073, facecolor=COLORS["light"],
                            edgecolor=COLORS["orange"], lw=1.2))
        ax.text(x, 0.54, str(idx + 1), ha="center", va="center",
                fontsize=9, fontweight="bold", color=COLORS["orange"])
        ax.text(x, 0.34, text, ha="center", va="top", fontsize=7.2)
        if idx < len(nodes) - 1:
            ax.add_patch(FancyArrowPatch((x + 0.08, 0.54),
                                         (x_values[idx + 1] - 0.08, 0.54),
                                         arrowstyle="->", mutation_scale=9,
                                         color=COLORS["gray"], lw=0.9))
    ax.text(
        0.50,
        0.11,
        "All five links are required before a quantitative disease claim.",
        ha="center",
        fontsize=7.8,
        color=COLORS["gray"],
    )
    ax.axis("off")


def _claim_boundary(ax):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.04, 0.93, "Interpretation boundary", fontsize=10,
            fontweight="bold", va="top")
    ax.add_patch(FancyBboxPatch(
        (0.08, 0.48), 0.84, 0.28, boxstyle="round,pad=0.03",
        facecolor="#E8F5EE", edgecolor=COLORS["green"], lw=1.0,
    ))
    ax.text(0.13, 0.69, "Allowed now", fontsize=8.5, fontweight="bold",
            color=COLORS["green"])
    ax.text(0.13, 0.58,
            "Mechanism-oriented hypotheses and future\n"
            "parameterization targets.", fontsize=8.2, va="center")
    ax.add_patch(FancyBboxPatch(
        (0.08, 0.12), 0.84, 0.24, boxstyle="round,pad=0.03",
        facecolor="#FFF3D6", edgecolor=COLORS["orange"], lw=1.0,
    ))
    ax.text(0.13, 0.30, "Withheld", fontsize=8.5, fontweight="bold",
            color=COLORS["orange"])
    ax.text(0.13, 0.20,
            "Disease trajectories, efficacy percentages,\n"
            "clinical windows, and patient outcomes.", fontsize=8.2,
            va="center")
    ax.axis("off")


def generate():
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6), constrained_layout=True)
    _mechanism_map(axes[0])
    _evidence_gate(axes[1])
    _claim_boundary(axes[2])
    for label, ax in zip(("a", "b", "c"), axes):
        _panel_label(ax, label)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=600, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)
    return OUT, PDF


if __name__ == "__main__":
    print(generate())
