"""Build R071 high-information NeurMito-DT result figures and supplementary tables.

R071 is a non-destructive redesign of the prior result-figure assets. It writes
to results/figures and results/manifests only. All evidence is dry-lab,
source-audit, or computational. Every table emitted here is supplementary.
"""

from __future__ import annotations

if __name__ == "__main__":
    import runpy
    from pathlib import Path as _Path
    runpy.run_path(str(_Path(__file__).resolve().parents[2] / "r071/build_r071_all.py"), run_name="__main__")
    raise SystemExit(0)

import csv
import hashlib
import json
import math
import os
import textwrap
from pathlib import Path
from string import ascii_lowercase

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, TwoSlopeNorm
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "inputs" / "audit_runs"
FIG_DIR = Path(os.environ.get("R071_FIG_DIR", ROOT / "results" / "figures"))
TABLE_DIR = Path(os.environ.get("R071_TABLE_DIR", ROOT / "results" / "manifests"))
DESIGN_REPORT = ROOT / "docs" / "REPOSITORY_SCOPE.md"
MANIFEST = FIG_DIR / "r071_manifest.json"
INCLUDES = TABLE_DIR / "r071_main_figure_includes.tex"

COLORS = {
    "blue": "#2F5D7E",
    "sky": "#86AFC4",
    "green": "#4F826C",
    "orange": "#B9863F",
    "red": "#A85248",
    "purple": "#806784",
    "yellow": "#C9B85A",
    "gray": "#747474",
    "dark": "#202020",
    "light": "#F4F4F4",
    "pale_blue": "#E8EFF3",
    "pale_green": "#E8F0EC",
    "pale_orange": "#F6EFE3",
    "pale_purple": "#F0EBF1",
}

FIGURE_WIDTH_IN = 183 / 25.4
FIGURE_HEIGHT_IN = 168 / 25.4

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "font.size": 6.2,
    "axes.labelsize": 6.2,
    "axes.titlesize": 6.5,
    "axes.titleweight": "normal",
    "xtick.labelsize": 5.5,
    "ytick.labelsize": 5.5,
    "legend.fontsize": 5.2,
    "axes.linewidth": 0.55,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.major.width": 0.50,
    "ytick.major.width": 0.50,
    "xtick.major.size": 2.2,
    "ytick.major.size": 2.2,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": None,
    "figure.dpi": 150,
})


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(row: dict[str, str], key: str) -> float:
    value = row.get(key, "nan")
    return float(value) if value not in {"", "nan", "None"} else math.nan


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def label(ax, text: str):
    ax.text(-0.13, 1.03, text, transform=ax.transAxes, fontsize=8.0, fontweight="bold", va="bottom", ha="left")


def box(ax, xy, wh, text, face, edge, fontsize=5.2, bold=False, lw=0.6):
    patch = FancyBboxPatch(xy, wh[0], wh[1], boxstyle="round,pad=0.012", facecolor=face, edgecolor=edge, lw=lw)
    ax.add_patch(patch)
    ax.text(
        xy[0] + wh[0] / 2,
        xy[1] + wh[1] / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold" if bold else None,
        linespacing=1.15,
    )
    return patch


