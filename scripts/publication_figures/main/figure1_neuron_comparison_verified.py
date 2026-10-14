"""R063 source-audited Figure 1 with heterogeneity overlay.

The figure uses the R042/R046/R047/R048/R060/R060B/R062 evidence chain. It
compares the matched R033/R039 primary cortical records with the higher-reserve
R060/R060B candidates under the maximal/spare-only contract, retains R046 as a
formula reference, and exposes the restricted mapping's source heterogeneity.
It contains no nine-neuron absolute OCR table, MCMC/posterior, neuron-type
ranking, calibrated parameter estimate, or external-validation claim.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np


plt.rcParams.update({
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7,
})


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "refine-logs" / "runs"
INPUTS = {
    "R042": RUNS / "R042" / "digitization_uncertainty_propagation.json",
    "R046": RUNS / "R046" / "pmc5667543_control_stage_digitization.json",
    "R047": RUNS / "R047" / "cross_source_formula_coordination.json",
    "R048": RUNS / "R048" / "maximal_spare_restricted_mapping.json",
    "R060": RUNS / "R060" / "pmc4454361_control_relative_digitization.json",
    "R060B": RUNS / "R060B" / "pmc5124357_control_relative_digitization.json",
    "R062": RUNS / "R062" / "conditional_heterogeneity_mapping.json",
}
OUT = ROOT / "figures" / "figure1_neuron_comparison.png"
PDF = ROOT / "figures" / "figure1_neuron_comparison.pdf"
METADATA = RUNS / "R051" / "figure1_metadata.json"
R063_MANIFEST = RUNS / "R063" / "figure1_heterogeneity_overlay_manifest.json"

COLORS = {
    "r033": "#0072B2",
    "r039": "#D55E00",
    "r060": "#009E73",
    "r060b": "#CC79A7",
    "r046": "#777777",
    "green": "#009E73",
    "orange": "#E69F00",
    "blocked": "#CC79A7",
    "light": "#F2F2F2",
}


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _panel_label(ax, label):
    ax.text(
        -0.12,
        1.07,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="top",
    )


def _clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)


def _source_endpoint_records(endpoint, r042, r060, r060b):
    low_intervals = r042["source_ratio_intervals"]
    return [
        {
            "source": "PMID:31931869",
            "label": "R033\nlow",
            "color": COLORS["r033"],
            "value": low_intervals["PMID:31931869"][endpoint]["nominal"],
            "low": low_intervals["PMID:31931869"][endpoint]["low"],
            "high": low_intervals["PMID:31931869"][endpoint]["high"],
        },
        {
            "source": "PMID:24056030",
            "label": "R039\nlow",
            "color": COLORS["r039"],
            "value": low_intervals["PMID:24056030"][endpoint]["nominal"],
            "low": low_intervals["PMID:24056030"][endpoint]["low"],
            "high": low_intervals["PMID:24056030"][endpoint]["high"],
        },
        {
            "source": "PMID:25081478",
            "label": "R060\nhigh",
            "color": COLORS["r060"],
            "value": r060["relative_ratios"][endpoint]["value"],
            "low": r060["relative_ratios"][endpoint]["interval"][0],
            "high": r060["relative_ratios"][endpoint]["interval"][1],
        },
        {
            "source": "PMID:27889640",
            "label": "R060B\nhigh",
            "color": COLORS["r060b"],
            "value": r060b["relative_ratios"][endpoint]["value"],
            "low": r060b["relative_ratios"][endpoint]["interval"][0],
            "high": r060b["relative_ratios"][endpoint]["interval"][1],
        },
    ]


def _ratio_panel(ax, endpoint, title, r042, r046, r060, r060b, r062):
    records = _source_endpoint_records(endpoint, r042, r060, r060b)
    x = np.arange(len(records))
    for xi, record in zip(x, records):
        value = record["value"]
        ax.errorbar(
            [xi],
            [value],
            yerr=[[value - record["low"]], [record["high"] - value]],
            fmt="none",
            ecolor=record["color"],
            elinewidth=2,
            capsize=4,
            capthick=1.2,
        )
        ax.scatter(
            [xi],
            [value],
            s=60,
            c=record["color"],
            zorder=3,
            edgecolor="white",
            lw=0.8,
        )

    f_interval = r046["stages"]["F"]["interval_percent_of_baseline"]
    if endpoint == "maximal_to_basal":
        reference = r046["stages"]["F"]["value_percent_of_baseline"] / 100.0
        ref_interval = [f_interval[0] / 100.0, f_interval[1] / 100.0]
    else:
        reference = r046["derived_observables"]["spare"][
            "value_percent_of_baseline"
        ] / 100.0
        spare_interval = r046["derived_observables"]["spare"][
            "interval_percent_of_baseline"
        ]
        ref_interval = [spare_interval[0] / 100.0, spare_interval[1] / 100.0]
    ax.errorbar(
        [4.7],
        [reference],
        yerr=[[reference - ref_interval[0]], [ref_interval[1] - reference]],
        fmt="^",
        color=COLORS["r046"],
        markerfacecolor="white",
        markersize=8,
        capsize=5,
        label="R046 formula reference",
    )
    low_mean = r062["source_groups"]["low_reserve_pair"]["mean_ratios"][endpoint]
    high_mean = r062["source_groups"]["high_reserve_pair"]["mean_ratios"][endpoint]
    ax.plot([-0.25, 1.25], [low_mean, low_mean], color="black", lw=1.2, ls="--")
    ax.plot([1.75, 3.25], [high_mean, high_mean], color="black", lw=1.2, ls="--")
    ax.axvspan(-0.45, 1.45, color=COLORS["r033"], alpha=0.05, lw=0)
    ax.axvspan(1.55, 3.45, color=COLORS["r060"], alpha=0.05, lw=0)
    ax.axvline(1.5, color="#BBBBBB", ls=":", lw=1)
    ax.axvline(4.15, color="#BBBBBB", ls=":", lw=1)
    ax.set_xticks([0, 1, 2, 3, 4.7], [record["label"] for record in records] + ["R046\nref."])
    ax.tick_params(axis="x", labelsize=7.4)
    ax.set_ylabel("Source-local ratio")
    ax.set_title(title, loc="left", fontweight="bold", fontsize=9)
    ax.text(
        0.98,
        0.04,
        "dashed: conditional group means; R046 not pooled",
        transform=ax.transAxes,
        ha="right",
        fontsize=6.8,
        color=COLORS["r046"],
    )
    _clean(ax)


def _heterogeneity_panel(ax, r042, r060, r060b, r062):
    endpoints = ["maximal_to_basal", "spare_to_basal"]
    labels = ["maximal/basal", "spare/basal"]
    for row, (endpoint, label) in enumerate(zip(endpoints, labels)):
        records = _source_endpoint_records(endpoint, r042, r060, r060b)
        for offset, record in zip((0.21, 0.07, -0.07, -0.21), records):
            ax.plot([record["low"], record["high"]], [row + offset] * 2,
                    color=record["color"], lw=4.5, solid_capstyle="round",
                    label=record["label"].replace("\n", " ") if row == 0 else None)
        low_mean = r062["source_groups"]["low_reserve_pair"]["mean_ratios"][endpoint]
        high_mean = r062["source_groups"]["high_reserve_pair"]["mean_ratios"][endpoint]
        ax.plot(
            [low_mean, high_mean],
            [row, row],
            color="#333333",
            lw=1.3,
            ls="--",
        )
    ax.set_yticks([0, 1], labels)
    ax.set_xlabel("Digitization interval and group means")
    ax.set_title("c  Low/high reserve source split", loc="left",
                 fontweight="bold", fontsize=9)
    ax.legend(frameon=False, fontsize=6.2, loc="lower right", ncol=2)
    _clean(ax)


def _formula_panel(ax, r047):
    terms = ["B", "O", "F", "N", "A", "P"]
    records = ["R033", "R039", "R046"]
    status_code = {
        "reported": 3,
        "digitized": 3,
        "inferred": 2,
        "inferred_conflicting": 1,
        "unavailable": 0,
    }
    matrix = np.asarray([
        [status_code[r047["records"][record]["terms"][term]] for term in terms]
        for record in records
    ])
    cmap = matplotlib.colors.ListedColormap(
        ["#DDDDDD", COLORS["blocked"], COLORS["orange"], COLORS["green"]]
    )
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    for row, record in enumerate(records):
        for col, term in enumerate(terms):
            status = r047["records"][record]["terms"][term]
            short = {
                "reported": "reported",
                "digitized": "digitized",
                "inferred": "inferred",
                "inferred_conflicting": "conflict",
                "unavailable": "missing",
            }[status]
            ax.text(col, row, short, ha="center", va="center", fontsize=6.5,
                    color="white" if status_code[status] in (1, 3) else "black")
    ax.set_xticks(np.arange(len(terms)), terms)
    ax.set_yticks(np.arange(len(records)), records)
    ax.set_title("d  Formula-status matrix", loc="left",
                 fontweight="bold", fontsize=9)
    ax.set_xlabel("B basal; O oligomycin; F FCCP; N non-mito; A ATP; P leak")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _mapping_panel(ax, r062):
    groups = ["low_reserve_pair", "high_reserve_pair"]
    labels = ["Low reserve\nR033/R039", "High reserve\nR060/R060B"]
    losses = [
        r062["conditional_group_rankings"][group]["top_ranked"][0]["loss"]
        for group in groups
    ]
    colors = [COLORS["r033"], COLORS["r060"]]
    ax.bar(np.arange(2), losses, color=colors, width=0.56)
    for xi, group in enumerate(groups):
        top = r062["conditional_group_rankings"][group]["top_ranked"][0]
        ax.text(
            xi,
            losses[xi] + 0.0015,
            f"g_H={top['multipliers']['g_H']}",
            ha="center",
            va="bottom",
            fontsize=7,
        )
    ax.set_xticks(np.arange(2), labels)
    ax.set_ylabel("Mean squared log-ratio loss")
    ax.set_title("e  Conditional diagnostic mapping", loc="left",
                 fontweight="bold", fontsize=9)
    _clean(ax)


def _gate_panel(ax, r048, r062):
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    rows = [
        ("Retained", "maximal/basal + spare/basal", COLORS["green"]),
        ("Excluded", "ATP-linked + proton leak fit targets", COLORS["blocked"]),
        ("Conditional", "low/high reserve split; no blind pooling", COLORS["orange"]),
        ("Withheld", "absolute calibration, MCMC, validation", COLORS["blocked"]),
    ]
    y_values = [0.78, 0.57, 0.36, 0.15]
    for (label, text, color), y in zip(rows, y_values):
        ax.add_patch(FancyBboxPatch(
            (0.04, y - 0.07), 0.92, 0.13,
            boxstyle="round,pad=0.015",
            facecolor=COLORS["light"], edgecolor=color, lw=1.1,
        ))
        ax.text(0.08, y, label, color=color, fontweight="bold", va="center",
                fontsize=7.6)
        ax.text(0.30, y, text, va="center", fontsize=7.2)
    ax.set_title("f  Interpretation boundary", loc="left", fontweight="bold", fontsize=9)
    assert r048["claim_gate"]["rank_stable_under_digitization"] is False
    assert r062["interpretation"]["calibrated_parameter_estimate"] is False


def build_metadata(r042, r046, r047, r048, r060, r060b, r062):
    return {
        "run_id": "R063",
        "status": "complete_figure1_heterogeneity_overlay",
        "outputs": {
            "png": str(OUT.relative_to(ROOT)).replace("\\", "/"),
            "pdf": str(PDF.relative_to(ROOT)).replace("\\", "/"),
        },
        "inputs": {
            name: {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(path),
            }
            for name, path in INPUTS.items()
        },
        "panels": {
            "a": "low and high source maximal-to-basal intervals with conditional group means",
            "b": "low and high source spare-to-basal intervals with conditional group means",
            "c": "low/high reserve source split across retained endpoints",
            "d": "reported/digitized/inferred/conflicting/unavailable term matrix",
            "e": "R062 conditional low/high reserve diagnostic mapping",
            "f": "rank-instability, heterogeneity, and claim boundary",
        },
        "source_roles": {
            "R033": "matched E18/DIV7 source-local record",
            "R039": "matched E18/DIV7 source-local record",
            "R060": "matched-candidate high-reserve source-local record; heterogeneity evidence only",
            "R060B": "backup high-reserve source-local record; heterogeneity evidence only",
            "R046": "DIV10 formula reference only; not fitted or pooled",
        },
        "used_endpoints": r048["used_endpoints"],
        "heterogeneity_overlay": {
            "enabled": True,
            "source_groups": {
                "low_reserve_pair": r062["source_groups"]["low_reserve_pair"]["sources"],
                "high_reserve_pair": r062["source_groups"]["high_reserve_pair"]["sources"],
            },
            "mean_ratios": {
                "low_reserve_pair": r062["source_groups"]["low_reserve_pair"]["mean_ratios"],
                "high_reserve_pair": r062["source_groups"]["high_reserve_pair"]["mean_ratios"],
            },
            "parameter_direction_shift_detected": r062["heterogeneity_summary"][
                "parameter_direction_shift_detected"
            ],
            "interpretation": "conditional_source_heterogeneity_not_calibration",
        },
        "claim_gate": {
            "source_values_pooled": False,
            "source_values_pooled_for_calibration": False,
            "r046_fitted": False,
            "absolute_ocr_displayed": False,
            "nine_neuron_ranking_displayed": False,
            "mcmc_or_posterior_displayed": False,
            "calibrated_parameter_estimate": False,
            "rank_stable_under_digitization": r048["claim_gate"][
                "rank_stable_under_digitization"
            ],
            "external_validation_claim_allowed": False,
        },
        "formula_contract_version": r047["minimum_common_observation_contract"][
            "version"
        ],
        "r046_formula_reference_available": r046["claim_gate"][
            "relative_stage_contract_available"
        ],
        "between_source_retained_endpoints_overlap": {
            endpoint: r042["between_source_interval_overlap"][endpoint]["overlaps"]
            for endpoint in r048["used_endpoints"]
        },
        "manuscript_modified": False,
    }


def generate():
    r042 = _read(INPUTS["R042"])
    r046 = _read(INPUTS["R046"])
    r047 = _read(INPUTS["R047"])
    r048 = _read(INPUTS["R048"])
    r060 = _read(INPUTS["R060"])
    r060b = _read(INPUTS["R060B"])
    r062 = _read(INPUTS["R062"])

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.4), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.06, h_pad=0.08, wspace=0.18, hspace=0.18)
    _ratio_panel(
        axes[0, 0], "maximal_to_basal", "a  Maximal/basal contract",
        r042, r046, r060, r060b, r062
    )
    _ratio_panel(
        axes[0, 1], "spare_to_basal", "b  Spare/basal contract",
        r042, r046, r060, r060b, r062
    )
    _heterogeneity_panel(axes[0, 2], r042, r060, r060b, r062)
    _formula_panel(axes[1, 0], r047)
    _mapping_panel(axes[1, 1], r062)
    _gate_panel(axes[1, 2], r048, r062)
    fig.suptitle(
        "Figure 1. Source-audited relative OCR contract with heterogeneity overlay\n"
        "Primary cortical source comparison; conditional diagnostic mapping only",
        fontsize=10.5,
        fontweight="bold",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=600, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)

    metadata = build_metadata(r042, r046, r047, r048, r060, r060b, r062)
    metadata["outputs"]["png_sha256"] = _sha256(OUT)
    metadata["outputs"]["pdf_sha256"] = _sha256(PDF)
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "run_id": "R063",
        "status": "complete_figure1_heterogeneity_overlay",
        "active_outputs": {
            "png": metadata["outputs"]["png"],
            "pdf": metadata["outputs"]["pdf"],
            "png_sha256": metadata["outputs"]["png_sha256"],
            "pdf_sha256": metadata["outputs"]["pdf_sha256"],
        },
        "metadata_path": str(METADATA.relative_to(ROOT)).replace("\\", "/"),
        "metadata_sha256": _sha256(METADATA),
        "heterogeneity_overlay": metadata["heterogeneity_overlay"],
        "claim_gate": metadata["claim_gate"],
        "manuscript_modified": False,
    }
    R063_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    R063_MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return OUT, PDF


if __name__ == "__main__":
    print(generate())
