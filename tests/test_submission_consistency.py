"""Scientific consistency checks on frozen evidence and corrected asset outputs."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest
from openpyxl import load_workbook
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from analysis.submission_contract import (
    MAIN_TITLES, SUPP_TITLES, ews_configurations, reserve_observations, sha256,
)

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "inputs/audit_runs"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_checkpoint_inputs_unchanged():
    expected = json.loads((ROOT / "inputs/locked_audit_hashes.json").read_text())["files"]
    actual = {p.relative_to(ROOT).as_posix(): sha256(p) for p in RUNS.rglob("*") if p.is_file()}
    assert actual == expected
    assert len(actual) == 24


def test_distinct_scan_and_diagnostic_cohort():
    scan = read_csv(RUNS / "R014B/resolved_transition_grid.csv")
    cohort = read_csv(RUNS / "R021/conditions.csv")
    assert len(scan) == 91
    assert len({r["rotenone_inhibition"] for r in scan}) == 13
    assert len({r["paraquat_index"] for r in scan}) == 7
    assert sum(r["resolved_endpoint_class"] == "near_fixed_depolarized_endpoint" for r in scan) == 63
    assert len(cohort) == 441


def test_source_definitions_not_forcibly_harmonized():
    rows = {r["record"]: r for r in reserve_observations()}
    assert rows["R033"]["spare_to_basal"] == pytest.approx(rows["R033"]["maximal_to_basal"] - 1)
    assert rows["R039"]["spare_to_basal"] == pytest.approx(rows["R039"]["maximal_to_basal"] - 1)
    assert rows["R060"]["spare_to_basal"] == pytest.approx(1.0396)
    assert rows["R060"]["definition_difference"] == pytest.approx(0.1124)
    assert rows["R060B"]["definition_difference"] == pytest.approx(-0.006)


def test_configuration_eligibility_and_recomputed_metrics():
    configs, eligibility = ews_configurations()
    predictions = read_csv(RUNS / "R023/test_predictions.csv")
    expected = {"locked_baseline": (124, 73, 2), "best_ews": (113, 62, 13),
                "best_dpsi": (126, 75, 0), "best_slope": (113, 62, 13)}
    for config in configs:
        assert (config["n"], config["positive_count"], config["excluded_count"]) == expected[config["model"]]
        selected = [r for r in predictions if r["model"] == config["model"]]
        labels = [int(r["label"]) for r in selected]
        probabilities = [float(r["probability"]) for r in selected]
        assert roc_auc_score(labels, probabilities) == pytest.approx(config["auroc"], abs=1e-12)
        assert average_precision_score(labels, probabilities) == pytest.approx(config["auprc"], abs=1e-12)
        assert brier_score_loss(labels, probabilities) == pytest.approx(config["brier"], abs=1e-12)
    assert len(eligibility) == 4 * 126


def test_all_lettered_panels_and_source_paths_present():
    book = load_workbook(ROOT / "results/source_data/NeurMito_Source_Data.xlsx", read_only=True, data_only=False)
    sheet = book["Panel_Map"]
    values = list(sheet.values)
    mapping = [dict(zip(values[0], row)) for row in values[1:]]
    expected = {(f"Figure {i}", chr(97+j)) for i, titles in MAIN_TITLES.items() for j in range(len(titles))}
    expected |= {(f"Supplementary Figure S{i}", chr(97+j)) for i, titles in SUPP_TITLES.items() for j in range(len(titles))}
    assert len(expected) == 89
    assert {(r["figure_id"], r["panel_id"]) for r in mapping} == expected
    assert len(mapping) == len(expected)
    for row in mapping:
        for path, digest in zip(row["source_files"].split(";"), row["source_sha256"].split(";")):
            assert sha256(ROOT / path) == digest
        assert (ROOT / row["figure_file"]).is_file()
        for name in (row["data_sheets"] or "").split(";"):
            if name:
                assert name in book.sheetnames and book[name].max_row > 1
    s2d = next(r for r in mapping if r["figure_id"] == "Supplementary Figure S2" and r["panel_id"] == "d")
    assert s2d["data_sheets"] == "Restricted_Mapping"
    book.close()


def test_disease_projection_preserves_original_coordinates():
    projections = read_csv(ROOT / "results/submission_data/F6_Projections.csv")
    assert [float(r["ros_weight"]) for r in projections] == pytest.approx([.8, .6, .8, .7, .6])
    assert [float(r["plotted_ros_coordinate"]) for r in projections] == pytest.approx([.8, .68, .96, .94, .92])
    for i, row in enumerate(projections):
        assert float(row["plotted_ros_coordinate"]) == pytest.approx(float(row["ros_weight"]) + .08*i)


def test_illustration_is_distinguished_from_cohort():
    rows = read_csv(ROOT / "results/submission_data/F4_Illustration.csv")
    assert len(rows) == 185
    assert np.diff([float(r["time_s"]) for r in rows]) == pytest.approx(np.full(184, .5))
    assert all("illustration" in r["evidence_type"] for r in rows)