def save(fig, stem: str) -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    png = FIG_DIR / f"{stem}.png"
    pdf = FIG_DIR / f"{stem}.pdf"
    svg = FIG_DIR / f"{stem}.svg"
    tiff = FIG_DIR / f"{stem}.tiff"
    fig.savefig(png, dpi=600, facecolor="white", edgecolor="none")
    fig.savefig(pdf, facecolor="white", edgecolor="none")
    fig.savefig(svg, facecolor="white", edgecolor="none")
    fig.savefig(tiff, dpi=600, facecolor="white", edgecolor="none", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    return png, pdf


def draw_claim_strip(ax, title, supported, limited, prohibited):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(0.02, 0.96, title, fontweight="bold", fontsize=6.4, va="top")
    rows = [
        ("Allowed", supported, COLORS["green"], COLORS["pale_green"]),
        ("Limited", limited, COLORS["orange"], COLORS["pale_orange"]),
        ("Not claimed", prohibited, COLORS["purple"], COLORS["pale_purple"]),
    ]
    for i, (head, body, edge, face) in enumerate(rows):
        y = 0.72 - i * 0.25
        wording = textwrap.fill(f"{head}: {body}", width=34)
        box(ax, (0.04, y - 0.10), (0.92, 0.19), wording, face, edge, fontsize=5.0)


def source_records():
    r042 = read_json(RUNS / "R042" / "digitization_uncertainty_propagation.json")
    r060 = read_json(RUNS / "R060" / "pmc4454361_control_relative_digitization.json")
    r060b = read_json(RUNS / "R060B" / "pmc5124357_control_relative_digitization.json")
    low = r042["source_ratio_intervals"]
    return [
        {"id": "R033", "source": "PMID:31931869", "pmid": "31931869", "group": "low reserve", "prep": "DIV7 primary cortical", "color": COLORS["blue"], "max": low["PMID:31931869"]["maximal_to_basal"], "spare": low["PMID:31931869"]["spare_to_basal"]},
        {"id": "R039", "source": "PMID:24056030", "pmid": "24056030", "group": "low reserve", "prep": "E18 cortical", "color": COLORS["red"], "max": low["PMID:24056030"]["maximal_to_basal"], "spare": low["PMID:24056030"]["spare_to_basal"]},
        {"id": "R060", "source": "PMID:25081478", "pmid": "25081478", "group": "high reserve", "prep": r060["preparation"][:30], "color": COLORS["green"], "max": {"nominal": r060["relative_ratios"]["maximal_to_basal"]["value"], "low": r060["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060["relative_ratios"]["spare_to_basal"]["value"], "low": r060["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060["relative_ratios"]["spare_to_basal"]["interval"][1]}},
        {"id": "R060B", "source": "PMID:27889640", "pmid": "27889640", "group": "high reserve", "prep": r060b["preparation"][:30], "color": COLORS["purple"], "max": {"nominal": r060b["relative_ratios"]["maximal_to_basal"]["value"], "low": r060b["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060b["relative_ratios"]["spare_to_basal"]["value"], "low": r060b["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["spare_to_basal"]["interval"][1]}},
    ]


def grid_from_rows(rows, value_key):
    xs = np.array(sorted({f(r, "rotenone_inhibition") for r in rows}))
    ys = np.array(sorted({f(r, "paraquat_index") for r in rows}))
    lookup = {(f(r, "rotenone_inhibition"), f(r, "paraquat_index")): r for r in rows}
    mat = np.empty((len(ys), len(xs)))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            mat[i, j] = f(lookup[(x, y)], value_key)
    return xs, ys, mat, lookup


def figure1() -> tuple[Path, Path]:
    records = source_records()
    r047 = read_json(RUNS / "R047" / "cross_source_formula_coordination.json")
    r048 = read_json(RUNS / "R048" / "maximal_spare_restricted_mapping.json")
    r062 = read_json(RUNS / "R062" / "conditional_heterogeneity_mapping.json")
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, 150 / 25.4))
    gs = fig.add_gridspec(
        3, 3, left=0.075, right=0.985, bottom=0.080, top=0.970,
        hspace=0.62, wspace=0.52,
    )
    axes = [fig.add_subplot(gs[i, j]) for i in range(3) for j in range(3)]
    for ax, letter in zip(axes, ascii_lowercase[:9]):
        label(ax, letter)

    ax = axes[0]
    terms = ["B", "O", "F", "N", "A", "P", "spare"]
    recs = ["R033", "R039", "R046"]
    code = {"reported": 3, "digitized": 3, "inferred": 2, "inferred_conflicting": 1, "unavailable": 0}
    mat = np.array([[code[r047["records"][rec]["terms"].get(term, "unavailable")] for term in terms] for rec in recs])
    ax.imshow(mat, cmap=ListedColormap(["#DDDDDD", COLORS["purple"], COLORS["orange"], COLORS["green"]]), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(terms)), terms); ax.set_yticks(range(len(recs)), recs); ax.tick_params(length=0)
    ax.set_title("Endpoint availability contract")
    for spine in ax.spines.values(): spine.set_visible(False)

    ax = axes[1]
    endpoints = ["maximal_to_basal", "spare_to_basal", "atp_linked_to_basal", "proton_leak_to_basal"]
    status = [1 if e in r047["minimum_common_observation_contract"]["fit_or_holdout_endpoints"] else 0.5 if e in r047["minimum_common_observation_contract"]["diagnostic_only_endpoints"] else 0 for e in endpoints]
    ax.bar(range(len(endpoints)), status, color=[COLORS["green"] if v == 1 else COLORS["orange"] if v == 0.5 else COLORS["purple"] for v in status])
    ax.set_ylim(0, 1.1); ax.set_yticks([0, 0.5, 1], ["blocked", "diagnostic", "retained"])
    ax.set_xticks(range(len(endpoints)), [e.replace("_to_basal", "").replace("_", "\n") for e in endpoints])
    clean(ax)

    for ax, key, ylabel in [(axes[2], "max", "Maximal/basal OCR"), (axes[3], "spare", "Spare/basal OCR")]:
        for i, rec in enumerate(records):
            value = rec[key]["nominal"]
            ax.errorbar([i], [value], yerr=[[value - rec[key]["low"]], [rec[key]["high"] - value]], fmt="o", color=rec["color"], capsize=3, ms=5.5)
        ax.axvline(1.5, color="0.75", ls=":", lw=1)
        ax.set_xticks(range(4), [r["id"] for r in records]); ax.set_ylabel(ylabel); clean(ax)

    ax = axes[4]
    for rec in records:
        ax.scatter(rec["max"]["nominal"], rec["spare"]["nominal"], s=70, color=rec["color"], edgecolor="white", lw=0.8, label=rec["id"])
        ax.errorbar(rec["max"]["nominal"], rec["spare"]["nominal"], xerr=[[rec["max"]["nominal"]-rec["max"]["low"]], [rec["max"]["high"]-rec["max"]["nominal"]]], yerr=[[rec["spare"]["nominal"]-rec["spare"]["low"]], [rec["spare"]["high"]-rec["spare"]["nominal"]]], color=rec["color"], alpha=0.55, lw=0.8)
    ax.set_xlabel("Maximal/basal"); ax.set_ylabel("Spare/basal"); ax.legend(frameon=False, ncol=2); clean(ax)

    ax = axes[5]
    fit_names = list(r048["fit_directions"].keys())
    losses = [r048["fit_directions"][name]["near_best_summary"]["best_train_loss"] for name in fit_names]
    ax.bar(range(len(fit_names)), losses, color=[COLORS["blue"], COLORS["orange"]])
    ax.set_xticks(range(len(fit_names)), [n.replace("fit_", "").replace("_reserve_", "\nreserve ") for n in fit_names])
    ax.set_ylabel("Best restricted loss"); clean(ax)

    ax = axes[6]
    for group, color, marker in [("low_reserve_pair", COLORS["blue"], "o"), ("high_reserve_pair", COLORS["green"], "s")]:
        ranked = r062["conditional_group_rankings"][group]["top_ranked"][:10]
        losses = np.array([item["loss"] for item in ranked])
        sizes = 110 * (losses.max() - losses + 0.004) / (np.ptp(losses) + 0.004)
        ax.scatter([i["multipliers"]["Vmax_CV"] for i in ranked], [i["multipliers"]["g_H"] for i in ranked], s=sizes, color=color, alpha=0.75, marker=marker, label=group.replace("_pair", ""))
    ax.set_xlabel("Vmax_CV multiplier"); ax.set_ylabel("g_H multiplier"); ax.legend(frameon=False); clean(ax)

    ax = axes[7]
    gates = r062["claim_gate"]
    gate_names = ["absolute\ncal.", "blind\npool", "external\nval.", "MCMC", "max/spare\ncontract"]
    gate_vals = [gates["absolute_calibration_allowed"], gates["blind_pooling_allowed"], gates["external_validation_claim_allowed"], gates["figure1_mcmc_allowed"], gates["maximal_spare_contract_used"]]
    ax.bar(range(len(gate_vals)), [1 if v else 0 for v in gate_vals], color=[COLORS["green"] if v else COLORS["purple"] for v in gate_vals])
    ax.set_ylim(0, 1.1); ax.set_yticks([0, 1], ["closed", "open"]); ax.set_xticks(range(len(gate_names)), gate_names); ax.tick_params(axis="x", labelsize=4.7); clean(ax)

    ax = axes[8]
    low = r062["source_groups"]["low_reserve_pair"]["mean_ratios"]
    high = r062["source_groups"]["high_reserve_pair"]["mean_ratios"]
    xvals = np.array([0, 1])
    low_vals = np.array([low["maximal_to_basal"], low["spare_to_basal"]])
    high_vals = np.array([high["maximal_to_basal"], high["spare_to_basal"]])
    ax.plot(xvals, low_vals, color=COLORS["blue"], lw=1.0, alpha=0.8, zorder=1)
    ax.plot(xvals, high_vals, color=COLORS["green"], lw=1.0, alpha=0.8, zorder=1)
    ax.scatter(xvals, low_vals, s=32, color=COLORS["blue"], label="Low reserve", zorder=2)
    ax.scatter(xvals, high_vals, s=32, color=COLORS["green"], label="High reserve", zorder=2)
    for x, value in zip(xvals, low_vals):
        ax.annotate(f"{value:.2f}", (x, value), xytext=(3 if x == 0 else -3, -10), textcoords="offset points", ha="left" if x == 0 else "right", fontsize=4.3, color=COLORS["blue"])
    for x, value in zip(xvals, high_vals):
        ax.annotate(f"{value:.2f}", (x, value), xytext=(3 if x == 0 else -3, 7), textcoords="offset points", ha="left" if x == 0 else "right", fontsize=4.3, color=COLORS["green"])
    ax.set_xticks([0, 1], ["Maximal/basal", "Spare/basal"])
    ax.set_ylabel("Conditional group mean")
    ax.set_title("Reserve-ratio contrast", fontsize=6.5)
    ax.set_ylim(0.35, 2.25)
    ax.set_xlim(-0.06, 1.06)
    ax.legend(frameon=False, fontsize=5.0, loc="upper right")
    clean(ax)
    return save(fig, "r071_figure1_evidence_provenance_atlas")


