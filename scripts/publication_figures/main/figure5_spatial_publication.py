# -*- coding: utf-8 -*-
"""
Publication Figure 5
Spatial heterogeneity along dopaminergic axons creates a distal-first collapse trajectory.

Data policy:
- Uses only validated project result tables under csv/
- Reframed around the main spatial degeneration result
- Keeps only data-supported summaries of spatial gradients and distal vulnerability

Outputs:
- figures/figure5_spatial_publication.png
- figures/figure5_spatial_publication.pdf
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyBboxPatch


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
    "proximal": "#355fb3",
    "distal": "#cf2e3c",
    "density": "#7a52b3",
    "atp": "#449648",
    "ros": "#d9822b",
    "vulnerability": "#a11d33",
    "axon": "#c7a0da",
    "safe": "#dcecff",
    "warning": "#fff2c2",
    "critical": "#f4b5b5",
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


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    fc: str = "white",
    ec: str = "0.6",
    lw: float = 0.8,
    radius: float = 0.03,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        fc=fc,
        ec=ec,
        lw=lw,
    )
    ax.add_patch(patch)
    return patch


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def load_vulnerability_regions() -> pd.DataFrame:
    path = CSV_DIR / "figure5_vulnerability_regions.csv"
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)
        for parts in reader:
            if not parts:
                continue
            rows.append(
                {
                    "region": parts[0],
                    "axonal_distance_um": float(parts[1]),
                    "vulnerability_score": float(parts[2]),
                }
            )
    return pd.DataFrame(rows)


def normalize(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    span = arr.max() - arr.min()
    if span == 0:
        return np.full_like(arr, 0.5)
    return (arr - arr.min()) / span


def first_threshold_time(time_s: np.ndarray, dpsi_mV: np.ndarray, threshold: float = 140.0) -> float:
    mask = dpsi_mV <= threshold
    if not np.any(mask):
        return float("nan")
    return float(time_s[np.argmax(mask)])


def panel_a_schematic(ax: plt.Axes, spatial_df: pd.DataFrame, vuln_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.50, 0.97, "Spatial axon model", ha="center", va="top", fontsize=8.3, fontweight="bold")
    ax.text(
        0.50,
        0.89,
        "A 1,000 um dopaminergic axon develops distal vulnerability as metabolic support declines.",
        ha="center",
        va="top",
        fontsize=6.4,
    )

    soma_center = (0.12, 0.58)
    ax.add_patch(Circle(soma_center, 0.060, fc="#c8a5d8", ec="#8e63aa", lw=1.0))
    ax.add_patch(Circle(soma_center, 0.020, fc="#6f3c8c", ec="none"))
    ax.plot([0.19, 0.86], [0.58, 0.58], color=COLORS["axon"], lw=10, solid_capstyle="round")
    ax.plot([0.19, 0.86], [0.58, 0.58], color="#936bb1", lw=1.0)
    ax.plot([0.86, 0.93], [0.58, 0.58], color="#e46c73", lw=4, solid_capstyle="round")
    for dy in [-0.10, -0.04, 0.05, 0.11]:
        ax.plot([0.93, 0.97], [0.58, 0.58 + dy], color="#e46c73", lw=1.8)
        ax.add_patch(Circle((0.97, 0.58 + dy), 0.008, fc="#e46c73", ec="none"))

    x_profile = spatial_df["axonal_distance_um"].to_numpy(dtype=float)
    density = spatial_df["mitochondrial_density"].to_numpy(dtype=float)
    for x_um, dens in zip(x_profile, density):
        x_ax = 0.20 + 0.64 * (x_um / 1000.0)
        size = 0.014 + 0.018 * (dens / density.max())
        ax.add_patch(Circle((x_ax, 0.58), size, fc="#dbc1e6", ec="#8e63aa", lw=0.7, alpha=0.92))

    for row in vuln_df.itertuples(index=False):
        x_ax = 0.20 + 0.64 * (float(row.axonal_distance_um) / 1000.0)
        ax.scatter(
            x_ax,
            0.79,
            s=26 + 68 * float(row.vulnerability_score),
            color=plt.cm.Reds(0.20 + 0.70 * float(row.vulnerability_score)),
            edgecolor="0.25",
            linewidth=0.5,
        )
        ax.plot([x_ax, x_ax], [0.68, 0.74], color="0.45", lw=0.6, ls=":")

    ax.text(0.03, 0.77, "Soma", fontsize=6.8)
    ax.text(0.20, 0.77, "Proximal", fontsize=6.8, color=COLORS["proximal"], fontweight="bold")
    ax.text(0.82, 0.77, "Distal", fontsize=6.8, color=COLORS["distal"], fontweight="bold")

    rounded_box(ax, 0.07, 0.11, 0.86, 0.22, fc="white", ec="#b99bd2", lw=0.9, radius=0.025)
    ax.text(0.21, 0.26, "Measured gradient", fontsize=6.5, fontweight="bold", ha="center")
    ax.text(0.21, 0.17, "mitochondrial density\nfalls distally", fontsize=6.1, ha="center")
    ax.text(0.50, 0.26, "Profile outputs", fontsize=6.5, fontweight="bold", ha="center")
    ax.text(0.50, 0.17, "DPsi, ATP, ROS\nalong the axon", fontsize=6.1, ha="center")
    ax.text(0.79, 0.26, "Predicted outcome", fontsize=6.5, fontweight="bold", ha="center")
    ax.text(0.79, 0.17, "distal-first collapse\nunder stress", fontsize=6.1, ha="center")


def panel_b_density_vulnerability(ax: plt.Axes, spatial_df: pd.DataFrame) -> None:
    panel_label(ax, "b")

    x = spatial_df["axonal_distance_um"].to_numpy(dtype=float)
    density = spatial_df["mitochondrial_density"].to_numpy(dtype=float)
    vulnerability = spatial_df["vulnerability_score"].to_numpy(dtype=float)

    ax.plot(x, density, color=COLORS["density"], lw=1.9, marker="o", ms=3.4, label="Density")
    ax.fill_between(x, density, density.min() - 0.03, color=COLORS["density"], alpha=0.10)

    ax2 = ax.twinx()
    ax2.plot(x, vulnerability, color=COLORS["vulnerability"], lw=1.8, marker="o", ms=3.2, label="Vulnerability")
    ax2.fill_between(x, 0, vulnerability, color=COLORS["vulnerability"], alpha=0.06)
    ax2.spines["top"].set_visible(False)

    drop_pct = (density[0] - density[-1]) / density[0] * 100
    vuln_delta = vulnerability[-1] - vulnerability[0]
    ax.text(
        0.04,
        0.96,
        f"Density: -{drop_pct:.0f}%\nVulnerability: +{vuln_delta:.2f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.9,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, 1000)
    ax.set_xlabel("Axon position (um)")
    ax.set_ylabel("Mitochondrial density", color=COLORS["density"])
    ax.tick_params(axis="y", colors=COLORS["density"])
    ax2.set_ylabel("Vulnerability score", color=COLORS["vulnerability"])
    ax2.tick_params(axis="y", colors=COLORS["vulnerability"])
    ax.set_title("Structural support falls while vulnerability rises toward the distal axon", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_c_profiles(ax: plt.Axes, spatial_df: pd.DataFrame) -> None:
    panel_label(ax, "c")

    x = spatial_df["axonal_distance_um"].to_numpy(dtype=float)
    dpsi = spatial_df["DPsi_mV"].to_numpy(dtype=float)
    atp = spatial_df["ATP_mM"].to_numpy(dtype=float)
    ros = spatial_df["ROS_uM"].to_numpy(dtype=float)

    ax.plot(x, normalize(dpsi), color=COLORS["proximal"], lw=1.8, marker="o", ms=3.3, label="DPsi")
    ax.plot(x, normalize(atp), color=COLORS["atp"], lw=1.8, marker="s", ms=3.3, label="ATP")
    ax.plot(x, normalize(ros), color=COLORS["ros"], lw=1.8, marker="D", ms=3.3, label="ROS")

    dpsi_drop = dpsi[0] - dpsi[-1]
    atp_drop = (atp[0] - atp[-1]) / atp[0] * 100
    ros_rise = (ros[-1] - ros[0]) / ros[0] * 100
    ax.text(
        0.04,
        0.96,
        f"Distal change:\nDPsi -{dpsi_drop:.0f} mV\nATP -{atp_drop:.0f}%\nROS +{ros_rise:.0f}%",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.9,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, 1000)
    ax.set_ylim(-0.04, 1.04)
    ax.set_xlabel("Axon position (um)")
    ax.set_ylabel("Normalized profile")
    ax.set_title("Distal bioenergetics weaken while oxidative stress rises", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="lower left")
    clean_axis(ax)


def panel_d_damage(ax: plt.Axes, damage_df: pd.DataFrame, distal_time: float, proximal_time: float) -> None:
    panel_label(ax, "d")

    time_s = damage_df["time_s"].to_numpy(dtype=float)
    time_min = time_s / 60.0
    prox = damage_df["DPsi_proximal_mV"].to_numpy(dtype=float)
    dist = damage_df["DPsi_distal_mV"].to_numpy(dtype=float)

    ax.plot(time_min, prox, color=COLORS["proximal"], lw=2.0, marker="o", ms=4.0, label="Proximal")
    ax.plot(time_min, dist, color=COLORS["distal"], lw=2.0, marker="o", ms=4.0, label="Distal")
    ax.axhline(140, color="0.55", lw=0.9, ls="--")
    ax.axvline(distal_time / 60.0, color=COLORS["distal"], lw=1.0, ls=":")
    ax.axvline(proximal_time / 60.0, color=COLORS["proximal"], lw=1.0, ls=":")
    ax.annotate(
        "",
        xy=(distal_time / 60.0, 94),
        xytext=(proximal_time / 60.0, 94),
        arrowprops=dict(arrowstyle="<->", color="0.20", lw=1.0),
    )
    ax.text(
        (distal_time + proximal_time) / 120.0,
        98,
        f"{proximal_time - distal_time:.0f} s lead",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color=COLORS["distal"],
        fontweight="bold",
    )
    ax.text(
        0.04,
        0.08,
        f"Distal collapse at {distal_time:.0f} s\nProximal collapse at {proximal_time:.0f} s",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.9,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0, time_min.max())
    ax.set_ylim(82, 184)
    ax.set_xlabel("Time (min)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("Under stress, the distal axon reaches collapse first", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_e_threshold_timing(ax: plt.Axes, distal_time: float, proximal_time: float) -> None:
    panel_label(ax, "e")

    labels = ["Distal", "Proximal"]
    times = np.array([distal_time, proximal_time], dtype=float)
    colors = [COLORS["distal"], COLORS["proximal"]]
    xpos = np.arange(len(labels))
    ax.bar(xpos, times, width=0.56, color=colors, alpha=0.84)
    ax.plot([0, 1], [times[0], times[1]], color="0.40", lw=1.0, ls="--")

    for i, value in enumerate(times):
        ax.text(i, value + 5, f"{value:.0f}s", ha="center", fontsize=6.9, fontweight="bold")

    ax.text(
        0.50,
        0.95,
        "Distal-first transition",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.1,
        color=COLORS["distal"],
        fontweight="bold",
    )
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Time to threshold crossing (s)")
    ax.set_title(r"First time $\Delta\Psi_m \leq 140$ mV", fontweight="bold", pad=7)
    ax.set_ylim(0, max(times) + 35)
    clean_axis(ax)


def panel_f_summary(ax: plt.Axes, spatial_df: pd.DataFrame, distal_time: float, proximal_time: float) -> None:
    panel_label(ax, "f")

    prox = spatial_df.iloc[0]
    dist = spatial_df.iloc[-1]
    changes = pd.DataFrame(
        {
            "metric": ["Density", "DPsi", "ATP", "ROS", "Vulnerability", "Collapse time"],
            "change_pct": [
                (float(dist["mitochondrial_density"]) / float(prox["mitochondrial_density"]) - 1.0) * 100,
                (float(dist["DPsi_mV"]) / float(prox["DPsi_mV"]) - 1.0) * 100,
                (float(dist["ATP_mM"]) / float(prox["ATP_mM"]) - 1.0) * 100,
                (float(dist["ROS_uM"]) / float(prox["ROS_uM"]) - 1.0) * 100,
                (float(dist["vulnerability_score"]) / float(prox["vulnerability_score"]) - 1.0) * 100,
                (distal_time / proximal_time - 1.0) * 100,
            ],
        }
    )

    colors = [
        COLORS["proximal"] if value < 0 else COLORS["distal"]
        for value in changes["change_pct"].to_numpy(dtype=float)
    ]
    y = np.arange(len(changes))
    vals = changes["change_pct"].to_numpy(dtype=float)

    ax.axvline(0, color="0.50", lw=0.9)
    ax.barh(y, vals, color=colors, alpha=0.84, edgecolor="0.25", height=0.60)
    for yi, value in zip(y, vals):
        ax.text(
            value + (3 if value >= 0 else -3),
            yi,
            f"{value:+.0f}%",
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=6.8,
            fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(changes["metric"])
    ax.invert_yaxis()
    ax.set_xlim(-45, 380)
    ax.set_xlabel("Distal change relative to the proximal segment (%)")
    ax.set_title("The distal axon simultaneously loses support and gains risk", fontweight="bold", pad=7)
    clean_axis(ax)


def make_figure5() -> tuple[Path, Path]:
    spatial_df = load_csv("figure5_spatial_profiles.csv")
    damage_df = load_csv("figure5_damage_propagation.csv")
    vuln_df = load_vulnerability_regions()

    proximal_time = first_threshold_time(
        damage_df["time_s"].to_numpy(dtype=float),
        damage_df["DPsi_proximal_mV"].to_numpy(dtype=float),
    )
    distal_time = first_threshold_time(
        damage_df["time_s"].to_numpy(dtype=float),
        damage_df["DPsi_distal_mV"].to_numpy(dtype=float),
    )

    fig = plt.figure(figsize=(12.8, 7.9), dpi=300)
    gs = fig.add_gridspec(
        2,
        6,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.10,
        wspace=0.88,
        hspace=0.72,
        height_ratios=[1.0, 0.96],
    )

    ax_a = fig.add_subplot(gs[0, 0:2])
    ax_b = fig.add_subplot(gs[0, 2:4])
    ax_c = fig.add_subplot(gs[0, 4:6])
    ax_d = fig.add_subplot(gs[1, 0:3])
    ax_e = fig.add_subplot(gs[1, 3:4])
    ax_f = fig.add_subplot(gs[1, 4:6])

    panel_a_schematic(ax_a, spatial_df, vuln_df)
    panel_b_density_vulnerability(ax_b, spatial_df)
    panel_c_profiles(ax_c, spatial_df)
    panel_d_damage(ax_d, damage_df, distal_time, proximal_time)
    panel_e_threshold_timing(ax_e, distal_time, proximal_time)
    panel_f_summary(ax_f, spatial_df, distal_time, proximal_time)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure5_spatial_publication.png"
    out_pdf = FIGURES_DIR / "figure5_spatial_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure5()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
