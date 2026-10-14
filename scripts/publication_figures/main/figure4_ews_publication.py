# -*- coding: utf-8 -*-
"""
Publication Figure 4
Early warning signals anticipate mitochondrial collapse before the transition point.

Data policy:
- Uses only validated project result tables under csv/
- Removes the schematic-heavy dashboard layout
- Reframed around an example pre-collapse trajectory and predictive performance

Outputs:
- figures/figure4_ews_publication.png
- figures/figure4_ews_publication.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


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
    "trajectory": "#2f2f2f",
    "variance": "#1f6fbf",
    "autocorr": "#f0a13a",
    "combined": "#d7191c",
    "ml": "#8b5a3c",
    "safe": "#d9f0d1",
    "warning": "#fff0b8",
    "critical": "#f6bbb2",
    "collapsed": "#efefef",
}


def load_csv(name: str, **kwargs) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path, **kwargs)


def panel_label(ax: plt.Axes, label: str, x: float = -0.11, y: float = 1.08) -> None:
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


def prepare_data() -> dict[str, object]:
    traj_df = load_csv("figure4_ews_trajectory.csv").sort_values("time_s").copy()
    perf_df = load_csv("figure4_ews_performance.csv")
    cv_df = load_csv("figure4_cross_validation.csv")
    lead_df = load_csv("figure4_lead_time_distribution.csv")
    cm_df = load_csv("figure4_confusion_matrix.csv", on_bad_lines="skip")

    collapse_idx = int((traj_df["DPsi_mV"] <= 140).idxmax())
    collapse_time = float(traj_df.loc[collapse_idx, "time_s"])
    traj_df["time_to_collapse_s"] = traj_df["time_s"].astype(float) - collapse_time

    trigger_idx = int((traj_df["composite_ews_score"] >= 0.7).idxmax())
    trigger_time = float(traj_df.loc[trigger_idx, "time_to_collapse_s"])
    lead_time_example = abs(trigger_time)

    traj_window = traj_df[
        traj_df["time_to_collapse_s"].between(-120, 20, inclusive="both")
    ].copy()

    cv_plot = cv_df[cv_df["fold"].astype(str).str.fullmatch(r"\d+")].copy()
    cv_plot["fold_num"] = cv_plot["fold"].astype(int)
    cv_plot = cv_plot.sort_values("fold_num")

    perf_map = {row["method"]: row for _, row in perf_df.iterrows()}

    cm_main = cm_df[cm_df["label"].isin(["actual_healthy", "actual_collapse"])].copy()
    cm_main["predicted_healthy"] = pd.to_numeric(cm_main["predicted_healthy"], errors="coerce")
    cm_main["predicted_collapse"] = pd.to_numeric(cm_main["predicted_collapse"], errors="coerce")
    tn = int(cm_main.loc[cm_main["label"] == "actual_healthy", "predicted_healthy"].iloc[0])
    fp = int(cm_main.loc[cm_main["label"] == "actual_healthy", "predicted_collapse"].iloc[0])
    fn = int(cm_main.loc[cm_main["label"] == "actual_collapse", "predicted_healthy"].iloc[0])
    tp = int(cm_main.loc[cm_main["label"] == "actual_collapse", "predicted_collapse"].iloc[0])

    total = float(lead_df["frequency"].sum())
    lead_mean = float(np.sum(lead_df["lead_time_s"] * lead_df["frequency"]) / total)
    lead_var = float(
        np.sum(lead_df["frequency"] * (lead_df["lead_time_s"] - lead_mean) ** 2) / total
    )
    lead_std = float(np.sqrt(lead_var))
    lead_mode = float(lead_df.loc[lead_df["frequency"].idxmax(), "lead_time_s"])

    return {
        "traj_df": traj_df,
        "traj_window": traj_window,
        "perf_map": perf_map,
        "cv_plot": cv_plot,
        "lead_df": lead_df,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "trigger_time": trigger_time,
        "lead_time_example": lead_time_example,
        "lead_mean": lead_mean,
        "lead_std": lead_std,
        "lead_mode": lead_mode,
    }


def stage_spans(traj_df: pd.DataFrame) -> list[tuple[float, float, str]]:
    x = traj_df["time_to_collapse_s"].to_numpy(dtype=float)
    labels = traj_df["warning_zone"].astype(str).to_numpy()

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


def add_state_spans(ax: plt.Axes, spans: list[tuple[float, float, str]]) -> None:
    colors = {
        "healthy": COLORS["safe"],
        "warning": COLORS["warning"],
        "critical": COLORS["critical"],
        "collapsed": COLORS["collapsed"],
    }
    for left, right, label in spans:
        ax.axvspan(left, right, color=colors.get(label, "#f3f3f3"), alpha=0.42, lw=0)


def panel_a_trajectory(
    axes: list[plt.Axes],
    traj_window: pd.DataFrame,
    trigger_time: float,
) -> None:
    panel_label(axes[0], "a")

    spans = stage_spans(traj_window)
    x = traj_window["time_to_collapse_s"].to_numpy(dtype=float)
    variance = traj_window["variance_mV2"].to_numpy(dtype=float)
    autocorr = traj_window["autocorrelation_lag1"].to_numpy(dtype=float)
    composite = traj_window["composite_ews_score"].to_numpy(dtype=float)
    dpsi = traj_window["DPsi_mV"].to_numpy(dtype=float)

    for ax in axes:
        add_state_spans(ax, spans)
        ax.axvline(trigger_time, color=COLORS["combined"], lw=1.0, ls="--")
        ax.axvline(0, color="0.25", lw=0.95, ls="--")
        clean_axis(ax)

    axes[0].plot(x, dpsi, color=COLORS["trajectory"], lw=2.0)
    axes[0].scatter([trigger_time, 0], [148, 140], color=[COLORS["combined"], "0.2"], s=22, zorder=3)
    axes[0].axhline(140, color="0.55", lw=0.85, ls=":")
    axes[0].annotate(
        "",
        xy=(trigger_time, 181.2),
        xytext=(0, 181.2),
        arrowprops=dict(arrowstyle="<->", color=COLORS["combined"], lw=1.0),
    )
    axes[0].text(
        trigger_time / 2,
        182.0,
        f"{abs(trigger_time):.0f} s lead",
        color=COLORS["combined"],
        fontsize=7.0,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    axes[0].text(
        0.01,
        1.16,
        "Example trajectory: the composite warning score rises before the collapse threshold is crossed",
        transform=axes[0].transAxes,
        ha="left",
        va="bottom",
        fontsize=8.4,
        fontweight="bold",
    )
    axes[0].text(
        0.01,
        1.05,
        "Colored bands indicate state progression inferred from the trajectory table.",
        transform=axes[0].transAxes,
        ha="left",
        va="bottom",
        fontsize=6.4,
        color="0.35",
    )
    axes[0].set_ylabel(r"$\Delta\Psi_m$ (mV)")
    axes[0].set_ylim(136, 183)

    axes[1].plot(x, variance, color=COLORS["variance"], lw=1.8)
    axes[1].fill_between(x, 0, variance, color=COLORS["variance"], alpha=0.13)
    axes[1].set_ylabel("Variance")
    axes[1].set_ylim(0, 24)

    axes[2].plot(x, autocorr, color=COLORS["autocorr"], lw=1.8)
    axes[2].fill_between(x, 0, autocorr, color=COLORS["autocorr"], alpha=0.13)
    axes[2].set_ylabel("Lag-1 AC")
    axes[2].set_ylim(0.28, 0.86)

    axes[3].plot(x, composite, color=COLORS["combined"], lw=2.0)
    axes[3].axhline(0.40, color="0.60", lw=0.8, ls=":")
    axes[3].axhline(0.70, color=COLORS["combined"], lw=0.9, ls=":")
    axes[3].text(3, 0.715, "alert threshold", color=COLORS["combined"], fontsize=6.2, ha="right")
    axes[3].set_ylabel("Composite")
    axes[3].set_xlabel("Time to collapse (s)")
    axes[3].set_ylim(0.18, 0.90)

    state_labels = [
        (-92, "stable"),
        (-32, "warning"),
        (-4, "critical"),
    ]
    for xpos, text in state_labels:
        axes[0].text(xpos, 137.0, text, fontsize=6.2, color="0.25", ha="center", va="bottom")

    axes[3].set_xlim(x.min(), x.max())
    axes[3].set_xticks([-120, -90, -60, -30, 0])
    for ax in axes[:-1]:
        ax.tick_params(labelbottom=False)


def panel_b_lead_distribution(
    ax: plt.Axes,
    lead_df: pd.DataFrame,
    lead_mean: float,
    lead_std: float,
    lead_mode: float,
    lead_time_example: float,
) -> None:
    panel_label(ax, "b")

    x = lead_df["lead_time_s"].to_numpy(dtype=float)
    freq = lead_df["frequency"].to_numpy(dtype=float)
    density = lead_df["probability_density"].to_numpy(dtype=float)

    ax.bar(x, freq, width=7.5, color=COLORS["variance"], alpha=0.75, edgecolor="white", lw=0.5)
    ax.set_xlim(5, 125)
    ax.set_ylim(0, 44)
    ax.set_xlabel("Lead time before collapse (s)")
    ax.set_ylabel("Frequency")
    ax.set_title(
        "Across runs, warnings typically arrive tens of seconds before collapse",
        fontweight="bold",
        pad=7,
    )
    ax.grid(axis="y", alpha=0.18, linewidth=0.5)

    ax2 = ax.twinx()
    ax2.plot(x, density, color=COLORS["combined"], lw=1.6)
    ax2.fill_between(x, 0, density, color=COLORS["combined"], alpha=0.08)
    ax2.set_ylim(0, max(0.22, density.max() * 1.12))
    ax2.set_ylabel("Probability density")
    ax2.spines["top"].set_visible(False)

    ax.axvline(lead_mean, color="0.35", lw=0.95, ls="--")
    ax.axvline(lead_time_example, color=COLORS["combined"], lw=0.95, ls=":")
    ax.text(
        0.98,
        0.95,
        (
            f"Mean = {lead_mean:.1f} s\n"
            f"SD = {lead_std:.1f} s\n"
            f"Mode = {lead_mode:.0f} s\n"
            f"Example trace = {lead_time_example:.0f} s"
        ),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.9,
        bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="0.72", lw=0.7),
    )
    clean_axis(ax)


def panel_c_cv_summary(ax: plt.Axes, cv_plot: pd.DataFrame, perf_map: dict[str, pd.Series]) -> None:
    panel_label(ax, "c")

    series = [
        ("ML only", cv_plot["ML_AUC"].to_numpy(dtype=float), COLORS["ml"], "ML"),
        ("EWS only", cv_plot["EWS_AUC"].to_numpy(dtype=float), COLORS["variance"], "EWS"),
        ("Combined", cv_plot["Combined_AUC"].to_numpy(dtype=float), COLORS["combined"], "Combined"),
    ]

    y_positions = np.array([0, 1, 2], dtype=float)
    jitter = np.linspace(-0.11, 0.11, len(cv_plot))
    for ypos, (label, values, color, key) in zip(y_positions, series):
        ax.scatter(
            values,
            np.full_like(values, ypos) + jitter,
            s=22,
            facecolor="white",
            edgecolor=color,
            linewidth=0.9,
            zorder=2,
        )
        ax.errorbar(
            values.mean(),
            ypos,
            xerr=values.std(ddof=0),
            fmt="o",
            ms=7.5,
            color=color,
            mec="black",
            mew=0.4,
            elinewidth=1.4,
            capsize=3.2,
            zorder=3,
        )
        ax.text(0.955, ypos, f"{float(perf_map[key]['AUC']):.2f}", fontsize=6.7, ha="right", va="center")

    combined_auc = float(perf_map["Combined"]["AUC"])
    ews_auc = float(perf_map["EWS"]["AUC"])
    ml_auc = float(perf_map["ML"]["AUC"])

    ax.text(
        0.03,
        0.95,
        (
            f"Combined vs EWS: +{combined_auc - ews_auc:.2f} AUC\n"
            f"Combined vs ML: +{combined_auc - ml_auc:.2f} AUC"
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.0,
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="0.72", lw=0.7),
    )

    ax.set_xlim(0.78, 0.96)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([item[0] for item in series])
    ax.set_xlabel("Cross-validated AUC")
    ax.set_title(
        "The combined predictor is both the strongest and the most stable",
        fontweight="bold",
        pad=7,
    )
    ax.grid(axis="x", alpha=0.18, linewidth=0.5)
    ax.text(0.958, 2.38, "overall", fontsize=6.2, ha="right", va="bottom", color="0.35")
    clean_axis(ax)


def draw_confusion_panel(
    ax_cm: plt.Axes,
    ax_metrics: plt.Axes,
    tn: int,
    fp: int,
    fn: int,
    tp: int,
    combined_row: pd.Series,
) -> None:
    panel_label(ax_cm, "d", x=-0.18, y=1.10)

    matrix = np.array([[tn, fp], [fn, tp]], dtype=float)
    cmap = LinearSegmentedColormap.from_list("cmred", ["#fff5f5", "#d7191c"])
    ax_cm.imshow(matrix, cmap=cmap, vmin=0, vmax=matrix.max())

    cell_labels = [[f"{tn}\nTN", f"{fp}\nFP"], [f"{fn}\nFN", f"{tp}\nTP"]]
    for i in range(2):
        for j in range(2):
            value = matrix[i, j]
            ax_cm.text(
                j,
                i,
                cell_labels[i][j],
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value > 0.6 * matrix.max() else "black",
                fontweight="bold" if value > 0.6 * matrix.max() else "normal",
            )

    ax_cm.set_xticks([0, 1])
    ax_cm.set_xticklabels(["Healthy", "Collapse"])
    ax_cm.set_yticks([0, 1])
    ax_cm.set_yticklabels(["Healthy", "Collapse"])
    ax_cm.set_xlabel("Predicted")
    ax_cm.set_ylabel("Actual")
    ax_cm.set_title("Operating-point confusion matrix", fontweight="bold", pad=7)
    ax_cm.tick_params(length=0)
    for spine in ax_cm.spines.values():
        spine.set_visible(False)

    metric_specs = [
        ("Accuracy", float(combined_row["accuracy"])),
        ("Sensitivity", float(combined_row["sensitivity"])),
        ("Specificity", float(combined_row["specificity"])),
        ("Precision", float(combined_row["precision"])),
    ]
    y_pos = np.arange(len(metric_specs))[::-1]
    values = [item[1] for item in metric_specs]
    labels = [item[0] for item in metric_specs]

    ax_metrics.barh(y_pos, values, color=COLORS["combined"], alpha=0.82, height=0.55)
    ax_metrics.set_xlim(0, 1.0)
    ax_metrics.set_yticks(y_pos)
    ax_metrics.set_yticklabels(labels)
    ax_metrics.set_xlabel("Score")
    ax_metrics.set_title("Performance at the chosen alert threshold", fontweight="bold", pad=7)
    for ypos, value in zip(y_pos, values):
        ax_metrics.text(value + 0.02, ypos, f"{value * 100:.0f}%", va="center", fontsize=6.9, fontweight="bold")
    ax_metrics.text(
        0.02,
        -0.28,
        (
            f"Combined AUC = {float(combined_row['AUC']):.2f}\n"
            f"Average precision = {float(combined_row['AP']):.2f}\n"
            f"False alarms = {fp}, missed collapses = {fn}"
        ),
        transform=ax_metrics.transAxes,
        ha="left",
        va="top",
        fontsize=6.9,
    )
    ax_metrics.grid(axis="x", alpha=0.18, linewidth=0.5)
    clean_axis(ax_metrics)


def make_figure4() -> tuple[Path, Path]:
    data = prepare_data()

    fig = plt.figure(figsize=(12.8, 7.9), dpi=300)
    outer = fig.add_gridspec(
        3,
        4,
        left=0.06,
        right=0.985,
        top=0.96,
        bottom=0.10,
        wspace=0.90,
        hspace=0.95,
        width_ratios=[1.25, 1.25, 1.0, 1.0],
    )

    traj_grid = outer[:, 0:2].subgridspec(4, 1, hspace=0.08)
    ax_a1 = fig.add_subplot(traj_grid[0, 0])
    ax_a2 = fig.add_subplot(traj_grid[1, 0], sharex=ax_a1)
    ax_a3 = fig.add_subplot(traj_grid[2, 0], sharex=ax_a1)
    ax_a4 = fig.add_subplot(traj_grid[3, 0], sharex=ax_a1)

    ax_b = fig.add_subplot(outer[0, 2:4])
    ax_c = fig.add_subplot(outer[1, 2:4])
    metrics_grid = outer[2, 2:4].subgridspec(1, 2, wspace=0.55, width_ratios=[1.0, 1.15])
    ax_d1 = fig.add_subplot(metrics_grid[0, 0])
    ax_d2 = fig.add_subplot(metrics_grid[0, 1])

    panel_a_trajectory(
        [ax_a1, ax_a2, ax_a3, ax_a4],
        data["traj_window"],
        float(data["trigger_time"]),
    )
    panel_b_lead_distribution(
        ax_b,
        data["lead_df"],
        float(data["lead_mean"]),
        float(data["lead_std"]),
        float(data["lead_mode"]),
        float(data["lead_time_example"]),
    )
    panel_c_cv_summary(ax_c, data["cv_plot"], data["perf_map"])
    draw_confusion_panel(
        ax_d1,
        ax_d2,
        int(data["tn"]),
        int(data["fp"]),
        int(data["fn"]),
        int(data["tp"]),
        data["perf_map"]["Combined"],
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIGURES_DIR / "figure4_ews_publication.png"
    out_pdf = FIGURES_DIR / "figure4_ews_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_figure4()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
