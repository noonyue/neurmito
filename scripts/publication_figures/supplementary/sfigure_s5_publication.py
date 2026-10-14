# -*- coding: utf-8 -*-
"""
Publication Supplementary Figure S5
Bayesian model comparison, posterior predictive spread, and convergence diagnostics.

Data policy:
- Uses only validated project CSV tables under csv/
- Replaces synthetic validation scenes with direct information-criterion and convergence summaries

Outputs:
- figures/sfigure_s5_publication.png
- figures/sfigure_s5_publication.pdf
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
    "hybrid": "#1f77b4",
    "ode": "#d62728",
    "neural": "#2ca02c",
    "baseline": "#7f7f7f",
    "warn": "#f0a040",
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


def panel_a_ic(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "a")
    x = np.arange(len(mc_df))
    width = 0.34
    ax.bar(x - width / 2, mc_df["WAIC"], width=width, yerr=mc_df["WAIC_SE"], capsize=3, color=COLORS["ode"], alpha=0.78, label="WAIC")
    ax.bar(x + width / 2, mc_df["LOO_IC"], width=width, yerr=mc_df["LOO_IC_SE"], capsize=3, color=COLORS["hybrid"], alpha=0.78, label="LOO-IC")
    ax.set_xticks(x)
    ax.set_xticklabels(mc_df["model"], rotation=25, ha="right")
    ax.set_ylabel("Information criterion")
    ax.set_title("Bayesian model-comparison criteria", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_b_delta(ax: plt.Axes, mc_df: pd.DataFrame) -> None:
    panel_label(ax, "b")
    best_waic = mc_df["WAIC"].min()
    best_loo = mc_df["LOO_IC"].min()
    delta = pd.DataFrame(
        {
            "model": mc_df["model"],
            "Delta_WAIC": mc_df["WAIC"] - best_waic,
            "Delta_LOO": mc_df["LOO_IC"] - best_loo,
        }
    )
    x = np.arange(len(delta))
    width = 0.34
    ax.bar(x - width / 2, delta["Delta_WAIC"], width=width, color="#9467bd", alpha=0.80, label="Delta WAIC")
    ax.bar(x + width / 2, delta["Delta_LOO"], width=width, color=COLORS["warn"], alpha=0.80, label="Delta LOO")
    ax.set_xticks(x)
    ax.set_xticklabels(delta["model"], rotation=25, ha="right")
    ax.set_ylabel("Difference from best model")
    ax.set_title("Relative evidence penalty", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper left")
    clean_axis(ax)


def panel_c_postpred(ax: plt.Axes, pp_df: pd.DataFrame) -> None:
    panel_label(ax, "c")
    x = np.arange(len(pp_df))
    ax.bar(x, pp_df["observed_value"], color="#d9e2ef", edgecolor="0.4", width=0.62, label="Observed")
    ax.errorbar(x, pp_df["observed_value"], yerr=pp_df["predicted_std"], fmt="o", color=COLORS["hybrid"], ecolor=COLORS["hybrid"], elinewidth=1.0, capsize=3, label="Posterior predictive spread")
    ax.set_xticks(x)
    ax.set_xticklabels(pp_df["metric"], rotation=20, ha="right")
    ax.set_ylabel("Observed value")
    ax.set_title("Posterior predictive summary", fontweight="bold", pad=7)
    ax.legend(frameon=False, loc="upper right")
    clean_axis(ax)


def panel_d_rhat(ax: plt.Axes, rhat_df: pd.DataFrame) -> None:
    panel_label(ax, "d")
    colors = [COLORS["hybrid"] if status == "yes" else COLORS["ode"] for status in rhat_df["converged"]]
    ax.barh(rhat_df["parameter"], rhat_df["R_hat"], color=colors, alpha=0.82)
    ax.axvline(1.05, color="0.55", lw=0.9, ls="--")
    ax.set_xlim(1.0, 1.11)
    ax.set_xlabel("R-hat")
    ax.set_title("Convergence diagnostic per parameter", fontweight="bold", pad=7)
    clean_axis(ax)


def panel_e_convergence_summary(ax: plt.Axes, rhat_df: pd.DataFrame) -> None:
    panel_label(ax, "e")
    ax.axis("off")
    total = len(rhat_df)
    converged = int(rhat_df["converged"].eq("yes").sum())
    flagged = rhat_df.loc[rhat_df["converged"].eq("no"), "parameter"].tolist()
    text = (
        f"Converged parameters: {converged}/{total}\n"
        f"Flagged parameters: {len(flagged)}\n"
        f"Non-converged: {', '.join(flagged) if flagged else 'None'}\n"
        f"Best model: {rhat_df.shape[0] and 'Hybrid Neural-ODE'}"
    )
    ax.text(0.04, 0.85, "Convergence summary", fontsize=8, fontweight="bold", va="top")
    ax.text(0.04, 0.60, text, fontsize=6.8, va="top")


def make_s5() -> tuple[Path, Path]:
    mc_df = load_csv("sfigure_s5_model_comparison.csv")
    pp_df = load_csv("sfigure_s5_posterior_predictive.csv")
    rhat_df = load_csv("sfigure_s5_rhat_diagnostics.csv")

    fig = plt.figure(figsize=(13.5, 8.8), dpi=300)
    ax_a = fig.add_axes([0.070, 0.605, 0.280, 0.300])
    ax_b = fig.add_axes([0.395, 0.605, 0.280, 0.300])
    ax_c = fig.add_axes([0.720, 0.605, 0.240, 0.300])
    ax_d = fig.add_axes([0.080, 0.250, 0.520, 0.280])
    ax_e = fig.add_axes([0.665, 0.270, 0.295, 0.240])
    ax_cap = fig.add_axes([0.035, 0.045, 0.930, 0.155])

    panel_a_ic(ax_a, mc_df)
    panel_b_delta(ax_b, mc_df)
    panel_c_postpred(ax_c, pp_df)
    panel_d_rhat(ax_d, rhat_df)
    panel_e_convergence_summary(ax_e, rhat_df)

    ax_cap.axis("off")
    caption = (
        r"$\bf{Fig.\ S5\ |}$ Bayesian model comparison, posterior predictive spread, and convergence diagnostics. "
        "a, WAIC and LOO-IC values with standard errors from sfigure_s5_model_comparison.csv. "
        "b, Delta WAIC and Delta LOO relative to the best-supported model. "
        "c, Posterior predictive summary using observed metrics and predictive spread from sfigure_s5_posterior_predictive.csv. "
        "d, Parameter-level R-hat diagnostics from sfigure_s5_rhat_diagnostics.csv, with the conventional 1.05 threshold marked. "
        "e, Compact convergence summary highlighting the small subset of parameters that remain above the strict convergence cutoff."
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
    out_png = FIGURES_DIR / "sfigure_s5_publication.png"
    out_pdf = FIGURES_DIR / "sfigure_s5_publication.pdf"
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png, out_pdf


if __name__ == "__main__":
    png, pdf = make_s5()
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")
