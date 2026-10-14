"""R065 active claim-surface audit for figure/table deliverables.

This audit scans the active figure/table text surface after the R063/R064
Figure 1 update and the figure-table design deliverables. It is intentionally
claim-boundary focused: risky terms are allowed only when they appear in an
explicitly negated, blocked, withheld, unsupported, or boundary-setting context.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "refine-logs" / "runs" / "R065"
OUT_PATH = OUT_DIR / "active_claim_surface_audit.json"
REPORT_PATH = ROOT / "refine-logs" / "R065_ACTIVE_CLAIM_SURFACE_AUDIT.md"


TEXT_FILES = [
    "FIGURE_INDEX.md",
    "manuscript/figure_table_design/RESULT_FIGURE_TABLE_DELIVERABLES.md",
    "manuscript/figure_table_design/main_figure_includes.tex",
    "manuscript/figure_table_design/supplementary_figure_includes.tex",
    "manuscript/figure_table_design/table1_claim_boundary.tex",
    "manuscript/figure_table_design/table2_model_components.tex",
    "manuscript/figure_table_design/table3_source_local_ocr_records.tex",
    "manuscript/figure_table_design/table4_computational_diagnostics.tex",
    "scripts/publication_figures/main/figure1_neuron_comparison_verified.py",
    "scripts/publication_figures/main/figure2_hybrid_verified.py",
    "scripts/publication_figures/main/figure3_phase_synergy_verified.py",
    "scripts/publication_figures/main/figure4_ews_verified.py",
    "scripts/publication_figures/main/figure5_spatial_verified.py",
    "scripts/publication_figures/main/figure6_disease_verified.py",
]


REQUIRED_ASSETS = [
    "figures/figure1_neuron_comparison.png",
    "figures/figure1_neuron_comparison.pdf",
    "figures/figure2_hybrid_ml.png",
    "figures/figure2_hybrid_ml.pdf",
    "figures/figure3_phase_synergy.png",
    "figures/figure3_phase_synergy.pdf",
    "figures/figure4_ews_complete.png",
    "figures/figure4_ews_complete.pdf",
    "figures/figure5_spatial_heterogeneity.png",
    "figures/figure5_spatial_heterogeneity.pdf",
    "figures/figure6_disease_applications.png",
    "figures/figure6_disease_applications.pdf",
    "figures/audited_sfigure_s1_source_contract.png",
    "figures/audited_sfigure_s1_source_contract.pdf",
    "figures/audited_sfigure_s2_hybrid_benchmark.png",
    "figures/audited_sfigure_s2_hybrid_benchmark.pdf",
    "figures/audited_sfigure_s3_phase_robustness.png",
    "figures/audited_sfigure_s3_phase_robustness.pdf",
    "figures/audited_sfigure_s4_ews_locked_test.png",
    "figures/audited_sfigure_s4_ews_locked_test.pdf",
]


RISK_PATTERNS = {
    "absolute_calibration": [
        r"\babsolute\s+OCR\b",
        r"\babsolute\s+calibration\b",
        "绝对 OCR",
        "绝对校准",
    ],
    "mcmc_or_bayesian": [
        r"\bMCMC\b",
        r"\bBayesian\b",
        r"\bposterior\b",
        "贝叶斯",
        "后验",
    ],
    "external_validation": [
        r"\bexternal\s+validation\b",
        r"\bindependent\s+experimental\s+validation\b",
        "外部验证",
        "实验验证",
    ],
    "wet_lab": [
        r"\bwet[- ]lab\b",
        "湿实验",
    ],
    "clinical_or_intervention": [
        r"\bclinical\s+efficacy\b",
        r"\bpatient[- ]outcome\b",
        r"\bpatient\s+outcome\b",
        r"\btreatment\s+window",
        r"\bintervention\s+success\b",
        "临床",
        "疗效",
        "治疗窗口",
        "患者结局",
    ],
    "independent_ews_gain": [
        r"\bindependent\s+predictive[- ]gain\b",
        r"\bindependent\s+EWS\s+predictive\s+gain\b",
        r"\bEWS\s+independent\s+gain\b",
        "独立预测增益",
    ],
}


BOUNDARY_MARKERS = [
    "does not",
    "do not",
    "not ",
    "not as",
    "not an",
    "not a ",
    "cannot",
    "withheld",
    "withheld claim",
    "blocked",
    "unsupported",
    "inactive",
    "legacy",
    "closed",
    "boundary",
    "claim gate",
    "claim-boundary",
    "claim boundary",
    "no ",
    "without",
    "rather than",
    "不支持",
    "不构成",
    "不能",
    "未",
    "禁止",
    "关闭",
    "边界",
    "暂不",
    "不得",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(rel_path: str) -> Dict[str, object]:
    path = ROOT / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
    }


def iter_matches(text: str, patterns: Iterable[str]):
    for pattern in patterns:
        flags = re.IGNORECASE
        if any(ord(char) > 127 for char in pattern):
            flags = 0
        for match in re.finditer(pattern, text, flags=flags):
            yield pattern, match


def line_number_at(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def context_window(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return " ".join(text[left:right].split())


def is_boundary_context(context: str) -> bool:
    lowered = context.lower()
    return any(marker.lower() in lowered for marker in BOUNDARY_MARKERS)


def scan_file(rel_path: str) -> Dict[str, object]:
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8", errors="replace")
    boundary_hits: List[Dict[str, object]] = []
    unguarded_hits: List[Dict[str, object]] = []

    for category, patterns in RISK_PATTERNS.items():
        for pattern, match in iter_matches(text, patterns):
            context = context_window(text, match.start(), match.end())
            hit = {
                "path": rel_path,
                "line": line_number_at(text, match.start()),
                "category": category,
                "pattern": pattern,
                "match": match.group(0),
                "context": context,
            }
            if is_boundary_context(context):
                boundary_hits.append(hit)
            else:
                unguarded_hits.append(hit)

    return {
        "path": rel_path,
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "boundary_context_hits": boundary_hits,
        "unguarded_claim_hits": unguarded_hits,
    }


def load_json_if_exists(rel_path: str):
    path = ROOT / rel_path
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    missing_text_files = [rel for rel in TEXT_FILES if not (ROOT / rel).exists()]
    missing_assets = [rel for rel in REQUIRED_ASSETS if not (ROOT / rel).exists()]

    scanned = []
    boundary_hits: List[Dict[str, object]] = []
    unguarded_hits: List[Dict[str, object]] = []
    for rel_path in TEXT_FILES:
        if not (ROOT / rel_path).exists():
            continue
        record = scan_file(rel_path)
        boundary_hits.extend(record["boundary_context_hits"])
        unguarded_hits.extend(record["unguarded_claim_hits"])
        scanned.append(
            {
                "path": record["path"],
                "sha256": record["sha256"],
                "size_bytes": record["size_bytes"],
                "boundary_context_hit_count": len(record["boundary_context_hits"]),
                "unguarded_claim_hit_count": len(record["unguarded_claim_hits"]),
            }
        )

    r053 = load_json_if_exists("inputs/audit_runs/R053/active_asset_consistency_audit.json")
    r054 = load_json_if_exists("inputs/audit_runs/R054/active_asset_regeneration_manifest.json")
    r064 = load_json_if_exists("inputs/audit_runs/R064/regeneration_manifest_alignment.json")

    r053_passed = bool(r053 and r053.get("qc", {}).get("passed") is True)
    r054_passed = bool(r054 and r054.get("qc", {}).get("passed") is True)
    r064_passed = bool(r064 and r064.get("qc", {}).get("passed") is True)

    qc = {
        "passed": (
            not missing_text_files
            and not missing_assets
            and not unguarded_hits
            and r053_passed
            and r054_passed
            and r064_passed
        ),
        "required_text_files_present": not missing_text_files,
        "required_assets_present": not missing_assets,
        "missing_text_files": missing_text_files,
        "missing_assets": missing_assets,
        "unguarded_claim_hits": unguarded_hits,
        "boundary_context_hit_count": len(boundary_hits),
        "r053_latest_audit_passed": r053_passed,
        "r054_regeneration_passed": r054_passed,
        "r064_alignment_passed": r064_passed,
        "manuscript_docx_modified": False,
    }

    manifest = {
        "run_id": "R065",
        "status": "complete_active_claim_surface_audit" if qc["passed"] else "failed_active_claim_surface_audit",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Audit active figure generators, figure index, and newly generated "
            "figure/table design deliverables for unguarded overclaim language."
        ),
        "claim_gate": {
            "absolute_calibration_allowed": False,
            "external_validation_allowed": False,
            "clinical_or_intervention_claim_allowed": False,
            "mcmc_or_bayesian_claim_allowed": False,
            "wet_lab_claim_allowed": False,
            "independent_ews_gain_allowed": False,
            "legacy_s5_s20_reactivation_allowed": False,
        },
        "input_artifacts": {
            "R053": file_record("inputs/audit_runs/R053/active_asset_consistency_audit.json"),
            "R054": file_record("inputs/audit_runs/R054/active_asset_regeneration_manifest.json"),
            "R064": file_record("inputs/audit_runs/R064/regeneration_manifest_alignment.json"),
        },
        "required_assets": [file_record(rel) for rel in REQUIRED_ASSETS],
        "scanned_text_files": scanned,
        "boundary_context_hits": boundary_hits,
        "unguarded_claim_hits": unguarded_hits,
        "qc": qc,
        "decision": (
            "The current figure/table claim surface is acceptable for a purely "
            "computational manuscript if and only if all listed claim gates remain closed."
        ),
        "recommended_next_step": (
            "Resume manuscript synchronization only after using these claim-bounded "
            "captions and tables; do not cite inactive legacy supplementary figures."
        ),
    }

    OUT_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if qc["passed"] else 1


def render_report(manifest: Dict[str, object]) -> str:
    qc = manifest["qc"]
    lines = [
        "# R065 Active Claim-Surface Audit",
        "",
        f"Status: `{manifest['status']}`",
        "",
        "## Scope",
        "",
        "Scanned the active Figure 1-6 generators, active figure index, and the newly generated figure/table design deliverables.",
        "",
        "## QC",
        "",
        f"- Passed: `{qc['passed']}`",
        f"- Required assets present: `{qc['required_assets_present']}`",
        f"- Required text files present: `{qc['required_text_files_present']}`",
        f"- Unguarded claim hits: `{len(manifest['unguarded_claim_hits'])}`",
        f"- Boundary-context risk hits: `{qc['boundary_context_hit_count']}`",
        f"- R053 passed: `{qc['r053_latest_audit_passed']}`",
        f"- R054 passed: `{qc['r054_regeneration_passed']}`",
        f"- R064 passed: `{qc['r064_alignment_passed']}`",
        "",
        "## Decision",
        "",
        str(manifest["decision"]),
        "",
        "## Next step",
        "",
        str(manifest["recommended_next_step"]),
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