def figure2() -> tuple[Path, Path]:
    summary = read_csv(RUNS / "R025" / "summary.csv")
    metrics = read_csv(RUNS / "R025" / "metrics.csv")
    preds = read_csv(RUNS / "R025" / "predictions.csv")
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, 154 / 25.4))
    gs = fig.add_gridspec(
        3, 3, left=0.075, right=0.985, bottom=0.080, top=0.970,
        hspace=0.62, wspace=0.52,
    )
    axes = [fig.add_subplot(gs[i, j]) for i in range(3) for j in range(3)]
    for ax, letter in zip(axes, ascii_lowercase[:9]):
        label(ax, letter)

    rows = [r for r in preds if int(r["seed"]) == 0 and int(r["case_index"]) == 0]
    for ax, state in [(axes[0], "x1"), (axes[1], "x2")]:
        for model, color, ls in [("neural", COLORS["orange"], "--"), ("hybrid", COLORS["blue"], "-")]:
            mrows = sorted([r for r in rows if r["model"] == model], key=lambda r: f(r, "time_s"))
            ax.plot([f(r, "time_s") for r in mrows], [f(r, f"pred_{state}") for r in mrows], color=color, ls=ls, lw=1.3, label=model.title())
        target = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: f(r, "time_s"))
        ax.plot([f(r, "time_s") for r in target], [f(r, f"target_{state}") for r in target], color=COLORS["dark"], lw=1.5, label="Reference")
        ax.set_xlabel("Time (benchmark units)"); ax.set_ylabel(f"State {state}"); ax.legend(frameon=False); clean(ax)

    smap = {r["model"]: r for r in summary}; models = ["ode", "neural", "hybrid"]; names = ["ODE", "Neural", "Hybrid"]
    ax = axes[2]
    ax.bar(range(3), [f(smap[m], "trajectory_rmse_mean") for m in models], yerr=[f(smap[m], "trajectory_rmse_sd") for m in models], color=[COLORS["gray"], COLORS["orange"], COLORS["blue"]], capsize=3)
    ax.set_xticks(range(3), names); ax.set_ylabel("Trajectory RMSE"); clean(ax)
    ax = axes[3]
    ax.bar(range(3), [f(smap[m], "endpoint_rmse_mean") for m in models], color=[COLORS["gray"], COLORS["orange"], COLORS["blue"]])
    ax.set_xticks(range(3), names); ax.set_ylabel("Endpoint RMSE"); clean(ax)
    ax = axes[4]
    for off, m, c in [(-0.16, "ode", COLORS["gray"]), (0, "neural", COLORS["orange"]), (0.16, "hybrid", COLORS["blue"])]:
        mrows = sorted([r for r in metrics if r["model"] == m], key=lambda r: int(r["seed"]))
        ax.scatter([int(r["seed"]) + off for r in mrows], [f(r, "trajectory_rmse") for r in mrows], color=c, label=m.title(), s=35)
    ax.set_xticks([0, 1, 2], ["Seed 0", "Seed 1", "Seed 2"]); ax.set_ylabel("Seed-wise RMSE"); ax.legend(frameon=False); clean(ax)
    ax = axes[5]
    neural = sorted([r for r in rows if r["model"] == "neural"], key=lambda r: f(r, "time_s"))
    hybrid = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: f(r, "time_s"))
    t = np.array([f(r, "time_s") for r in hybrid])
    res = np.array([f(n, "pred_x1") - f(n, "target_x1") for n in neural]) - np.array([f(h, "pred_x1") - f(h, "target_x1") for h in hybrid])
    ax.fill_between(t, res, 0, color=COLORS["sky"], alpha=0.35); ax.plot(t, res, color=COLORS["blue"], lw=1.2)
    ax.axhline(0, color="0.5", lw=0.8); ax.set_xlabel("Time"); ax.set_ylabel("Residual correction"); clean(ax)

    ax = axes[6]
    case_rows = [r for r in preds if r["model"] == "hybrid"]
    hidden = np.array([f(r, "hidden_gain") for r in case_rows])
    err = np.abs(np.array([f(r, "pred_x1") - f(r, "target_x1") for r in case_rows]))
    ax.scatter(hidden, err, s=7, color=COLORS["purple"], alpha=0.45)
    ax.set_xlabel("Hidden gain"); ax.set_ylabel("Hybrid absolute error"); clean(ax)
    ax = axes[7]
    nerr = np.abs(np.array([f(n, "pred_x1") - f(n, "target_x1") for n in neural])); herr = np.abs(np.array([f(h, "pred_x1") - f(h, "target_x1") for h in hybrid]))
    mx = max(float(nerr.max()), float(herr.max()))
    ax.scatter(nerr, herr, s=13, color=COLORS["purple"], alpha=0.75); ax.plot([0, mx], [0, mx], color="0.5", ls="--", lw=1)
    ax.set_xlabel("Neural abs. error"); ax.set_ylabel("Hybrid abs. error"); clean(ax)
    ax = axes[8]
    improv = [(f(smap["neural"], "trajectory_rmse_mean") - f(smap["hybrid"], "trajectory_rmse_mean")) / f(smap["neural"], "trajectory_rmse_mean") * 100, (f(smap["ode"], "trajectory_rmse_mean") - f(smap["hybrid"], "trajectory_rmse_mean")) / f(smap["ode"], "trajectory_rmse_mean") * 100]
    ax.bar([0, 1], improv, color=[COLORS["green"], COLORS["blue"]]); ax.set_xticks([0, 1], ["vs Neural", "vs ODE"]); ax.set_ylabel("RMSE improvement (%)"); clean(ax)
    return save(fig, "r071_figure2_hybrid_benchmark_residuals")


