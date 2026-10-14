"""Build a resolved computational phase-grid artifact from R011-R014A.

This post-processing step merges the R011 refined scan with all later tail
extensions, then exports a discrete endpoint-class grid and a final-DPsi grid.
It deliberately avoids inventing a continuous collapse threshold.
"""

import argparse
import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_R011 = PROJECT_ROOT / "inputs/audit_runs/R011/transition_refinement_grid.csv"
DEFAULT_TAILS = [
    PROJECT_ROOT / "inputs/audit_runs/R012/tail_extension_grid.csv",
    PROJECT_ROOT / "inputs/audit_runs/R013/deep_tail_grid.csv",
    PROJECT_ROOT / "inputs/audit_runs/R014/final_tail_grid.csv",
    PROJECT_ROOT / "inputs/audit_runs/R014A/persistent_tail_grid.csv",
]
DEFAULT_OUTPUT = PROJECT_ROOT / "inputs/audit_runs/R014B"
DEFAULT_FIGURE = PROJECT_ROOT / "figures/figure3_resolved_phase_grid.png"
DEFAULT_PDF = PROJECT_ROOT / "figures/figure3_resolved_phase_grid.pdf"


def _key(row):
    return float(row["rotenone_inhibition"]), float(row["paraquat_index"])


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _to_float(value):
    return float(value)


def resolve_rows(r011_csv, tail_csvs):
    """Merge the latest tail result into each R011 refined-grid row."""
    base_rows = _read_csv(r011_csv)
    resolved = {_key(row): dict(row) for row in base_rows}

    for tail_csv in tail_csvs:
        for tail_row in _read_csv(tail_csv):
            key = _key(tail_row)
            if key not in resolved:
                continue
            row = resolved[key]
            row["resolved_endpoint_class"] = tail_row["endpoint_class"]
            row["resolved_duration_s"] = tail_row["duration_s"]
            row["resolved_final_dpsi_mv"] = tail_row["final_dpsi_mv"]
            row["resolved_final_atp_m_mm"] = tail_row["final_atp_m_mm"]
            row["resolved_endpoint_eligible_for_phase_diagram"] = (
                tail_row["endpoint_eligible_for_phase_diagram"]
            )
            row["resolved_physiology_qualified_endpoint"] = (
                tail_row["physiology_qualified_endpoint"]
            )
            row["resolved_source_run"] = tail_csv.parent.name

    for row in resolved.values():
        row.setdefault("resolved_endpoint_class", row["endpoint_class"])
        row.setdefault("resolved_duration_s", row["duration_s"])
        row.setdefault("resolved_final_dpsi_mv", row["final_dpsi_mv"])
        row.setdefault("resolved_final_atp_m_mm", row["final_atp_m_mm"])
        row.setdefault(
            "resolved_endpoint_eligible_for_phase_diagram",
            str(row["endpoint_eligible_for_phase_diagram"]),
        )
        row.setdefault(
            "resolved_physiology_qualified_endpoint",
            str(row["physiology_qualified_endpoint"]),
        )
        row.setdefault("resolved_source_run", "R011")

    return sorted(
        resolved.values(),
        key=lambda row: (_to_float(row["paraquat_index"]), _to_float(row["rotenone_inhibition"])),
    )


def class_counts(rows):
    counts = {}
    for row in rows:
        label = row["resolved_endpoint_class"]
        counts[label] = counts.get(label, 0) + 1
    return counts


