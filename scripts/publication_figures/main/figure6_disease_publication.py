# -*- coding: utf-8 -*-
"""
Legacy exploratory Figure 6 renderer.

The CSV inputs used here are fixed disease scenarios without a source-audited
measurement-to-parameter mapping or held-out external benchmark.  Do not use
this renderer for scientific interpretation; use
``figure6_disease_verified.py`` via ``module5.figure6_disease_applications``.

Data policy:
- Uses legacy project scenario tables under csv/
- Does not establish external consistency, clinical efficacy, or intervention
  windows

Outputs:
- figures/figure6_disease_publication.png
- figures/figure6_disease_publication.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle


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
    "PD": "#2171b5",
    "AD": "#756bb1",
    "ALS": "#e6550d",
    "WT": "#31a354",
    "combined": "#d7191c",
    "control": "#9a9a9a",
    "ews": "#cf2e3c",
    "atp": "#3f8f3f",
    "ca": "#756bb1",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


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


def first_threshold(values: np.ndarray, time_s: np.ndarray, threshold: float, direction: str) -> float:
    arr = np.asarray(values, dtype=float)
    time_arr = np.asarray(time_s, dtype=float)
    if direction == "below":
        mask = arr <= threshold
    else:
        mask = arr >= threshold
    if not np.any(mask):
        return float("nan")
    return float(time_arr[np.argmax(mask)])


def pd_state_spans(df: pd.DataFrame) -> list[tuple[float, float, str]]:
    x = df["time_s"].to_numpy(dtype=float) / 60.0
    labels = df["intervention_status"].astype(str).to_numpy()
    if len(x) < 2:
        return []
    boundaries = np.empty(len(x) + 1)
    boundaries[1:-1] = 0.5 * (x[:-1] + x[1:])
    boundaries[0] = x[0] - 0.5 * (x[1] - x[0])
    boundaries[-1] = x[-1] + 0.5 * (x[-1] - x[-2])
    spans: list[tuple[float, float, str]] = []
    start = 0
    for idx in range(1, len(labels) + 1):
        if idx == len(labels) or labels[idx] != labels[start]:
            spans.append((boundaries[start], boundaries[idx], labels[start]))
            start = idx
    return spans


def add_pd_spans(ax: plt.Axes, spans: list[tuple[float, float, str]]) -> None:
    colors = {
        "no_intervention": "#d9f0d1",
        "early_warning": "#fff0b8",
        "intervention_window": "#f6bbb2",
        "critical": "#efc6c6",
        "collapsed": "#efefef",
    }
    for left, right, label in spans:
        ax.axvspan(left, right, color=colors.get(label, "#f3f3f3"), alpha=0.42, lw=0)


def impairment_matrix(multi_df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    diseases = ["PD", "AD", "ALS"]
    mechs = ["Complex I", "ROS", "Ca buffering", "Axonal transport"]
    values = []
    for disease in diseases:
        row = multi_df.loc[multi_df["disease"].eq(disease)].iloc[0]
        values.append(
            [
                1.0 - float(row["complex_I_activity"]),
                float(row["ROS_production"]) - 1.0,
                1.0 - float(row["Ca_buffering"]),
                1.0 - float(row["axonal_transport"]),
            ]
        )
    return np.array(values, dtype=float), diseases, mechs


def panel_a_fingerprint(ax: plt.Axes, multi_df: pd.DataFrame) -> None:
    panel_label(ax, "a")

    matrix, diseases, mechs = impairment_matrix(multi_df)
    im = ax.imshow(matrix, cmap="Reds", vmin=0.0, vmax=0.55, aspect="auto")

    for i in range(matrix.shape[0]):
        max_idx = int(np.argmax(matrix[i]))
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                color="white" if value > 0.30 else "black",
                fontsize=7.0,
                fontweight="bold" if j == max_idx else "normal",
            )
        ax.add_patch(Rectangle((max_idx - 0.5, i - 0.5), 1, 1, fill=False, ec="white", lw=1.4))

    ax.set_xticks(np.arange(len(mechs)))
    ax.set_xticklabels(mechs)
    ax.set_yticks(np.arange(len(diseases)))
    ax.set_yticklabels(diseases)
    ax.set_title(
        "Each disease reaches mitochondrial criticality through a different dominant mechanism",
        fontweight="bold",
        pad=7,
    )
    ax.text(
        0.99,
        -0.22,
        "Higher values indicate stronger deviation from the control baseline.",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.2,
        color="0.35",
    )
    clean_axis(ax)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)


def panel_b_pd(ax: plt.Axes, pd_df: pd.DataFrame, pd_collapse_s: float, trigger_s: float) -> None:
    panel_label(ax, "b")

    t_min = pd_df["time_s"].to_numpy(dtype=float) / 60.0
    dpsi = pd_df["DPsi_mV"].to_numpy(dtype=float)
    ews = pd_df["EWS_score"].to_numpy(dtype=float)

    spans = pd_state_spans(pd_df)
    add_pd_spans(ax, spans)
    ax.plot(t_min, dpsi, color=COLORS["PD"], lw=2.0, marker="o", ms=3.8, label="DPsi")
    ax.axhline(140, color="0.55", lw=0.9, ls=":")
    ax.axvline(trigger_s / 60.0, color=COLORS["ews"], lw=1.0, ls="--")
    ax.axvline(pd_collapse_s / 60.0, color="0.25", lw=1.0, ls="--")

    ax2 = ax.twinx()
    ax2.plot(t_min, ews, color=COLORS["ews"], lw=1.6, ls="--", marker="s", ms=3.4, label="EWS")
    ax2.axhline(0.70, color=COLORS["ews"], lw=0.9, ls=":")
    ax2.spines["top"].set_visible(False)

    ax.annotate(
        "",
        xy=(trigger_s / 60.0, 176),
        xytext=(pd_collapse_s / 60.0, 176),
        arrowprops=dict(arrowstyle="<->", color=COLORS["ews"], lw=1.0),
    )
    ax.text(
        (trigger_s + pd_collapse_s) / 120.0,
        177.3,
        f"{pd_collapse_s - trigger_s:.0f} s warning lead",
        color=COLORS["ews"],
        fontsize=7.0,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    ax.text(
        0.03,
        0.06,
        f"EWS >= 0.7 at {trigger_s/60.0:.2f} min\nCollapse at {pd_collapse_s/60.0:.2f} min",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlabel("Time (min)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)", color=COLORS["PD"])
    ax.tick_params(axis="y", colors=COLORS["PD"])
    ax2.set_ylabel("EWS score", color=COLORS["ews"])
    ax2.tick_params(axis="y", colors=COLORS["ews"])
    ax.set_title("PD: the early-warning signal enters the actionable window just before collapse", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_c_ad(ax: plt.Axes, ad_df: pd.DataFrame, atp_failure_s: float, ca_overload_s: float) -> None:
    panel_label(ax, "c")

    t_min = ad_df["time_s"].to_numpy(dtype=float) / 60.0
    atp = ad_df["ATP_mM"].to_numpy(dtype=float)
    ca_nM = ad_df["Ca_uM"].to_numpy(dtype=float) * 1000.0

    ax.plot(t_min, atp, color=COLORS["atp"], lw=2.0, marker="o", ms=3.8)
    ax.axhline(3.0, color=COLORS["atp"], lw=0.9, ls=":")
    ax.axvline(atp_failure_s / 60.0, color=COLORS["atp"], lw=1.0, ls="--")

    ax2 = ax.twinx()
    ax2.plot(t_min, ca_nM, color=COLORS["ca"], lw=1.8, ls="--", marker="s", ms=3.4)
    ax2.axhline(500, color=COLORS["ca"], lw=0.9, ls=":")
    ax2.axvline(ca_overload_s / 60.0, color=COLORS["ca"], lw=1.0, ls="--")
    ax2.spines["top"].set_visible(False)

    ax.annotate(
        "",
        xy=(ca_overload_s / 60.0, 4.88),
        xytext=(atp_failure_s / 60.0, 4.88),
        arrowprops=dict(arrowstyle="<->", color=COLORS["ca"], lw=1.0),
    )
    ax.text(
        (ca_overload_s + atp_failure_s) / 120.0,
        4.93,
        f"{atp_failure_s - ca_overload_s:.0f} s gap",
        color=COLORS["ca"],
        fontsize=7.0,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    ax.text(
        0.03,
        0.06,
        f"Ca >= 500 nM at {ca_overload_s/60.0:.2f} min\nATP <= 3 mM at {atp_failure_s/60.0:.2f} min",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlabel("Time (min)")
    ax.set_ylabel("ATP (mM)", color=COLORS["atp"])
    ax.tick_params(axis="y", colors=COLORS["atp"])
    ax2.set_ylabel(r"Ca$^{2+}$ (nM)", color=COLORS["ca"])
    ax2.tick_params(axis="y", colors=COLORS["ca"])
    ax.set_title("AD: calcium overload appears before ATP failure is complete", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_d_als(ax: plt.Axes, als_df: pd.DataFrame, combined_collapse_s: float) -> None:
    panel_label(ax, "d")

    t_min = als_df["time_s"].to_numpy(dtype=float) / 60.0
    wt = als_df["DPsi_WT_mV"].to_numpy(dtype=float)
    transport = als_df["DPsi_transport_failure_mV"].to_numpy(dtype=float)
    sod1 = als_df["DPsi_SOD1_mV"].to_numpy(dtype=float)
    combined = als_df["DPsi_combined_mV"].to_numpy(dtype=float)

    ax.plot(t_min, wt, color=COLORS["WT"], lw=1.8, label="WT")
    ax.plot(t_min, transport, color=COLORS["ALS"], lw=1.6, ls="--", label="Transport failure")
    ax.plot(t_min, sod1, color=COLORS["AD"], lw=1.6, ls=":", label="SOD1")
    ax.plot(t_min, combined, color=COLORS["combined"], lw=2.2, marker="D", ms=3.6, label="Combined")
    ax.axhline(140, color="0.55", lw=0.9, ls=":")
    ax.axvline(combined_collapse_s / 60.0, color=COLORS["combined"], lw=1.0, ls="--")
    ax.text(
        0.03,
        0.06,
        f"Combined collapse at {combined_collapse_s/60.0:.2f} min\nSingle-hit collapse at 2.00 min",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlabel("Time (min)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("ALS: combined insults outrun either single-hit trajectory", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_e_pd_window(ax: plt.Axes, pd_int_df: pd.DataFrame) -> None:
    panel_label(ax, "e")

    inhibit = pd_int_df["inhibition_pct"].to_numpy(dtype=float)
    success = pd_int_df["intervention_success_rate"].to_numpy(dtype=float)
    ax.plot(inhibit, success, color=COLORS["PD"], lw=2.0, marker="o", ms=3.8)
    ax.axvspan(25, 35, color="#d9f0d1", alpha=0.65)
    ax.axvline(40, color="0.50", lw=0.9, ls=":")
    ax.text(
        30,
        94,
        "Optimal window\n25-35%",
        ha="center",
        va="top",
        fontsize=7.0,
        color="#2c7c31",
        fontweight="bold",
    )
    ax.text(
        0.03,
        0.07,
        "Success drops sharply once intervention starts after 40% inhibition.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.7,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(8, 82)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Complex I inhibition at intervention (%)")
    ax.set_ylabel("Intervention success (%)")
    ax.set_title("PD: therapeutic success depends on a narrow inhibition window", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_f_ad_treatment(ax: plt.Axes, blocker_df: pd.DataFrame, vuln_df: pd.DataFrame) -> None:
    panel_label(ax, "f")

    t_min = blocker_df["treatment_time_s"].to_numpy(dtype=float) / 60.0
    eff = blocker_df["calcium_blocker_efficacy"].to_numpy(dtype=float)
    ax.plot(t_min, eff, color=COLORS["AD"], lw=2.0, marker="o", ms=3.8)
    ax.fill_between(t_min, eff, 0, color=COLORS["AD"], alpha=0.06)
    ax.text(
        0.03,
        0.93,
        f"Efficacy falls from {eff[0]:.0f}% to {eff[-1]:.0f}%\nwithin {t_min[-1]:.2f} min.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    inset = ax.inset_axes([0.56, 0.16, 0.40, 0.58])
    plot_df = vuln_df.iloc[::-1].copy().reset_index(drop=True)
    vals = plot_df["vulnerability_score"].to_numpy(dtype=float)
    colors = [
        "#31a354" if v < 0.4 else "#f0b429" if v < 0.6 else "#e6550d" if v < 0.8 else "#d7191c"
        for v in vals
    ]
    ypos = np.arange(len(plot_df))
    inset.barh(ypos, vals, color=colors, edgecolor="white", height=0.55)
    inset.set_yticks(ypos)
    inset.set_yticklabels(plot_df["region"])
    inset.set_xlim(0, 1.0)
    inset.set_title("Regional risk", fontsize=6.4, pad=3)
    inset.tick_params(labelsize=5.8)
    inset.spines["top"].set_visible(False)
    inset.spines["right"].set_visible(False)
    inset.spines["left"].set_visible(False)
    inset.grid(axis="x", alpha=0.12, linewidth=0.4)
    inset.text(0.87, 0.90, "CA1", transform=inset.transAxes, fontsize=5.8, color="#d7191c", fontweight="bold")

    ax.set_xlim(-0.05, max(t_min) + 0.15)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Time from onset (min)")
    ax.set_ylabel("Blocker efficacy (%)")
    ax.set_title("AD: treatment efficacy collapses quickly while CA1 remains the most vulnerable region", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_g_als_rescue(ax: plt.Axes, bio_df: pd.DataFrame, no_int_s: float, early_s: float, late_s: float) -> None:
    panel_label(ax, "g")

    t_min = bio_df["time_s"].to_numpy(dtype=float) / 60.0
    no_int = bio_df["DPsi_no_intervention_mV"].to_numpy(dtype=float)
    early = bio_df["DPsi_early_boost_mV"].to_numpy(dtype=float)
    late = bio_df["DPsi_late_boost_mV"].to_numpy(dtype=float)

    ax.plot(t_min, no_int, color=COLORS["control"], lw=1.7, ls="--", label="No intervention")
    ax.plot(t_min, early, color=COLORS["PD"], lw=2.0, marker="o", ms=3.6, label="Early boost")
    ax.plot(t_min, late, color=COLORS["ALS"], lw=1.8, ls=":", marker="s", ms=3.4, label="Late boost")
    ax.axhline(140, color="0.55", lw=0.9, ls=":")
    ax.axvline(no_int_s / 60.0, color=COLORS["control"], lw=1.0, ls="--")
    ax.axvline(early_s / 60.0, color=COLORS["PD"], lw=1.0, ls="--")
    ax.annotate(
        "",
        xy=(no_int_s / 60.0, 92),
        xytext=(early_s / 60.0, 92),
        arrowprops=dict(arrowstyle="<->", color=COLORS["PD"], lw=1.0),
    )
    ax.text(
        (no_int_s + early_s) / 120.0,
        96,
        f"+{early_s - no_int_s:.0f} s",
        color=COLORS["PD"],
        fontsize=7.0,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    ax.text(
        0.03,
        0.06,
        (
            f"No intervention <= 140 mV at {no_int_s/60.0:.2f} min\n"
            f"Early boost <= 140 mV at {early_s/60.0:.2f} min\n"
            f"Late boost <= 140 mV at {late_s/60.0:.2f} min"
        ),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.7,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlabel("Time (min)")
    ax.set_ylabel(r"$\Delta\Psi_m$ (mV)")
    ax.set_title("ALS: only early mitochondrial biogenesis support meaningfully delays collapse", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def make_figure6() -> tuple[Path, Path]:
    pd_traj = load_csv("figure6_pd_trajectory.csv")
    pd_int = load_csv("figure6_pd_intervention_window.csv")
    ad_energy = load_csv("figure6_ad_energy_calcium.csv")
    ad_blocker = load_csv("figure6_ad_calcium_blocker.csv")
    ad_vuln = load_csv("figure6_ad_ca1_vulnerability.csv")
    als_syn = load_csv("figure6_als_synergy.csv")
    als_bio = load_csv("figure6_als_biogenesis.csv")
    multi = load_csv("figure6_multi_disease_comparison.csv")

    pd_collapse_s = first_threshold(pd_traj["DPsi_mV"], pd_traj["time_s"], 140.0, "below")
    pd_trigger_s = first_threshold(pd_traj["EWS_score"], pd_traj["time_s"], 0.70, "above")
    atp_failure_s = first_threshold(ad_energy["ATP_mM"], ad_energy["time_s"], 3.0, "below")
    ca_overload_s = first_threshold(ad_energy["Ca_uM"] * 1000.0, ad_energy["time_s"], 500.0, "above")
    als_combined_s = first_threshold(als_syn["DPsi_combined_mV"], als_syn["time_s"], 140.0, "below")
    als_no_int_s = first_threshold(als_bio["DPsi_no_intervention_mV"], als_bio["time_s"], 140.0, "below")
    als_early_s = first_threshold(als_bio["DPsi_early_boost_mV"], als_bio["time_s"], 140.0, "below")
    als_late_s = first_threshold(als_bio["DPsi_late_boost_mV"], als_bio["time_s"], 140.0, "below")

    fig = plt.figure(figsize=(12.8, 8.5), dpi=300)
    gs = fig.add_gridspec(
        3,
        6,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.09,
        wspace=0.85,
        hspace=0.92,
        height_ratios=[0.55, 1.0, 1.0],
    )

    ax_a = fig.add_subplot(gs[0, 0:6])
    ax_b = fig.add_subplot(gs[1, 0:2])
    ax_c = fig.add_subplot(gs[1, 2:4])
    ax_d = fig.add_subplot(gs[1, 4:6])
    ax_e = fig.add_subplot(gs[2, 0:2])
    ax_f = fig.add_subplot(gs[2, 2:4])
    ax_g = fig.add_subplot(gs[2, 4:6])

    panel_a_fingerprint(ax_a, multi)
    panel_b_pd(ax_b, pd_traj, pd_collapse_s, pd_trigger_s)
    panel_c_ad(ax_c, ad_energy, atp_failure_s, ca_overload_s)
    panel_d_als(ax_d, als_syn, als_combined_s)
    panel_e_pd_window(ax_e, pd_int)
    panel_f_ad_treatment(ax_f, ad_blocker, ad_vuln)
    panel_g_als_rescue(ax_g, als_bio, als_no_int_s, als_early_s, als_late_s)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure6_disease_publication.png"
    out_pdf = FIGURES_DIR / "figure6_disease_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure6()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