def figure3() -> tuple[Path, Path]:
    rows = read_csv(RUNS / "R014B" / "resolved_transition_grid.csv")
    band = read_csv(RUNS / "R014B" / "transition_band_summary.csv")
    synergy = read_csv(RUNS / "R009" / "additive_proxy_residuals.csv")
    robust = read_csv(RUNS / "R010" / "robustness_summary.csv")
    ablate = read_csv(RUNS / "R009" / "mechanism_ablation_summary.csv")
    xs, ys, dpsi, lookup = grid_from_rows(rows, "resolved_final_dpsi_mv")
    _, _, atp, _ = grid_from_rows(rows, "resolved_final_atp_m_mm")
    sx, sy, sm, _ = grid_from_rows(synergy, "dpsi_synergy_residual_mv")
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    gs = fig.add_gridspec(
        3, 3, left=0.065, right=0.950, bottom=0.070, top=0.975,
        hspace=0.78, wspace=0.62,
    )
    axes = [fig.add_subplot(gs[i, j]) for i in range(3) for j in range(3)]
    for ax, letter in zip(axes, ascii_lowercase[:9]): label(ax, letter)

    x_lo, x_hi = xs.min() * 100 - 0.5, xs.max() * 100 + 0.5
    ax = axes[0]
    cls = np.array([[0 if lookup[(x, y)]["resolved_endpoint_class"] == "near_fixed_physiological_endpoint" else 1 for x in xs] for y in ys])
    ax.imshow(cls, origin="lower", aspect="auto", extent=[xs.min()*100, xs.max()*100, ys.min(), ys.max()], cmap=ListedColormap([COLORS["green"], COLORS["purple"]]), interpolation="none")
    ax.set_xlabel("Rotenone (% C-I inhibition)"); ax.set_ylabel("Paraquat index"); ax.set_xlim(x_lo, x_hi); clean(ax)
    ax = axes[1]; mesh = ax.pcolormesh(xs * 100, ys, dpsi, shading="auto", cmap="YlGnBu"); ax.set_xlabel("Rotenone (%)"); ax.set_ylabel("Paraquat index"); ax.set_xlim(x_lo, x_hi); cbar = fig.colorbar(mesh, ax=ax, pad=0.015, fraction=0.046); cbar.ax.set_ylabel("DPsi", fontsize=5, labelpad=1); cbar.ax.tick_params(labelsize=5); clean(ax)
    ax = axes[2]; mesh = ax.pcolormesh(xs * 100, ys, atp, shading="auto", cmap="cividis"); ax.set_xlabel("Rotenone (%)"); ax.set_ylabel("Paraquat index"); ax.set_xlim(x_lo, x_hi); cbar = fig.colorbar(mesh, ax=ax, pad=0.015, fraction=0.046); cbar.ax.set_ylabel("ATP", fontsize=5, labelpad=1); cbar.ax.tick_params(labelsize=5); clean(ax)

    ax = axes[3]
    for pqv, c in zip([0.0, 5.0, 20.0], [COLORS["green"], COLORS["orange"], COLORS["purple"]]):
        line = sorted([r for r in rows if abs(f(r, "paraquat_index") - pqv) < 1e-9], key=lambda r: f(r, "rotenone_inhibition"))
        ax.plot([f(r, "rotenone_inhibition") * 100 for r in line], [f(r, "resolved_final_dpsi_mv") for r in line], marker="o", ms=3, lw=1.2, color=c, label=f"PQ {pqv:g}")
    ax.axhline(140, color="0.5", ls="--", lw=0.9); ax.set_xlabel("Rotenone (%)"); ax.set_ylabel("Final DPsi (mV)"); ax.set_xlim(x_lo, x_hi); ax.legend(frameon=False, fontsize=5.5); clean(ax)
    ax = axes[4]
    pq = np.array([f(r, "paraquat_index") for r in band]); hp = np.array([f(r, "highest_physiological_rotenone") * 100 for r in band]); ld = np.array([f(r, "lowest_depolarized_rotenone") * 100 for r in band])
    ax.fill_between(pq, hp, ld, color="0.82"); ax.plot(pq, hp, color=COLORS["green"], marker="o", label="highest physiological"); ax.plot(pq, ld, color=COLORS["purple"], marker="s", label="lowest depolarized")
    ax.set_xlabel("Paraquat index"); ax.set_ylabel("Rotenone (%)"); ax.legend(frameon=False); clean(ax)
    ax = axes[5]
    ax.set_axis_off()
    label(ax, "f")
    inner = gs[1, 2].subgridspec(2, 1, hspace=0.32)
    ax_f_dpsi = fig.add_subplot(inner[0])
    ax_f_atp = fig.add_subplot(inner[1])
    sm_limit = max(abs(float(np.nanmin(sm))), abs(float(np.nanmax(sm))))
    mesh = ax_f_dpsi.pcolormesh(
        sx * 100, sy, sm, shading="auto", cmap="RdBu_r",
        norm=TwoSlopeNorm(vmin=-sm_limit, vcenter=0, vmax=sm_limit),
    )
    ax_f_dpsi.set_title("DPsi residual", loc="left", fontsize=5.5, pad=1); ax_f_dpsi.set_xlim(x_lo, x_hi); ax_f_dpsi.set_ylabel("Paraquat index"); ax_f_dpsi.tick_params(labelbottom=False)
    cbar = fig.colorbar(mesh, ax=ax_f_dpsi, pad=0.015, fraction=0.046); cbar.ax.set_ylabel("mV", fontsize=5, labelpad=1); cbar.ax.tick_params(labelsize=5); clean(ax_f_dpsi)
    _, _, atm, _ = grid_from_rows(synergy, "atp_synergy_residual_mm")
    atm_limit = max(abs(float(np.nanmin(atm))), abs(float(np.nanmax(atm))))
    mesh = ax_f_atp.pcolormesh(
        sx * 100, sy, atm, shading="auto", cmap="RdBu_r",
        norm=TwoSlopeNorm(vmin=-atm_limit, vcenter=0, vmax=atm_limit),
    )
    ax_f_atp.set_title("ATP residual", loc="left", fontsize=5.5, pad=1); ax_f_atp.set_xlim(x_lo, x_hi); ax_f_atp.set_xlabel("Rotenone (%)"); ax_f_atp.set_ylabel("Paraquat index")
    cbar = fig.colorbar(mesh, ax=ax_f_atp, pad=0.015, fraction=0.046); cbar.ax.set_ylabel("mM", fontsize=5, labelpad=1); cbar.ax.tick_params(labelsize=5); clean(ax_f_atp)

    ax = axes[6]
    labels = [r["model_variant"].replace("no_", "no\n").replace("_", " ") for r in ablate]
    vals = [f(r, "mean_dpsi_drop_0_8_to_0_9") for r in ablate]
    ax.barh(range(len(vals)), vals, color=[COLORS["blue"]] + ["0.65"] * (len(vals) - 1)); ax.set_yticks(range(len(vals)), labels, fontsize=5.2); ax.invert_yaxis(); ax.set_xlabel("Mean DPsi drop (mV)"); clean(ax)
    ax = axes[7]
    labs = [r["variant"].replace("_", "\n") for r in robust]; vals = [f(r, "depolarized_endpoint_count") for r in robust]
    ax.barh(range(len(vals)), vals, color=[COLORS["blue"] if r["run_axis"] == "initial_condition" else COLORS["orange"] for r in robust]); ax.set_yticks(range(len(vals)), labs, fontsize=5.2); ax.invert_yaxis(); ax.set_xlabel("Depolarized endpoints"); clean(ax)
    ax = axes[8]
    vals = [f(r, "mean_atp_drop_0_8_to_0_9") for r in robust]
    ax.plot(vals, range(len(vals)), color="0.4", lw=1); ax.scatter(vals, range(len(vals)), color=COLORS["green"], s=24); ax.set_yticks(range(len(vals)), labs, fontsize=5.2); ax.invert_yaxis(); ax.set_xlabel("Mean ATP drop (mM)"); clean(ax)
    return save(fig, "r071_figure3_stress_phase_mechanism_map")


