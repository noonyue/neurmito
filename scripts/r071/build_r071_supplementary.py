"""Build R071 supplementary figures for NeurMito-DT.

 This generator creates a separate R071 supplementary asset set. Quantitative
+ panels read from audited refinement logs. Conceptual panels are explicitly
+ labelled as computational scope or reproducibility aids, not biological data.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from string import ascii_lowercase

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "inputs" / "audit_runs"
FIG_DIR = ROOT / "results" / "supplementary_figures"
TABLE_DIR = ROOT / "results" / "manifests"
MANIFEST = ROOT / "results" / "manifests" / "r071_supplementary_manifest.json"
INCLUDES = TABLE_DIR / "r071_supplementary_figure_includes.tex"

COLORS = {
    "blue": "#0072B2",
    "sky": "#56B4E9",
    "green": "#009E73",
    "orange": "#E69F00",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "gray": "#6C757D",
    "dark": "#222222",
    "light": "#F2F2F2",
    "pale_blue": "#EAF2F8",
    "pale_green": "#E8F5EE",
    "pale_orange": "#FFF3D6",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7.6,
    "axes.labelsize": 7.6,
    "axes.titlesize": 8.4,
    "xtick.labelsize": 6.8,
    "ytick.labelsize": 6.8,
    "legend.fontsize": 6.6,
    "axes.linewidth": 0.75,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
})


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_label(ax, text: str):
    ax.text(-0.10, 1.06, text, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")


def box(ax, xy, wh, text, face, edge, fontsize=7.2, bold=False):
    patch = FancyBboxPatch(xy, wh[0], wh[1], boxstyle="round,pad=0.018", facecolor=face, edgecolor=edge, lw=0.9)
    ax.add_patch(patch)
    ax.text(xy[0] + wh[0] / 2, xy[1] + wh[1] / 2, text, ha="center", va="center", fontsize=fontsize, fontweight="bold" if bold else None)
    return patch


def save(fig, stem: str) -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    # Supplementary composites are embedded at roughly half their canvas width.
    # Preserve a readable displayed font without changing any plotted values.
    from matplotlib.text import Text
    for item in fig.findobj(match=Text):
        if item.get_fontsize() < 10.0:
            item.set_fontsize(10.0)
    png = FIG_DIR / f"{stem}.png"
    pdf = FIG_DIR / f"{stem}.pdf"
    fig.savefig(png, dpi=600, facecolor="white", edgecolor="none")
    fig.savefig(pdf, facecolor="white", edgecolor="none")
    plt.close(fig)
    return png, pdf


def source_records():
    r042 = read_json(RUNS / "R042" / "digitization_uncertainty_propagation.json")
    r060 = read_json(RUNS / "R060" / "pmc4454361_control_relative_digitization.json")
    r060b = read_json(RUNS / "R060B" / "pmc5124357_control_relative_digitization.json")
    low = r042["source_ratio_intervals"]
    return [
        {"id": "R033", "source": "PMID:31931869", "group": "low", "color": COLORS["blue"], "max": low["PMID:31931869"]["maximal_to_basal"], "spare": low["PMID:31931869"]["spare_to_basal"]},
        {"id": "R039", "source": "PMID:24056030", "group": "low", "color": COLORS["red"], "max": low["PMID:24056030"]["maximal_to_basal"], "spare": low["PMID:24056030"]["spare_to_basal"]},
        {"id": "R060", "source": "PMID:25081478", "group": "high", "color": COLORS["green"], "max": {"nominal": r060["relative_ratios"]["maximal_to_basal"]["value"], "low": r060["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060["relative_ratios"]["spare_to_basal"]["value"], "low": r060["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060["relative_ratios"]["spare_to_basal"]["interval"][1]}},
        {"id": "R060B", "source": "PMID:27889640", "group": "high", "color": COLORS["purple"], "max": {"nominal": r060b["relative_ratios"]["maximal_to_basal"]["value"], "low": r060b["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060b["relative_ratios"]["spare_to_basal"]["value"], "low": r060b["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["spare_to_basal"]["interval"][1]}},
    ]


def source_audit_s1() -> tuple[Path, Path]:
    records = source_records()
    r047 = read_json(RUNS / "R047" / "cross_source_formula_coordination.json")
    r042 = read_json(RUNS / "R042" / "digitization_uncertainty_propagation.json")
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 7.0), constrained_layout=True)
    axes = axes.ravel()
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)

    ax = axes[0]
    endpoints = ["max", "spare"]
    offsets = [-0.18, 0.18]
    for x, rec in enumerate(records):
        for off, key, marker in zip(offsets, endpoints, ["o", "s"]):
            value = rec[key]["nominal"]
            ax.errorbar([x + off], [value], yerr=[[value - rec[key]["low"]], [rec[key]["high"] - value]], fmt=marker, color=rec["color"], capsize=3, ms=5)
    ax.set_xticks(range(len(records)), [r["id"] for r in records])
    ax.set_ylabel("Source-local ratio")
    ax.scatter([], [], marker="o", color="0.3", label="maximal/basal")
    ax.scatter([], [], marker="s", color="0.3", label="spare/basal")
    ax.legend(frameon=False)
    clean(ax)

    ax = axes[1]
    terms = ["B", "O", "F", "N", "A", "P"]
    recs = ["R033", "R039", "R046"]
    code = {"reported": 3, "digitized": 3, "inferred": 2, "inferred_conflicting": 1, "unavailable": 0}
    mat = np.array([[code[r047["records"][rec]["terms"][term]] for term in terms] for rec in recs])
    ax.imshow(mat, cmap=ListedColormap(["#DDDDDD", COLORS["purple"], COLORS["orange"], COLORS["green"]]), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(terms)), terms)
    ax.set_yticks(range(len(recs)), recs)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax = axes[2]
    overlap = r042["between_source_interval_overlap"]
    keys = ["maximal_to_basal", "spare_to_basal", "atp_linked_to_basal", "proton_leak_to_basal"]
    vals = [1 if overlap[k]["overlaps"] else 0 for k in keys]
    ax.bar(range(len(keys)), vals, color=[COLORS["green"] if v else COLORS["orange"] for v in vals])
    ax.set_ylim(0, 1.2)
    ax.set_yticks([0, 1], ["no", "yes"])
    ax.set_xticks(range(len(keys)), [k.replace("_to_basal", "").replace("_", "\n") for k in keys])
    ax.set_ylabel("Interval overlap")
    clean(ax)

    ax = axes[3]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    contract = r047["minimum_common_observation_contract"]
    rows = [("Retained", "maximal/basal;\nsource-specific spare/basal", COLORS["green"]),
            ("Diagnostic", "proton leak with\nsource formula flag", COLORS["orange"]),
            ("Blocked", "ATP-linked; oligomycin/basal;\nabsolute OCR", COLORS["purple"])]
    for i, (head, body, color) in enumerate(rows):
        y = 0.72 - i * 0.25
        box(ax, (0.04, y - 0.08), (0.92, 0.15), f"{head}\n{body}", "white", color, fontsize=6.8)

    ax = axes[4]
    xvals = [r["max"]["nominal"] for r in records]
    yvals = [r["spare"]["nominal"] for r in records]
    for rec, x, y in zip(records, xvals, yvals):
        ax.scatter(x, y, color=rec["color"], s=70, edgecolor="white", lw=0.8)
        ax.text(x + 0.01, y, rec["id"], fontsize=7)
    ax.set_xlabel("Maximal/basal")
    ax.set_ylabel("Spare/basal")
    clean(ax)

    ax = axes[5]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    box(ax, (0.08, 0.60), (0.84, 0.20), "Supported now\nsource-local relative OCR evidence", COLORS["pale_green"], COLORS["green"], fontsize=7.2)
    box(ax, (0.08, 0.27), (0.84, 0.27), "Outside inference scope\nabsolute OCR calibration\npooled fitting\nbiological validation", COLORS["pale_orange"], COLORS["orange"], fontsize=10.0)
    return save(fig, "r071_sfigure_s1_source_contract_audit")


def mapping_s2() -> tuple[Path, Path]:
    r048 = read_json(RUNS / "R048" / "maximal_spare_restricted_mapping.json")
    r062 = read_json(RUNS / "R062" / "conditional_heterogeneity_mapping.json")
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 7.0), constrained_layout=True)
    axes = axes.ravel()
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)

    directions = list(r048["fit_directions"].keys())
    ax = axes[0]
    losses = [r048["fit_directions"][d]["near_best_summary"]["best_train_loss"] for d in directions]
    ax.bar(range(len(directions)), losses, color=[COLORS["blue"], COLORS["orange"]])
    ax.set_xticks(range(len(directions)), [d.replace("_", "\n") for d in directions], rotation=0)
    ax.set_ylabel("Best train loss")
    clean(ax)

    ax = axes[1]
    for group, color, marker in [("low_reserve_pair", COLORS["blue"], "o"), ("high_reserve_pair", COLORS["green"], "s")]:
        items = r062["conditional_group_rankings"][group]["top_ranked"][:10]
        ax.scatter([i["multipliers"]["Vmax_CV"] for i in items], [i["multipliers"]["g_H"] for i in items], s=[75 / (1 + 80 * i["loss"]) for i in items], color=color, marker=marker, alpha=0.75, label=group.replace("_pair", ""))
    ax.set_xlabel("Vmax_CV multiplier")
    ax.set_ylabel("g_H multiplier")
    ax.legend(frameon=False)
    clean(ax)

    ax = axes[2]
    groups = ["low_reserve_pair", "high_reserve_pair"]
    best = [r062["conditional_group_rankings"][g]["near_best_summary"]["near_best_count"] for g in groups]
    ax.bar(range(2), best, color=[COLORS["blue"], COLORS["green"]])
    ax.set_xticks(range(2), ["low\nreserve", "high\nreserve"])
    ax.set_ylabel("Near-best candidates")
    clean(ax)

    ax = axes[3]
    cats = []
    vals = []
    for d in directions:
        st = r048["fit_directions"][d]["digitization_interval_rank_stability"]
        cats.append(d.replace("fit_", "").replace("_reserve_", "\nreserve "))
        vals.append(st["unique_winners"])
    ax.bar(range(len(cats)), vals, color=COLORS["purple"])
    ax.set_xticks(range(len(cats)), cats)
    ax.set_ylabel("Unique winners under corners")
    clean(ax)

    ax = axes[4]
    x = [0, 1]
    low_mean = r062["source_groups"]["low_reserve_pair"]["mean_ratios"]
    high_mean = r062["source_groups"]["high_reserve_pair"]["mean_ratios"]
    ax.plot(x, [low_mean["maximal_to_basal"], high_mean["maximal_to_basal"]], marker="o", color=COLORS["blue"], label="maximal/basal")
    ax.plot(x, [low_mean["spare_to_basal"], high_mean["spare_to_basal"]], marker="s", color=COLORS["orange"], label="spare/basal")
    ax.set_xticks(x, ["low", "high"])
    ax.set_ylabel("Conditional group mean")
    ax.legend(frameon=False)
    clean(ax)

    ax = axes[5]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    gate = r062["claim_gate"]
    lines = [f"absolute calibration: {gate['absolute_calibration_allowed']}", f"blind pooling: {gate['blind_pooling_allowed']}", f"maximal/spare contract: {gate['maximal_spare_contract_used']}", f"MCMC figure: {gate['figure1_mcmc_allowed']}"]
    box(ax, (0.08, 0.20), (0.84, 0.58), "Claim gate\n" + "\n".join(lines), COLORS["pale_orange"], COLORS["orange"], fontsize=7.2)
    return save(fig, "r071_sfigure_s2_restricted_mapping_sensitivity")


def hybrid_s3() -> tuple[Path, Path]:
    summary = read_csv(RUNS / "R025" / "summary.csv")
    metrics = read_csv(RUNS / "R025" / "metrics.csv")
    preds = read_csv(RUNS / "R025" / "predictions.csv")
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 7.0), constrained_layout=True)
    axes = axes.ravel()
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)
    models = ["ode", "neural", "hybrid"]
    colors = [COLORS["gray"], COLORS["orange"], COLORS["blue"]]
    smap = {r["model"]: r for r in summary}
    axes[0].bar(range(3), [float(smap[m]["trajectory_rmse_mean"]) for m in models], yerr=[float(smap[m]["trajectory_rmse_sd"]) for m in models], color=colors, capsize=3)
    axes[0].set_xticks(range(3), [m.title() for m in models]); axes[0].set_ylabel("Trajectory RMSE"); clean(axes[0])
    axes[1].bar(range(3), [float(smap[m]["endpoint_rmse_mean"]) for m in models], color=colors)
    axes[1].set_xticks(range(3), [m.title() for m in models]); axes[1].set_ylabel("Endpoint RMSE"); clean(axes[1])
    ax = axes[2]
    for off, model, color in [(-0.13, "neural", COLORS["orange"]), (0.13, "hybrid", COLORS["blue"]), (0.0, "ode", COLORS["gray"] )]:
        rows = sorted([r for r in metrics if r["model"] == model], key=lambda r: int(r["seed"]))
        ax.scatter([int(r["seed"]) + off for r in rows], [float(r["trajectory_rmse"]) for r in rows], color=color, s=38, label=model.title())
    ax.set_xticks([0, 1, 2], ["0", "1", "2"]); ax.set_xlabel("Seed"); ax.set_ylabel("Trajectory RMSE"); ax.legend(frameon=False); clean(ax)
    rows = [r for r in preds if r["seed"] == "0" and r["case_index"] == "0"]
    for idx, state in enumerate(["x1", "x2"]):
        ax = axes[3 + idx]
        for model, color in [("neural", COLORS["orange"]), ("hybrid", COLORS["blue"] )]:
            rs = sorted([r for r in rows if r["model"] == model], key=lambda r: float(r["time_s"]))
            ax.plot([float(r["time_s"]) for r in rs], [float(r[f"pred_{state}"]) for r in rs], color=color, lw=1.3, label=model.title())
        target = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: float(r["time_s"]))
        ax.plot([float(r["time_s"]) for r in target], [float(r[f"target_{state}"]) for r in target], color=COLORS["dark"], lw=1.4, label="Reference")
        ax.set_xlabel("Time"); ax.set_ylabel(state); ax.legend(frameon=False); clean(ax)
    ax = axes[5]
    n = sorted([r for r in rows if r["model"] == "neural"], key=lambda r: float(r["time_s"]))
    h = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: float(r["time_s"]))
    ne = np.abs(np.array([float(r["target_x1"]) - float(r["pred_x1"]) for r in n]))
    he = np.abs(np.array([float(r["target_x1"]) - float(r["pred_x1"]) for r in h]))
    ax.scatter(ne, he, s=12, color=COLORS["purple"], alpha=0.75)
    mx = max(float(ne.max()), float(he.max()))
    ax.plot([0, mx], [0, mx], color="0.5", ls="--", lw=1)
    ax.set_xlabel("Neural absolute error")
    ax.set_ylabel("Hybrid absolute error")
    clean(ax)
    return save(fig, "r071_sfigure_s3_hybrid_benchmark_details")


def phase_s4() -> tuple[Path, Path]:
    resolved = read_csv(RUNS / "R014B" / "resolved_transition_grid.csv")
    band = read_csv(RUNS / "R014B" / "transition_band_summary.csv")
    residual = read_csv(RUNS / "R009" / "additive_proxy_residuals.csv")
    robust = read_csv(RUNS / "R010" / "robustness_summary.csv")
    ablation = read_csv(RUNS / "R009" / "mechanism_ablation_summary.csv")
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 7.0), constrained_layout=True)
    axes = axes.ravel()
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)
    xs = np.array(sorted({as_float(r, "rotenone_inhibition") for r in resolved}))
    ys = np.array(sorted({as_float(r, "paraquat_index") for r in resolved}))
    lookup = {(as_float(r, "rotenone_inhibition"), as_float(r, "paraquat_index")): r for r in resolved}
    dpsi = np.array([[as_float(lookup[(x, y)], "resolved_final_dpsi_mv") for x in xs] for y in ys])
    cls = np.array([[0 if lookup[(x, y)]["resolved_endpoint_class"] == "near_fixed_physiological_endpoint" else 1 for x in xs] for y in ys])
    axes[0].pcolormesh(xs * 100, ys, cls, shading="auto", cmap=ListedColormap([COLORS["green"], COLORS["purple"]]), vmin=0, vmax=1)
    axes[0].set_xlabel("Rotenone (%)"); axes[0].set_ylabel("Paraquat index"); clean(axes[0])
    mesh = axes[1].pcolormesh(xs * 100, ys, dpsi, shading="auto", cmap="viridis")
    axes[1].set_xlabel("Rotenone (%)"); axes[1].set_ylabel("Paraquat index"); fig.colorbar(mesh, ax=axes[1], pad=0.02).set_label("Final DPsi (mV)") ; clean(axes[1])
    pq = [as_float(r, "paraquat_index") for r in band]
    axes[2].plot(pq, [as_float(r, "highest_physiological_rotenone") * 100 for r in band], marker="o", color=COLORS["green"], label="highest physiological")
    axes[2].plot(pq, [as_float(r, "lowest_depolarized_rotenone") * 100 for r in band], marker="s", color=COLORS["purple"], label="lowest depolarized")
    axes[2].set_xlabel("Paraquat index"); axes[2].set_ylabel("Rotenone (%)"); axes[2].legend(frameon=False); clean(axes[2])
    sx = np.array(sorted({as_float(r, "rotenone_inhibition") for r in residual}))
    sy = np.array(sorted({as_float(r, "paraquat_index") for r in residual}))
    sl = {(as_float(r, "rotenone_inhibition"), as_float(r, "paraquat_index")): r for r in residual}
    sm = np.array([[as_float(sl[(x, y)], "dpsi_synergy_residual_mv") for x in sx] for y in sy])
    im = axes[3].pcolormesh(sx * 100, sy, sm, shading="auto", cmap="PuOr")
    axes[3].set_xlabel("Rotenone (%)"); axes[3].set_ylabel("Paraquat index"); fig.colorbar(im, ax=axes[3], pad=0.02).set_label("DPsi residual"); clean(axes[3])
    axes[4].bar(range(len(ablation)), [as_float(r, "depolarized_endpoint_count") for r in ablation], color=[COLORS["blue"]] + ["0.65"] * (len(ablation) - 1))
    axes[4].set_xticks(range(len(ablation)), [r["model_variant"].replace("no_", "no\n").replace("_", " ") for r in ablation], rotation=20, ha="right")
    axes[4].set_ylabel("Depolarized endpoints") ; clean(axes[4])
    axes[5].bar(range(len(robust)), [as_float(r, "depolarized_endpoint_count") for r in robust], color=[COLORS["blue"] if r["run_axis"] == "initial_condition" else COLORS["orange"] for r in robust])
    axes[5].set_xticks(range(len(robust)), [r["variant"].replace("_", "\n") for r in robust], rotation=20, ha="right")
    axes[5].set_ylabel("Depolarized endpoints") ; clean(axes[5])
    return save(fig, "r071_sfigure_s4_phase_robustness_details")


def ews_s5() -> tuple[Path, Path]:
    qc = read_json(RUNS / "R021" / "qc_summary.json")
    split = read_csv(RUNS / "R021" / "split_manifest.csv")
    events = read_csv(RUNS / "R021" / "events.csv")
    metrics = read_json(RUNS / "R023" / "locked_test_metrics.json")
    controls = read_json(RUNS / "R023" / "negative_controls.json")
    preds = read_csv(RUNS / "R023" / "test_predictions.csv")
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 7.0), constrained_layout=True)
    axes = axes.ravel()
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)
    axes[0].bar(qc["split_counts"].keys(), qc["split_counts"].values(), color=[COLORS["blue"], COLORS["orange"], COLORS["green"]])
    axes[0].set_ylabel("Groups") ; clean(axes[0])
    counts = qc["endpoint_class_counts"]
    axes[1].bar(["physiological", "depolarized"], [counts["near_fixed_physiological_endpoint"], counts["near_fixed_depolarized_endpoint"]], color=[COLORS["green"], COLORS["purple"]])
    axes[1].set_ylabel("Endpoint-labelled groups"); clean(axes[1])
    positive_times = [float(r["event_time_s"]) for r in events if r["label"] == "1" and r["event_time_s"] != "nan"]
    axes[2].hist(positive_times, bins=18, color=COLORS["purple"], alpha=0.85)
    axes[2].set_xlabel("Event time (s)"); axes[2].set_ylabel("Positive groups"); clean(axes[2])
    names = [m["model"] for m in metrics]
    axes[3].bar(range(len(names)), [m["auroc"] for m in metrics], color=COLORS["blue"], label="AUROC")
    axes[3].scatter(range(len(names)), [m["auprc"] for m in metrics], color=COLORS["green"], label="AUPRC", zorder=3)
    axes[3].set_xticks(range(len(names)), [n.replace("_", "\n") for n in names], rotation=20)
    axes[3].set_ylim(0, 1.05); axes[3].legend(frameon=False); clean(axes[3])
    axes[4].bar(range(len(names)), [m["brier"] for m in metrics], color=COLORS["orange"])
    axes[4].set_xticks(range(len(names)), [n.replace("_", "\n") for n in names], rotation=20); axes[4].set_ylabel("Brier score"); clean(axes[4])
    perm = controls["group_label_permutation"]
    tshuf = controls["within_trajectory_time_shuffle"]
    axes[5].errorbar([0], [perm["auroc_median"]], yerr=[[perm["auroc_median"] - perm["auroc_ci_low"]], [perm["auroc_ci_high"] - perm["auroc_median"]]], fmt="o", color=COLORS["gray"], capsize=4, label="label permutation")
    axes[5].scatter([1], [tshuf["auroc"]], color=COLORS["orange"], label="time shuffle")
    axes[5].scatter([2], [perm["observed_locked_auroc"]], color=COLORS["blue"], label="observed locked")
    axes[5].set_xticks([0, 1, 2], ["baseline\npermuted", "EWS\ntime shuffled", "baseline\nobserved"]); axes[5].set_ylim(0, 1.05); axes[5].set_ylabel("AUROC"); axes[5].legend(frameon=False); clean(axes[5])
    return save(fig, "r071_sfigure_s5_ews_locked_test_details")


def reproducibility_s6(outputs_so_far: dict[str, tuple[Path, Path]]) -> tuple[Path, Path]:
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.7), constrained_layout=True)
    for ax, letter in zip(axes, ascii_lowercase):
        panel_label(ax, letter)
    ax = axes[0]; ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    for i, txt in enumerate(["Audited\ninput logs", "R071-S\ngenerator", "Figures", "Manifest\nchecksums"]):
        x = 0.05 + i * 0.24
        box(ax, (x, 0.44), (0.17, 0.22), txt, COLORS["pale_blue"], COLORS["blue"], fontsize=6.8, bold=True)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + 0.17, 0.55), (x + 0.24, 0.55), arrowstyle="->", mutation_scale=9, color=COLORS["gray"]))
    ax = axes[1]
    input_paths = sorted(RUNS.rglob("*.csv")) + sorted(RUNS.rglob("*.json"))
    sizes = [p.stat().st_size / 1024 for p in input_paths if p.exists()]
    labels = [p.parent.name + "/" + p.name[:16] for p in input_paths if p.exists()]
    order = np.argsort(sizes)[-8:]
    ax.barh(range(len(order)), [sizes[i] for i in order], color=COLORS["green"])
    ax.set_yticks(range(len(order)), [labels[i] for i in order], fontsize=6.0)
    ax.set_xlabel("Input file size (KB)")
    clean(ax)
    ax = axes[2]; ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    text = f"Generated assets\n{len(outputs_so_far)} supplementary figures before manifest\n\nScope\ncomputational/source-audit only\nno assay, imaging, organism, or person-level data generated"
    box(ax, (0.08, 0.20), (0.84, 0.58), text, COLORS["pale_green"], COLORS["green"], fontsize=7.4)
    return save(fig, "r071_sfigure_s6_reproducibility_map")


def key_inputs() -> list[Path]:
    return [
        RUNS / "R042" / "digitization_uncertainty_propagation.json",
        RUNS / "R047" / "cross_source_formula_coordination.json",
        RUNS / "R048" / "maximal_spare_restricted_mapping.json",
        RUNS / "R062" / "conditional_heterogeneity_mapping.json",
        RUNS / "R025" / "summary.csv",
        RUNS / "R025" / "metrics.csv",
        RUNS / "R025" / "predictions.csv",
        RUNS / "R014B" / "resolved_transition_grid.csv",
        RUNS / "R014B" / "transition_band_summary.csv",
        RUNS / "R009" / "additive_proxy_residuals.csv",
        RUNS / "R009" / "mechanism_ablation_summary.csv",
        RUNS / "R010" / "robustness_summary.csv",
        RUNS / "R021" / "qc_summary.json",
        RUNS / "R021" / "split_manifest.csv",
        RUNS / "R021" / "events.csv",
        RUNS / "R023" / "locked_test_metrics.json",
        RUNS / "R023" / "negative_controls.json",
    ]


def write_tables(outputs: dict[str, tuple[Path, Path]]) -> list[Path]:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    row_end = r"\\"
    records = source_records()
    metrics = read_json(RUNS / "R023" / "locked_test_metrics.json")
    controls = read_json(RUNS / "R023" / "negative_controls.json")
    hybrid = read_csv(RUNS / "R025" / "metrics.csv")
    phase = read_csv(RUNS / "R010" / "robustness_summary.csv")
    tables = {}
    tables["r071_legacy_unused_supp_table_s1_source_ratio_intervals.tex"] = "\n".join([
        r"\begin{table}[t]", r"\centering", r"\caption{R071 supplementary source-local OCR ratio intervals.}", r"\label{tab:r071_legacy_unused_supp_source_ratios}", r"\begin{tabular}{lllll}", r"\toprule", f"Record & Source & Group & Maximal/basal & Spare/basal {row_end}", r"\midrule",
        *[f"{r['id']} & {r['source']} & {r['group']} & {r['max']['nominal']:.3f} [{r['max']['low']:.3f}, {r['max']['high']:.3f}] & {r['spare']['nominal']:.3f} [{r['spare']['low']:.3f}, {r['spare']['high']:.3f}] {row_end}" for r in records],
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])
    tables["r071_legacy_unused_supp_table_s2_hybrid_seed_metrics.tex"] = "\n".join([
        r"\begin{table}[t]", r"\centering", r"\caption{R071 supplementary per-seed hidden-residual benchmark metrics.}", r"\label{tab:r071_legacy_unused_supp_hybrid_seed_metrics}", r"\begin{tabular}{llll}", r"\toprule", f"Model & Seed & Trajectory RMSE & Endpoint RMSE {row_end}", r"\midrule",
        *[f"{r['model']} & {r['seed']} & {float(r['trajectory_rmse']):.4f} & {float(r['endpoint_rmse']):.4f} {row_end}" for r in hybrid],
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])
    tables["r071_legacy_unused_supp_table_s3_phase_robustness_summary.tex"] = "\n".join([
        r"\begin{table}[t]", r"\centering", r"\caption{R071 supplementary reduced-ODE robustness summary.}", r"\label{tab:r071_legacy_unused_supp_phase_robustness}", r"\begin{tabular}{lllll}", r"\toprule", f"Axis & Variant & Conditions & Depolarized endpoints & Mean DPsi drop {row_end}", r"\midrule",
        *[f"{r['run_axis']} & {r['variant']} & {r['n_conditions']} & {r['depolarized_endpoint_count']} & {float(r['mean_dpsi_drop_0_8_to_0_9']):.3f} {row_end}" for r in phase],
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])
    tables["r071_legacy_unused_supp_table_s4_ews_negative_controls.tex"] = "\n".join([
        r"\begin{table}[t]", r"\centering", r"\caption{R071 supplementary locked EWS metrics and negative controls.}", r"\label{tab:r071_legacy_unused_supp_ews_controls}", r"\begin{tabular}{llll}", r"\toprule", f"Item & Metric & Value & Boundary {row_end}", r"\midrule",
        *[f"{m['model']} & AUROC/AUPRC/Brier & {m['auroc']:.3f}/{m['auprc']:.3f}/{m['brier']:.4f} & locked computational diagnostic {row_end}" for m in metrics],
        f"label permutation & AUROC median [CI] & {controls['group_label_permutation']['auroc_median']:.3f} [{controls['group_label_permutation']['auroc_ci_low']:.3f}, {controls['group_label_permutation']['auroc_ci_high']:.3f}] & negative-control sanity check {row_end}",
        f"time shuffle & AUROC/AUPRC & {controls['within_trajectory_time_shuffle']['auroc']:.3f}/{controls['within_trajectory_time_shuffle']['auprc']:.3f} & negative-control sanity check {row_end}",
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])
    tables["r071_legacy_unused_supp_table_s5_reproducibility_inputs.tex"] = "\n".join([
        r"\begin{table}[t]", r"\centering", r"\caption{R071 supplementary reproducibility input manifest.}", r"\label{tab:r071_legacy_unused_supp_repro_inputs}", r"\begin{tabular}{lll}", r"\toprule", f"Input artifact & Size (bytes) & SHA-256 prefix {row_end}", r"\midrule",
        *[f"{rel(p)} & {p.stat().st_size} & {sha256(p)[:12]} {row_end}" for p in key_inputs() if p.exists()],
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])
    paths = []
    for name, text in tables.items():
        path = TABLE_DIR / name
        path.write_text(text + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def write_includes(outputs: dict[str, tuple[Path, Path]]) -> Path:
    captions = {
        "r071_sfigure_s1_source_contract_audit": ("Source-contract audit for the OCR evidence layer.", "fig:r071_supp_source_contract"),
        "r071_sfigure_s2_restricted_mapping_sensitivity": ("Restricted maximal/spare mapping and heterogeneity sensitivity.", "fig:r071_supp_mapping"),
        "r071_sfigure_s3_hybrid_benchmark_details": ("Per-seed and trajectory details for the controlled Hybrid Neural-ODE benchmark.", "fig:r071_supp_hybrid"),
        "r071_sfigure_s4_phase_robustness_details": ("Reduced-ODE phase, synergy, ablation, and robustness details.", "fig:r071_supp_phase"),
        "r071_sfigure_s5_ews_locked_test_details": ("Locked EWS cohort, metric, and negative-control details.", "fig:r071_supp_ews"),
        "r071_sfigure_s6_reproducibility_map": ("R071 supplementary reproducibility map and input-file footprint.", "fig:r071_supp_repro"),
    }
    chunks = ["% R071 supplementary figure include snippets. Generated from computational/source-audit assets."]
    for stem, (_, pdf) in outputs.items():
        caption, lab = captions[stem]
        chunks.extend(["", r"\begin{figure}[t]", r"    \centering", f"    \\includegraphics[width=0.95\\textwidth]{{{rel(pdf)}}}", f"    \\caption{{{caption} These supplementary panels report only computational or source-audited evidence; no new assay, imaging, organism, or person-level data were generated.}}", f"    \\label{{{lab}}}", r"\end{figure}"])
    INCLUDES.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return INCLUDES


def main() -> int:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    outputs = {
        "r071_sfigure_s1_source_contract_audit": source_audit_s1(),
        "r071_sfigure_s2_restricted_mapping_sensitivity": mapping_s2(),
        "r071_sfigure_s3_hybrid_benchmark_details": hybrid_s3(),
        "r071_sfigure_s4_phase_robustness_details": phase_s4(),
        "r071_sfigure_s5_ews_locked_test_details": ews_s5(),
    }
    outputs["r071_sfigure_s6_reproducibility_map"] = reproducibility_s6(outputs)
    includes = write_includes(outputs)
    manifest = {
        "run_id": "R071-S",
        "status": "complete",
        "scope": "computational/source-audit supplementary material only",
        "figures": {stem: {"png": rel(png), "pdf": rel(pdf), "png_sha256": sha256(png), "pdf_sha256": sha256(pdf)} for stem, (png, pdf) in outputs.items()},
        "supplementary_tables": "see figures/r071/r071_manifest.json; all R071 tables are supplementary",
        "includes": {"path": rel(includes), "sha256": sha256(includes)},
        "inputs": {rel(p): sha256(p) for p in key_inputs() if p.exists()},
        "manuscript_modified": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"figures": {k: [rel(v[0]), rel(v[1])] for k, v in outputs.items()}, "includes": rel(includes), "manifest": rel(MANIFEST)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