def transition_band_summary(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(_to_float(row["paraquat_index"]), []).append(row)

    summaries = []
    for paraquat, group in sorted(grouped.items()):
        phys = [
            _to_float(row["rotenone_inhibition"])
            for row in group
            if row["resolved_endpoint_class"] == "near_fixed_physiological_endpoint"
        ]
        dep = [
            _to_float(row["rotenone_inhibition"])
            for row in group
            if row["resolved_endpoint_class"] == "near_fixed_depolarized_endpoint"
        ]
        highest_phys = max(phys) if phys else np.nan
        lowest_depol = min(dep) if dep else np.nan
        gap = lowest_depol - highest_phys if phys and dep else np.nan
        summaries.append(
            {
                "paraquat_index": paraquat,
                "n_conditions": len(group),
                "n_physiological": len(phys),
                "n_depolarized": len(dep),
                "highest_physiological_rotenone": highest_phys,
                "lowest_depolarized_rotenone": lowest_depol,
                "observed_transition_gap": gap,
            }
        )
    return summaries


def _grid(rows, value_key):
    rotenone = sorted({_to_float(row["rotenone_inhibition"]) for row in rows})
    paraquat = sorted({_to_float(row["paraquat_index"]) for row in rows})
    lookup = {_key(row): row for row in rows}
    matrix = np.empty((len(paraquat), len(rotenone)), dtype=float)
    for i, para in enumerate(paraquat):
        for j, rot in enumerate(rotenone):
            matrix[i, j] = float(lookup[(rot, para)][value_key])
    return np.asarray(rotenone), np.asarray(paraquat), matrix


def _write_csv(path, rows):
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _plot(rows, figure_path, pdf_path):
    rot, pq, dpsi = _grid(rows, "resolved_final_dpsi_mv")
    _, _, class_grid = _grid(
        [
            dict(row, resolved_numeric_class=(
                0.0 if row["resolved_endpoint_class"] == "near_fixed_physiological_endpoint" else 1.0
            ))
            for row in rows
        ],
        "resolved_numeric_class",
    )
    band_rows = transition_band_summary(rows)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), constrained_layout=True)
    cmap = ListedColormap(["#4dac26", "#d01c8b"])

    im_class = axes[0].imshow(
        class_grid,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap=cmap,
        extent=[
            rot.min() * 100 - 1.0,
            rot.max() * 100 + 1.0,
            pq.min() - 0.5,
            pq.max() + 0.5,
        ],
        vmin=0,
        vmax=1,
    )
    axes[0].set_title("Resolved endpoint class", fontweight="bold")
    axes[0].set_xlabel("Rotenone (% Complex I inhibition)")
    axes[0].set_ylabel("Paraquat index (µM)")
    axes[0].set_yticks(pq)
    axes[0].set_xticks(rot[[0, 2, 4, 6, 8, 10, 12]] * 100)
    axes[0].grid(color="white", linewidth=0.4, alpha=0.55)
    axes[0].text(
        0.02,
        0.98,
        "Green: physiological\nPink: depolarized",
        transform=axes[0].transAxes,
        va="top",
        fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85),
    )

    mesh = axes[1].pcolormesh(
        rot * 100,
        pq,
        dpsi,
        shading="auto",
        cmap="viridis",
    )
    axes[1].set_title(r"Resolved final $\Delta\Psi_m$", fontweight="bold")
    axes[1].set_xlabel("Rotenone (% Complex I inhibition)")
    axes[1].set_ylabel("Paraquat index (µM)")
    axes[1].set_yticks(pq)
    axes[1].set_xticks(rot[[0, 2, 4, 6, 8, 10, 12]] * 100)
    axes[1].grid(color="white", linewidth=0.4, alpha=0.45)
    cbar = fig.colorbar(mesh, ax=axes[1], pad=0.02)
    cbar.set_label(r"$\Delta\Psi_m$ (mV)")

    for summary in band_rows:
        y = summary["paraquat_index"]
        x0 = summary["highest_physiological_rotenone"] * 100
        x1 = summary["lowest_depolarized_rotenone"] * 100
        axes[0].plot([x0, x1], [y, y], color="black", linewidth=1.3, zorder=5)
        axes[1].plot([x0, x1], [y, y], color="white", linewidth=1.2, zorder=5)

    fig.suptitle(
        "Resolved computational phase grid (R011-R014A)\n"
        "Long-tail endpoint resolution; no formal collapse threshold defined",
        fontsize=10,
        fontweight="bold",
    )
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=600, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def run_resolved_phase_figure(
    r011_csv=DEFAULT_R011,
    tail_csvs=None,
    output_dir=DEFAULT_OUTPUT,
    figure_path=DEFAULT_FIGURE,
    pdf_path=DEFAULT_PDF,
):
    r011_csv = Path(r011_csv)
    output_dir = Path(output_dir)
    figure_path = Path(figure_path)
    pdf_path = Path(pdf_path)
    if not r011_csv.is_absolute():
        r011_csv = PROJECT_ROOT / r011_csv
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    if not figure_path.is_absolute():
        figure_path = PROJECT_ROOT / figure_path
    if not pdf_path.is_absolute():
        pdf_path = PROJECT_ROOT / pdf_path
    tail_csvs = list(DEFAULT_TAILS if tail_csvs is None else tail_csvs)
    tail_csvs = [
        path if Path(path).is_absolute() else PROJECT_ROOT / Path(path)
        for path in tail_csvs
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = resolve_rows(r011_csv, tail_csvs)
    band_rows = transition_band_summary(rows)

    resolved_csv = output_dir / "resolved_transition_grid.csv"
    band_csv = output_dir / "transition_band_summary.csv"
    metadata_path = output_dir / "metadata.json"
    _write_csv(resolved_csv, rows)
    _write_csv(band_csv, band_rows)
    _plot(rows, figure_path, pdf_path)

    metadata = {
        "run_id": "R014B",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "resolved computational phase-grid export after tail extension",
        "input_r011_csv": str(r011_csv),
        "input_tail_csvs": [str(path) for path in tail_csvs],
        "n_conditions": len(rows),
        "resolved_endpoint_class_counts": class_counts(rows),
        "formal_phase_boundary_defined": False,
        "collapse_threshold_defined": False,
        "resolved_csv": resolved_csv.name,
        "band_csv": band_csv.name,
        "figure_png": str(figure_path.relative_to(PROJECT_ROOT)),
        "figure_pdf": str(pdf_path.relative_to(PROJECT_ROOT)),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return resolved_csv, band_csv, metadata_path, figure_path, pdf_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--r011-csv", type=Path, default=DEFAULT_R011)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure-path", type=Path, default=DEFAULT_FIGURE)
    parser.add_argument("--pdf-path", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()
    result = run_resolved_phase_figure(
        r011_csv=args.r011_csv,
        output_dir=args.output_dir,
        figure_path=args.figure_path,
        pdf_path=args.pdf_path,
    )
    print("resolved_csv:", result[0])
    print("band_csv:", result[1])
    print("metadata:", result[2])
    print("figure_png:", result[3])
    print("figure_pdf:", result[4])
    print("class_counts:", class_counts(result[-1]))


if __name__ == "__main__":
    main()

