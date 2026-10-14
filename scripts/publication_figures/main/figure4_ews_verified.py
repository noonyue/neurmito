"""Data-driven Figure 4 from R021-R023; no synthetic ROC or intervention panels."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
R021 = ROOT / "refine-logs/runs/R021"
R023 = ROOT / "refine-logs/runs/R023"
OUT = ROOT / "figures/figure4_ews_complete.png"
PDF = ROOT / "figures/figure4_ews_complete.pdf"


def _csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def generate():
    conditions = _csv(R021 / "conditions.csv")
    test = [row for row in conditions if row["split"] == "test"]
    positive = [row for row in test if row["label"] == "1"]
    representative = min(positive, key=lambda row: float(row["event_time_s"]))
    trajectories = [
        row for row in _csv(R021 / "trajectories.csv")
        if row["group_key"] == representative["group_key"]
    ]
    trajectories.sort(key=lambda row: float(row["time_s"]))
    t = np.asarray([float(row["time_s"]) for row in trajectories])
    dpsi = np.asarray([float(row["dpsi_mv"]) for row in trajectories])
    atp = np.asarray([float(row["atp_m_mm"]) for row in trajectories])
    window = max(5, int(round(20.0 / max(np.median(np.diff(t)), 1e-9))))
    variance = np.full_like(dpsi, np.nan)
    ac = np.full_like(dpsi, np.nan)
    for i in range(window, len(dpsi)):
        values = dpsi[i - window:i]
        variance[i] = np.var(values, ddof=1)
        if np.std(values[:-1]) > 0 and np.std(values[1:]) > 0:
            ac[i] = np.corrcoef(values[:-1], values[1:])[0, 1]

    metrics = json.loads((R023 / "locked_test_metrics.json").read_text(encoding="utf-8"))
    controls = json.loads((R023 / "negative_controls.json").read_text(encoding="utf-8"))
    predictions = _csv(R023 / "test_predictions.csv")

    fig, axes = plt.subplots(2, 3, figsize=(11, 6.8), constrained_layout=True)
    ax = axes[0, 0]
    ax.plot(t, dpsi, color="#2166ac", lw=1.5)
    ax.axhline(140, color="#d01c8b", ls="--", lw=1, label="Operational event marker")
    ax.axvline(float(representative["event_time_s"]), color="#d01c8b", ls=":", lw=1)
    ax.set(xlabel="Time (s)", ylabel="DPsi (mV)", title="a  Representative test trajectory")
    ax.legend(fontsize=6)

    ax = axes[0, 1]
    ax.plot(t, variance, color="#e08214", label="Rolling variance")
    ax2 = ax.twinx()
    ax2.plot(t, ac, color="#8073ac", label="Lag-1 AC")
    ax.set(xlabel="Time (s)", ylabel="Variance", title="b  Descriptive EWS dynamics")
    ax2.set_ylabel("Lag-1 AC")

    ax = axes[0, 2]
    labels = np.asarray([int(row["label"]) for row in predictions if row["model"] == "locked_baseline"])
    probs = np.asarray([float(row["probability"]) for row in predictions if row["model"] == "locked_baseline"])
    ax.boxplot([probs[labels == 0], probs[labels == 1]], labels=["Physiological", "Depolarized"])
    ax.set(ylabel="Locked DPsi + ATPm probability", title="c  Locked test separation")

    ax = axes[1, 0]
    names = [item["model"] for item in metrics]
    auc = [item["auroc"] for item in metrics]
    ax.bar(np.arange(len(names)), auc, color=["#2166ac", "#e08214", "#4dac26", "#8073ac"])
    ax.set_xticks(np.arange(len(names)), ["Locked\nbaseline", "Best\nEWS", "DPsi", "Slope"], rotation=20)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("AUROC")
    ax.set_title("d  Locked test comparison")

    ax = axes[1, 1]
    perm = controls["group_label_permutation"]
    ax.errorbar([0], [perm["auroc_median"]], yerr=[[perm["auroc_median"] - perm["auroc_ci_low"]], [perm["auroc_ci_high"] - perm["auroc_median"]]], fmt="o", color="#636363", label="Permutation null")
    ax.scatter([1], [perm["observed_locked_auroc"]], color="#2166ac", label="Observed locked baseline")
    ax.set_xticks([0, 1], ["Permuted", "Observed"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("AUROC")
    ax.set_title("e  Group-label negative control")
    ax.legend(fontsize=6)

    ax = axes[1, 2]
    lead = [
        float(row["event_time_s"]) - float(row["target_time_s"])
        for row in predictions
        if row["model"] == "locked_baseline" and row["label"] == "1"
    ]
    ax.hist(lead, bins=10, color="#d01c8b", alpha=0.8)
    ax.set(xlabel="Lead time (s)", ylabel="Positive groups", title="f  Locked baseline lead time")

    fig.suptitle(
        "Figure 4. Data-driven endpoint separation and EWS diagnostics\n"
        "R021-R023 computational cohort; no independent EWS predictive gain",
        fontsize=11,
        fontweight="bold",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=600, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)
    return OUT, PDF


if __name__ == "__main__":
    print(generate())
