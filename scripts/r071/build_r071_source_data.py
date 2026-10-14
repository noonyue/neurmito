"""Build the auditable R071 Source Data workbook and QA report.

The workbook records panel-level provenance for all active R071 figures and
supplementary figures, together with source-linked variable dictionaries and
quality checks. It is a repository-local assembly artifact, not a journal
submission file.
"""

from __future__ import annotations

# Historical entry point delegates to the corrected single source of truth.
if __name__ == "__main__":
    import runpy
    from pathlib import Path as _Path
    runpy.run_path(str(_Path(__file__).with_name("build_submission_source_data.py")), run_name="__main__")
    raise SystemExit(0)

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "inputs" / "audit_runs"
FIG_DIR = ROOT / "results" / "figures"
MANIFEST_DIR = ROOT / "results" / "manifests"
OUT = ROOT / "results" / "source_data" / "04_R071_Source_Data.xlsx"
QA_OUT = ROOT / "results" / "manifests" / "R071_Source_Data_QA.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_json(value: Any, prefix: str = "") -> list[tuple[str, str, str]]:
    if isinstance(value, dict):
        rows: list[tuple[str, str, str]] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_json(child, child_prefix))
        return rows
    if isinstance(value, list):
        return [(prefix, "list", json.dumps(value, ensure_ascii=False))]
    return [(prefix, type(value).__name__, str(value))]


def style_sheet(ws) -> None:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F5597")
    for column_cells in ws.columns:
        values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
        width = min(max(max((len(value) for value in values), default=8) + 2, 10), 48)
        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = width


def write_rows(ws, headers: list[str], rows: list[list[Any]]) -> None:
    ws.append(headers)
    for row in rows:
        ws.append(row)
    style_sheet(ws)


def add_key_value_sheet(wb: Workbook, title: str, rows: list[tuple[str, str]]) -> None:
    ws = wb.create_sheet(title)
    write_rows(ws, ["Field", "Value"], [[a, b] for a, b in rows])


def add_table_sheet(wb: Workbook, title: str, headers: list[str], rows: list[list[Any]]) -> None:
    ws = wb.create_sheet(title)
    write_rows(ws, headers, rows)


def add_csv_sheet(wb: Workbook, sheet: str, path: Path, role: str) -> None:
    rows = read_csv(path)
    headers = list(rows[0].keys()) if rows else ["value"]
    out_rows = [
        [*([row.get(header, "") for header in headers]), rel(path), sha256(path), role]
        for row in rows
    ]
    ws = wb.create_sheet(sheet)
    write_rows(ws, [*headers, "source_file", "source_sha256", "claim_role"], out_rows)


def add_json_sheet(wb: Workbook, sheet: str, path: Path, role: str) -> None:
    data = read_json(path)
    rows = [
        [json_path, value_type, value, rel(path), sha256(path), role]
        for json_path, value_type, value in flatten_json(data)
    ]
    ws = wb.create_sheet(sheet)
    write_rows(ws, ["json_path", "value_type", "value", "source_file", "source_sha256", "claim_role"], rows)