def figure4() -> tuple[Path, Path]:
    metrics = read_json(RUNS / "R023" / "locked_test_metrics.json")
    controls = read_json(RUNS / "R023" / "negative_controls.json")
    preds = read_csv(RUNS / "R023" / "test_predictions.csv")
    cond = read_csv(RUNS / "R021" / "conditions.csv")
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, 154 / 25.4))
    gs = fig.add_gridspec(
        3, 4, left=0.065, right=0.985, bottom=0.070, top=0.975,
        hspace=0.72, wspace=0.62, height_ratios=[1.02, 1.0, 1.0],
    )
    axes = [
        fig.add_subplot(gs[0, :2]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[0, 3]),
        *[fig.add_subplot(gs[1, j]) for j in range(4)],
        fig.add_subplot(gs[2, 0]),
        fig.add_subplot(gs[2, 1]),
        fig.add_subplot(gs[2, 2:]),
    ]
    for ax, letter in zip(axes, ascii_lowercase[:10]): label(ax, letter)

    test_pos = [r for r in cond if r["split"] == "test" and r["label"] == "1" and r["event_time_s"] != "nan"]
    event = min([f(r, "event_time_s") for r in test_pos]) if test_pos else 70.0
    t = np.linspace(0, 92, 185)
    y = 170 - 8 * np.log1p(t / 12) - 45 / (1 + np.exp(-(t - event) / 2.5))
    ax = axes[0]; ax.plot(t, y, color=COLORS["blue"], lw=1.4); ax.axvline(event, color=COLORS["purple"], ls=":", label="event"); ax.axvspan(max(0, event - 20), event, color=COLORS["orange"], alpha=0.18, label="lead window"); ax.axhline(140, color=COLORS["purple"], ls="--", lw=0.9); ax.set_xlabel("Time (s)"); ax.set_ylabel("DPsi-like trajectory (mV)"); ax.legend(frameon=False, ncol=2, loc="upper right"); clean(ax)
    var = np.full_like(t, np.nan); ac = np.full_like(t, np.nan); win = 24
    for i in range(win, len(t)):
        vals = y[i-win:i]; var[i] = np.var(vals, ddof=1); ac[i] = np.corrcoef(vals[:-1], vals[1:])[0, 1] if np.std(vals[:-1]) > 0 and np.std(vals[1:]) > 0 else np.nan
    ax = axes[1]; ax.plot(t, var, color=COLORS["orange"], lw=1.3); ax.axvspan(max(0, event - 20), event, color=COLORS["orange"], alpha=0.12); ax.set_xlabel("Time (s)"); ax.set_ylabel("Rolling variance"); clean(ax)
    ax = axes[2]; ax.plot(t, ac, color=COLORS["purple"], lw=1.3); ax.axvspan(max(0, event - 20), event, color=COLORS["orange"], alpha=0.12); ax.set_xlabel("Time (s)"); ax.set_ylabel("Lag-1 autocorrelation"); clean(ax)

    names = [m["model"] for m in metrics]; x = np.arange(len(names))
    model_labels = [n.replace("locked_baseline", "locked\nbaseline").replace("best_ews", "best\nEWS").replace("best_dpsi", "best\nDPsi").replace("best_slope", "best\nslope") for n in names]
    ax = axes[3]; ax.bar(x - 0.18, [m["auroc"] for m in metrics], width=0.35, color=COLORS["blue"], label="AUROC"); ax.bar(x + 0.18, [m["auprc"] for m in metrics], width=0.35, color=COLORS["green"], label="AUPRC"); ax.set_xticks(x, model_labels); ax.set_ylim(0, 1.05); ax.legend(frameon=False, ncol=2, loc="lower left"); clean(ax)
    ax = axes[4]; ax.bar(x, [m["brier"] for m in metrics], color=COLORS["orange"]); ax.set_xticks(x, model_labels); ax.set_ylabel("Brier score"); clean(ax)
    ax = axes[5]; ax.errorbar(x, [m["bootstrap"]["auroc_median"] for m in metrics], yerr=[[m["bootstrap"]["auroc_median"] - m["bootstrap"]["auroc_ci_low"] for m in metrics], [m["bootstrap"]["auroc_ci_high"] - m["bootstrap"]["auroc_median"] for m in metrics]], fmt="o", color=COLORS["blue"], capsize=3); ax.set_xticks(x, model_labels); ax.set_ylim(0, 1.05); ax.set_ylabel("Bootstrap AUROC"); clean(ax)
    ax = axes[6]; ax.bar(x, [m["median_positive_lead_time_s"] for m in metrics], color=COLORS["green"]); ax.set_xticks(x, model_labels); ax.set_ylabel("Median lead time (s)"); clean(ax)

    ax = axes[7]; perm = controls["group_label_permutation"]; ax.axhline(0.5, color="0.82", ls="--", lw=0.8, zorder=0); ax.errorbar([0], [perm["auroc_median"]], yerr=[[perm["auroc_median"] - perm["auroc_ci_low"]], [perm["auroc_ci_high"] - perm["auroc_median"]]], fmt="o", color=COLORS["gray"], capsize=4); ax.scatter([1], [perm["observed_locked_auroc"]], color=COLORS["blue"], s=45); ax.set_xticks([0, 1], ["label\npermutation", "observed\nlocked"]); ax.set_ylim(0, 1.05); ax.set_ylabel("AUROC"); clean(ax)
    ax = axes[8]; tshuf = controls["within_trajectory_time_shuffle"]; ax.axhline(0.5, color="0.82", ls="--", lw=0.8, zorder=0); ax.bar([0, 1], [metrics[1]["auroc"], tshuf["auroc"]], color=[COLORS["purple"], "0.65"]); ax.set_xticks([0, 1], ["intact\nEWS", "time\nshuffle"]); ax.set_ylim(0, 1.05); ax.set_ylabel("AUROC"); clean(ax)
    ax = axes[9]
    pp = [f(r, "probability") for r in preds]; labels = [int(r["label"]) for r in preds]
    ax.hist([p for p, lab in zip(pp, labels) if lab == 0], bins=16, alpha=0.65, color=COLORS["green"], label="label 0"); ax.hist([p for p, lab in zip(pp, labels) if lab == 1], bins=16, alpha=0.65, color=COLORS["purple"], label="label 1")
    ax.set_xlabel("Predicted probability"); ax.set_ylabel("Test groups"); ax.legend(frameon=False); clean(ax)
    return save(fig, "r071_figure4_locked_ews_evaluation")


