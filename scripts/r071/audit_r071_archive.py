"""Audit the R071 code-only checkout before creating a public archive."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
import yaml


REQUIRED_AUDIT_INPUTS = (
    "R009/additive_proxy_residuals.csv",
    "R009/mechanism_ablation_summary.csv",
    "R009/final_dpsi_by_variant_matrix.csv",
    "R010/robustness_summary.csv",
    "R010/robustness_grid.csv",
    "R014B/resolved_transition_grid.csv",
    "R014B/transition_band_summary.csv",
    "R021/qc_summary.json",
    "R021/events.csv",
    "R021/conditions.csv",
    "R021/split_manifest.csv",
    "R023/locked_test_metrics.json",
    "R023/negative_controls.json",
    "R023/test_predictions.csv",
    "R025/summary.csv",
    "R025/metrics.csv",
    "R025/predictions.csv",
    "R025/metadata.json",
    "R042/digitization_uncertainty_propagation.json",
    "R047/cross_source_formula_coordination.json",
    "R048/maximal_spare_restricted_mapping.json",
    "R060/pmc4454361_control_relative_digitization.json",
    "R060B/pmc5124357_control_relative_digitization.json",
    "R062/conditional_heterogeneity_mapping.json",
)


def _tracked_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", "."],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def audit(root: Path) -> dict[str, object]:
    tracked = _tracked_files(root)
    missing_inputs = [
        path for path in REQUIRED_AUDIT_INPUTS
        if not (root / "inputs" / "audit_runs" / path).is_file()
    ]
    cff_text = (root / "CITATION.cff").read_text(encoding="utf-8") if (root / "CITATION.cff").is_file() else ""
    placeholders = [
        token for token in ("PLACEHOLDER", "AUTHOR_CONFIRMATION_REQUIRED", "XXXX", "TBD")
        if token.lower() in cff_text.lower()
    ]
    try:
        cff = yaml.safe_load(cff_text) or {}
        if not isinstance(cff, dict) or not cff.get("authors"):
            placeholders.append("Missing software authors; author confirmation required")
    except yaml.YAMLError:
        placeholders.append("Invalid CFF YAML; author confirmation required")
    legacy_scripts = sorted(
        path for path in tracked
        if path.startswith("scripts/publication_figures/supplementary/sfigure_s")
        and any(f"sfigure_s{number}_" in path for number in range(7, 21))
    )
    required_entry_points = [
        "scripts/r071/build_r071_all.py",
        "scripts/r071/build_r071_supplementary.py",
        "scripts/r071/build_r071_source_data.py",
        "analysis/reproduce_r071.py",
        "tests/test_r071_smoke.py",
        "LICENSE",
        "README.md",
        "CITATION.cff",
    ]
    missing_entry_points = [path for path in required_entry_points if not (root / path).is_file()]

    findings = [
        {
            "id": "D-02",
            "severity": "blocker" if missing_inputs else "pass",
            "message": "Locked audit-run inputs are incomplete." if missing_inputs else "All 24 locked audit-run inputs are present.",
            "details": missing_inputs,
        },
        {
            "id": "D-01-CFF",
            "severity": "blocker" if placeholders else "pass",
            "message": "CITATION.cff contains unresolved metadata placeholders." if placeholders else "CITATION.cff has no known placeholders.",
            "details": placeholders,
        },
        {
            "id": "D-01-ENTRYPOINTS",
            "severity": "blocker" if missing_entry_points else "pass",
            "message": "Required R071 archive files are missing." if missing_entry_points else "Required R071 archive files are present.",
            "details": missing_entry_points,
        },
        {
            "id": "D-01-LEGACY",
            "severity": "review" if legacy_scripts else "pass",
            "message": "Legacy supplementary S7-S20 scripts remain tracked; repository-owner disposition is required." if legacy_scripts else "Legacy supplementary S7-S20 scripts are absent from the candidate archive.",
            "details": legacy_scripts,
        },
    ]
    return {
        "root": str(root),
        "required_audit_input_count": len(REQUIRED_AUDIT_INPUTS),
        "tracked_file_count": len(tracked),
        "findings": findings,
        "blocker_count": sum(item["severity"] == "blocker" for item in findings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = audit(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for finding in report["findings"]:
            print(f"[{finding['severity'].upper()}] {finding['id']}: {finding['message']}")
            for detail in finding["details"]:
                print(f"  - {detail}")
    return 2 if report["blocker_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