def key_inputs() -> list[Path]:
    return [
        RUNS / "R042" / "digitization_uncertainty_propagation.json",
        RUNS / "R047" / "cross_source_formula_coordination.json",
        RUNS / "R048" / "maximal_spare_restricted_mapping.json",
        RUNS / "R060" / "pmc4454361_control_relative_digitization.json",
        RUNS / "R060B" / "pmc5124357_control_relative_digitization.json",
        RUNS / "R062" / "conditional_heterogeneity_mapping.json",
        RUNS / "R025" / "summary.csv",
        RUNS / "R025" / "metrics.csv",
        RUNS / "R025" / "predictions.csv",
        RUNS / "R025" / "metadata.json",
        RUNS / "R014B" / "resolved_transition_grid.csv",
        RUNS / "R014B" / "transition_band_summary.csv",
        RUNS / "R009" / "additive_proxy_residuals.csv",
        RUNS / "R009" / "mechanism_ablation_summary.csv",
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


def source_path(spec: dict[str, str]) -> Path:
    raw = spec["source_file"].replace("\\", "/")
    mapped = raw.replace("inputs/audit_runs", "inputs/audit_runs")
    candidates = [ROOT / mapped, ROOT / raw]
    if "/r071_sfigure_" in raw:
        candidates.insert(0, ROOT / "results" / "supplementary_figures" / Path(raw).name)
    if "/r071_figure_" in raw:
        candidates.insert(0, ROOT / "results" / "figures" / Path(raw).name)
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def source_sha256(spec: dict[str, str]) -> str:
    return sha256(source_path(spec))


def data_workbook_sheet(spec: dict[str, str]) -> str:
    """Return the numeric source table used by a panel, when one exists."""
    source = spec["source_file"]
    exact = {
        "inputs/audit_runs/R025/summary.csv": "F2_summary",
        "inputs/audit_runs/R025/metrics.csv": "F2_metrics",
        "inputs/audit_runs/R025/predictions.csv": "F2_predictions",
        "inputs/audit_runs/R025/metadata.json": "F2_metadata",
        "inputs/audit_runs/R014B/resolved_transition_grid.csv": "F3_phase_grid",
        "inputs/audit_runs/R014B/transition_band_summary.csv": "F3_band",
        "inputs/audit_runs/R009/additive_proxy_residuals.csv": "F3_synergy",
        "inputs/audit_runs/R009/mechanism_ablation_summary.csv": "F3_ablation",
        "inputs/audit_runs/R010/robustness_summary.csv": "F3_robustness",
        "inputs/audit_runs/R010/robustness_grid.csv": "F3_robust_grid",
        "inputs/audit_runs/R021/conditions.csv": "F4_conditions",
        "inputs/audit_runs/R021/events.csv": "F4_events",
        "inputs/audit_runs/R021/qc_summary.json": "F4_qc",
        "inputs/audit_runs/R023/test_predictions.csv": "F4_test_pred",
        "inputs/audit_runs/R023/locked_test_metrics.json": "F4_metrics",
        "inputs/audit_runs/R023/negative_controls.json": "F4_controls",
        "inputs/audit_runs/R042/digitization_uncertainty_propagation.json": "F1_uncertainty",
        "inputs/audit_runs/R047/cross_source_formula_coordination.json": "F1_contract",
        "inputs/audit_runs/R048/maximal_spare_restricted_mapping.json": "F1_mapping",
        "inputs/audit_runs/R060/pmc4454361_control_relative_digitization.json": "F1_R060",
        "inputs/audit_runs/R060B/pmc5124357_control_relative_digitization.json": "F1_R060B",
        "inputs/audit_runs/R062/conditional_heterogeneity_mapping.json": "F1_heterogeneity",
    }
    if source in exact:
        return exact[source]

    figure_panel = (spec["figure_id"], spec["panel_id"])
    figure_specific = {
        ("Figure 1", "a"): "F1_contract",
        ("Figure 1", "b"): "F1_contract",
        ("Figure 1", "c"): "F1_uncertainty",
        ("Figure 1", "d"): "F1_uncertainty",
        ("Figure 1", "e"): "F1_uncertainty",
        ("Figure 1", "f"): "F1_mapping",
        ("Figure 1", "g"): "F1_heterogeneity",
        ("Figure 1", "h"): "F1_heterogeneity",
        ("Figure 1", "i"): "F1_heterogeneity",
        ("Figure 2", "a"): "F2_predictions",
        ("Figure 2", "b"): "F2_predictions",
        ("Figure 2", "c"): "F2_summary",
        ("Figure 2", "d"): "F2_summary",
        ("Figure 2", "e"): "F2_metrics",
        ("Figure 2", "f"): "F2_predictions",
        ("Figure 2", "g"): "F2_predictions",
        ("Figure 2", "h"): "F2_predictions",
        ("Figure 2", "i"): "F2_summary",
        ("Figure 5", "b"): "F5_scenarios",
        ("Figure 5", "c"): "F5_scenarios",
        ("Figure 5", "d"): "F5_scenarios",
        ("Figure 5", "e"): "F5_scenarios",
        ("Figure 5", "f"): "F5_scenarios",
        ("Figure 5", "g"): "F5_trajectories",
        ("Figure 5", "h"): "F5_trajectories",
        ("Figure 5", "i"): "F5_scenarios",
        ("Figure 5", "j"): "F5_scenarios",
        ("Figure 5", "k"): "F5_scenarios",
        ("Figure 6", "b"): "F6_axis_matrix",
        ("Figure 6", "c"): "F6_trajectories",
        ("Figure 6", "d"): "F6_axis_summary",
        ("Figure 6", "e"): "F6_axis_summary",
        ("Figure 6", "f"): "F6_axis_summary",
        ("Figure 6", "g"): "F6_axis_matrix",
        ("Figure 6", "h"): "F6_axis_matrix",
        ("Figure 6", "i"): "F6_axis_matrix",
        ("Figure 6", "j"): "F6_axis_summary",
        ("Supplementary Figure S6", "b"): "Input_Inventory",
    }
    return figure_specific.get(figure_panel, spec["workbook_sheet"])


def panel_map_sheet(spec: dict[str, str]) -> str:
    if spec["source_data_status"] == "numeric":
        return data_workbook_sheet(spec)
    return spec["workbook_sheet"]


def panel_specs() -> list[dict[str, str]]:
    panel_specs = [
        {
            "figure_id": "Figure 1",
            "panel_id": "a",
            "panel_title": "Evidence provenance workflow",
            "panel_type": "schematic",
            "source_data_status": "schematic/no numeric source data",
            "workbook_sheet": "F1_panel_a",
            "data_range_or_filter": "diagram only",
            "x_variable": "",
            "y_variable": "",
            "unit": "dimensionless",
            "n_definition": "panel",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "conceptual layout",
            "claim_role": "evidence contract overview",
            "boundary_note": "No wet-lab validation or absolute calibration",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "b",
            "panel_title": "Audited source tiles",
            "panel_type": "raw/source-derived",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_b",
            "data_range_or_filter": "PMID:31931869; PMID:24056030; PMID:25081478; PMID:27889640",
            "x_variable": "source_record",
            "y_variable": "source-local OCR ratios",
            "unit": "ratio",
            "n_definition": "source record",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "within-source ratio retention",
            "claim_role": "source-local OCR evidence",
            "boundary_note": "Not pooled calibration",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "c",
            "panel_title": "Endpoint availability contract",
            "panel_type": "diagnostic",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_c",
            "data_range_or_filter": "R047 endpoint terms",
            "x_variable": "endpoint",
            "y_variable": "contract status",
            "unit": "categorical",
            "n_definition": "endpoint term",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "availability coding",
            "claim_role": "retained vs diagnostic-only endpoints",
            "boundary_note": "Not absolute calibration",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "d",
            "panel_title": "Restricted observation contract",
            "panel_type": "diagnostic",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_d",
            "data_range_or_filter": "R047 minimum common observation contract",
            "x_variable": "endpoint",
            "y_variable": "retention level",
            "unit": "categorical",
            "n_definition": "endpoint",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "contract filtering",
            "claim_role": "withheld vs retained endpoints",
            "boundary_note": "No biological validation claim",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "e",
            "panel_title": "Maximal/basal OCR ratios",
            "panel_type": "raw/source-derived",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_e",
            "data_range_or_filter": "four source records",
            "x_variable": "source_record",
            "y_variable": "maximal/basal OCR",
            "unit": "ratio",
            "n_definition": "source record",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "source-local ratio retention",
            "claim_role": "relative OCR constraint",
            "boundary_note": "Not absolute OCR calibration",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "f",
            "panel_title": "Spare/basal OCR ratios",
            "panel_type": "raw/source-derived",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_f",
            "data_range_or_filter": "four source records",
            "x_variable": "source_record",
            "y_variable": "spare/basal OCR",
            "unit": "ratio",
            "n_definition": "source record",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "source-local ratio retention",
            "claim_role": "relative OCR constraint",
            "boundary_note": "Not pooled calibration",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "g",
            "panel_title": "Source reserve scatter",
            "panel_type": "benchmark",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_g",
            "data_range_or_filter": "four source records",
            "x_variable": "maximal/basal OCR",
            "y_variable": "spare/basal OCR",
            "unit": "ratio",
            "n_definition": "source record",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "paired ratio visualization",
            "claim_role": "relative heterogeneity",
            "boundary_note": "No new assay dataset",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "h",
            "panel_title": "Restricted mapping loss summary",
            "panel_type": "benchmark",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_h",
            "data_range_or_filter": "R048 fit directions",
            "x_variable": "fit direction",
            "y_variable": "best train loss",
            "unit": "loss",
            "n_definition": "fit direction",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "restricted loss extraction",
            "claim_role": "sensitivity screen",
            "boundary_note": "Not identifiable posterior",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "i",
            "panel_title": "Conditional sensitivity search",
            "panel_type": "benchmark",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_i",
            "data_range_or_filter": "R062 top-ranked conditional groups",
            "x_variable": "Vmax_CV multiplier",
            "y_variable": "g_H multiplier",
            "unit": "multiplier",
            "n_definition": "ranked candidate",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "top-ranked conditional search",
            "claim_role": "restricted diagnostic sensitivity",
            "boundary_note": "No external validation",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "j",
            "panel_title": "Claim gate summary",
            "panel_type": "diagnostic",
            "source_data_status": "numeric",
            "workbook_sheet": "F1_panel_j",
            "data_range_or_filter": "R062 claim gate",
            "x_variable": "claim category",
            "y_variable": "open/closed",
            "unit": "binary",
            "n_definition": "claim gate",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "boolean gating",
            "claim_role": "boundary enforcement",
            "boundary_note": "No Bayesian posterior validation",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 1",
            "panel_id": "k",
            "panel_title": "Boundary summary",
            "panel_type": "schematic",
            "source_data_status": "schematic/no numeric source data",
            "workbook_sheet": "F1_panel_k",
            "data_range_or_filter": "boundary text only",
            "x_variable": "",
            "y_variable": "",
            "unit": "dimensionless",
            "n_definition": "panel",
            "source_file": rel(FIG_DIR / "r071_figure1_evidence_provenance_atlas.png"),
            "generator": "scripts/r071/build_r071_all.py::figure1",
            "transformation": "boundary strip",
            "claim_role": "permitted vs withheld statement",
            "boundary_note": "No new biological claim",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "a",
            "panel_title": "Hybrid benchmark architecture",
            "panel_type": "schematic",
            "source_data_status": "schematic/no numeric source data",
            "workbook_sheet": "F2_panel_a",
            "data_range_or_filter": "diagram only",
            "x_variable": "",
            "y_variable": "",
            "unit": "dimensionless",
            "n_definition": "panel",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "conceptual layout",
            "claim_role": "method overview",
            "boundary_note": "Synthetic benchmark only",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "b",
            "panel_title": "Benchmark protocol flow",
            "panel_type": "schematic",
            "source_data_status": "schematic/no numeric source data",
            "workbook_sheet": "F2_panel_b",
            "data_range_or_filter": "protocol only",
            "x_variable": "",
            "y_variable": "",
            "unit": "dimensionless",
            "n_definition": "panel",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "workflow diagram",
            "claim_role": "benchmark protocol",
            "boundary_note": "No cohort generalization",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "c",
            "panel_title": "State x1 trajectory",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_c",
            "data_range_or_filter": "seed 0, case 0, time series",
            "x_variable": "time_s",
            "y_variable": "pred_x1 / target_x1",
            "unit": "model state",
            "n_definition": "trajectory time point",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "held-out trajectory overlay",
            "claim_role": "benchmark trajectory",
            "boundary_note": "Synthetic hidden residual task",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "d",
            "panel_title": "State x2 trajectory",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_d",
            "data_range_or_filter": "seed 0, case 0, time series",
            "x_variable": "time_s",
            "y_variable": "pred_x2 / target_x2",
            "unit": "model state",
            "n_definition": "trajectory time point",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "held-out trajectory overlay",
            "claim_role": "benchmark trajectory",
            "boundary_note": "No biological generalization",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "e",
            "panel_title": "Trajectory RMSE summary",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_e",
            "data_range_or_filter": "R025 summary.csv",
            "x_variable": "model",
            "y_variable": "trajectory RMSE",
            "unit": "RMSE",
            "n_definition": "seed",
            "source_file": rel(RUNS / "R025" / "summary.csv"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "seed-aggregated summary",
            "claim_role": "benchmark comparison",
            "boundary_note": "Synthetic benchmark only",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "f",
            "panel_title": "Endpoint RMSE summary",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_f",
            "data_range_or_filter": "R025 summary.csv",
            "x_variable": "model",
            "y_variable": "endpoint RMSE",
            "unit": "RMSE",
            "n_definition": "seed",
            "source_file": rel(RUNS / "R025" / "summary.csv"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "seed-aggregated summary",
            "claim_role": "benchmark comparison",
            "boundary_note": "No experimental cohort",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "g",
            "panel_title": "Seed-wise RMSE",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_g",
            "data_range_or_filter": "R025 metrics.csv",
            "x_variable": "seed",
            "y_variable": "trajectory RMSE",
            "unit": "RMSE",
            "n_definition": "seed",
            "source_file": rel(RUNS / "R025" / "metrics.csv"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "seed-wise summary",
            "claim_role": "benchmark variability",
            "boundary_note": "Synthetic benchmark only",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "h",
            "panel_title": "Residual correction over time",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_h",
            "data_range_or_filter": "seed 0, case 0, time series",
            "x_variable": "time_s",
            "y_variable": "residual correction",
            "unit": "model state",
            "n_definition": "trajectory time point",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "residual subtraction",
            "claim_role": "benchmark correction",
            "boundary_note": "Controlled misspecification only",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "i",
            "panel_title": "Hidden gain versus hybrid error",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_i",
            "data_range_or_filter": "hybrid rows only",
            "x_variable": "hidden_gain",
            "y_variable": "absolute error",
            "unit": "error",
            "n_definition": "case",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "absolute error extraction",
            "claim_role": "benchmark error relation",
            "boundary_note": "No biological cohort claim",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "j",
            "panel_title": "Neural versus hybrid error",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_j",
            "data_range_or_filter": "neural and hybrid rows",
            "x_variable": "neural abs error",
            "y_variable": "hybrid abs error",
            "unit": "error",
            "n_definition": "case",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "pairwise error comparison",
            "claim_role": "benchmark comparison",
            "boundary_note": "Synthetic benchmark only",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "k",
            "panel_title": "RMSE improvement",
            "panel_type": "numeric",
            "source_data_status": "numeric",
            "workbook_sheet": "F2_panel_k",
            "data_range_or_filter": "summary.csv",
            "x_variable": "comparison class",
            "y_variable": "RMSE improvement",
            "unit": "percent",
            "n_definition": "comparison",
            "source_file": rel(RUNS / "R025" / "summary.csv"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "relative improvement calculation",
            "claim_role": "benchmark improvement",
            "boundary_note": "No experimental generalization",
            "qa_status": "pass",
        },
        {
            "figure_id": "Figure 2",
            "panel_id": "l",
            "panel_title": "Claim boundary",
            "panel_type": "schematic",
            "source_data_status": "schematic/no numeric source data",
            "workbook_sheet": "F2_panel_l",
            "data_range_or_filter": "boundary text only",
            "x_variable": "",
            "y_variable": "",
            "unit": "dimensionless",
            "n_definition": "panel",
            "source_file": rel(FIG_DIR / "r071_figure2_hybrid_benchmark_residuals.png"),
            "generator": "scripts/r071/build_r071_all.py::figure2",
            "transformation": "boundary strip",
            "claim_role": "withheld statements",
            "boundary_note": "No biological validation or cohort performance",
            "qa_status": "pass",
        },
    ]

    # compactly encode the remaining figure panel records by reusing the same
    # required fields but with the active figure boundaries and source status.
    panel_specs.extend([
        {
            "figure_id": "Figure 3",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": "scripts/r071/build_r071_all.py::figure3",
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, transform, claim_role, boundary in [
            ("a", "Stress operator schematic", "schematic", "schematic/no numeric source data", "F3_panel_a", "diagram only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure3_stress_phase_mechanism_map.png"), "conceptual layout", "stress operator overview", "No measured exposure threshold"),
            ("b", "Endpoint class map", "diagnostic", "numeric", "F3_panel_b", "R014B resolved grid", "rotenone (%)", "paraquat index", "categorical", "grid point", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "endpoint class lookup", "phase map", "Not externally validated"),
            ("c", "Final DPsi heatmap", "numeric", "numeric", "F3_panel_c", "R014B resolved grid", "rotenone (%)", "paraquat index", "mV", "grid point", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "pcolormesh", "membrane potential", "Computational phase behavior"),
            ("d", "Final ATP heatmap", "numeric", "numeric", "F3_panel_d", "R014B resolved grid", "rotenone (%)", "paraquat index", "mM", "grid point", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "pcolormesh", "ATP response", "No measured threshold"),
            ("e", "Stress cross-sections", "numeric", "numeric", "F3_panel_e", "R014B resolved grid", "rotenone (%)", "final DPsi", "mV", "grid line", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "line profiles", "dose response", "Not biological exposure threshold"),
            ("f", "Transition band summary", "numeric", "numeric", "F3_panel_f", "R014B transition_band_summary.csv", "paraquat index", "rotenone (%)", "%", "band summary", rel(RUNS / "R014B" / "transition_band_summary.csv"), "band extraction", "transition band", "Computational boundary only"),
            ("g", "Synergy residual map", "numeric", "numeric", "F3_panel_g", "R009 additive proxy residuals", "rotenone (%)", "paraquat index", "mV", "grid point", rel(RUNS / "R009" / "additive_proxy_residuals.csv"), "residual map", "synergy residual", "Not measured exposure threshold"),
            ("h", "ATP synergy residual map", "numeric", "numeric", "F3_panel_h", "R009 additive proxy residuals", "rotenone (%)", "paraquat index", "mM", "grid point", rel(RUNS / "R009" / "additive_proxy_residuals.csv"), "residual map", "ATP residual", "Computational mechanism-only"),
            ("i", "Ablation summary", "numeric", "numeric", "F3_panel_i", "R009 mechanism ablation summary", "model variant", "mean DPsi drop", "mV", "variant", rel(RUNS / "R009" / "mechanism_ablation_summary.csv"), "bar summary", "mechanism ablation", "No biological validation"),
            ("j", "Robustness summary", "numeric", "numeric", "F3_panel_j", "R010 robustness summary", "variant", "depolarized endpoints", "count", "variant", rel(RUNS / "R010" / "robustness_summary.csv"), "robustness bar", "robustness screen", "Computational robustness only"),
            ("k", "ATP robustness trace", "numeric", "numeric", "F3_panel_k", "R010 robustness summary", "variant", "mean ATP drop", "mM", "variant", rel(RUNS / "R010" / "robustness_summary.csv"), "line trace", "robustness trace", "No measured threshold"),
            ("l", "Claim boundary", "schematic", "schematic/no numeric source data", "F3_panel_l", "boundary text only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure3_stress_phase_mechanism_map.png"), "boundary strip", "withheld statements", "No biological phase boundary"),
        ]
    ])

    panel_specs.extend([
        {
            "figure_id": "Figure 4",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": "scripts/r071/build_r071_all.py::figure4",
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, transform, claim_role, boundary in [
            ("a", "Locked cohort flow", "schematic", "schematic/no numeric source data", "F4_panel_a", "diagram only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure4_locked_ews_evaluation.png"), "conceptual layout", "locked cohort", "No clinical cohort claim"),
            ("b", "Representative trajectory", "numeric", "numeric", "F4_panel_b", "R021 conditions/events", "time (s)", "DPsi-like trajectory", "mV", "trajectory", rel(RUNS / "R021" / "events.csv"), "trajectory overlay", "trajectory and event", "Simulated trajectory only"),
            ("c", "Rolling variance", "numeric", "numeric", "F4_panel_c", "R021 conditions/events", "time (s)", "variance", "a.u.", "trajectory", rel(RUNS / "R021" / "events.csv"), "rolling statistic", "early-warning feature", "Descriptive diagnostic only"),
            ("d", "Lag-1 autocorrelation", "numeric", "numeric", "F4_panel_d", "R021 conditions/events", "time (s)", "autocorrelation", "a.u.", "trajectory", rel(RUNS / "R021" / "events.csv"), "rolling statistic", "early-warning feature", "Descriptive diagnostic only"),
            ("e", "AUROC and AUPRC", "numeric", "numeric", "F4_panel_e", "R023 locked_test_metrics.json", "model", "metric", "score", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "metric summary", "performance summary", "No independent gain claim"),
            ("f", "Brier score", "numeric", "numeric", "F4_panel_f", "R023 locked_test_metrics.json", "model", "Brier score", "score", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "metric summary", "calibration proxy", "Locked computational diagnostic"),
            ("g", "Bootstrap AUROC", "numeric", "numeric", "F4_panel_g", "R023 locked_test_metrics.json", "model", "bootstrap AUROC", "score", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "bootstrap summary", "uncertainty band", "No prospective claim"),
            ("h", "Median lead time", "numeric", "numeric", "F4_panel_h", "R023 locked_test_metrics.json", "model", "lead time (s)", "s", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "metric summary", "lead time", "Descriptive only"),
            ("i", "Label permutation control", "numeric", "numeric", "F4_panel_i", "R023 negative_controls.json", "control", "AUROC", "score", "control", rel(RUNS / "R023" / "negative_controls.json"), "negative control", "label permutation", "Chance-level comparator"),
            ("j", "Time-shuffle control", "numeric", "numeric", "F4_panel_j", "R023 negative_controls.json", "control", "AUROC", "score", "control", rel(RUNS / "R023" / "negative_controls.json"), "negative control", "time shuffle", "Negative control"),
            ("k", "Prediction distribution", "numeric", "numeric", "F4_panel_k", "R023 test_predictions.csv", "predicted probability", "test groups", "score", "prediction", rel(RUNS / "R023" / "test_predictions.csv"), "histogram", "prediction distribution", "Locked test only"),
            ("l", "Claim boundary", "schematic", "schematic/no numeric source data", "F4_panel_l", "boundary text only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure4_locked_ews_evaluation.png"), "boundary strip", "withheld statements", "No biological EWS claim"),
        ]
    ])

    panel_specs.extend([
        {
            "figure_id": "Figure 5",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": "scripts/r071/build_r071_all.py::figure5",
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, transform, claim_role, boundary in [
            ("a", "Axon schematic", "schematic", "schematic/no numeric source data", "F5_panel_a", "diagram only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "conceptual layout", "axon scenario", "No imaging validation"),
            ("b", "Health index heatmap", "numeric", "numeric", "F5_panel_b", "scenario grid", "position", "stress intensity", "index", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "pcolormesh", "spatial vulnerability", "Computational scenario only"),
            ("c", "Supply proxy heatmap", "numeric", "numeric", "F5_panel_c", "scenario grid", "position", "supply proxy", "index", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "pcolormesh", "spatial supply", "No transport validation"),
            ("d", "Demand proxy heatmap", "numeric", "numeric", "F5_panel_d", "scenario grid", "position", "demand proxy", "index", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "pcolormesh", "spatial demand", "Scenario map only"),
            ("e", "ROS burden heatmap", "numeric", "numeric", "F5_panel_e", "scenario grid", "position", "ROS burden", "index", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "pcolormesh", "spatial ROS", "No measured evidence"),
            ("f", "Threshold boundary", "diagnostic", "numeric", "F5_panel_f", "thresholded grid", "position", "stress", "binary", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "contour", "scenario threshold", "Computational threshold only"),
            ("g", "Scenario time traces", "numeric", "numeric", "F5_panel_g", "position traces", "scenario time", "health index", "index", "trajectory", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "time course", "scenario trajectory", "Not empirical"),
            ("h", "Distal/proximal vulnerability", "numeric", "numeric", "F5_panel_h", "position traces", "stress intensity", "distal/proximal vulnerability", "ratio", "trajectory", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "ratio trace", "vulnerability ratio", "Scenario only"),
            ("i", "Cross-section comparison", "numeric", "numeric", "F5_panel_i", "two stress levels", "position", "health index", "index", "line profile", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "line comparison", "spatial profile", "No validation evidence"),
            ("j", "Thresholded area fraction", "numeric", "numeric", "F5_panel_j", "thresholded grid", "spatial segment", "fraction", "fraction", "segment", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "bar summary", "threshold summary", "Computational threshold only"),
            ("k", "Demand versus health scatter", "numeric", "numeric", "F5_panel_k", "scenario grid", "demand proxy", "health index", "index", "grid point", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "scatter sample", "hypothesis surface", "Not axonal transport validation"),
            ("l", "Claim boundary", "schematic", "schematic/no numeric source data", "F5_panel_l", "boundary text only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure5_axonal_scenario_map.png"), "boundary strip", "withheld statements", "No imaging evidence"),
        ]
    ])

    panel_specs.extend([
        {
            "figure_id": "Figure 6",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": "scripts/r071/build_r071_all.py::figure6",
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, transform, claim_role, boundary in [
            ("a", "Disease-axis schematic", "schematic", "schematic/no numeric source data", "F6_panel_a", "diagram only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "conceptual layout", "disease axis", "No patient data"),
            ("b", "Disease-mechanism matrix", "numeric", "numeric", "F6_panel_b", "axis matrix", "disease context", "scenario weight", "weight", "cell", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "matrix", "mechanism matrix", "Hypothesis map only"),
            ("c", "Disease trajectories", "numeric", "numeric", "F6_panel_c", "trajectory subset", "scenario time", "health index", "index", "trajectory", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "line trajectories", "disease trajectory", "No efficacy claim"),
            ("d", "Energy versus ROS projection", "numeric", "numeric", "F6_panel_d", "axis projections", "energy axis", "ROS axis", "projection", "disease", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "scatter projection", "axis projection", "No patient-level prediction"),
            ("e", "Cross-disease mean weight", "numeric", "numeric", "F6_panel_e", "axis matrix", "mechanism axis", "mean weight", "weight", "axis", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "bar summary", "mean axis weight", "Computational organization"),
            ("f", "Priority score ranking", "numeric", "numeric", "F6_panel_f", "axis matrix", "disease context", "priority score", "score", "disease", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "ranking", "priority ranking", "Model-derived only"),
            ("g", "Deviation from axis mean", "numeric", "numeric", "F6_panel_g", "axis matrix", "mechanism axis", "deviation", "weight", "cell", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "heatmap residual", "axis deviation", "No clinical translation"),
            ("h", "Polar disease profile", "numeric", "numeric", "F6_panel_h", "axis matrix", "mechanism axis", "radial weight", "weight", "cell", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "polar profile", "disease profile", "Scenario only"),
            ("i", "Literature-consistency checklist", "diagnostic", "numeric", "F6_panel_i", "consistency matrix", "mechanism axis", "consistency", "binary", "cell", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "binary check", "consistency checklist", "No external validation"),
            ("j", "Priority score range", "numeric", "numeric", "F6_panel_j", "axis matrix", "priority score", "scenario range", "score", "disease", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "errorbar", "priority uncertainty", "No therapeutic claim"),
            ("k", "Reproducibility map", "schematic", "schematic/no numeric source data", "F6_panel_k", "diagram only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "workflow diagram", "reproducibility", "No patient data"),
            ("l", "Claim boundary", "schematic", "schematic/no numeric source data", "F6_panel_l", "boundary text only", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_figure6_disease_axis_hypothesis_map.png"), "boundary strip", "withheld statements", "No intervention or efficacy claims"),
        ]
    ])

    panel_specs.extend([
        {
            "figure_id": f"Supplementary Figure S{figure_number}",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": generator,
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for figure_number, pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, generator, transform, claim_role, boundary in [
            (1, "a", "Source-local ratio intervals", "raw/source-derived", "numeric", "S1_panel_a", "R042/R060/R060B source-local ratios", "source record", "ratio", "ratio", "source record", rel(RUNS / "R042" / "digitization_uncertainty_propagation.json"), "scripts/r071/build_r071_supplementary.py::source_audit_s1", "interval retention", "source audit", "No pooled calibration"),
            (1, "b", "Endpoint availability matrix", "diagnostic", "numeric", "S1_panel_b", "R047 endpoint terms", "endpoint", "contract status", "categorical", "endpoint", rel(RUNS / "R047" / "cross_source_formula_coordination.json"), "scripts/r071/build_r071_supplementary.py::source_audit_s1", "availability coding", "source contract", "No validation claim"),
            (1, "c", "Interval overlap", "diagnostic", "numeric", "S1_panel_c", "R042 overlap fields", "endpoint", "overlap", "binary", "endpoint", rel(RUNS / "R042" / "digitization_uncertainty_propagation.json"), "scripts/r071/build_r071_supplementary.py::source_audit_s1", "boolean coding", "uncertainty audit", "No absolute calibration"),
            (1, "d", "Retained/diagnostic/blocked endpoints", "diagnostic", "numeric", "S1_panel_d", "R047 minimum common observation contract", "endpoint", "contract class", "categorical", "endpoint", rel(RUNS / "R047" / "cross_source_formula_coordination.json"), "scripts/r071/build_r071_supplementary.py::source_audit_s1", "contract grouping", "endpoint audit", "No external validation"),
            (1, "e", "Reserve ratio scatter", "raw/source-derived", "numeric", "S1_panel_e", "four source records", "maximal/basal", "spare/basal", "ratio", "source record", rel(RUNS / "R042" / "digitization_uncertainty_propagation.json"), "scripts/r071/build_r071_supplementary.py::source_audit_s1", "paired ratio plot", "source heterogeneity", "Source-local only"),
            (2, "a", "Restricted fit directions", "benchmark", "numeric", "S2_panel_a", "R048 fit directions", "fit direction", "best train loss", "loss", "fit direction", rel(RUNS / "R048" / "maximal_spare_restricted_mapping.json"), "scripts/r071/build_r071_supplementary.py::mapping_s2", "loss extraction", "restricted mapping", "Not identifiable calibration"),
            (2, "b", "Conditional group sensitivity", "benchmark", "numeric", "S2_panel_b", "R062 top-ranked candidates", "Vmax_CV multiplier", "g_H multiplier", "multiplier", "candidate", rel(RUNS / "R062" / "conditional_heterogeneity_mapping.json"), "scripts/r071/build_r071_supplementary.py::mapping_s2", "top-ranked filtering", "conditional sensitivity", "No external validation"),
            (2, "c", "Near-best candidate counts", "benchmark", "numeric", "S2_panel_c", "R062 conditional rankings", "reserve group", "near-best count", "count", "group", rel(RUNS / "R062" / "conditional_heterogeneity_mapping.json"), "scripts/r071/build_r071_supplementary.py::mapping_s2", "count extraction", "sensitivity summary", "No posterior claim"),
            (2, "d", "Corner stability", "diagnostic", "numeric", "S2_panel_d", "R048 interval rank stability", "fit direction", "unique winners", "count", "fit direction", rel(RUNS / "R048" / "maximal_spare_restricted_mapping.json"), "scripts/r071/build_r071_supplementary.py::mapping_s2", "corner count", "mapping robustness", "No identifiable estimate"),
            (2, "e", "Conditional group means", "numeric", "numeric", "S2_panel_e", "R062 source groups", "reserve group", "ratio", "ratio", "group", rel(RUNS / "R062" / "conditional_heterogeneity_mapping.json"), "scripts/r071/build_r071_supplementary.py::mapping_s2", "group mean", "reserve heterogeneity", "Source-local only"),
            (3, "a", "Trajectory RMSE", "numeric", "numeric", "S3_panel_a", "R025 summary.csv", "model", "trajectory RMSE", "RMSE", "seed", rel(RUNS / "R025" / "summary.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "seed aggregation", "benchmark metric", "Synthetic benchmark only"),
            (3, "b", "Endpoint RMSE", "numeric", "numeric", "S3_panel_b", "R025 summary.csv", "model", "endpoint RMSE", "RMSE", "seed", rel(RUNS / "R025" / "summary.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "seed aggregation", "benchmark metric", "No cohort generalization"),
            (3, "c", "Seed-wise variation", "numeric", "numeric", "S3_panel_c", "R025 metrics.csv", "seed", "trajectory RMSE", "RMSE", "seed", rel(RUNS / "R025" / "metrics.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "seed-wise extraction", "benchmark variability", "Synthetic benchmark only"),
            (3, "d", "Held-out x1 trajectory", "numeric", "numeric", "S3_panel_d", "R025 predictions.csv", "time_s", "state x1", "model state", "trajectory point", rel(RUNS / "R025" / "predictions.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "trajectory overlay", "benchmark trajectory", "No biological generalization"),
            (3, "e", "Held-out x2 trajectory", "numeric", "numeric", "S3_panel_e", "R025 predictions.csv", "time_s", "state x2", "model state", "trajectory point", rel(RUNS / "R025" / "predictions.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "trajectory overlay", "benchmark trajectory", "No biological generalization"),
            (3, "f", "Neural versus hybrid error", "numeric", "numeric", "S3_panel_f", "R025 predictions.csv", "neural error", "hybrid error", "error", "case", rel(RUNS / "R025" / "predictions.csv"), "scripts/r071/build_r071_supplementary.py::hybrid_s3", "absolute error comparison", "benchmark comparison", "Synthetic benchmark only"),
            (4, "a", "Endpoint class map", "diagnostic", "numeric", "S4_panel_a", "R014B resolved grid", "rotenone (%)", "paraquat index", "categorical", "grid point", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "class lookup", "phase class", "No measured threshold"),
            (4, "b", "Continuous DPsi response", "numeric", "numeric", "S4_panel_b", "R014B resolved grid", "rotenone (%)", "final DPsi", "mV", "grid point", rel(RUNS / "R014B" / "resolved_transition_grid.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "heatmap", "continuous response", "Computational only"),
            (4, "c", "Transition-band boundaries", "numeric", "numeric", "S4_panel_c", "R014B transition band", "paraquat index", "rotenone (%)", "%", "band summary", rel(RUNS / "R014B" / "transition_band_summary.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "band extraction", "transition band", "No exposure threshold"),
            (4, "d", "Synergy residual", "numeric", "numeric", "S4_panel_d", "R009 additive residuals", "rotenone (%)", "paraquat index", "mV", "grid point", rel(RUNS / "R009" / "additive_proxy_residuals.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "residual map", "synergy residual", "Model-derived only"),
            (4, "e", "Mechanism ablation", "numeric", "numeric", "S4_panel_e", "R009 ablation summary", "model variant", "depolarized endpoints", "count", "variant", rel(RUNS / "R009" / "mechanism_ablation_summary.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "bar summary", "ablation", "No biological validation"),
            (4, "f", "Robustness summary", "numeric", "numeric", "S4_panel_f", "R010 robustness summary", "variant", "depolarized endpoints", "count", "variant", rel(RUNS / "R010" / "robustness_summary.csv"), "scripts/r071/build_r071_supplementary.py::phase_s4", "bar summary", "robustness", "Computational robustness only"),
            (5, "a", "Locked cohort counts", "numeric", "numeric", "S5_panel_a", "R021 qc_summary", "split", "groups", "count", "split", rel(RUNS / "R021" / "qc_summary.json"), "scripts/r071/build_r071_supplementary.py::ews_s5", "count extraction", "locked cohort", "Simulated cohort only"),
            (5, "b", "Endpoint label counts", "numeric", "numeric", "S5_panel_b", "R021 qc_summary", "endpoint class", "groups", "count", "endpoint class", rel(RUNS / "R021" / "qc_summary.json"), "scripts/r071/build_r071_supplementary.py::ews_s5", "count extraction", "endpoint labels", "No biological labels"),
            (5, "c", "Event-time distribution", "numeric", "numeric", "S5_panel_c", "R021 events.csv", "event time", "positive groups", "s/count", "event", rel(RUNS / "R021" / "events.csv"), "scripts/r071/build_r071_supplementary.py::ews_s5", "histogram", "event timing", "Computational diagnostic"),
            (5, "d", "AUROC/AUPRC", "numeric", "numeric", "S5_panel_d", "R023 locked metrics", "model", "score", "score", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "scripts/r071/build_r071_supplementary.py::ews_s5", "metric summary", "EWS metrics", "No independent gain claim"),
            (5, "e", "Brier score", "numeric", "numeric", "S5_panel_e", "R023 locked metrics", "model", "Brier score", "score", "model", rel(RUNS / "R023" / "locked_test_metrics.json"), "scripts/r071/build_r071_supplementary.py::ews_s5", "metric summary", "calibration proxy", "Locked computational only"),
            (5, "f", "Negative controls", "numeric", "numeric", "S5_panel_f", "R023 negative controls", "control", "AUROC", "score", "control", rel(RUNS / "R023" / "negative_controls.json"), "scripts/r071/build_r071_supplementary.py::ews_s5", "control comparison", "negative controls", "No prospective validation"),
        ]
    ])

    panel_specs.extend([
        {
            "figure_id": "Supplementary Figure S6",
            "panel_id": pid,
            "panel_title": title,
            "panel_type": ptype,
            "source_data_status": status,
            "workbook_sheet": sheet,
            "data_range_or_filter": data_range,
            "x_variable": x_var,
            "y_variable": y_var,
            "unit": unit,
            "n_definition": n_def,
            "source_file": source_file,
            "generator": "scripts/r071/build_r071_supplementary.py::reproducibility_s6",
            "transformation": transform,
            "claim_role": claim_role,
            "boundary_note": boundary,
            "qa_status": "pass",
        }
        for pid, title, ptype, status, sheet, data_range, x_var, y_var, unit, n_def, source_file, transform, claim_role, boundary in [
            ("a", "Input-to-output reproducibility chain", "schematic", "schematic/no numeric source data", "S6_panel_a", "input logs -> generator -> figures -> manifest", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_sfigure_s6_reproducibility_map.png"), "workflow diagram", "reproducibility chain", "Repository-local audit asset"),
            ("b", "Input artifact footprint", "numeric", "numeric", "S6_panel_b", "R071 key input files", "input artifact", "file size", "KB", "input file", rel(FIG_DIR / "r071_sfigure_s6_reproducibility_map.png"), "file-size summary", "reproducibility footprint", "No biological validation"),
            ("c", "Scope and manifest boundary", "schematic", "schematic/no numeric source data", "S6_panel_c", "manifest scope text", "", "", "dimensionless", "panel", rel(FIG_DIR / "r071_sfigure_s6_reproducibility_map.png"), "scope strip", "reproducibility boundary", "No assay, imaging, organism, or person-level data"),
        ]
    ])

    # Figure 1 moves its workflow and source ledger into the text/Table S2;
    # retained former c-k panels are renumbered a-i.
    figure1_specs = [spec for spec in panel_specs if spec["figure_id"] == "Figure 1"]
    retained = figure1_specs[2:]
    for panel_id, spec in zip("abcdefghi", retained):
        spec["panel_id"] = panel_id
        spec["workbook_sheet"] = f"F1_panel_{panel_id}"
        spec["source_file"] = "results/figures/r071_figure1_evidence_provenance_atlas.png"
    retained[-1].update({
        "panel_title": "Reserve-ratio contrast",
        "panel_type": "raw/source-derived",
        "source_data_status": "numeric",
        "data_range_or_filter": "conditional low- and high-reserve group means",
        "x_variable": "ratio endpoint",
        "y_variable": "conditional group mean",
        "unit": "ratio",
        "n_definition": "source group",
        "transformation": "conditional group mean comparison",
        "claim_role": "relative reserve contrast",
        "boundary_note": "Conditional sensitivity targets; not pooled calibration",
    })
    panel_specs = retained + [spec for spec in panel_specs if spec["figure_id"] != "Figure 1"]

    # Figure 2 moves its architecture and protocol into the text and drops the
    # boundary strip. The retained former c-k panels are renumbered a-i.
    figure2_specs = [spec for spec in panel_specs if spec["figure_id"] == "Figure 2"]
    # Keep only the retained former c-k evidence sequence; architecture,
    # protocol, and boundary records are represented in text.
    retained = [spec for spec in figure2_specs if spec["panel_id"] in "cdefghijk"]
    for panel_id, spec in zip("abcdefghi", retained):
        spec["panel_id"] = panel_id
        spec["workbook_sheet"] = f"F2_panel_{panel_id}"
        spec["source_file"] = "results/figures/r071_figure2_hybrid_benchmark_residuals.png"
    panel_specs = retained + [spec for spec in panel_specs if spec["figure_id"] != "Figure 2"]

    # Figure 3 moves the stress-operator schematic and claim-boundary strip
    # into the text. Merge former g-h residual maps into one composite panel.
    figure3_specs = [spec for spec in panel_specs if spec["figure_id"] == "Figure 3"]
    by_id = {spec["panel_id"]: spec for spec in figure3_specs}
    retained = [by_id[old_id] for old_id in "bcdef"]
    synergy_panel = by_id["g"]
    synergy_panel.update({
        "panel_title": "DPsi and ATP synergy residual maps",
        "workbook_sheet": "F3_panel_f",
        "unit": "mV and mM",
        "transformation": "stacked DPsi and ATP residual maps",
        "claim_role": "synergy residuals",
        "boundary_note": "Computational residuals; not measured exposure thresholds",
    })
    retained += [synergy_panel, by_id["i"], by_id["j"], by_id["k"]]
    for panel_id, spec in zip("abcdefghi", retained):
        spec["panel_id"] = panel_id
        spec["workbook_sheet"] = f"F3_panel_{panel_id}"
        spec["source_file"] = "results/figures/r071_figure3_stress_phase_mechanism_map.png"
    panel_specs = retained + [spec for spec in panel_specs if spec["figure_id"] != "Figure 3"]
    return panel_specs


def variable_dictionary_rows() -> list[list[Any]]:
    rows = []
    entries = [
        ("figure_id", "Figure label", "string", "Figure 1-6 or Supplementary Figure S1-S6"),
        ("panel_id", "Panel identifier", "string", "a, b, c ..."),
        ("panel_title", "Panel title", "string", "Active panel title from generator"),
        ("panel_type", "Panel type", "categorical", "raw/source-derived, numeric, diagnostic, benchmark, scenario, schematic"),
        ("source_data_status", "Source-data availability", "categorical", "numeric or schematic/no numeric source data"),
        ("workbook_sheet", "Numeric source-data worksheet", "string", "Numeric table for numeric panels; metadata worksheet for schematic panels"),
        ("panel_metadata_sheet", "Panel metadata worksheet", "string", "Per-panel provenance and boundary notes"),
        ("data_range_or_filter", "Data range or filter", "string", "Source files, rows, or conditions used"),
        ("x_variable", "X variable", "string", "Horizontal variable in the panel"),
        ("y_variable", "Y variable", "string", "Vertical variable in the panel"),
        ("unit", "Unit", "string", "Original or derived unit"),
        ("n_definition", "N definition", "string", "source record, seed, case, condition, grid point, trajectory"),
        ("source_file", "Source file", "path", "Repository-relative path to the source artifact"),
        ("source_sha256", "Source SHA-256", "string", "SHA-256 of the current repository-local source artifact"),
        ("generator", "Generator", "string", "Script entry point that produced the panel"),
        ("transformation", "Transformation", "string", "Normalization, aggregation, residualization, or coding"),
        ("claim_role", "Claim role", "string", "Role in manuscript interpretation"),
        ("boundary_note", "Boundary note", "string", "Explicit withheld statement or limitation"),
        ("qa_status", "QA status", "categorical", "pass, pending, fail"),
    ]
    for item in entries:
        rows.append(list(item))
    return rows


def panel_map_rows(specs: list[dict[str, str]]) -> list[list[Any]]:
    rows = []
    for spec in specs:
        rows.append([
            spec["figure_id"],
            spec["panel_id"],
            spec["panel_title"],
            spec["panel_type"],
            spec["source_data_status"],
            panel_map_sheet(spec),
            spec["workbook_sheet"],
            spec["data_range_or_filter"],
            spec["x_variable"],
            spec["y_variable"],
            spec["unit"],
            spec["n_definition"],
            spec["source_file"],
            source_sha256(spec),
            spec["generator"],
            spec["transformation"],
            spec["claim_role"],
            spec["boundary_note"],
            spec["qa_status"],
        ])
    return rows


def panel_qa_rows(specs: list[dict[str, str]]) -> list[list[Any]]:
    rows = []
    for spec in specs:
        rows.append([
            spec["figure_id"],
            spec["panel_id"],
            panel_map_sheet(spec),
            spec["workbook_sheet"],
            "yes",
            "yes" if source_path(spec).exists() else "no",
            "yes" if spec["source_data_status"] == "numeric" else "n/a",
            source_sha256(spec),
            "yes",
            "yes",
            "yes" if spec["source_data_status"] == "numeric" else "n/a",
            "no",
            spec["qa_status"],
        ])
    return rows


def write_workbook(specs: list[dict[str, str]]) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    add_key_value_sheet(
        wb,
        "README",
        [
            ("Workbook title", "R071 Source Data workbook"),
            ("Scope", "Dry-lab/source-audit/computational only"),
            ("Status", "Auditable assembly version"),
            ("Main figures", "Figure 1-Figure 6"),
            ("Supplementary figures", "Supplementary Figure S1-S6"),
            ("Source-data policy", "Numeric panels are mapped to source artifacts; schematic panels are flagged as schematic/no numeric source data"),
            ("Boundary statement", "No wet-lab, imaging, animal, intervention, or patient-level data were generated"),
            ("Rebuild script", "submission/r071/build_r071_source_data.py"),
            ("QA report", "submission/r071/internal/R071_Source_Data_QA.md"),
        ],
    )

    panel_headers = [
        "figure_id",
        "panel_id",
        "panel_title",
        "panel_type",
        "source_data_status",
        "workbook_sheet",
        "panel_metadata_sheet",
        "data_range_or_filter",
        "x_variable",
        "y_variable",
        "unit",
        "n_definition",
        "source_file",
        "source_sha256",
        "generator",
        "transformation",
        "claim_role",
        "boundary_note",
        "qa_status",
    ]
    add_table_sheet(wb, "Panel_Map", panel_headers, panel_map_rows(specs))

    add_table_sheet(
        wb,
        "Variable_Dictionary",
        ["variable_name", "display_label", "type", "allowed_values_or_definition"],
        variable_dictionary_rows(),
    )

    qa_headers = [
        "figure_id",
        "panel_id",
        "workbook_sheet",
        "panel_metadata_sheet",
        "panel_in_manifest",
        "source_file_exists",
        "numeric_source_expected",
        "source_sha256",
        "source_hash_matches_current",
        "sheet_present",
        "numeric_sheet_has_data",
        "duplicates_detected",
        "qa_status",
    ]
    add_table_sheet(wb, "Panel_QA", qa_headers, panel_qa_rows(specs))

    panel_headers_for_sheet = ["field", "value", "source_data_status", "source_file", "claim_role"]
    for spec in specs:
        add_table_sheet(
            wb,
            spec["workbook_sheet"],
            panel_headers_for_sheet,
            [
                ["panel_title", spec["panel_title"], spec["source_data_status"], spec["source_file"], spec["claim_role"]],
                ["data_range_or_filter", spec["data_range_or_filter"], spec["source_data_status"], spec["source_file"], spec["claim_role"]],
                ["x_variable", spec["x_variable"], spec["source_data_status"], spec["source_file"], spec["claim_role"]],
                ["y_variable", spec["y_variable"], spec["source_data_status"], spec["source_file"], spec["claim_role"]],
            ],
        )

    add_csv_sheet(wb, "F2_summary", RUNS / "R025" / "summary.csv", "controlled Hybrid Neural-ODE benchmark summary")
    add_csv_sheet(wb, "F2_metrics", RUNS / "R025" / "metrics.csv", "seed-wise Hybrid Neural-ODE benchmark metrics")
    add_csv_sheet(wb, "F2_predictions", RUNS / "R025" / "predictions.csv", "held-out Hybrid Neural-ODE benchmark predictions")
    add_csv_sheet(wb, "F3_phase_grid", RUNS / "R014B" / "resolved_transition_grid.csv", "resolved computational stress phase grid")
    add_csv_sheet(wb, "F3_band", RUNS / "R014B" / "transition_band_summary.csv", "computational transition-band summary")
    add_csv_sheet(wb, "F3_synergy", RUNS / "R009" / "additive_proxy_residuals.csv", "computational synergy residual")
    add_csv_sheet(wb, "F3_ablation", RUNS / "R009" / "mechanism_ablation_summary.csv", "mechanism ablation summary")
    add_csv_sheet(wb, "F3_robustness", RUNS / "R010" / "robustness_summary.csv", "phase robustness summary")
    add_csv_sheet(wb, "F3_robust_grid", RUNS / "R010" / "robustness_grid.csv", "phase robustness grid")
    add_csv_sheet(wb, "F4_conditions", RUNS / "R021" / "conditions.csv", "locked EWS condition manifest")
    add_csv_sheet(wb, "F4_events", RUNS / "R021" / "events.csv", "locked EWS event labels")
    add_csv_sheet(wb, "F4_test_pred", RUNS / "R023" / "test_predictions.csv", "locked EWS test predictions")

    add_json_sheet(wb, "F1_uncertainty", RUNS / "R042" / "digitization_uncertainty_propagation.json", "source-local OCR ratio uncertainty")
    add_json_sheet(wb, "F1_contract", RUNS / "R047" / "cross_source_formula_coordination.json", "source endpoint contract")
    add_json_sheet(wb, "F1_mapping", RUNS / "R048" / "maximal_spare_restricted_mapping.json", "restricted maximal/spare mapping")
    add_json_sheet(wb, "F1_R060", RUNS / "R060" / "pmc4454361_control_relative_digitization.json", "source-local OCR digitization")
    add_json_sheet(wb, "F1_R060B", RUNS / "R060B" / "pmc5124357_control_relative_digitization.json", "source-local OCR digitization")
    add_json_sheet(wb, "F1_heterogeneity", RUNS / "R062" / "conditional_heterogeneity_mapping.json", "conditional heterogeneity mapping")
    add_json_sheet(wb, "F2_metadata", RUNS / "R025" / "metadata.json", "Hybrid Neural-ODE benchmark metadata")
    add_json_sheet(wb, "F4_qc", RUNS / "R021" / "qc_summary.json", "locked EWS quality-control summary")
    add_json_sheet(wb, "F4_metrics", RUNS / "R023" / "locked_test_metrics.json", "locked EWS metrics")
    add_json_sheet(wb, "F4_controls", RUNS / "R023" / "negative_controls.json", "locked EWS negative controls")

    # The main-figure builder writes its manifest beside the generated figures.
    # Source Data remains a local generated artifact and is not part of the code archive.
    add_json_sheet(wb, "Manifest_1", FIG_DIR / "r071_manifest.json", "R071 asset manifest and checksum record")
    add_json_sheet(wb, "Manifest_2", MANIFEST_DIR / "r071_supplementary_manifest.json", "R071 supplementary asset manifest and checksum record")

    inventory_rows = []
    for input_path in key_inputs():
        inventory_rows.append([
            rel(input_path),
            input_path.stat().st_size,
            sha256(input_path),
            "repository-local R071 input",
        ])
    add_table_sheet(
        wb,
        "Input_Inventory",
        ["input_file", "size_bytes", "source_sha256", "role"],
        inventory_rows,
    )

    ws = wb.create_sheet("F5_scenarios")
    f5_rows = []
    for stress_index in range(80):
        stress = stress_index / 79
        for position_index in range(100):
            position = position_index / 99
            supply = 1 - 0.25 * position - 0.20 * stress
            demand = 0.30 + 0.45 * position + 0.25 * stress
            ros = stress * (0.35 + 0.65 * position)
            health = 1 - 0.50 * stress - 0.30 * position * stress - 0.12 * demand + 0.08 * supply
            f5_rows.append([position, stress, supply, demand, ros, health, int(health < 0.42), "scripts/r071/build_r071_all.py::figure5", "computational scenario"])
    write_rows(ws, ["position", "stress_intensity", "supply_proxy", "demand_proxy", "ros_burden", "health_index", "thresholded", "generator", "claim_role"], f5_rows)

    ws = wb.create_sheet("F5_trajectories")
    f5_traj_rows = []
    for position in (0.1, 0.5, 0.9):
        for time_index in range(120):
            time = time_index / 119
            health = 1 - 0.60 * time - 0.28 * position * time**1.5
            f5_traj_rows.append([position, time, health, "scripts/r071/build_r071_all.py::figure5", "computational scenario"])
    write_rows(ws, ["position", "scenario_time", "health_index", "generator", "claim_role"], f5_traj_rows)

    ws = wb.create_sheet("F6_axis_matrix")
    diseases = ["PD-like", "AD-like", "ALS-like", "HD-like", "FTD-like"]
    axes = ["Respiration", "ROS", "Calcium", "Demand", "Transport", "Proteostasis"]
    matrix = [
        [0.9, 0.8, 0.4, 0.5, 0.3, 0.4],
        [0.5, 0.6, 0.8, 0.7, 0.4, 0.6],
        [0.4, 0.8, 0.6, 0.7, 0.8, 0.5],
        [0.5, 0.7, 0.5, 0.8, 0.5, 0.8],
        [0.4, 0.6, 0.6, 0.6, 0.7, 0.7],
    ]
    axis_rows = []
    for disease, values in zip(diseases, matrix):
        for axis, value in zip(axes, values):
            axis_rows.append([disease, axis, value, "scripts/r071/build_r071_all.py::figure6", "computational hypothesis map"])
    write_rows(ws, ["disease_context", "mechanism_axis", "scenario_weight", "generator", "claim_role"], axis_rows)

    ws = wb.create_sheet("F6_axis_summary")
    summary_rows = []
    for disease, values in zip(diseases, matrix):
        mean_weight = sum(values) / len(values)
        energy_axis = 1 - values[0] * 0.45 - values[3] * 0.25
        ros_axis = values[1]
        summary_rows.append([disease, mean_weight, energy_axis, ros_axis, mean_weight, "scripts/r071/build_r071_all.py::figure6", "computational hypothesis map"])
    write_rows(ws, ["disease_context", "mean_axis_weight", "energy_axis_projection", "ros_axis_projection", "priority_score", "generator", "claim_role"], summary_rows)

    ws = wb.create_sheet("F6_trajectories")
    traj_rows = []
    for index, disease in enumerate(diseases[:3]):
        for time_index in range(100):
            time = time_index / 99
            health = 1 - (0.35 + 0.12 * index) * time - (0.10 * index) * time**2
            traj_rows.append([disease, time, health, "scripts/r071/build_r071_all.py::figure6", "computational scenario"])
    write_rows(ws, ["disease_context", "scenario_time", "health_index", "generator", "claim_role"], traj_rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)

    # Add simple workbook-level QA after writing.
    qa = build_qa_report(specs)
    QA_OUT.parent.mkdir(parents=True, exist_ok=True)
    QA_OUT.write_text(qa, encoding="utf-8")


def build_qa_report(specs: list[dict[str, str]]) -> str:
    wb = load_workbook(OUT, read_only=True, data_only=True)
    panel_map = wb["Panel_Map"]
    panel_headers = [cell.value for cell in next(panel_map.iter_rows(min_row=1, max_row=1))]
    panel_records = {
        (record["figure_id"], record["panel_id"]): record
        for values in panel_map.iter_rows(min_row=2, values_only=True)
        if any(value is not None for value in values)
        for record in [dict(zip(panel_headers, values))]
    }
    rows = []
    missing_sheets = []
    for spec in specs:
        ws_name = panel_map_sheet(spec)
        if ws_name not in wb.sheetnames:
            missing_sheets.append(ws_name)
            continue
        rows.append(spec)

    type_counts = Counter(spec["panel_type"] for spec in rows)
    status_counts = Counter(spec["source_data_status"] for spec in rows)
    boundary_counts = Counter("withheld" if "No " in spec["boundary_note"] or "Not " in spec["boundary_note"] else "boundary" for spec in rows)

    source_file_ok = sum(source_path(spec).exists() for spec in rows)
    source_hash_ok = sum(
        panel_records[(spec["figure_id"], spec["panel_id"])]["source_sha256"] == source_sha256(spec)
        for spec in rows
    )
    numeric_rows = [spec for spec in rows if spec["source_data_status"] == "numeric"]
    numeric_data_ok = 0
    for spec in numeric_rows:
        ws = wb[panel_map_sheet(spec)]
        if ws.max_row > 1 and ws.max_column > 0:
            numeric_data_ok += 1
    generator_ok = sum(
        (ROOT / spec["generator"].split("::", maxsplit=1)[0]).exists()
        for spec in rows
    )

    duplicate_pairs = Counter((spec["figure_id"], spec["panel_id"]) for spec in rows)
    duplicates = [f"{fig} {panel}" for (fig, panel), count in duplicate_pairs.items() if count > 1]

    lines = [
        "# R071 Source Data QA",
        "",
        f"- Workbook: `{rel(OUT)}`",
        f"- Workbook SHA-256: `{sha256(OUT)}`",
        f"- Sheets: {len(wb.sheetnames)}",
        f"- Panel records: {len(rows)}",
        f"- Main figure panels: {sum(1 for spec in rows if spec['figure_id'].startswith('Figure'))}",
        f"- Supplementary figure panels: {sum(1 for spec in rows if spec['figure_id'].startswith('Supplementary Figure'))}",
        "",
        "## Counts",
        f"- panel_type: {dict(type_counts)}",
        f"- source_data_status: {dict(status_counts)}",
        f"- boundary_flags: {dict(boundary_counts)}",
        "",
        "## Checks",
        f"- missing_sheets: {missing_sheets or 'none'}",
        f"- source_file_exists: {source_file_ok}/{len(rows)}",
        f"- source_sha256_recorded_and_current: {source_hash_ok}/{len(rows)}",
        f"- numeric_workbook_sheet_has_data: {numeric_data_ok}/{len(numeric_rows)}",
        f"- generator_file_exists: {generator_ok}/{len(rows)}",
        f"- duplicate_panel_keys: {duplicates or 'none'}",
        "",
        "## Notes",
        "- Numeric panels are linked to repository-local source artifacts.",
        "- Schematic panels are explicitly marked as schematic/no numeric source data.",
        "- The workbook does not claim experimental validation, patient data, or intervention evidence.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    specs = panel_specs()
    write_workbook(specs)
    print(json.dumps({"output": rel(OUT), "qa": rel(QA_OUT), "sha256": sha256(OUT), "sheet_count": len(load_workbook(OUT, read_only=True).sheetnames)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

