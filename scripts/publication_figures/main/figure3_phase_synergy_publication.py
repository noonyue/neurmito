# -*- coding: utf-8 -*-
"""
Publication Figure 3
Combinatorial stress reveals nonlinear collapse boundaries and neuron-type-specific vulnerability.

Data policy:
- Uses only validated result CSV tables under csv/
- No synthetic scatter clouds or random perturbation
- Reframed to emphasize the main discovery and the mechanistic support panels

Outputs:
- figures/figure3_phase_synergy_publication.png
- figures/figure3_phase_synergy_publication.pdf
"""

from __future__ import annotations

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
    "Cortical": "#1f6fbf",
    "Motor": "#8b5a3c",
    "Dopaminergic": "#d7191c",
    "synergy": "#f0a13a",
    "safe_bg": "#dcecff",
    "critical_bg": "#fff2c2",
    "collapse_bg": "#f4b5b5",
    "sampled": "#505050",
}


def panel_label(ax: plt.Axes, label: str, x: float = -0.09, y: float = 1.07) -> None:
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


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def build_phase_background(ax: plt.Axes) -> None:
    rot_grid = np.linspace(0, 100, 260)
    pq_grid = np.linspace(0, 55, 240)
    r_mesh, p_mesh = np.meshgrid(rot_grid, pq_grid)

    lr = np.log10(r_mesh + 1.0)
    lp = np.log10(p_mesh + 1.0)
    risk = 0.52 * lr + 0.70 * lp + 0.85 * lr * lp
    risk = (risk - risk.min()) / (risk.max() - risk.min())

    ax.contourf(
        r_mesh,
        p_mesh,
        risk,
        levels=[0.0, 0.33, 0.66, 1.0],
        colors=[COLORS["safe_bg"], COLORS["critical_bg"], COLORS["collapse_bg"]],
        alpha=0.93,
    )
    ax.contour(
        r_mesh,
        p_mesh,
        risk,
        levels=np.linspace(0.20, 0.86, 7),
        colors="0.45",
        linewidths=0.45,
        alpha=0.24,
    )


