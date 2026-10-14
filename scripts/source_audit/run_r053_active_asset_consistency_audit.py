"""R053 active asset consistency audit.

R051 and R052 replaced the risky Figure 1 and supplementary assets with a
source-audited computational set. This audit checks that the project-facing
asset layer is internally consistent:

* active main/supplementary files exist and are hashable;
* public module entry points delegate to audited generators;
* R051/R052 claim gates remain closed for unsupported claims;
* FIGURE_INDEX's active section does not point at legacy ``*_publication``
  assets;
* legacy publication assets are retained only in an inactive provenance section.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R053" / "active_asset_consistency_audit.json"
FIGURE_INDEX = ROOT / "FIGURE_INDEX.md"
R049 = RUNS / "R049" / "computational_claim_boundary.json"
R051 = RUNS / "R051" / "figure1_metadata.json"
R052 = RUNS / "R052" / "audited_supplementary_manifest.json"

ACTIVE_MAIN = {
    "Figure 1": {
        "png": "figures/figure1_neuron_comparison.png",
        "pdf": "figures/figure1_neuron_comparison.pdf",
        "generator": "scripts/publication_figures/main/figure1_neuron_comparison_verified.py",
        "entry_point": "module1/figure1_neuron_comparison.py",
    },
    "Figure 2": {
        "png": "figures/figure2_hybrid_ml.png",
        "pdf": "figures/figure2_hybrid_ml.pdf",
        "generator": "scripts/publication_figures/main/figure2_hybrid_verified.py",
        "entry_point": "module2/figure2_hybrid_ml.py",
    },
    "Figure 3": {
        "png": "figures/figure3_phase_synergy.png",
        "pdf": "figures/figure3_phase_synergy.pdf",
        "generator": "scripts/publication_figures/main/figure3_phase_synergy_verified.py",
        "entry_point": "module3/figure3_phase_synergy.py",
    },
    "Figure 4": {
        "png": "figures/figure4_ews_complete.png",
        "pdf": "figures/figure4_ews_complete.pdf",
        "generator": "scripts/publication_figures/main/figure4_ews_verified.py",
        "entry_point": "module4/figure4_ews_complete.py",
    },
    "Figure 5": {
        "png": "figures/figure5_spatial_heterogeneity.png",
        "pdf": "figures/figure5_spatial_heterogeneity.pdf",
        "generator": "scripts/publication_figures/main/figure5_spatial_verified.py",
        "entry_point": "module5/figure5_spatial_heterogeneity.py",
    },
    "Figure 6": {
        "png": "figures/figure6_disease_applications.png",
        "pdf": "figures/figure6_disease_applications.pdf",
        "generator": "scripts/publication_figures/main/figure6_disease_verified.py",
        "entry_point": "module5/figure6_disease_applications.py",
    },
}

LEGACY_PATTERNS = [
    "figure1_neuron_publication",
    "figure2_hybrid_publication",
    "figure3_phase_synergy_publication",
    "figure4_ews_publication",
    "figure5_spatial_publication",
    "figure6_disease_publication",
    "sfigure_s2_publication",
    "sfigure_s5_publication",
    "sfigure_s9_publication",
    "sfigure_s10_publication",
    "sfigure_s16_publication",
    "sfigure_s18_publication",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(relative_path: str) -> dict:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": _sha256(path) if path.exists() else None,
    }


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _active_index_section(text: str) -> str:
    marker = "## Active audited asset set"
    if marker not in text:
        return ""
    after = text.split(marker, 1)[1]
    if "\n---" in after:
        return after.split("\n---", 1)[0]
    return after


def _inactive_index_section(text: str) -> str:
    marker = "## Inactive legacy publication asset inventory"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1]


def _audit_main_assets() -> dict:
    output = {}
    for figure, item in ACTIVE_MAIN.items():
        generator = ROOT / item["generator"]
        entry_point = ROOT / item["entry_point"]
        generator_stem = generator.stem
        entry_text = entry_point.read_text(encoding="utf-8", errors="replace")
        output[figure] = {
            "png": _artifact(item["png"]),
            "pdf": _artifact(item["pdf"]),
            "generator": _artifact(item["generator"]),
            "entry_point": _artifact(item["entry_point"]),
            "entry_point_delegates": generator_stem in entry_text,
            "active_paths_are_not_legacy_publication": (
                "_publication" not in item["png"] and "_publication" not in item["pdf"]
            ),
        }
    return output


def _audit_supplementary_assets(r052: dict) -> dict:
    output = {}
    for label, item in r052["active_supplementary_figures"].items():
        png = _artifact(item["png"])
        pdf = _artifact(item["pdf"])
        output[label] = {
            "png": png,
            "pdf": pdf,
            "manifest_status": item["status"],
            "manifest_png_sha256_matches": png["sha256"] == item["png_sha256"],
            "manifest_pdf_sha256_matches": pdf["sha256"] == item["pdf_sha256"],
            "active_paths_are_not_legacy_publication": (
                "_publication" not in item["png"] and "_publication" not in item["pdf"]
            ),
            "scope": item["scope"],
        }
    return output


def _audit_manifest_hashes(r051: dict) -> dict:
    png = _artifact(r051["outputs"]["png"])
    pdf = _artifact(r051["outputs"]["pdf"])
    return {
        "figure1_png_sha256_matches_metadata": (
            png["sha256"] == r051["outputs"]["png_sha256"]
        ),
        "figure1_pdf_sha256_matches_metadata": (
            pdf["sha256"] == r051["outputs"]["pdf_sha256"]
        ),
        "figure1_png": png,
        "figure1_pdf": pdf,
    }


def build_audit() -> dict:
    r049 = _read_json(R049)
    r051 = _read_json(R051)
    r052 = _read_json(R052)
    index_text = FIGURE_INDEX.read_text(encoding="utf-8", errors="replace")
    active_section = _active_index_section(index_text)
    inactive_section = _inactive_index_section(index_text)
    main_assets = _audit_main_assets()
    supplementary_assets = _audit_supplementary_assets(r052)
    manifest_hashes = _audit_manifest_hashes(r051)

    missing_main = [
        label
        for label, item in main_assets.items()
        if not all(item[key]["exists"] for key in ("png", "pdf", "generator", "entry_point"))
    ]
    missing_supplementary = [
        label
        for label, item in supplementary_assets.items()
        if not item["png"]["exists"] or not item["pdf"]["exists"]
    ]
    delegation_failures = [
        label for label, item in main_assets.items() if not item["entry_point_delegates"]
    ]
    supplementary_hash_mismatches = [
        label
        for label, item in supplementary_assets.items()
        if not item["manifest_png_sha256_matches"]
        or not item["manifest_pdf_sha256_matches"]
    ]
    active_section_legacy_hits = [
        pattern for pattern in LEGACY_PATTERNS if pattern in active_section
    ]
    inactive_section_missing_legacy = [
        pattern for pattern in LEGACY_PATTERNS if pattern not in inactive_section
    ]

    r051_gate = r051["claim_gate"]
    r052_gate = r052["claim_gate"]
    claim_gates_closed = {
        "r049_absolute_calibration_allowed": r049["claim_gate_snapshot"][
            "absolute_calibration_allowed"
        ] is False,
        "r049_external_validation_allowed": r049["claim_gate_snapshot"][
            "external_validation_claim_allowed"
        ] is False,
        "r051_absolute_ocr_displayed": r051_gate["absolute_ocr_displayed"] is False,
        "r051_mcmc_or_posterior_displayed": (
            r051_gate["mcmc_or_posterior_displayed"] is False
        ),
        "r051_external_validation_claim_allowed": (
            r051_gate["external_validation_claim_allowed"] is False
        ),
        "r052_all_unsupported_claims_false": all(value is False for value in r052_gate.values()),
    }

    qc = {
        "missing_main_assets": missing_main,
        "missing_supplementary_assets": missing_supplementary,
        "entry_point_delegation_failures": delegation_failures,
        "supplementary_manifest_hash_mismatches": supplementary_hash_mismatches,
        "active_section_legacy_hits": active_section_legacy_hits,
        "inactive_section_missing_legacy": inactive_section_missing_legacy,
        "main_paths_are_nonlegacy": all(
            item["active_paths_are_not_legacy_publication"]
            for item in main_assets.values()
        ),
        "supplementary_paths_are_nonlegacy": all(
            item["active_paths_are_not_legacy_publication"]
            for item in supplementary_assets.values()
        ),
        "figure1_manifest_hashes_match": all(
            manifest_hashes[key]
            for key in (
                "figure1_png_sha256_matches_metadata",
                "figure1_pdf_sha256_matches_metadata",
            )
        ),
        "claim_gates_closed": all(claim_gates_closed.values()),
    }
    qc["passed"] = (
        not missing_main
        and not missing_supplementary
        and not delegation_failures
        and not supplementary_hash_mismatches
        and not active_section_legacy_hits
        and not inactive_section_missing_legacy
        and qc["main_paths_are_nonlegacy"]
        and qc["supplementary_paths_are_nonlegacy"]
        and qc["figure1_manifest_hashes_match"]
        and qc["claim_gates_closed"]
    )

    return {
        "run_id": "R053",
        "status": "complete_active_asset_consistency_audit",
        "main_assets": main_assets,
        "supplementary_assets": supplementary_assets,
        "manifest_hashes": manifest_hashes,
        "claim_gates_closed": claim_gates_closed,
        "figure_index": {
            "path": "FIGURE_INDEX.md",
            "active_section_has_audited_supplements": all(
                stem in active_section
                for stem in (
                    "audited_sfigure_s1_source_contract",
                    "audited_sfigure_s2_hybrid_benchmark",
                    "audited_sfigure_s3_phase_robustness",
                    "audited_sfigure_s4_ews_locked_test",
                )
            ),
            "active_section_legacy_hits": active_section_legacy_hits,
            "inactive_section_missing_legacy": inactive_section_missing_legacy,
        },
        "input_manifests": {
            "R049": {
                "path": str(R049.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R049),
            },
            "R051": {
                "path": str(R051.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R051),
            },
            "R052": {
                "path": str(R052.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(R052),
            },
        },
        "qc": qc,
        "manuscript_modified": False,
    }


def main():
    payload = build_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

