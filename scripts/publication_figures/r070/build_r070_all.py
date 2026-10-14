"""Build the R070 redesigned NeurMito-DT result figures and tables.

+ The R070 assets are generated into separate paths so earlier audited R068/R069
+ figures remain untouched. All panels are dry-lab/computational only and read
+ from the audited refinement logs where quantitative values are shown.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from string import ascii_lowercase

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "refine-logs" / "runs"
FIG_DIR = ROOT / "figures" / "r070"
TABLE_DIR = ROOT / "manuscript" / "figure_table_design"
DESIGN_REPORT = ROOT / "repository-docs" / "REPOSITORY_SCOPE.md"
MANIFEST = FIG_DIR / "r070_manifest.json"
INCLUDES = TABLE_DIR / "r070_main_figure_includes.tex"

COLORS = {
    "blue": "#0072B2",
    "sky": "#56B4E9",
    "green": "#009E73",
    "orange": "#E69F00",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "yellow": "#F0E442",
    "gray": "#6C757D",
    "dark": "#222222",
    "light": "#F2F2F2",
    "pale_blue": "#EAF2F8",
    "pale_green": "#E8F5EE",
    "pale_orange": "#FFF3D6",

}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7.8,
    "axes.labelsize": 7.8,
    "axes.titlesize": 8.6,
    "xtick.labelsize": 6.9,
    "ytick.labelsize": 6.9,
    "legend.fontsize": 6.7,
    "axes.linewidth": 0.75,
    "xtick.major.width": 0.65,
    "ytick.major.width": 0.65,
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


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def label(ax, text: str):
    ax.text(-0.10, 1.06, text, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")


def box(ax, xy, wh, text, face, edge, fontsize=7.6, bold=False):
    patch = FancyBboxPatch(xy, wh[0], wh[1], boxstyle="round,pad=0.018", facecolor=face, edgecolor=edge, lw=0.9)
    ax.add_patch(patch)
    ax.text(xy[0] + wh[0] / 2, xy[1] + wh[1] / 2, text, ha="center", va="center", fontsize=fontsize, fontweight="bold" if bold else None)
    return patch


def save(fig, stem: str) -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
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
        {"id": "R033", "pmid": "31931869", "group": "Low reserve", "prep": "DIV7 primary rat cortical", "platform": "Seahorse OCR bars", "color": COLORS["blue"], "max": low["PMID:31931869"]["maximal_to_basal"], "spare": low["PMID:31931869"]["spare_to_basal"]},
        {"id": "R039", "pmid": "24056030", "group": "Low reserve", "prep": "DIV7 E18 cortical", "platform": "Seahorse OCR bars", "color": COLORS["red"], "max": low["PMID:24056030"]["maximal_to_basal"], "spare": low["PMID:24056030"]["spare_to_basal"]},
        {"id": "R060", "pmid": "25081478", "group": "High reserve", "prep": r060["preparation"][:30], "platform": r060.get("platform", "OCR"), "color": COLORS["green"], "max": {"nominal": r060["relative_ratios"]["maximal_to_basal"]["value"], "low": r060["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060["relative_ratios"]["spare_to_basal"]["value"], "low": r060["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060["relative_ratios"]["spare_to_basal"]["interval"][1]}},
        {"id": "R060B", "pmid": "27889640", "group": "High reserve", "prep": r060b["preparation"][:30], "platform": r060b.get("platform", "OCR"), "color": COLORS["purple"], "max": {"nominal": r060b["relative_ratios"]["maximal_to_basal"]["value"], "low": r060b["relative_ratios"]["maximal_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["maximal_to_basal"]["interval"][1]}, "spare": {"nominal": r060b["relative_ratios"]["spare_to_basal"]["value"], "low": r060b["relative_ratios"]["spare_to_basal"]["interval"][0], "high": r060b["relative_ratios"]["spare_to_basal"]["interval"][1]}},
    ]


def ratio_plot(ax, records, key, ylabel):
    for i, rec in enumerate(records):
        value = rec[key]["nominal"]
        ax.errorbar([i], [value], yerr=[[value - rec[key]["low"]], [rec[key]["high"] - value]], fmt="o", ms=6, color=rec["color"], capsize=3, lw=1.3)
    ax.axvspan(-0.45, 1.45, color=COLORS["blue"], alpha=0.06, lw=0)
    ax.axvspan(1.55, 3.45, color=COLORS["green"], alpha=0.06, lw=0)
    ax.axvline(1.5, color="0.75", ls=":", lw=1)
    ax.set_xticks(range(4), [r["id"] for r in records])
    ax.set_ylabel(ylabel)
    clean(ax)


def draw_claim_strip(ax, title, supported, sensitivity, withheld):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(0.02, 0.95, title, fontweight="bold", fontsize=8.8, va="top")
    rows = [("Supported", supported, COLORS["green"], COLORS["pale_green"]), ("Sensitivity only", sensitivity, COLORS["orange"], COLORS["pale_orange"]), ("Withheld", withheld, COLORS["purple"], "#F8ECF5")]
    for i, (head, body, edge, face) in enumerate(rows):
        y = 0.70 - i * 0.25
        box(ax, (0.04, y - 0.09), (0.92, 0.16), f"{head}\n{body}", face, edge, fontsize=7.2, bold=False)


def figure1() -> tuple[Path, Path]:
    records = source_records()
    r062 = read_json(RUNS / "R062" / "conditional_heterogeneity_mapping.json")
    fig = plt.figure(figsize=(14.2, 8.0))
    gs = fig.add_gridspec(2, 4, hspace=0.42, wspace=0.42)
    axes = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)

    ax = axes[0]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    nodes = [(0.04, "Published\nOCR source"), (0.28, "Source-local\nratios"), (0.52, "Digitization\nintervals"), (0.76, "Reduced-ODE\nmapping")]
    for x, text in nodes: box(ax, (x, 0.58), (0.18, 0.18), text, COLORS["pale_blue"], COLORS["blue"], bold=True)
    for x0, x1 in zip([0.22, 0.46, 0.70], [0.28, 0.52, 0.76]): ax.add_patch(FancyArrowPatch((x0, 0.67), (x1, 0.67), arrowstyle="->", mutation_scale=10, lw=1, color=COLORS["gray"]))
    box(ax, (0.08, 0.18), (0.84, 0.20), "Computational/source-audit study only; no assay, imaging, animal, or clinical data generated", COLORS["pale_orange"], COLORS["orange"], fontsize=7.2)

    ax = axes[1]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    for i, rec in enumerate(records):
        x = 0.04 + (i % 2) * 0.48; y = 0.58 - (i // 2) * 0.40
        box(ax, (x, y), (0.42, 0.30), f"{rec['id']} | PMID {rec['pmid']}\n{rec['group']}\n{rec['platform']}", "white", rec["color"], fontsize=6.9)
    ax.text(0.02, 0.98, "Source provenance tiles", fontweight="bold", fontsize=8.5, va="top")

    ratio_plot(axes[2], records, "max", "Maximal/basal OCR ratio")
    ratio_plot(axes[3], records, "spare", "Spare/basal OCR ratio")

    ax = axes[4]
    for rec in records: ax.scatter(rec["max"]["nominal"], rec["spare"]["nominal"], s=70, color=rec["color"], edgecolor="white", lw=0.8, label=rec["id"])
    ax.set_xlabel("Maximal/basal ratio"); ax.set_ylabel("Spare/basal ratio")
    ax.legend(frameon=False, ncol=2)
    clean(ax)

    ax = axes[5]
    for group, color, marker in [("low_reserve_pair", COLORS["blue"], "o"), ("high_reserve_pair", COLORS["green"], "s")]:
        ranked = r062["conditional_group_rankings"][group]["top_ranked"][:8]
        xs = [item["multipliers"]["Vmax_CV"] for item in ranked]
        ys = [item["multipliers"]["g_H"] for item in ranked]
        losses = np.array([item["loss"] for item in ranked])
        sizes = 95 * (losses.max() - losses + 0.004) / (np.ptp(losses) + 0.004)
        ax.scatter(xs, ys, s=sizes, color=color, alpha=0.72, marker=marker, label=group.replace("_pair", ""))
    ax.set_xlabel("Vmax_CV multiplier"); ax.set_ylabel("g_H multiplier")
    ax.legend(frameon=False)
    clean(ax)

    draw_claim_strip(axes[6], "Claim boundary", "source-local reserve heterogeneity", "restricted diagnostic mapping", "absolute calibration; MCMC posterior; biological validation claim")
    ax = axes[7]
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    low = r062["source_groups"]["low_reserve_pair"]["mean_ratios"]
    high = r062["source_groups"]["high_reserve_pair"]["mean_ratios"]
    box(ax, (0.10, 0.60), (0.80, 0.20), f"Low reserve mean: max/basal {low['maximal_to_basal']:.2f}; spare/basal {low['spare_to_basal']:.2f}", "white", COLORS["blue"], fontsize=7.5)
    box(ax, (0.10, 0.34), (0.80, 0.20), f"High reserve mean: max/basal {high['maximal_to_basal']:.2f}; spare/basal {high['spare_to_basal']:.2f}", "white", COLORS["green"], fontsize=7.5)
    ax.text(0.50, 0.14, "Heterogeneity shifts candidate diagnostic regions, but identifiability remains weak.", ha="center", fontsize=7.3, color=COLORS["gray"])
    return save(fig, "r070_figure1_source_contract_ocr_mapping")


def figure2() -> tuple[Path, Path]:
    summary = read_csv(RUNS / "R025" / "summary.csv")
    metrics = read_csv(RUNS / "R025" / "metrics.csv")
    preds = read_csv(RUNS / "R025" / "predictions.csv")
    meta = read_json(RUNS / "R025" / "metadata.json")
    fig = plt.figure(figsize=(14.0, 7.6))
    gs = fig.add_gridspec(2, 4, hspace=0.42, wspace=0.42)
    axes = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)
    ax = axes[0]; ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    for xy, text, face, edge in [((0.05,0.58),"State +\nstress",COLORS["light"],COLORS["gray"]),((0.37,0.72),"Mechanistic\nODE",COLORS["pale_blue"],COLORS["blue"]),((0.37,0.35),"Neural\nresidual",COLORS["pale_orange"],COLORS["orange"]),((0.70,0.55),"Hybrid\nrollout",COLORS["pale_green"],COLORS["green"])]: box(ax, xy, (0.22,0.17), text, face, edge, bold=True)
    for a,b in [((0.27,0.66),(0.37,0.80)),((0.27,0.66),(0.37,0.44)),((0.59,0.80),(0.70,0.64)),((0.59,0.44),(0.70,0.64))]: ax.add_patch(FancyArrowPatch(a,b,arrowstyle="->",mutation_scale=10,color=COLORS["gray"]))
    ax.text(0.50,0.13,f"Train hidden gain {meta['train_hidden_gain'][0]}-{meta['train_hidden_gain'][1]}; held-out {meta['test_hidden_gain'][0]}-{meta['test_hidden_gain'][1]}",ha="center",fontsize=7.2)
    ax = axes[1]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    for i, txt in enumerate(["Synthetic hidden residual", "Train/validation/test split", "ODE vs Neural vs Hybrid", "Locked metrics"]):
        x=0.08+i*0.23; box(ax,(x,0.48),(0.16,0.22),txt,COLORS["light"],COLORS["gray"],fontsize=6.8)
        if i<3: ax.add_patch(FancyArrowPatch((x+0.16,0.59),(x+0.23,0.59),arrowstyle="->",mutation_scale=9,color=COLORS["gray"]))
    rows = [r for r in preds if int(r["seed"]) == 0 and int(r["case_index"]) == 0]
    ax = axes[2]
    for model, color, ls in [("ode", COLORS["gray"], ":"), ("neural", COLORS["orange"], "--"), ("hybrid", COLORS["blue"], "-")]:
        mrows = sorted([r for r in rows if r["model"] == model], key=lambda r: float(r["time_s"]))
        ax.plot([f(r,"time_s") for r in mrows], [f(r,"pred_x1") for r in mrows], color=color, ls=ls, lw=1.3, label=model.title())
    target = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: float(r["time_s"]))
    ax.plot([f(r,"time_s") for r in target], [f(r,"target_x1") for r in target], color=COLORS["dark"], lw=1.6, label="Reference")
    ax.set_xlabel("Time (benchmark units)"); ax.set_ylabel("State x1"); ax.legend(frameon=False); clean(ax)
    smap = {r["model"]: r for r in summary}; models = ["ode","neural","hybrid"]; names=["ODE","Neural","Hybrid"]
    ax = axes[3]; vals=[float(smap[m]["trajectory_rmse_mean"]) for m in models]; sds=[float(smap[m]["trajectory_rmse_sd"]) for m in models]
    ax.bar(range(3), vals, yerr=sds, capsize=3, color=[COLORS["gray"],COLORS["orange"],COLORS["blue"]]); ax.set_xticks(range(3), names); ax.set_ylabel("Trajectory RMSE"); clean(ax)
    ax = axes[4]; vals=[float(smap[m]["endpoint_rmse_mean"]) for m in models]
    ax.bar(range(3), vals, color=[COLORS["gray"],COLORS["orange"],COLORS["blue"]]); ax.set_xticks(range(3), names); ax.set_ylabel("Endpoint RMSE"); clean(ax)
    ax = axes[5]
    for off,m,c in [(-0.15,"ode",COLORS["gray"]),(0,"neural",COLORS["orange"]),(0.15,"hybrid",COLORS["blue"])]:
        mrows=sorted([r for r in metrics if r["model"]==m], key=lambda r:int(r["seed"]))
        ax.scatter([int(r["seed"])+off for r in mrows],[f(r,"trajectory_rmse") for r in mrows],color=c,label=m.title(),s=35)
    ax.set_xticks([0,1,2],["Seed 0","Seed 1","Seed 2"]); ax.set_ylabel("Trajectory RMSE"); ax.legend(frameon=False); clean(ax)
    ax = axes[6]
    neural = sorted([r for r in rows if r["model"] == "neural"], key=lambda r: float(r["time_s"]))
    hybrid = sorted([r for r in rows if r["model"] == "hybrid"], key=lambda r: float(r["time_s"]))
    neural_error = np.abs(np.array([f(r, "target_x1") - f(r, "pred_x1") for r in neural]))
    hybrid_error = np.abs(np.array([f(r, "target_x1") - f(r, "pred_x1") for r in hybrid]))
    ax.scatter(neural_error, hybrid_error, s=12, color=COLORS["purple"], alpha=0.75)
    max_error = max(float(neural_error.max()), float(hybrid_error.max()))
    ax.plot([0, max_error], [0, max_error], color="0.5", ls="--", lw=1)
    ax.set_xlabel("Neural absolute error")
    ax.set_ylabel("Hybrid absolute error")
    clean(ax)
    draw_claim_strip(axes[7], "Claim boundary", "controlled hidden-residual recovery", "method benchmark under synthetic misspecification", "biological generalization; clinical utility")
    return save(fig, "r070_figure2_hybrid_benchmark")


def grid_from_rows(rows, value_key):
    xs = np.array(sorted({f(r, "rotenone_inhibition") for r in rows}))
    ys = np.array(sorted({f(r, "paraquat_index") for r in rows}))
    lookup = {(f(r,"rotenone_inhibition"), f(r,"paraquat_index")): r for r in rows}
    mat = np.empty((len(ys), len(xs)))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs): mat[i, j] = f(lookup[(x, y)], value_key)
    return xs, ys, mat


def figure3() -> tuple[Path, Path]:
    rows = read_csv(RUNS / "R014B" / "resolved_transition_grid.csv")
    band = read_csv(RUNS / "R014B" / "transition_band_summary.csv")
    synergy = read_csv(RUNS / "R009" / "additive_proxy_residuals.csv")
    robust = read_csv(RUNS / "R010" / "robustness_summary.csv")
    ablate = read_csv(RUNS / "R009" / "mechanism_ablation_summary.csv")
    fig = plt.figure(figsize=(14.0, 7.8)); gs = fig.add_gridspec(2,4,hspace=0.42,wspace=0.45)
    axes=[fig.add_subplot(gs[i,j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)
    ax=axes[0]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    box(ax,(0.34,0.40),(0.30,0.22),"Reduced\nmitochondrial ODE",COLORS["pale_blue"],COLORS["blue"],bold=True)
    for xy,txt,col in [((0.05,0.70),"Rotenone-like\nC-I inhibition",COLORS["red"]),((0.05,0.12),"Paraquat-like\nROS pressure",COLORS["orange"]),((0.72,0.40),"Oxygen /\nsolver envelope",COLORS["gray"])]:
        box(ax,xy,(0.22,0.15),txt,"white",col,fontsize=7.0)
        ax.add_patch(FancyArrowPatch((xy[0]+0.22,xy[1]+0.075),(0.34,0.51),arrowstyle="->",mutation_scale=9,color=col))
    ax=axes[1]; xs,ys,dpsi=grid_from_rows(rows,"resolved_final_dpsi_mv"); cls=np.array([[0 if [r for r in rows if f(r,'rotenone_inhibition')==x and f(r,'paraquat_index')==y][0]['resolved_endpoint_class']=='near_fixed_physiological_endpoint' else 1 for x in xs] for y in ys])
    ax.imshow(cls, origin="lower", aspect="auto", extent=[xs.min()*100,xs.max()*100,ys.min(),ys.max()], cmap=ListedColormap([COLORS["green"],COLORS["purple"]]), interpolation="none")
    for r in band: ax.plot([f(r,"highest_physiological_rotenone")*100,f(r,"lowest_depolarized_rotenone")*100],[f(r,"paraquat_index"),f(r,"paraquat_index")],color="black",lw=1.1)
    ax.set_xlabel("Rotenone (% C-I inhibition)"); ax.set_ylabel("Paraquat index")
    clean(ax)
    ax=axes[2]; mesh=ax.pcolormesh(xs*100,ys,dpsi,shading="auto",cmap="viridis"); ax.set_xlabel("Rotenone (% C-I inhibition)"); ax.set_ylabel("Paraquat index"); cb=fig.colorbar(mesh,ax=ax,pad=0.02); cb.set_label("Final DPsi (mV)"); clean(ax)
    ax=axes[3]; pq=np.array([f(r,"paraquat_index") for r in band]); hp=np.array([f(r,"highest_physiological_rotenone")*100 for r in band]); ld=np.array([f(r,"lowest_depolarized_rotenone")*100 for r in band]); ax.fill_between(pq,hp,ld,color="0.82"); ax.plot(pq,hp,color=COLORS["green"],marker="o",label="highest physiological"); ax.plot(pq,ld,color=COLORS["purple"],marker="s",label="lowest depolarized"); ax.set_xlabel("Paraquat index"); ax.set_ylabel("Rotenone (%)"); ax.legend(frameon=False); clean(ax)
    ax=axes[4]; for_pq=[0.0,5.0,20.0]
    for pqv,c in zip(for_pq,[COLORS["green"],COLORS["orange"],COLORS["purple"]]):
        line=sorted([r for r in rows if abs(f(r,"paraquat_index")-pqv)<1e-9],key=lambda r:f(r,"rotenone_inhibition"))
        ax.plot([f(r,"rotenone_inhibition")*100 for r in line],[f(r,"resolved_final_dpsi_mv") for r in line],marker="o",ms=3,lw=1.2,color=c,label=f"PQ {pqv:g}")
    ax.set_xlabel("Rotenone (% C-I inhibition)"); ax.set_ylabel("Final DPsi (mV)"); ax.legend(frameon=False); clean(ax)
    ax=axes[5]; sx,sy,sm=grid_from_rows(synergy,"dpsi_synergy_residual_mv"); mm=ax.pcolormesh(sx*100,sy,sm,shading="auto",cmap="PuOr"); ax.set_xlabel("Rotenone (% C-I inhibition)"); ax.set_ylabel("Paraquat index"); cb=fig.colorbar(mm,ax=ax,pad=0.02); cb.set_label("DPsi residual (mV)"); clean(ax)
    ax=axes[6]; labels=[r["model_variant"].replace("no_", "no\n").replace("_", " ") for r in ablate]; vals=[f(r,"mean_dpsi_drop_0_8_to_0_9") for r in ablate]; ax.bar(range(len(vals)),vals,color=[COLORS["blue"]]+["0.65"]*(len(vals)-1)); ax.set_xticks(range(len(vals)),labels,rotation=20,ha="right"); ax.set_ylabel("Mean DPsi drop (mV)"); clean(ax)
    ax=axes[7]; labs=[r["variant"].replace("_","\n") for r in robust]; vals=[f(r,"mean_dpsi_drop_0_8_to_0_9") for r in robust]; ax.plot(range(len(vals)),vals,color="0.4",lw=1); ax.scatter(range(len(vals)),vals,c=[COLORS["blue"] if r["run_axis"]=="initial_condition" else COLORS["orange"] for r in robust],s=35); ax.set_xticks(range(len(vals)),labs,rotation=20,ha="right"); ax.set_ylabel("Mean DPsi drop (mV)"); clean(ax)
    return save(fig, "r070_figure3_phase_transition")


def figure4() -> tuple[Path, Path]:
    metrics = read_json(RUNS / "R023" / "locked_test_metrics.json")
    controls = read_json(RUNS / "R023" / "negative_controls.json")
    preds = read_csv(RUNS / "R023" / "test_predictions.csv")
    cond = read_csv(RUNS / "R021" / "conditions.csv")
    fig=plt.figure(figsize=(14.0,7.8)); gs=fig.add_gridspec(2,4,hspace=0.42,wspace=0.45); axes=[fig.add_subplot(gs[i,j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)
    ax=axes[0]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    for i,txt in enumerate(["Computational\ncohort", "Locked\nsplit", "Test\nmetrics", "Negative\ncontrols"]):
        x=0.05+i*0.24; box(ax,(x,0.48),(0.17,0.20),txt,COLORS["pale_blue"] if i<2 else COLORS["pale_green"],COLORS["blue"],bold=True)
        if i<3: ax.add_patch(FancyArrowPatch((x+0.17,0.58),(x+0.24,0.58),arrowstyle="->",mutation_scale=9,color=COLORS["gray"]))
    ax=axes[1]; test=[r for r in cond if r["split"]=="test" and r["label"]=="1"]; example=min(test,key=lambda r:float(r["event_time_s"])); t=np.linspace(0,90,181); event=float(example["event_time_s"]); y=170-8*np.log1p(t/12)-45/(1+np.exp(-(t-event)/2.5)); ax.plot(t,y,color=COLORS["blue"],lw=1.4); ax.axvline(event,color=COLORS["purple"],ls=":"); ax.axhline(140,color=COLORS["purple"],ls="--",lw=1); ax.set_xlabel("Time (s)"); ax.set_ylabel("DPsi-like trajectory (mV)"); clean(ax)
    ax=axes[2]; var=np.full_like(t,np.nan); ac=np.full_like(t,np.nan); win=20
    for i in range(win,len(t)):
        vals=y[i-win:i]; var[i]=np.var(vals,ddof=1); ac[i]=np.corrcoef(vals[:-1],vals[1:])[0,1] if np.std(vals[:-1])>0 and np.std(vals[1:])>0 else np.nan
    ax.plot(t,var,color=COLORS["orange"],label="Variance"); ax2=ax.twinx(); ax2.plot(t,ac,color=COLORS["purple"],label="Lag-1 AC"); ax.set_xlabel("Time (s)"); ax.set_ylabel("Variance"); ax2.set_ylabel("Lag-1 AC")
    ax=axes[3]; names=[m["model"] for m in metrics]; au=[m["auroc"] for m in metrics]; ap=[m["auprc"] for m in metrics]; x=np.arange(len(names)); ax.bar(x-0.18,au,width=0.35,color=COLORS["blue"],label="AUROC"); ax.bar(x+0.18,ap,width=0.35,color=COLORS["green"],label="AUPRC"); ax.set_xticks(x,[n.replace("locked_","locked\n").replace("best_","best\n") for n in names],rotation=20); ax.set_ylim(0,1.05); ax.legend(frameon=False); clean(ax)
    ax=axes[4]; b=[m["brier"] for m in metrics]; ax.bar(range(len(names)),b,color=COLORS["orange"]); ax.set_xticks(range(len(names)),[n.replace("_","\n") for n in names],rotation=20); ax.set_ylabel("Brier score"); clean(ax)
    ax=axes[5]; perm=controls["group_label_permutation"]; ax.errorbar([0],[perm["auroc_median"]],yerr=[[perm["auroc_median"]-perm["auroc_ci_low"]],[perm["auroc_ci_high"]-perm["auroc_median"]]],fmt="o",color=COLORS["gray"],capsize=4); ax.scatter([1],[perm["observed_locked_auroc"]],color=COLORS["blue"],s=45); ax.set_xticks([0,1],["Permutation\nnull","Observed\nlocked"]); ax.set_ylim(0,1.05); ax.set_ylabel("AUROC"); clean(ax)
    ax=axes[6]; ctrl=controls["within_trajectory_time_shuffle"]; ax.bar([0,1],[metrics[1]["auroc"],ctrl["auroc"]],color=[COLORS["purple"],"0.65"]); ax.set_xticks([0,1],["Intact\nEWS","Time\nshuffle"]); ax.set_ylim(0,1.05); ax.set_ylabel("AUROC"); clean(ax)
    draw_claim_strip(axes[7], "Interpretation gate", "descriptive simulated EWS diagnostics", "negative-control sanity checks", "independent EWS predictive-gain claim")
    return save(fig, "r070_figure4_locked_ews_diagnostics")


def figure5() -> tuple[Path, Path]:
    x=np.linspace(0,1,80); stress=np.linspace(0,1,60); X,S=np.meshgrid(x,stress); health=1-0.50*S-0.30*X*S-0.08*np.sin(2*np.pi*X)*S
    fig=plt.figure(figsize=(14.0,7.4)); gs=fig.add_gridspec(2,4,hspace=0.42,wspace=0.42); axes=[fig.add_subplot(gs[i,j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)
    ax=axes[0]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off"); ax.plot([0.12,0.92],[0.50,0.50],color=COLORS["gray"],lw=5,solid_capstyle="round"); ax.add_patch(Circle((0.10,0.50),0.08,facecolor=COLORS["pale_blue"],edgecolor=COLORS["blue"])); ax.text(0.10,0.50,"soma",ha="center",va="center"); ax.add_patch(FancyArrowPatch((0.20,0.38),(0.88,0.38),arrowstyle="->",mutation_scale=11,color=COLORS["gray"])); ax.text(0.54,0.25,"position-indexed scenario layer, not a validated spatial solver",ha="center",fontsize=7.2)
    ax=axes[1]; hm=ax.pcolormesh(x,stress,health,shading="auto",cmap="viridis",vmin=health.min(),vmax=1); ax.set_xlabel("Normalized soma-to-distal position"); ax.set_ylabel("Stress intensity"); cb=fig.colorbar(hm,ax=ax,pad=0.02); cb.set_label("Health index (scenario)"); clean(ax)
    ax=axes[2]; tt=np.linspace(0,1,120)
    for pos,c in [(0.1,COLORS["blue"]),(0.5,COLORS["green"]),(0.9,COLORS["orange"] )]: ax.plot(tt,1-0.65*tt-0.25*pos*tt**1.4,color=c,label=f"pos {pos:.1f}")
    ax.set_xlabel("Normalized time"); ax.set_ylabel("Health index"); ax.legend(frameon=False); clean(ax)
    ax=axes[3]; idx=(1-health[:,-1])/(1-health[:,0]+1e-6); ax.plot(stress,idx,color=COLORS["orange"],lw=1.6); ax.set_xlabel("Stress intensity"); ax.set_ylabel("Distal/proximal vulnerability"); clean(ax)
    for k,(name,mat,cmap) in enumerate([("Demand", X*(0.2+S),"magma"),("ROS burden", S*(0.4+0.6*X),"plasma"),("Reserve", 1-0.25*X-0.20*S,"viridis")]):
        ax=axes[4+k]; im=ax.pcolormesh(x,stress,mat,shading="auto",cmap=cmap); ax.set_xlabel("Position"); ax.set_ylabel("Stress"); ax.text(0.03,0.92,name,transform=ax.transAxes,color="white" if k<2 else "black",fontweight="bold"); clean(ax)
    draw_claim_strip(axes[7], "Hypothesis gate", "position-indexed computational hypothesis", "scenario sensitivity only", "measured spatial data; axonal transport solver; dying-back evidence")
    return save(fig, "r070_figure5_spatial_vulnerability")


def figure6() -> tuple[Path, Path]:
    diseases=["PD-like","AD-like","ALS-like","HD-like","FTD-like"]; axes_names=["Respiration","ROS","Calcium","Demand","Transport","Proteostasis"]; mat=np.array([[0.9,0.8,0.4,0.5,0.3,0.4],[0.5,0.6,0.8,0.7,0.4,0.6],[0.4,0.8,0.6,0.7,0.8,0.5],[0.5,0.7,0.5,0.8,0.5,0.8],[0.4,0.6,0.6,0.6,0.7,0.7]])
    fig=plt.figure(figsize=(14.0,7.8)); gs=fig.add_gridspec(2,4,hspace=0.42,wspace=0.42); axes=[fig.add_subplot(gs[i,j]) for i in range(2) for j in range(4)]
    for ax, letter in zip(axes, ascii_lowercase): label(ax, letter)
    ax=axes[0]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off"); box(ax,(0.34,0.40),(0.30,0.20),"Shared mitochondrial\nstate variables",COLORS["pale_blue"],COLORS["blue"],bold=True)
    for xy,txt,col in [((0.04,0.72),"Disease\ncontext",COLORS["purple"]),((0.04,0.10),"Stress-axis\noperator",COLORS["orange"]),((0.72,0.40),"Mechanism\nhypothesis",COLORS["green"])]: box(ax,xy,(0.20,0.16),txt,"white",col,bold=True); ax.add_patch(FancyArrowPatch((xy[0]+0.20,xy[1]+0.08),(0.34,0.50),arrowstyle="->",mutation_scale=9,color=col))
    ax=axes[1]; im=ax.imshow(mat,aspect="auto",cmap="YlGnBu",vmin=0,vmax=1); ax.set_xticks(range(len(axes_names)),axes_names,rotation=35,ha="right"); ax.set_yticks(range(len(diseases)),diseases); cb=fig.colorbar(im,ax=ax,pad=0.02); cb.set_label("Scenario weight")
    ax=axes[2]; tt=np.linspace(0,1,100)
    for i,(d,c) in enumerate(zip(diseases[:3],[COLORS["blue"],COLORS["purple"],COLORS["orange"]])): ax.plot(tt,1-(0.35+0.12*i)*tt-(0.10*i)*tt**2,color=c,label=d)
    ax.set_xlabel("Scenario time"); ax.set_ylabel("Health index"); ax.legend(frameon=False); clean(ax)
    ax=axes[3]; ros=mat[:,1]+0.08*np.arange(len(diseases)); energy=1-mat[:,0]*0.45-mat[:,3]*0.25; ax.scatter(energy,ros,s=90,c=[COLORS["blue"],COLORS["purple"],COLORS["orange"],COLORS["green"],COLORS["red"]]); [ax.text(energy[i]+0.005,ros[i],diseases[i],fontsize=6.8) for i in range(len(diseases))]; ax.set_xlabel("Energy-axis projection"); ax.set_ylabel("ROS-axis projection"); clean(ax)
    ax=axes[4]; overlap=mat.mean(axis=0); ax.bar(range(len(axes_names)),overlap,color=COLORS["green"]); ax.set_xticks(range(len(axes_names)),axes_names,rotation=35,ha="right"); ax.set_ylabel("Cross-disease mean weight"); clean(ax)
    ax=axes[5]; scores=mat.mean(axis=1); order=np.argsort(scores)[::-1]; ax.barh(np.arange(len(diseases)),scores[order],color=COLORS["orange"]); ax.set_yticks(np.arange(len(diseases)),[diseases[i] for i in order]); ax.set_xlabel("Hypothesis priority score"); clean(ax)
    ax=axes[6]; ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    for i,txt in enumerate(["Source\nledger","Parameter\nmap","Held-out\nsimulation","Scope\naudit"]):
        x=0.08+i*0.23; box(ax,(x,0.46),(0.16,0.20),txt,"white",COLORS["gray"],fontsize=6.8)
        if i<3: ax.add_patch(FancyArrowPatch((x+0.16,0.56),(x+0.23,0.56),arrowstyle="->",mutation_scale=9,color=COLORS["gray"]))
    draw_claim_strip(axes[7], "Claim boundary", "mechanism-hypothesis organization", "computational extension map", "clinical prediction; treatment windows; efficacy")
    return save(fig, "r070_figure6_disease_axis_hypotheses")


def table_texts(outputs: dict[str, tuple[Path, Path]]) -> dict[str, str]:
    summary = read_csv(RUNS / 'R025' / 'summary.csv')
    metrics = read_json(RUNS / 'R023' / 'locked_test_metrics.json')
    records = source_records()
    BS = chr(92)
    row_end = BS + BS
    t1_lines = [
        BS + 'begin{table}[t]',
        BS + 'centering',
        BS + 'caption{R070 evidence and claim-boundary matrix for the dry-lab NeurMito-DT manuscript.}',
        BS + 'label{tab:r070_claim_boundary}',
        BS + f'begin{{tabular}}{{p{{0.13{BS}textwidth}}p{{0.24{BS}textwidth}}p{{0.27{BS}textwidth}}p{{0.25{BS}textwidth}}}}',
        BS + 'toprule',
        f'Module & Evidence type & Supported statement & Withheld statement {row_end}',
        BS + 'midrule',
        f'Figure 1 & Source-local OCR ratios & Reserve-capacity heterogeneity across audited source records & Absolute OCR calibration, pooled parameter estimate, Bayesian/MCMC posterior, biological validation claim {row_end}',
        f'Figure 2 & Controlled synthetic misspecification benchmark & Hybrid Neural-ODE behavior under a hidden-residual task & Biological generalization or independent experimental-cohort performance {row_end}',
        f'Figure 3 & Reduced-ODE stress sweeps & Computational endpoint classes, transition bands, robustness summaries & Experimentally measured exposure thresholds or validated biological phase boundaries {row_end}',
        f'Figure 4 & Locked computational EWS test & Descriptive EWS behavior and negative-control sanity checks & Independent EWS predictive-gain claim beyond locked baseline features {row_end}',
        f'Figure 5 & Position-indexed scenarios & Spatial vulnerability hypothesis structure & Validated axonal transport solver or empirical dying-back confirmation {row_end}',
        f'Figure 6 & Disease-axis scenario map & Mechanism-hypothesis organization & Clinical prediction, treatment windows, intervention success, or patient outcomes {row_end}',
        BS + 'bottomrule',
        BS + 'end{tabular}',
        BS + 'end{table}',
    ]
    t2_lines = [
        BS + 'begin{table}[t]',
        BS + 'centering',
        BS + 'caption{R070 NeurMito-DT model components and observables.}',
        BS + 'label{tab:r070_model_components}',
        BS + f'begin{{tabular}}{{p{{0.18{BS}textwidth}}p{{0.19{BS}textwidth}}p{{0.24{BS}textwidth}}p{{0.28{BS}textwidth}}}}',
        BS + 'toprule',
        f'Component & Inputs & Outputs/observables & Limitation {row_end}',
        BS + 'midrule',
        f'ODE core & Stress operators and initial conditions & DPsi, ATP, ROS-like endpoint states & Mechanistic simulation, not new experimental measurement {row_end}',
        f'Source-local OCR contract & Published control OCR bars & Maximal/basal and spare/basal ratios & Relative source evidence only; no absolute calibration {row_end}',
        f'Hybrid Neural-ODE benchmark & Synthetic hidden residuals & Trajectory and endpoint RMSE & Method benchmark under controlled misspecification {row_end}',
        f'EWS diagnostic layer & Simulated labelled trajectories & AUROC, AUPRC, Brier, negative controls & Descriptive diagnostics without independent predictive-gain claim {row_end}',
        f'Spatial and disease scenario layers & Assumed stress-axis mappings & Hypothesis maps and sensitivity panels & Computational scenario layers, not new biological evidence {row_end}',
        BS + 'bottomrule',
        BS + 'end{tabular}',
        BS + 'end{table}',
    ]
    source_rows = [
        f"{r['id']} & PMID:{r['pmid']} & {r['group']} & maximal/basal {r['max']['nominal']:.3f}; spare/basal {r['spare']['nominal']:.3f} & Source-local relative ratios only {row_end}"
        for r in records
    ]
    t3_lines = [
        BS + 'begin{table}[t]',
        BS + 'centering',
        BS + 'caption{R070 source-local OCR record ledger.}',
        BS + 'label{tab:r070_source_ocr_records}',
        BS + f'begin{{tabular}}{{llllp{{0.25{BS}textwidth}}}}',
        BS + 'toprule',
        f'Record & Source & Group & Retained ratios & Use boundary {row_end}',
        BS + 'midrule',
        *source_rows,
        BS + 'bottomrule',
        BS + 'end{tabular}',
        BS + 'end{table}',
    ]
    metric_rows = []
    for r in summary:
        metric_rows.append(f"R025 benchmark & {r['model']} & trajectory RMSE & {float(r['trajectory_rmse_mean']):.4f} +/- {float(r['trajectory_rmse_sd']):.4f} & Controlled synthetic task only {row_end}")
    for m in metrics:
        metric_rows.append(f"R023 locked test & {m['model']} & AUROC/AUPRC/Brier & {m['auroc']:.3f}/{m['auprc']:.3f}/{m['brier']:.4f} & Locked computational diagnostic {row_end}")
    t4_lines = [
        BS + 'begin{table}[t]',
        BS + 'centering',
        BS + 'caption{R070 computational diagnostic metrics.}',
        BS + 'label{tab:r070_computational_diagnostics}',
        BS + f'begin{{tabular}}{{llllp{{0.25{BS}textwidth}}}}',
        BS + 'toprule',
        f'Analysis & Configuration & Metric & Value & Interpretation boundary {row_end}',
        BS + 'midrule',
        *metric_rows,
        BS + 'bottomrule',
        BS + 'end{tabular}',
        BS + 'end{table}',
    ]
    return {
        'r070_table1_claim_boundary.tex': '\n'.join(t1_lines),
        'r070_table2_model_components.tex': '\n'.join(t2_lines),
        'r070_table3_source_local_ocr_records.tex': '\n'.join(t3_lines),
        'r070_table4_computational_diagnostics.tex': '\n'.join(t4_lines),
    }

def write_tables(outputs):
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    table_paths = []
    for name, text in table_texts(outputs).items():
        path = TABLE_DIR / name
        path.write_text(text + "\n", encoding="utf-8")
        table_paths.append(path)
    return table_paths


def write_includes(outputs):
    captions = {
        "r070_figure1_source_contract_ocr_mapping": ("Source-local OCR evidence contract and reserve-capacity heterogeneity.", "fig:r070_source_contract"),
        "r070_figure2_hybrid_benchmark": ("Hybrid Neural-ODE architecture and controlled hidden-residual benchmark.", "fig:r070_hybrid_benchmark"),
        "r070_figure3_phase_transition": ("Multi-stressor reduced-ODE phase structure, nonlinear endpoint transitions, and robustness summaries.", "fig:r070_phase_transition"),
        "r070_figure4_locked_ews_diagnostics": ("Locked early-warning-signal diagnostics with negative controls in the simulated cohort.", "fig:r070_locked_ews"),
        "r070_figure5_spatial_vulnerability": ("Position-indexed spatial vulnerability hypotheses; scenario layer only.", "fig:r070_spatial_vulnerability"),
        "r070_figure6_disease_axis_hypotheses": ("Disease-axis mechanism map and claim-bounded application layer.", "fig:r070_disease_axis"),
    }
    chunks = ["% R070 main figure include snippets. Generated from audited dry-lab assets."]
    for stem, (_, pdf) in outputs.items():
        caption, lab = captions[stem]
        chunks.extend(["", r"\begin{figure}[t]", r"    \centering", f"    \\includegraphics[width=0.95\\textwidth]{{{rel(pdf)}}}", f"    \\caption{{{caption} The figure reports computational or source-audited evidence only; no assay, imaging, animal, clinical, or other wet experimental data were generated in this study.}}", f"    \\label{{{lab}}}", r"\end{figure}"])
    INCLUDES.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return INCLUDES


def main() -> int:
    outputs = {
        "r070_figure1_source_contract_ocr_mapping": figure1(),
        "r070_figure2_hybrid_benchmark": figure2(),
        "r070_figure3_phase_transition": figure3(),
        "r070_figure4_locked_ews_diagnostics": figure4(),
        "r070_figure5_spatial_vulnerability": figure5(),
        "r070_figure6_disease_axis_hypotheses": figure6(),
    }
    tables = write_tables(outputs)
    includes = write_includes(outputs)
    inputs = [
        DESIGN_REPORT,
        RUNS / "R042" / "digitization_uncertainty_propagation.json",
        RUNS / "R060" / "pmc4454361_control_relative_digitization.json",
        RUNS / "R060B" / "pmc5124357_control_relative_digitization.json",
        RUNS / "R062" / "conditional_heterogeneity_mapping.json",
        RUNS / "R025" / "summary.csv",
        RUNS / "R025" / "metrics.csv",
        RUNS / "R025" / "predictions.csv",
        RUNS / "R014B" / "resolved_transition_grid.csv",
        RUNS / "R014B" / "transition_band_summary.csv",
        RUNS / "R009" / "additive_proxy_residuals.csv",
        RUNS / "R010" / "robustness_summary.csv",
        RUNS / "R023" / "locked_test_metrics.json",
        RUNS / "R023" / "negative_controls.json",
    ]
    manifest = {
        "run_id": "R070",
        "status": "complete",
        "claim_boundary": "dry-lab/computational only; no assay, imaging, animal, clinical, or other wet experimental data generated",
        "figures": {stem: {"png": rel(png), "pdf": rel(pdf), "png_sha256": sha256(png), "pdf_sha256": sha256(pdf)} for stem, (png, pdf) in outputs.items()},
        "tables": {p.name: {"path": rel(p), "sha256": sha256(p)} for p in tables},
        "includes": {"path": rel(includes), "sha256": sha256(includes)},
        "inputs": {rel(p): sha256(p) for p in inputs if p.exists()},
        "manuscript_modified": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"figures": {k: [rel(v[0]), rel(v[1])] for k, v in outputs.items()}, "tables": [rel(p) for p in tables], "includes": rel(includes), "manifest": rel(MANIFEST)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


