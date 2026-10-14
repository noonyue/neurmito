# -*- coding: utf-8 -*-
"""Generate the data-driven computational Figure 3 from qualified ODE runs.

The figure uses only the R009-R014B result chain:
- resolved rotenone x paraquat endpoint grid;
- long-tail endpoint-resolution trajectory;
- ROS-feedback ablation;
- initial-condition and solver robustness.

It does not fit a continuous collapse surface or claim bistability/hysteresis.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = PROJECT_ROOT / "refine-logs" / "runs"
FIGURES_DIR = PROJECT_ROOT / "figures"

plt.rcParams.update(
    {
        "font.family": "DejaVu Serif",
        "font.size": 7.8,
        "axes.labelsize": 7.6,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "legend.fontsize": 6.5,
        "axes.linewidth": 0.75,
        "xtick.major.width": 0.65,
        "ytick.major.width": 0.65,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    }
)

COLORS = {
    "physiological": "#009E73",
    "depolarized": "#CC79A7",
    "transition": "#000000",
    "ic": "#0072B2",
    "solver": "#D55E00",
    "full_model": "#0072B2",
    "ablation": "#999999",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.18,
        1.08,
        label,
        transform=ax.transAxes,
        fontweight="bold",
        fontsize=12,
        ha="left",
        va="top",
    )


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def resolved_grid(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rotenone = np.asarray(sorted({as_float(row, "rotenone_inhibition") for row in rows}))
    paraquat = np.asarray(sorted({as_float(row, "paraquat_index") for row in rows}))
    lookup = {(as_float(row, "rotenone_inhibition"), as_float(row, "paraquat_index")): row for row in rows}
    classes = np.empty((len(paraquat), len(rotenone)), dtype=float)
    dpsi = np.empty_like(classes)

    for row_index, pq in enumerate(paraquat):
        for col_index, rot in enumerate(rotenone):
            row = lookup[(rot, pq)]
            classes[row_index, col_index] = (
                0.0
                if row["resolved_endpoint_class"] == "near_fixed_physiological_endpoint"
                else 1.0
            )
            dpsi[row_index, col_index] = as_float(row, "resolved_final_dpsi_mv")
    return rotenone, paraquat, classes, dpsi


def plot_endpoint_class(
    ax: plt.Axes,
    rows: list[dict[str, str]],
    band_rows: list[dict[str, str]],
) -> None:
    panel_label(ax, "a")
    rotenone, paraquat, classes, _ = resolved_grid(rows)
    cmap = ListedColormap([COLORS["physiological"], COLORS["depolarized"]])
    ax.imshow(
        classes,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap=cmap,
        extent=[
            rotenone.min() * 100 - 0.5,
            rotenone.max() * 100 + 0.5,
            paraquat.min() - 0.5,
            paraquat.max() + 0.5,
        ],
        vmin=0,
        vmax=1,
    )
    for row in band_rows:
        pq = as_float(row, "paraquat_index")
        left = as_float(row, "highest_physiological_rotenone") * 100
        right = as_float(row, "lowest_depolarized_rotenone") * 100
        ax.plot([left, right], [pq, pq], color=COLORS["transition"], linewidth=1.25, zorder=5)

    ax.scatter([], [], marker="s", s=32, color=COLORS["physiological"], label="Physiological endpoint")
    ax.scatter([], [], marker="s", s=32, color=COLORS["depolarized"], label="Depolarized endpoint")
    ax.plot([], [], color=COLORS["transition"], linewidth=1.25, label="Resolved grid transition")
    ax.set_xlabel("Rotenone (% Complex I inhibition)")
    ax.set_ylabel("Paraquat index (µM)")
    ax.set_xticks([80, 83, 85, 87, 89, 91, 95])
    ax.set_yticks(paraquat)
    ax.legend(frameon=False, loc="upper left", handlelength=1.6)
    clean_axis(ax)


def plot_dpsi_grid(
    ax: plt.Axes,
    rows: list[dict[str, str]],
    band_rows: list[dict[str, str]],
) -> None:
    panel_label(ax, "b")
    rotenone, paraquat, _, dpsi = resolved_grid(rows)
    mesh = ax.pcolormesh(rotenone * 100, paraquat, dpsi, shading="auto", cmap="viridis")
    for row in band_rows:
        pq = as_float(row, "paraquat_index")
        left = as_float(row, "highest_physiological_rotenone") * 100
        right = as_float(row, "lowest_depolarized_rotenone") * 100
        ax.plot([left, right], [pq, pq], color="white", linewidth=1.2, zorder=5)

    ax.set_xlabel("Rotenone (% Complex I inhibition)")
    ax.set_ylabel("Paraquat index (µM)")
    ax.set_xticks([80, 83, 85, 87, 89, 91, 95])
    ax.set_yticks(paraquat)
    cbar = ax.figure.colorbar(mesh, ax=ax, pad=0.02)
    cbar.set_label(r"Final $\Delta\Psi_m$ (mV)")
    clean_axis(ax)


def plot_transition_band(ax: plt.Axes, band_rows: list[dict[str, str]]) -> None:
    panel_label(ax, "c")
    pq = np.asarray([as_float(row, "paraquat_index") for row in band_rows])
    highest_phys = np.asarray([as_float(row, "highest_physiological_rotenone") * 100 for row in band_rows])
    lowest_depol = np.asarray([as_float(row, "lowest_depolarized_rotenone") * 100 for row in band_rows])
    ax.fill_between(pq, highest_phys, lowest_depol, color="0.75", alpha=0.65, label="Resolved grid interval")
    ax.plot(pq, highest_phys, color=COLORS["physiological"], marker="o", linewidth=1.8, label="Highest physiological")
    ax.plot(pq, lowest_depol, color=COLORS["depolarized"], marker="s", linewidth=1.8, label="Lowest depolarized")
    ax.set_xlabel("Paraquat index (µM)")
    ax.set_ylabel("Rotenone (% Complex I inhibition)")
    ax.set_ylim(81, 87)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def unresolved_count(path: Path) -> int:
    return sum(
        row["endpoint_class"] in {"continuing_depletion", "slow_drift_not_converged"}
        for row in load_csv(path)
    )


def plot_tail_resolution(ax: plt.Axes) -> None:
    panel_label(ax, "d")
    stages = [
        ("5k", RUNS_DIR / "R011/transition_refinement_grid.csv"),
        ("10k", RUNS_DIR / "R012/tail_extension_grid.csv"),
        ("30k", RUNS_DIR / "R013/deep_tail_grid.csv"),
        ("60k", RUNS_DIR / "R014/final_tail_grid.csv"),
        ("120k", RUNS_DIR / "R014A/persistent_tail_grid.csv"),
    ]
    labels = [stage[0] for stage in stages]
    unresolved = np.asarray([unresolved_count(stage[1]) for stage in stages])
    x = np.arange(len(labels))
    ax.step(x, unresolved, where="mid", color=COLORS["transition"], linewidth=1.7)
    ax.scatter(x, unresolved, color=COLORS["transition"], s=28, zorder=3)
    for xpos, value in zip(x, unresolved):
        ax.text(xpos, value + 0.7, str(int(value)), ha="center", va="bottom", fontsize=6.7)
    ax.set_xticks(x, labels)
    ax.set_xlabel("Maximum integration horizon (s)")
    ax.set_ylabel("Unresolved conditions")
    ax.set_ylim(-0.5, max(unresolved) + 3)
    ax.text(
        0.47,
        0.94,
        "19 uncertain at 5k s\n0 remaining at 120k s",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.20", facecolor="white", edgecolor="0.75", linewidth=0.5),
    )
    clean_axis(ax)


def plot_ablation(ax: plt.Axes, rows: list[dict[str, str]]) -> None:
    panel_label(ax, "e")
    labels = {
        "full_model": "Full",
        "no_ros_induced_leak": "No ROS\nleak",
        "no_h2o2_c1_feedback": "No H$_2$O$_2$\nfeedback",
        "no_ros_leak_no_h2o2_c1_feedback": "No both",
    }
    x = np.arange(len(rows))
    values = np.asarray([as_float(row, "mean_dpsi_drop_0_8_to_0_9") for row in rows])
    colors = [
        COLORS["full_model"] if row["model_variant"] == "full_model" else COLORS["ablation"]
        for row in rows
    ]
    ax.bar(x, values, color=colors, width=0.72)
    ax.set_xticks(x, [labels[row["model_variant"]] for row in rows])
    ax.set_ylabel(r"Mean $\Delta\Psi_m$ drop, 80→90% (mV)")
    ax.set_ylim(0, max(values) + 8)
    ax.text(
        0.03,
        0.94,
        "14/49 depolarized\nin every variant",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
    )
    clean_axis(ax)


def plot_robustness(
    ax: plt.Axes,
    summary_rows: list[dict[str, str]],
    robustness_rows: list[dict[str, str]],
) -> None:
    panel_label(ax, "f")
    labels = {
        "default_ic": "Default\nIC",
        "low_energy_reduced_ic": "Low-energy\nIC",
        "high_energy_oxidized_ic": "High-energy\nIC",
        "LSODA": "LSODA",
        "BDF": "BDF",
        "Radau": "Radau",
    }
    x = np.arange(len(summary_rows))
    values = np.asarray([as_float(row, "mean_dpsi_drop_0_8_to_0_9") for row in summary_rows])
    point_colors = [
        COLORS["ic"] if row["run_axis"] == "initial_condition" else COLORS["solver"]
        for row in summary_rows
    ]
    ax.plot(x, values, color="0.4", linewidth=1.0, zorder=1)
    ax.scatter(x, values, color=point_colors, s=34, zorder=2)

    mismatch_by_variant = {}
    for row in robustness_rows:
        variant = row["variant"]
        mismatch_by_variant.setdefault(variant, 0)
        mismatch_by_variant[variant] += (
            str(row["same_endpoint_class_as_default_lsoda"]).strip().lower() != "true"
        )
    for xpos, row in zip(x, summary_rows):
        variant = row["variant"]
        ax.text(xpos, values[xpos] + 0.25, f"{mismatch_by_variant[variant]}/49", ha="center", fontsize=6.2)

    ax.set_xticks(x, [labels[row["variant"]] for row in summary_rows])
    ax.set_ylabel(r"Mean $\Delta\Psi_m$ drop, 80→90% (mV)")
    ax.set_ylim(34.8, 36.8)
    ax.text(
        0.03,
        0.10,
        "Blue: initial-condition variants\nOrange: independent solvers",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.4,
    )
    clean_axis(ax)


def make_figure3() -> tuple[Path, Path]:
    resolved_rows = load_csv(RUNS_DIR / "R014B/resolved_transition_grid.csv")
    band_rows = load_csv(RUNS_DIR / "R014B/transition_band_summary.csv")
    ablation_rows = load_csv(RUNS_DIR / "R009/mechanism_ablation_summary.csv")
    robustness_summary = load_csv(RUNS_DIR / "R010/robustness_summary.csv")
    robustness_rows = load_csv(RUNS_DIR / "R010/robustness_grid.csv")

    fig, axes = plt.subplots(2, 3, figsize=(12.6, 7.2))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.10, top=0.96, wspace=0.48, hspace=0.48)

    plot_endpoint_class(axes[0, 0], resolved_rows, band_rows)
    plot_dpsi_grid(axes[0, 1], resolved_rows, band_rows)
    plot_transition_band(axes[0, 2], band_rows)
    plot_tail_resolution(axes[1, 0])
    plot_ablation(axes[1, 1], ablation_rows)
    plot_robustness(axes[1, 2], robustness_summary, robustness_rows)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure3_phase_synergy.png"
    out_pdf = FIGURES_DIR / "figure3_phase_synergy.pdf"
    fig.savefig(out_png, dpi=600, facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure3()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