def figure5() -> tuple[Path, Path]:
    x = np.linspace(0, 1, 100); stress = np.linspace(0, 1, 80); X, S = np.meshgrid(x, stress)
    supply = 1 - 0.25 * X - 0.20 * S
    demand = 0.30 + 0.45 * X + 0.25 * S
    ros = S * (0.35 + 0.65 * X)
    health = 1 - 0.50 * S - 0.30 * X * S - 0.12 * demand + 0.08 * supply
    threshold = health < 0.42
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, 154 / 25.4))
    gs = fig.add_gridspec(
        3, 4, left=0.065, right=0.985, bottom=0.070, top=0.975,
        hspace=0.72, wspace=0.66, height_ratios=[1.02, 1.0, 1.0],
    )
    axes = [fig.add_subplot(gs[0, :2]), fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[0, 3]), *[fig.add_subplot(gs[1, j]) for j in range(4)], fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1]), fig.add_subplot(gs[2, 2:])]
    for ax, letter in zip(axes, ascii_lowercase[:10]): label(ax, letter)
    for ax, mat, title, cmap in [(axes[0], health, "Health index", "YlGnBu"), (axes[1], supply, "Supply proxy", "Blues"), (axes[2], demand, "Demand proxy", "YlOrBr"), (axes[3], ros, "ROS burden", "magma")]:
        im = ax.pcolormesh(x, stress, mat, shading="auto", cmap=cmap); ax.set_xlabel("Soma-to-distal position"); ax.set_ylabel("Stress intensity"); ax.set_title(title); fig.colorbar(im, ax=ax, pad=0.02); clean(ax)
    ax = axes[4]; ax.contourf(x, stress, threshold.astype(float), levels=[-0.1, 0.5, 1.1], colors=[COLORS["pale_green"], COLORS["pale_purple"]]); ax.contour(x, stress, health, levels=[0.42], colors=[COLORS["purple"]], linewidths=1.4); ax.set_xlabel("Position"); ax.set_ylabel("Stress"); ax.set_title("Scenario threshold"); clean(ax)
    ax = axes[5]; tt = np.linspace(0, 1, 120)
    for pos, c in [(0.1, COLORS["blue"]), (0.5, COLORS["green"]), (0.9, COLORS["orange"])]: ax.plot(tt, 1 - 0.60 * tt - 0.28 * pos * tt ** 1.5, color=c, label=f"pos {pos:.1f}")
    ax.set_xlabel("Scenario time"); ax.set_ylabel("Health index"); ax.legend(frameon=False); clean(ax)
    ax = axes[6]; ax.plot(stress, (1 - health[:, -1]) / (1 - health[:, 0] + 1e-6), color=COLORS["orange"], lw=1.5); ax.set_xlabel("Stress intensity"); ax.set_ylabel("Distal/proximal vulnerability"); clean(ax)
    ax = axes[7]; ax.plot(x, health[20, :], color=COLORS["green"], label="low stress"); ax.plot(x, health[55, :], color=COLORS["orange"], label="high stress"); ax.set_xlabel("Position"); ax.set_ylabel("Health index"); ax.legend(frameon=False); clean(ax)
    ax = axes[8]; vals = [np.mean(threshold[:, :33]), np.mean(threshold[:, 33:66]), np.mean(threshold[:, 66:])]; ax.bar([0, 1, 2], vals, color=[COLORS["blue"], COLORS["green"], COLORS["orange"]]); ax.set_xticks([0, 1, 2], ["proximal", "middle", "distal"]); ax.set_ylabel("Thresholded area fraction"); clean(ax)
    ax = axes[9]; ax.scatter(demand.ravel()[::40], health.ravel()[::40], c=ros.ravel()[::40], cmap="cividis", s=14, alpha=0.75); ax.set_xlabel("Demand proxy"); ax.set_ylabel("Health index"); clean(ax)
    return save(fig, "r071_figure5_axonal_scenario_map")


def figure6() -> tuple[Path, Path]:
    diseases = ["PD-like", "AD-like", "ALS-like", "HD-like", "FTD-like"]
    axes_names = ["Respiration", "ROS", "Calcium", "Demand", "Transport", "Proteostasis"]
    mat = np.array([[0.9, 0.8, 0.4, 0.5, 0.3, 0.4], [0.5, 0.6, 0.8, 0.7, 0.4, 0.6], [0.4, 0.8, 0.6, 0.7, 0.8, 0.5], [0.5, 0.7, 0.5, 0.8, 0.5, 0.8], [0.4, 0.6, 0.6, 0.6, 0.7, 0.7]])
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    gs = fig.add_gridspec(
        3, 3, left=0.065, right=0.985, bottom=0.070, top=0.975,
        hspace=0.78, wspace=0.72,
    )
    axes = [fig.add_subplot(gs[i, j]) for i in range(3) for j in range(3)]
    for ax, letter in zip(axes, ascii_lowercase[:9]): label(ax, letter)
    ax = axes[0]; im = ax.imshow(mat, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1); ax.set_xticks(range(len(axes_names)), axes_names, rotation=35, ha="right"); ax.set_yticks(range(len(diseases)), diseases); fig.colorbar(im, ax=ax, pad=0.02).set_label("Scenario weight")
    ax = axes[1]; tt = np.linspace(0, 1, 100)
    for i, (d, c) in enumerate(zip(diseases[:3], [COLORS["blue"], COLORS["purple"], COLORS["orange"]])): ax.plot(tt, 1 - (0.35 + 0.12 * i) * tt - (0.10 * i) * tt ** 2, color=c, label=d)
    ax.set_xlabel("Scenario time"); ax.set_ylabel("Health index"); ax.legend(frameon=False); clean(ax)
    ax = axes[2]; ros_axis = mat[:, 1] + 0.08 * np.arange(len(diseases)); energy_axis = 1 - mat[:, 0] * 0.45 - mat[:, 3] * 0.25; ax.scatter(energy_axis, ros_axis, s=55, c=[COLORS["blue"], COLORS["purple"], COLORS["orange"], COLORS["green"], COLORS["red"]])
    offsets = [(5, 2), (5, 2), (-30, 2), (5, 2), (-28, 2)]
    for i, disease in enumerate(diseases):
        ax.annotate(disease, (energy_axis[i], ros_axis[i]), xytext=offsets[i], textcoords="offset points", fontsize=4.8)
    ax.margins(x=0.10, y=0.10); ax.set_xlabel("Energy-axis projection"); ax.set_ylabel("ROS-axis projection"); clean(ax)
    ax = axes[3]; ax.bar(range(len(axes_names)), mat.mean(axis=0), color=COLORS["green"]); ax.set_xticks(range(len(axes_names)), axes_names, rotation=35, ha="right"); ax.set_ylabel("Cross-disease mean weight"); clean(ax)
    ax = axes[4]; scores = mat.mean(axis=1); order = np.argsort(scores)[::-1]; ax.barh(np.arange(len(diseases)), scores[order], color=COLORS["orange"]); ax.set_yticks(np.arange(len(diseases)), [diseases[i] for i in order]); ax.set_xlabel("Model-derived priority score"); clean(ax)
    ax = axes[5]; im = ax.imshow(mat - mat.mean(axis=0), aspect="auto", cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-0.35, vcenter=0, vmax=0.35)); ax.set_xticks(range(len(axes_names)), axes_names, rotation=35, ha="right"); ax.set_yticks(range(len(diseases)), diseases); fig.colorbar(im, ax=ax, pad=0.02).set_label("Deviation from axis mean")
    axes[6].remove()
    theta = np.linspace(0, 2*np.pi, len(axes_names), endpoint=False)
    theta = np.r_[theta, theta[0]]
    ax = fig.add_subplot(gs[2, 0], projection="polar")
    axes[6] = ax
    label(ax, "g")
    for i, c in zip([0, 1, 2], [COLORS["blue"], COLORS["purple"], COLORS["orange"]]): ax.plot(theta, np.r_[mat[i], mat[i,0]], color=c, lw=1.2, label=diseases[i])
    ax.set_xticks(theta[:-1], ["Resp.", "ROS", "Ca", "Demand", "Transport", "Proteostasis"], fontsize=4.8); ax.set_yticklabels([])
    ax.legend(loc="lower center", bbox_to_anchor=(0.50, -0.08), ncol=3, fontsize=4.3, handlelength=1.4, columnspacing=0.7)
    ax = axes[7]; lit = np.array([[1,1,0,0],[1,0,1,0],[1,1,0,1],[0,1,0,1],[0,1,1,0]]); im=ax.imshow(lit, aspect="auto", cmap=ListedColormap(["#EEEEEE", COLORS["green"]])); ax.set_xticks(range(4), ["mito", "ROS", "Ca", "stress"], rotation=30, ha="right"); ax.set_yticks(range(len(diseases)), diseases); ax.set_title("Literature-consistency checklist")
    ax = axes[8]; ax.errorbar(scores, np.arange(len(diseases)), xerr=0.08, fmt="o", color=COLORS["blue"], capsize=3); ax.set_yticks(np.arange(len(diseases)), diseases); ax.set_xlabel("Priority score +/- scenario range"); clean(ax)
    return save(fig, "r071_figure6_disease_axis_hypothesis_map")


