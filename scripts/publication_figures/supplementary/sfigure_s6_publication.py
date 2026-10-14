"""
Publication Supplementary Figure S6
Hybrid Neural-ODE training diagnostics rebuilt from validated project CSV tables.

Data policy:
- Uses only real project result tables under csv/
- Replaces unsupported archive schematics with directly supported summaries

Outputs:
- figures/sfigure_s6_publication.png
- figures/sfigure_s6_publication.pdf
"""

from __future__ import annotations

import textwrap
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
    "gradient": "#2f6fb0",
    "cumulative": "#8b62c5",
    "heat_low": "#eff4fb",
    "heat_high": "#d7191c",
    "hybrid": "#2f6fb0",
    "baseline": "#c35a5a",
    "positive": "#59a14f",
    "negative": "#d7191c",
    "neutral": "#9a9a9a",
}


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
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


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def prepare_data() -> dict[str, pd.DataFrame]:
    gradient_df = load_csv("sfigure_s6_gradient_flow.csv").copy()
    hyper_df = load_csv("sfigure_s6_hyperparameter_sensitivity.csv").copy()
    perf_df = load_csv("sfigure_s6_performance_metrics.csv").copy()

    gradient_df = gradient_df.sort_values("gradient_norm", ascending=False).reset_index(drop=True)
    gradient_df["share"] = gradient_df["gradient_norm"] / gradient_df["gradient_norm"].sum()
    gradient_df["cumulative_share"] = gradient_df["share"].cumsum()
    gradient_df["rank"] = np.arange(1, len(gradient_df) + 1)

    hyper_df["mean_impact"] = hyper_df[["OCR_impact", "ATP_impact"]].mean(axis=1)
    hyper_df = hyper_df.sort_values("mean_impact", ascending=False).reset_index(drop=True)

    perf_df["higher_is_better"] = perf_df["metric"].eq("AUROC")
    perf_df["directional_ratio"] = np.where(
        perf_df["higher_is_better"],
        perf_df["Hybrid_Model"] / perf_df["Baseline_ODE"],
        perf_df["Baseline_ODE"] / perf_df["Hybrid_Model"],
    )
    perf_df["directional_log2_ratio"] = np.log2(perf_df["directional_ratio"])

    rmse_df = perf_df.loc[perf_df["metric"].str.contains("RMSE", regex=False)].copy()
    summary_df = perf_df.copy()
    return {
        "gradient_df": gradient_df,
        "hyper_df": hyper_df,
        "rmse_df": rmse_df,
        "perf_df": summary_df,
    }


