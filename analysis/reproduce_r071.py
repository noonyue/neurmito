"""Generate R071 assets locally; generated outputs are not distributed."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDERS = {
    "main": ROOT / "scripts" / "r071" / "build_r071_all.py",
    "supplementary": ROOT / "scripts" / "r071" / "build_r071_supplementary.py",
}
SOURCE_DATA_BUILDER = ROOT / "scripts" / "r071" / "build_submission_source_data.py"

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


def require_local_audit_inputs() -> None:
    audit_dir = ROOT / "inputs" / "audit_runs"
    missing = [name for name in REQUIRED_AUDIT_INPUTS if not (audit_dir / name).is_file()]
    if not missing:
        return
    raise SystemExit(
        "R071 full regeneration requires the locked audit-run inputs under "
        "inputs/audit_runs/. Missing files: " + ", ".join(missing) + ". "
        "Provide the complete approved input set before claiming a full rebuild."
    )

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["main", "supplementary", "all"], default="all")
    args = parser.parse_args()
    require_local_audit_inputs()
    subprocess.run([sys.executable, str(SOURCE_DATA_BUILDER)], cwd=ROOT, check=True)
    names = ("main", "supplementary") if args.only == "all" else (args.only,)
    for name in names:
        subprocess.run([sys.executable, str(BUILDERS[name])], cwd=ROOT, check=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