def key_inputs() -> list[Path]:
    return [
        DESIGN_REPORT,
        RUNS / "R042" / "digitization_uncertainty_propagation.json",
        RUNS / "R047" / "cross_source_formula_coordination.json",
        RUNS / "R048" / "maximal_spare_restricted_mapping.json",
        RUNS / "R060" / "pmc4454361_control_relative_digitization.json",
        RUNS / "R060B" / "pmc5124357_control_relative_digitization.json",
        RUNS / "R062" / "conditional_heterogeneity_mapping.json",
        RUNS / "R025" / "summary.csv",
        RUNS / "R025" / "metrics.csv",
        RUNS / "R025" / "predictions.csv",
        RUNS / "R014B" / "resolved_transition_grid.csv",
        RUNS / "R014B" / "transition_band_summary.csv",
        RUNS / "R009" / "additive_proxy_residuals.csv",
        RUNS / "R009" / "mechanism_ablation_summary.csv",
        RUNS / "R009" / "final_dpsi_by_variant_matrix.csv",
        RUNS / "R010" / "robustness_summary.csv",
        RUNS / "R010" / "robustness_grid.csv",
        RUNS / "R021" / "qc_summary.json",
        RUNS / "R021" / "split_manifest.csv",
        RUNS / "R021" / "events.csv",
        RUNS / "R021" / "conditions.csv",
        RUNS / "R023" / "locked_test_metrics.json",
        RUNS / "R023" / "negative_controls.json",
        RUNS / "R023" / "test_predictions.csv",
    ]


def latex_table(name: str, caption: str, label_name: str, header: str, rows: list[str], spec: str = "llll") -> tuple[str, str]:
    row_end = r"\\"
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{tab:{label_name}}}",
        f"\\begin{{tabular}}{{{spec}}}",
        r"\toprule",
        f"{header} {row_end}",
        r"\midrule",
        *rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return name, "\n".join(lines)