def panel_a_gradient(ax: plt.Axes, gradient_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    plot_df = gradient_df.sort_values("gradient_norm", ascending=True)
    y = np.arange(len(plot_df))
    bars = ax.barh(y, plot_df["gradient_norm"], color=COLORS["gradient"], alpha=0.86)
    for bar, value in zip(bars, plot_df["gradient_norm"].to_numpy(dtype=float)):
        ax.text(value + 0.015, bar.get_y() + bar.get_height() / 2, f"{value:.2f}", va="center", fontsize=6.0)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["parameter"])
    ax.set_xlabel("Gradient norm")
    ax.set_title("Dominant gradient-carrying parameters", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_b_cumulative(ax: plt.Axes, gradient_df: pd.DataFrame) -> None:
    panel_label(ax, "b")
    x = gradient_df["rank"].to_numpy(dtype=int)
    cumulative = gradient_df["cumulative_share"].to_numpy(dtype=float)
    ax.plot(x, cumulative, color=COLORS["cumulative"], marker="o", ms=4.0, lw=1.5)
    ax.fill_between(x, 0, cumulative, color=COLORS["cumulative"], alpha=0.15)
    ax.axhline(0.50, color="0.65", lw=0.8, ls="--")
    ax.axhline(0.75, color="0.65", lw=0.8, ls=":")
    ax.axvspan(0.7, 3.3, color="#eee7f8", alpha=0.45)
    for xi, value in zip(x, cumulative):
        ax.text(xi, value + 0.03, f"{value:.2f}", ha="center", fontsize=6.0)
    ax.set_xlim(0.6, len(x) + 0.4)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Parameter rank")
    ax.set_ylabel("Cumulative share")
    ax.set_title("Gradient concentration profile", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_c_hyper(ax: plt.Axes, hyper_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    value_df = hyper_df.set_index("hyperparam")[["OCR_impact", "ATP_impact"]]
    im = ax.imshow(value_df.to_numpy(dtype=float), cmap="OrRd", vmin=0.0, vmax=0.9, aspect="auto")
    ax.set_xticks(np.arange(len(value_df.columns)))
    ax.set_xticklabels(["OCR", "ATP"])
    ax.set_yticks(np.arange(len(value_df.index)))
    ax.set_yticklabels(value_df.index)
    for i in range(value_df.shape[0]):
        for j in range(value_df.shape[1]):
            value = float(value_df.iloc[i, j])
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=6.0,
                color="white" if value >= 0.45 else "black",
            )
    ax.set_title("Hyperparameter sensitivity matrix", fontweight="bold", pad=7)
    clean_axis(ax)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("Impact score", fontsize=6.2)
    cbar.ax.tick_params(labelsize=5.8)


def panel_d_rmse(ax: plt.Axes, rmse_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    x = np.arange(len(rmse_df))
    width = 0.34
    bars1 = ax.bar(
        x - width / 2,
        rmse_df["Hybrid_Model"],
        width=width,
        color=COLORS["hybrid"],
        alpha=0.84,
        label="Hybrid Neural-ODE",
    )
    bars2 = ax.bar(
        x + width / 2,
        rmse_df["Baseline_ODE"],
        width=width,
        color=COLORS["baseline"],
        alpha=0.78,
        label="Baseline ODE",
    )
    for bars in (bars1, bars2):
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(rmse_df["Hybrid_Model"].max(), rmse_df["Baseline_ODE"].max()) * 0.025,
                f"{value:.2f}",
                ha="center",
                fontsize=6.0,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(rmse_df["metric"], rotation=18, ha="right")
    ax.set_ylabel("RMSE")
    ax.set_title("Held-out error metrics", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_e_tradeoff(ax: plt.Axes, perf_df: pd.DataFrame) -> None:
    panel_label(ax, "e")
    plot_df = perf_df.sort_values("directional_log2_ratio", ascending=True).copy()
    y = np.arange(len(plot_df))
    colors = [
        COLORS["positive"] if value > 0.03 else COLORS["negative"] if value < -0.03 else COLORS["neutral"]
        for value in plot_df["directional_log2_ratio"].to_numpy(dtype=float)
    ]
    bars = ax.barh(y, plot_df["directional_log2_ratio"], color=colors, alpha=0.86)
    ax.axvline(0, color="0.45", lw=0.9)
    for bar, ratio in zip(bars, plot_df["directional_ratio"].to_numpy(dtype=float)):
        x_text = bar.get_width() + (0.10 if bar.get_width() >= 0 else -0.10)
        ax.text(x_text, bar.get_y() + bar.get_height() / 2, f"x{ratio:.2f}", va="center", ha="left" if bar.get_width() >= 0 else "right", fontsize=6.0)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["metric"])
    ax.set_xlabel("Directional log2 ratio (>0 favors Hybrid)")
    ax.set_title("Performance trade-off against baseline", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_f_summary(ax: plt.Axes, gradient_df: pd.DataFrame, hyper_df: pd.DataFrame, perf_df: pd.DataFrame) -> None:
    panel_label(ax, "f")
    ax.axis("off")
    top_param = gradient_df.iloc[0]
    top3_share = float(gradient_df.loc[gradient_df["rank"] <= 3, "share"].sum())
    top_hyper = hyper_df.iloc[0]
    hybrid_wins = int((perf_df["directional_log2_ratio"] > 0).sum())
    baseline_wins = int((perf_df["directional_log2_ratio"] < 0).sum())
    best_metric = perf_df.sort_values("directional_log2_ratio", ascending=False).iloc[0]
    weakest_metric = perf_df.sort_values("directional_log2_ratio", ascending=True).iloc[0]
    text = (
        "Training summary\n\n"
        f"Top gradient parameter:\n{top_param['parameter']} ({float(top_param['gradient_norm']):.2f})\n\n"
        f"Top-3 gradient share:\n{top3_share:.1%}\n\n"
        f"Most sensitive hyperparameter:\n{top_hyper['hyperparam']}\n(mean impact {float(top_hyper['mean_impact']):.2f})\n\n"
        f"Directional metric wins:\nHybrid {hybrid_wins} | Baseline {baseline_wins}\n\n"
        f"Strongest Hybrid gain:\n{best_metric['metric']} (x{float(best_metric['directional_ratio']):.2f})\n\n"
        f"Largest Hybrid deficit:\n{weakest_metric['metric']} (x{float(weakest_metric['directional_ratio']):.2f})"
    )
    ax.text(
        0.05,
        0.95,
        text,
        ha="left",
        va="top",
        fontsize=7.0,
        bbox=dict(boxstyle="round,pad=0.45", fc="#fafafa", ec="0.65", lw=0.8),
    )


def make_s6() -> tuple[Path, Path]:
    data = prepare_data()

    fig = plt.figure(figsize=(13.5, 8.8), dpi=300)
    ax_a = fig.add_axes([0.060, 0.565, 0.250, 0.315])
    ax_b = fig.add_axes([0.360, 0.565, 0.235, 0.315])
    ax_c = fig.add_axes([0.675, 0.565, 0.260, 0.315])
    ax_d = fig.add_axes([0.075, 0.185, 0.370, 0.265])
    ax_e = fig.add_axes([0.515, 0.185, 0.270, 0.265])
    ax_f = fig.add_axes([0.820, 0.190, 0.140, 0.255])
    ax_cap = fig.add_axes([0.035, 0.035, 0.930, 0.090])

    panel_a_gradient(ax_a, data["gradient_df"])
    panel_b_cumulative(ax_b, data["gradient_df"])
    panel_c_hyper(ax_c, data["hyper_df"])
    panel_d_rmse(ax_d, data["rmse_df"])
    panel_e_tradeoff(ax_e, data["perf_df"])
    panel_f_summary(ax_f, data["gradient_df"], data["hyper_df"], data["perf_df"])

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S6\ |}$ Hybrid Neural-ODE training diagnostics rebuilt from validated supplementary result tables. "
        "a, Parameter-wise gradient norms from sfigure_s6_gradient_flow.csv, highlighting the mechanistic terms that carry the strongest training signal. "
        "b, Cumulative contribution of the ranked gradient norms, showing that a small subset of parameters accounts for most of the recorded gradient magnitude. "
        "c, Hyperparameter sensitivity matrix from sfigure_s6_hyperparameter_sensitivity.csv for OCR and ATP outputs. "
        "d, Direct Hybrid-versus-Baseline comparison for the three reported RMSE metrics from sfigure_s6_performance_metrics.csv. "
        "e, Direction-aware performance ratio across all reported metrics, where values above zero favor the Hybrid model after accounting for whether larger or smaller values are desirable. "
        "f, Compact numerical summary of dominant gradient targets, leading hyperparameter sensitivity, and the observed win-loss trade-off versus the baseline model. "
        "Because no real epoch-resolved gradient trajectories, network-architecture provenance table, or state-level neural-contribution matrix is available in the project outputs, this publication version intentionally omits the unsupported schematic panels used in the archive draft."
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
    out_png = FIGURES_DIR / "sfigure_s6_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s6_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s6()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