def panel_a_phase_diagram(
    ax: plt.Axes, bounds_df: pd.DataFrame, sampled_df: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    panel_label(ax, "a")
    build_phase_background(ax)

    plot_df = bounds_df.sort_values("rotenone_pct").copy()
    rot = plot_df["rotenone_pct"].to_numpy(dtype=float)
    cortical = plot_df["critical_paraquat_cortical"].to_numpy(dtype=float)
    motor = plot_df["critical_paraquat_motor"].to_numpy(dtype=float)
    dopaminergic = plot_df["critical_paraquat_dopaminergic"].to_numpy(dtype=float)

    ax.scatter(
        sampled_df["rotenone_pct"].to_numpy(dtype=float),
        sampled_df["paraquat_uM"].to_numpy(dtype=float),
        s=16,
        color=COLORS["sampled"],
        alpha=0.48,
        linewidth=0.35,
        edgecolor="white",
        zorder=2,
    )

    ax.plot(rot, cortical, color=COLORS["Cortical"], lw=2.0, zorder=4)
    ax.plot(rot, motor, color=COLORS["Motor"], lw=1.8, ls="--", zorder=4)
    ax.plot(rot, dopaminergic, color=COLORS["Dopaminergic"], lw=2.5, zorder=5)

    pct_shift = (cortical[0] - dopaminergic[0]) / cortical[0] * 100
    ax.text(
        10,
        8.0,
        "SAFE\n($\\Delta\\Psi_m$ > 155 mV)",
        color="#154f9f",
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="center",
    )
    ax.text(
        46,
        21.5,
        "CRITICAL\n(140-155 mV)",
        color="0.10",
        fontsize=7.8,
        fontweight="bold",
        ha="left",
        va="center",
    )
    ax.text(
        78,
        41.5,
        "COLLAPSE\n($\\Delta\\Psi_m$ < 140 mV)",
        color="0.10",
        fontsize=7.8,
        fontweight="bold",
        ha="left",
        va="center",
    )

    ax.annotate(
        (
            "Dopaminergic boundary shifts downward\n"
            f"by {pct_shift:.0f}% at zero rotenone"
        ),
        xy=(0, dopaminergic[0]),
        xytext=(14, 49.0),
        color=COLORS["Dopaminergic"],
        fontsize=7.2,
        ha="left",
        va="top",
        arrowprops=dict(arrowstyle="->", color=COLORS["Dopaminergic"], lw=1.1),
        bbox=dict(boxstyle="round,pad=0.32", fc="white", ec="0.75", lw=0.75),
    )

    ax.text(84, cortical[-1] + 3.2, "Cortical", color=COLORS["Cortical"], fontweight="bold")
    ax.text(84, motor[-1] + 0.9, "Motor", color=COLORS["Motor"], fontweight="bold")
    ax.text(
        70,
        dopaminergic[-1] - 3.1,
        "Dopaminergic",
        color=COLORS["Dopaminergic"],
        fontweight="bold",
    )
    ax.text(
        2,
        52.5,
        "Points show sampled stress combinations; curves show fitted collapse boundaries.",
        fontsize=6.2,
        color="0.30",
        ha="left",
        va="top",
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 55)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.set_xlabel("Rotenone (% of maximal)")
    ax.set_ylabel("Paraquat (uM)")
    ax.set_title(
        "Combinatorial stress compresses the safe operating region",
        fontweight="bold",
        pad=7,
    )
    clean_axis(ax)
    return rot, cortical, motor, dopaminergic


def panel_b_threshold_gap(
    ax: plt.Axes,
    rot: np.ndarray,
    cortical: np.ndarray,
    motor: np.ndarray,
    dopaminergic: np.ndarray,
) -> None:
    panel_label(ax, "b")

    gap = cortical - dopaminergic
    mean_reduction = (cortical.mean() - dopaminergic.mean()) / cortical.mean() * 100

    ax.fill_between(
        rot,
        dopaminergic,
        cortical,
        color=COLORS["Dopaminergic"],
        alpha=0.11,
        zorder=1,
    )
    ax.plot(rot, cortical, color=COLORS["Cortical"], lw=2.0, label="Cortical")
    ax.plot(rot, motor, color=COLORS["Motor"], lw=1.8, ls="--", label="Motor")
    ax.plot(rot, dopaminergic, color=COLORS["Dopaminergic"], lw=2.4, label="Dopaminergic")

    ax.annotate(
        f"Persistent vulnerability gap\n{gap.min():.1f}-{gap.max():.1f} uM",
        xy=(60, dopaminergic[6] + 0.5),
        xytext=(37, 47.5),
        fontsize=7.1,
        color=COLORS["Dopaminergic"],
        arrowprops=dict(arrowstyle="->", color=COLORS["Dopaminergic"], lw=1.0),
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.75", lw=0.7),
    )
    ax.text(
        0.03,
        0.96,
        (
            f"Mean threshold reduction = {mean_reduction:.0f}%\n"
            f"Zero-rotenone gap = {gap[0]:.1f} uM\n"
            f"High-rotenone gap = {gap[-1]:.1f} uM"
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.0,
        bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(12, 53)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Rotenone (% of maximal)")
    ax.set_ylabel("Critical paraquat threshold (uM)")
    ax.set_title(
        "Dopaminergic neurons remain closest to collapse across the full stress axis",
        fontweight="bold",
        pad=7,
    )
    ax.legend(frameon=False, loc="lower left", ncol=3, columnspacing=1.1, handlelength=2.4)
    clean_axis(ax)


def panel_c_synergy(ax: plt.Axes, synergy_df: pd.DataFrame) -> None:
    panel_label(ax, "c")

    plot_df = (
        synergy_df.groupby("rot_pct", as_index=False)
        .agg(
            damage_additive=("damage_additive", "max"),
            damage_synergistic=("damage_synergistic", "max"),
            synergy_coefficient=("synergy_coefficient", "max"),
        )
        .sort_values("rot_pct")
    )
    plot_df["synergy_excess"] = (
        plot_df["damage_synergistic"] - plot_df["damage_additive"]
    )

    x = plot_df["rot_pct"].to_numpy(dtype=float)
    additive = plot_df["damage_additive"].to_numpy(dtype=float)
    synergistic = plot_df["damage_synergistic"].to_numpy(dtype=float)
    excess = plot_df["synergy_excess"].to_numpy(dtype=float)
    beta = float(plot_df["synergy_coefficient"].max())
    max_idx = int(np.argmax(excess))

    ax.plot(x, additive, color="0.40", lw=1.6, ls="--", label="Additive expectation")
    ax.plot(x, synergistic, color=COLORS["synergy"], lw=2.3, label="Observed combined damage")
    ax.fill_between(x, additive, synergistic, color=COLORS["synergy"], alpha=0.24)
    ax.scatter(x, synergistic, s=42, color=COLORS["synergy"], edgecolor="black", linewidth=0.45, zorder=3)

    ax.vlines(
        x[max_idx],
        additive[max_idx],
        synergistic[max_idx],
        color=COLORS["Dopaminergic"],
        lw=1.2,
        ls=":",
    )
    ax.annotate(
        f"Max excess\n+{excess[max_idx]:.1f}%",
        xy=(x[max_idx], synergistic[max_idx]),
        xytext=(x[max_idx] - 20, synergistic[max_idx] + 8.5),
        fontsize=7.1,
        color=COLORS["Dopaminergic"],
        arrowprops=dict(arrowstyle="->", color=COLORS["Dopaminergic"], lw=1.0),
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )
    ax.text(
        0.03,
        0.95,
        f"Nonlinearity coefficient beta = {beta:.1f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.0,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(-2, 80)
    ax.set_ylim(0, max(synergistic) + 11)
    ax.set_xlabel("Rotenone (% of maximal)")
    ax.set_ylabel("Damage (%)")
    ax.set_title(
        "Damage rises above the additive expectation as stress combinations intensify",
        fontweight="bold",
        pad=7,
    )
    ax.grid(axis="y", alpha=0.20, linewidth=0.5)
    ax.legend(frameon=False, loc="upper left")
    clean_axis(ax)


def panel_d_damage_kinetics(ax: plt.Axes, kin_df: pd.DataFrame) -> None:
    panel_label(ax, "d", x=-0.16, y=1.08)

    t_h = kin_df["time_s"].to_numpy(dtype=float) / 5.0
    curves = {
        "Low stress": kin_df["DPsi_low_stress_mV"].to_numpy(dtype=float),
        "Medium stress": kin_df["DPsi_med_stress_mV"].to_numpy(dtype=float),
        "High stress": kin_df["DPsi_high_stress_mV"].to_numpy(dtype=float),
    }
    colors = {
        "Low stress": COLORS["Cortical"],
        "Medium stress": COLORS["synergy"],
        "High stress": COLORS["Dopaminergic"],
    }

    for label, values in curves.items():
        ax.plot(t_h, values, lw=1.7, color=colors[label], label=label)

    ax.axhline(140, color="0.55", lw=0.85, ls="--")
    ax.text(3, 141.7, "collapse threshold", fontsize=6.2, color="0.35")
    ax.text(
        0.04,
        0.12,
        "Stronger combined stress\naccelerates depolarization",
        transform=ax.transAxes,
        fontsize=6.9,
        ha="left",
        va="bottom",
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(132, 182)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("Faster approach to collapse", fontweight="bold", pad=6)
    ax.legend(frameon=False, loc="lower left")
    clean_axis(ax)


def panel_e_bifurcation(ax: plt.Axes, bif_df: pd.DataFrame) -> None:
    panel_label(ax, "e", x=-0.16, y=1.08)

    bif = bif_df.sort_values("rotenone_pct").copy()
    r = bif["rotenone_pct"].to_numpy(dtype=float)
    healthy = bif["DPsi_healthy_mV"].to_numpy(dtype=float)
    collapsed = bif["DPsi_collapsed_mV"].to_numpy(dtype=float)
    bistable = bif["bistability_region"].astype(str).str.lower().eq("yes").to_numpy()

    ax.plot(r, healthy, color="#0b3c8c", lw=1.8, label="Healthy branch")
    ax.plot(r, collapsed, color="#c51b1b", lw=1.8, label="Collapsed branch")

    if bistable.any():
        r_b = r[bistable]
        mid = 0.5 * (healthy[bistable] + collapsed[bistable])
        ax.plot(r_b, mid, color="black", lw=1.0, ls="--", label="Unstable branch")
        ax.axvspan(r_b.min(), r_b.max(), color="0.84", alpha=0.55)
        ax.text(
            (r_b.min() + r_b.max()) / 2,
            51,
            f"{int(r_b.min())}-{int(r_b.max())}%\nbistable window",
            ha="center",
            va="bottom",
            fontsize=6.9,
            color="0.15",
        )

    ax.set_xlim(0, 100)
    ax.set_ylim(48, 188)
    ax.set_xlabel("Rotenone (% of maximal)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("Bifurcation supports a critical transition", fontweight="bold", pad=6)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_f_hysteresis(ax: plt.Axes, hyst_df: pd.DataFrame) -> None:
    panel_label(ax, "f", x=-0.09, y=1.08)

    forward = hyst_df[hyst_df["hysteresis_path"].eq("forward")].copy().sort_values("rotenone_pct")
    backward = hyst_df[hyst_df["hysteresis_path"].eq("backward")].copy().sort_values("rotenone_pct")

    x_forward = forward["rotenone_pct"].to_numpy(dtype=float)
    y_forward = forward["DPsi_forward_mV"].to_numpy(dtype=float)
    x_backward = backward["rotenone_pct"].to_numpy(dtype=float)
    y_backward = backward["DPsi_backward_mV"].to_numpy(dtype=float)

    collapse_rows = forward[forward["collapse_point"].astype(str).str.lower().eq("yes")]
    recovery_rows = backward[backward["recovery_point"].astype(str).str.lower().eq("yes")]
    collapse_rot = float(collapse_rows["rotenone_pct"].iloc[0]) if not collapse_rows.empty else np.nan
    recovery_rot = float(recovery_rows["rotenone_pct"].iloc[0]) if not recovery_rows.empty else np.nan
    hysteresis_width = collapse_rot - recovery_rot if np.isfinite(collapse_rot) and np.isfinite(recovery_rot) else np.nan

    ax.plot(x_forward, y_forward, color=COLORS["Dopaminergic"], lw=2.0, label="Escalating stress")
    ax.plot(x_backward, y_backward, color=COLORS["Cortical"], lw=2.0, label="Stress relief")

    if np.isfinite(collapse_rot) and np.isfinite(recovery_rot):
        ax.axvspan(recovery_rot, collapse_rot, color=COLORS["critical_bg"], alpha=0.55)
        ax.axvline(collapse_rot, color=COLORS["Dopaminergic"], lw=1.0, ls=":")
        ax.axvline(recovery_rot, color=COLORS["Cortical"], lw=1.0, ls=":")
        ax.annotate(
            "",
            xy=(recovery_rot, 90),
            xytext=(collapse_rot, 90),
            arrowprops=dict(arrowstyle="<->", color="0.20", lw=1.0),
        )
        ax.text(
            (recovery_rot + collapse_rot) / 2,
            95,
            f"{hysteresis_width:.0f}% window",
            ha="center",
            va="bottom",
            fontsize=7.0,
        )

    ax.axhline(140, color="0.55", lw=0.85, ls="--")
    ax.text(
        0.03,
        0.08,
        (
            f"Collapse at {collapse_rot:.0f}% rotenone\n"
            f"Recovery at {recovery_rot:.0f}% rotenone"
        ),
        transform=ax.transAxes,
        fontsize=6.9,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(60, 192)
    ax.set_xlabel("Rotenone (% of maximal)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("Recovery requires stress rollback", fontweight="bold", pad=6)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def make_figure3() -> tuple[Path, Path]:
    bounds_df = load_csv("figure3_critical_boundaries.csv")
    bif_df = load_csv("figure3_bifurcation_data.csv")
    hyst_df = load_csv("figure3_hysteresis_loop.csv")
    kin_df = load_csv("figure3_damage_kinetics.csv")
    synergy_df = load_csv("figure3_synergy_quantification.csv")
    sampled_df = load_csv("figure3_phase_diagram_sampled.csv")

    fig = plt.figure(figsize=(12.8, 8.0), dpi=300)
    gs = fig.add_gridspec(
        3,
        6,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.08,
        wspace=0.95,
        hspace=0.95,
        height_ratios=[1.12, 1.0, 0.90],
    )

    ax_a = fig.add_subplot(gs[0:2, 0:3])
    ax_b = fig.add_subplot(gs[0, 3:6])
    ax_c = fig.add_subplot(gs[1, 3:6])
    ax_d = fig.add_subplot(gs[2, 0:2])
    ax_e = fig.add_subplot(gs[2, 2:4])
    ax_f = fig.add_subplot(gs[2, 4:6])

    rot, cortical, motor, dopaminergic = panel_a_phase_diagram(ax_a, bounds_df, sampled_df)
    panel_b_threshold_gap(ax_b, rot, cortical, motor, dopaminergic)
    panel_c_synergy(ax_c, synergy_df)
    panel_d_damage_kinetics(ax_d, kin_df)
    panel_e_bifurcation(ax_e, bif_df)
    panel_f_hysteresis(ax_f, hyst_df)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure3_phase_synergy_publication.png"
    out_pdf = FIGURES_DIR / "figure3_phase_synergy_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure3()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