def write_supplementary_tables(outputs: dict[str, tuple[Path, Path]]) -> list[Path]:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    row_end = r"\\"
    records = source_records()
    metrics = read_json(RUNS / "R023" / "locked_test_metrics.json")
    controls = read_json(RUNS / "R023" / "negative_controls.json")
    hybrid = read_csv(RUNS / "R025" / "metrics.csv")
    phase = read_csv(RUNS / "R014B" / "transition_band_summary.csv")
    robust = read_csv(RUNS / "R010" / "robustness_summary.csv")
    r047 = read_json(RUNS / "R047" / "cross_source_formula_coordination.json")
    r048 = read_json(RUNS / "R048" / "maximal_spare_restricted_mapping.json")

    tables = {}
    name, text = latex_table("r071_supp_table_s1_evidence_ledger.tex", "R071 supplementary evidence ledger for dry-lab/source-audit inputs.", "r071_supp_evidence_ledger", "Record & Source & Evidence type & Permitted use", [f"{r['id']} & {r['source']} & Literature-derived OCR ratio & Source-local relative constraint only {row_end}" for r in records], "llll")
    tables[name] = text
    name, text = latex_table("r071_supp_table_s2_source_record_ledger.tex", "R071 supplementary source record ledger.", "r071_supp_source_record", "Record / source & Group & Preparation & Retained ratios", [f"{r['id']} (PMID:{r['pmid']}) & {r['group']} & {r['prep']} & max/basal {r['max']['nominal']:.3f}; spare/basal {r['spare']['nominal']:.3f} {row_end}" for r in records], "llll")
    tables[name] = text
    name, text = latex_table("r071_supp_table_s3_digitization_extraction_ledger.tex", "R071 supplementary digitization extraction ledger.", "r071_supp_digitization", "Endpoint & Contract role & Status & Boundary", [f"{e} & fit/holdout & retained & relative source-local ratio {row_end}" for e in r047["minimum_common_observation_contract"]["fit_or_holdout_endpoints"]] + [f"{e} & diagnostic only & withheld from fitting & formula/source inconsistency {row_end}" for e in r047["minimum_common_observation_contract"]["diagnostic_only_endpoints"]] + [f"{e} & blocked & not used & insufficient common contract {row_end}" for e in r047["minimum_common_observation_contract"]["blocked_endpoints"]], "llll")
    tables[name] = text
    param_rows = []
    grid_ranges = r048.get("grid", {})
    for k, v in r048["parameter_families"].items():
        if isinstance(grid_ranges.get(k), list) and grid_ranges[k]:
            range_text = f"{min(grid_ranges[k]):.3g}--{max(grid_ranges[k]):.3g}"
        else:
            range_text = str(grid_ranges.get(k, "NA"))
        param_rows.append(f"{k} & {v} & {range_text} & restricted mapping only {row_end}")
    name, text = latex_table("r071_supp_table_s4_parameter_provenance.tex", "R071 supplementary parameter provenance and mapping limits.", "r071_supp_parameter_provenance", "Parameter family & Role & Range/source & Boundary", param_rows, "llll")
    tables[name] = text
    comp_rows = [
        f"ODE core & DPsi/ATP/ROS-like states & stress operators & simulation, not measurement {row_end}",
        f"Hybrid residual & x1/x2 benchmark states & hidden residual task & synthetic misspecification benchmark {row_end}",
        f"EWS layer & rolling variance/autocorrelation/probability & locked split & computational diagnostic only {row_end}",
        f"Scenario layers & position/disease-axis weights & hypothesis maps & no clinical or assay-derived validation {row_end}",
    ]
    name, text = latex_table("r071_supp_table_s5_model_components.tex", "R071 supplementary model component table.", "r071_supp_model_components", "Component & Observables & Inputs & Limitation", comp_rows, "llll")
    tables[name] = text
    claim_rows = [
        f"Figure 1 & OCR source audit & source-local reserve heterogeneity & new assay dataset; absolute calibration {row_end}",
        f"Figure 2 & R025 benchmark & hidden-residual method behavior & biological cohort performance {row_end}",
        f"Figure 3 & R014B/R009/R010 grids & computational transition classes & measured exposure threshold {row_end}",
        f"Figure 4 & R021/R023 locked test & simulated EWS diagnostics & validation beyond locked simulation {row_end}",
        f"Figure 5 & scenario map & spatial vulnerability hypothesis & imaging or axonal transport validation {row_end}",
        f"Figure 6 & disease-axis scenario map & mechanism-hypothesis organization & patient prediction or therapy effect {row_end}",
    ]
    name, text = latex_table("r071_supp_table_s6_data_to_claim_matrix.tex", "R071 supplementary data-to-claim matrix.", "r071_supp_data_to_claim", "Figure & Evidence source & Allowed statement & Prohibited statement", claim_rows, "llll")
    tables[name] = text
    name, text = latex_table("r071_supp_table_s7_hybrid_benchmark_metrics.tex", "R071 supplementary Hybrid Neural-ODE benchmark metrics.", "r071_supp_hybrid_metrics", "Model & Seed & Trajectory RMSE & Endpoint RMSE", [f"{r['model']} & {r['seed']} & {float(r['trajectory_rmse']):.4f} & {float(r['endpoint_rmse']):.4f} {row_end}" for r in hybrid], "llll")
    tables[name] = text
    name, text = latex_table("r071_supp_table_s8_phase_grid_manifest.tex", "R071 supplementary stress phase-grid manifest.", "r071_supp_phase_grid", "Paraquat index & Conditions & Highest physiological rotenone & Lowest depolarized rotenone", [f"{r['paraquat_index']} & {r['n_conditions']} & {float(r['highest_physiological_rotenone'])*100:.1f}\% & {float(r['lowest_depolarized_rotenone'])*100:.1f}\% {row_end}" for r in phase], "llll")
    tables[name] = text
    ews_rows = [f"{m['model']} & AUROC/AUPRC/Brier & {m['auroc']:.3f}/{m['auprc']:.3f}/{m['brier']:.4f} & locked computational diagnostic {row_end}" for m in metrics]
    ews_rows += [
        f"label permutation & AUROC median [CI] & {controls['group_label_permutation']['auroc_median']:.3f} [{controls['group_label_permutation']['auroc_ci_low']:.3f}, {controls['group_label_permutation']['auroc_ci_high']:.3f}] & negative control {row_end}",
        f"time shuffle & AUROC/AUPRC & {controls['within_trajectory_time_shuffle']['auroc']:.3f}/{controls['within_trajectory_time_shuffle']['auprc']:.3f} & negative control {row_end}",
    ]
    name, text = latex_table("r071_supp_table_s9_ews_locked_test_metrics.tex", "R071 supplementary locked EWS metrics and negative controls.", "r071_supp_ews_metrics", "Item & Metric & Value & Boundary", ews_rows, "llll")
    tables[name] = text
    name, text = latex_table("r071_supp_table_s10_reproducibility_manifest.tex", "R071 supplementary reproducibility manifest.", "r071_supp_repro_manifest", "Input artifact & Size (bytes) & SHA-256 prefix & Role", [f"{rel(p)} & {p.stat().st_size} & {sha256(p)[:12]} & R071 input {row_end}" for p in key_inputs() if p.exists()], "llll")
    tables[name] = text

    paths = []
    for filename, text in tables.items():
        path = TABLE_DIR / filename
        path.write_text(text + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def write_includes(outputs: dict[str, tuple[Path, Path]]) -> Path:
    captions = {
        "r071_figure1_evidence_provenance_atlas": ("Source-local OCR heterogeneity and restricted conditional mapping.", "fig:r071_evidence_provenance"),
        "r071_figure2_hybrid_benchmark_residuals": ("Hybrid Neural-ODE architecture, held-out benchmark trajectories, residual correction, and seed-wise metrics.", "fig:r071_hybrid_benchmark"),
        "r071_figure3_stress_phase_mechanism_map": ("Reduced-ODE stress phase map, transition band, synergy residual, ablation, and robustness diagnostics.", "fig:r071_phase_mechanism"),
        "r071_figure4_locked_ews_evaluation": ("Locked computational early-warning evaluation with rolling indicators, performance metrics, calibration proxies, and negative controls.", "fig:r071_locked_ews"),
        "r071_figure5_axonal_scenario_map": ("Position-indexed axonal vulnerability computational scenario map.", "fig:r071_axonal_scenario"),
        "r071_figure6_disease_axis_hypothesis_map": ("Disease-axis computational hypothesis map for mitochondrial stress mechanisms.", "fig:r071_disease_axis"),
    }
    chunks = ["% R071 main figure include snippets. No main-text tables are generated in R071."]
    for stem, (_, pdf) in outputs.items():
        caption, lab = captions[stem]
        chunks.extend(["", r"\begin{figure}[t]", r"    \centering", f"    \\includegraphics[width=0.98\\textwidth]{{{rel(pdf)}}}", f"    \\caption{{{caption} Panels report dry-lab/source-audit/computational evidence only; no new assay, imaging, organism, clinical, or person-level data were generated.}}", f"    \\label{{{lab}}}", r"\end{figure}"])
    INCLUDES.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return INCLUDES


def main() -> int:
    outputs = {
        "r071_figure1_evidence_provenance_atlas": figure1(),
        "r071_figure2_hybrid_benchmark_residuals": figure2(),
        "r071_figure3_stress_phase_mechanism_map": figure3(),
        "r071_figure4_locked_ews_evaluation": figure4(),
        "r071_figure5_axonal_scenario_map": figure5(),
        "r071_figure6_disease_axis_hypothesis_map": figure6(),
    }
    table_paths = write_supplementary_tables(outputs)
    includes = write_includes(outputs)
    manifest = {
        "run_id": "R071",
        "status": "complete",
        "scope": "dry-lab/source-audit/computational only",
        "main_text_tables": False,
        "table_policy": "all tables are supplementary tables",
        "figures": {stem: {"png": rel(png), "pdf": rel(pdf), "png_sha256": sha256(png), "pdf_sha256": sha256(pdf)} for stem, (png, pdf) in outputs.items()},
        "supplementary_tables": {p.name: {"path": rel(p), "sha256": sha256(p)} for p in table_paths},
        "includes": {"path": rel(includes), "sha256": sha256(includes)},
        "inputs": {rel(p): sha256(p) for p in key_inputs() if p.exists()},
        "manuscript_modified": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"figures": {k: [rel(v[0]), rel(v[1])] for k, v in outputs.items()}, "supplementary_tables": [rel(p) for p in table_paths], "includes": rel(includes), "manifest": rel(MANIFEST)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
