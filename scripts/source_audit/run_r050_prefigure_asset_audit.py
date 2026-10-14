"""R050 pre-figure asset and provenance audit.

The audit inventories current and legacy main figures, classifies the existing
supplementary figure set against the R049 claim boundary, and detects whether
the project-facing figure index still points at legacy outputs. It does not
modify figures or manuscript files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
R049 = ROOT / "refine-logs" / "runs" / "R049" / "computational_claim_boundary.json"
FIGURE_INDEX = ROOT / "FIGURE_INDEX.md"
OUT = (
    ROOT
    / "refine-logs"
    / "runs"
    / "R050"
    / "prefigure_asset_audit.json"
)


CURRENT_MAIN = {
    "Figure 1": {
        "png": "figures/figure1_neuron_comparison.png",
        "pdf": "figures/figure1_neuron_comparison.pdf",
        "generator": (
            "scripts/publication_figures/main/"
            "figure1_neuron_comparison_verified.py"
        ),
        "entry_point": "module1/figure1_neuron_comparison.py",
        "status": "HOLD_R051_REBUILD",
        "reason": (
            "The downgrade is claim-safe, but it still displays nine provisional "
            "absolute OCR scenarios, reports the now-stale 0/9 source count, and "
            "does not present the R047/R048 maximal/spare-only evidence."
        ),
        "allowed_use": "internal provenance/scenario audit only",
    },
    "Figure 2": {
        "png": "figures/figure2_hybrid_ml.png",
        "pdf": "figures/figure2_hybrid_ml.pdf",
        "generator": "scripts/publication_figures/main/figure2_hybrid_verified.py",
        "entry_point": "module2/figure2_hybrid_ml.py",
        "status": "CURRENT_COMPUTATIONAL",
        "reason": "Built from the R025 controlled misspecification benchmark.",
        "allowed_use": "controlled in-silico method benchmark only",
    },
    "Figure 3": {
        "png": "figures/figure3_phase_synergy.png",
        "pdf": "figures/figure3_phase_synergy.pdf",
        "generator": (
            "scripts/publication_figures/main/"
            "figure3_phase_synergy_verified.py"
        ),
        "entry_point": "module3/figure3_phase_synergy.py",
        "status": "CURRENT_COMPUTATIONAL",
        "reason": "Built from the endpoint-qualified R009-R014B evidence chain.",
        "allowed_use": (
            "qualified reduced-ODE endpoint transition; no bistability or wet-lab claim"
        ),
    },
    "Figure 4": {
        "png": "figures/figure4_ews_complete.png",
        "pdf": "figures/figure4_ews_complete.pdf",
        "generator": "scripts/publication_figures/main/figure4_ews_verified.py",
        "entry_point": "module4/figure4_ews_complete.py",
        "status": "CURRENT_COMPUTATIONAL",
        "reason": "Built from R021-R023 locked computational cohort results.",
        "allowed_use": (
            "endpoint separation and descriptive EWS diagnostics; no independent EWS gain"
        ),
    },
    "Figure 5": {
        "png": "figures/figure5_spatial_heterogeneity.png",
        "pdf": "figures/figure5_spatial_heterogeneity.pdf",
        "generator": "scripts/publication_figures/main/figure5_spatial_verified.py",
        "entry_point": "module5/figure5_spatial_heterogeneity.py",
        "status": "CURRENT_CONCEPTUAL",
        "reason": "R028 replacement contains no quantitative spatial prediction.",
        "allowed_use": "position-indexed hypothesis and future spatial-model gate only",
    },
    "Figure 6": {
        "png": "figures/figure6_disease_applications.png",
        "pdf": "figures/figure6_disease_applications.pdf",
        "generator": "scripts/publication_figures/main/figure6_disease_verified.py",
        "entry_point": "module5/figure6_disease_applications.py",
        "status": "CURRENT_CONCEPTUAL",
        "reason": "R029 replacement is a qualitative mechanism-to-model hypothesis map.",
        "allowed_use": "disease-mechanism hypotheses; no trajectory, efficacy, or clinical window",
    },
}


LEGACY_MAIN = {
    f"Figure {number}": {
        "png": f"figures/figure{number}_{stem}_publication.png",
        "pdf": f"figures/figure{number}_{stem}_publication.pdf",
        "status": "LEGACY_HOLD_NOT_ACTIVE",
    }
    for number, stem in (
        (1, "neuron"),
        (2, "hybrid"),
        (3, "phase_synergy"),
        (4, "ews"),
        (5, "spatial"),
        (6, "disease"),
    )
}


SUPPLEMENTARY_STATUS = {
    1: ("CONDITIONAL_SCHEMATIC", "Framework schematic only; not a result figure."),
    2: ("BLOCKED_EXPERIMENTAL_LABEL", "Expected/simulated content is labelled as experimental validation."),
    3: ("HOLD_UNAUDITED_COMPUTATIONAL", "Sensitivity inputs and provenance require a current audit."),
    4: ("HOLD_LEGACY_MODEL_SUPPORT", "Legacy cross-validation/model-support tables are not tied to a current run."),
    5: ("BLOCKED_BAYESIAN", "Bayesian/posterior diagnostics are not supported by a real MCMC run."),
    6: ("HOLD_REBUILD_FROM_R025", "Training diagnostics must be rebuilt from the R025 controlled benchmark."),
    7: ("HOLD_REBUILD_FROM_R014B", "Phase support must be rebuilt from the qualified R009-R014B chain."),
    8: ("HOLD_REBUILD_FROM_R021_R023", "EWS support must reflect the absence of independent EWS gain."),
    9: ("BLOCKED_SPATIAL_VALIDATION", "R028 found no coupled spatial solver or quantitative validation."),
    10: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    11: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    12: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    13: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    14: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    15: ("BLOCKED_DISEASE_QUANTIFICATION", "Treatment and progression values lack an audited disease mapping."),
    16: ("BLOCKED_POSTERIOR_UNCERTAINTY", "Posterior uncertainty is not supported by a real MCMC run."),
    17: ("HOLD_UNAUDITED_DERIVED_ANALYSIS", "PCA/clustering input contract is not frozen."),
    18: ("BLOCKED_UNSUPPORTED_EVALUATION", "Anomaly ROC/AUC inputs are not tied to an audited benchmark."),
    19: ("CONDITIONAL_COMPUTE_BENCHMARK", "May be retained only after hardware/timing provenance is verified."),
    20: ("HOLD_LEGACY_AGGREGATE", "Aggregate training/validation and throughput panels mix legacy inputs."),
}


STALE_TABLES = {
    "supplementary/supplementary_table_s1_complete_parameters.csv": (
        "BLOCKED_STALE_SPECIFICATION"
    ),
    "supplementary/supplementary_table_s2_ode_equations.csv": (
        "BLOCKED_STALE_SPECIFICATION"
    ),
    "supplementary/supplementary_table_s3_reaction_rates.csv": (
        "BLOCKED_STALE_SPECIFICATION"
    ),
    "supplementary/supplementary_table_s4_conserved_pools.csv": (
        "BLOCKED_STALE_SPECIFICATION"
    ),
    "supplementary/supplementary_table_s5_neuron_type_references.csv": (
        "BLOCKED_UNVERIFIED_SOURCES"
    ),
    "supplementary/supplementary_table_s8_ews_thresholds.csv": (
        "BLOCKED_UNSUPPORTED_PERFORMANCE"
    ),
    "supplementary/supplementary_table_s9_disease_phenotypes.csv": (
        "BLOCKED_DISEASE_QUANTIFICATION"
    ),
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(relative_path):
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "sha256": _sha256(path) if path.exists() else None,
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def _audit_main(definitions):
    audited = {}
    for figure, metadata in definitions.items():
        item = dict(metadata)
        item["artifacts"] = {
            "png": _artifact(metadata["png"]),
            "pdf": _artifact(metadata["pdf"]),
        }
        if "generator" in metadata:
            item["generator_artifact"] = _artifact(metadata["generator"])
        if "entry_point" in metadata:
            entry = ROOT / metadata["entry_point"]
            generator_name = Path(metadata["generator"]).stem
            entry_text = entry.read_text(encoding="utf-8", errors="replace")
            item["entry_point_artifact"] = _artifact(metadata["entry_point"])
            item["entry_point_delegates_to_audited_generator"] = (
                generator_name in entry_text
            )
        audited[figure] = item
    return audited


def _audit_supplementary():
    output = {}
    for number, (status, reason) in SUPPLEMENTARY_STATUS.items():
        stem = f"sfigure_s{number}_publication"
        output[f"S{number}"] = {
            "status": status,
            "reason": reason,
            "artifacts": {
                "png": _artifact(f"figures/{stem}.png"),
                "pdf": _artifact(f"figures/{stem}.pdf"),
                "generator": _artifact(
                    f"scripts/publication_figures/supplementary/{stem}.py"
                ),
            },
        }
    return output


def build_audit():
    r049 = json.loads(R049.read_text(encoding="utf-8"))
    figure_index_text = FIGURE_INDEX.read_text(encoding="utf-8", errors="replace")
    current_main = _audit_main(CURRENT_MAIN)
    legacy_main = _audit_main(LEGACY_MAIN)
    supplementary = _audit_supplementary()
    missing_current = [
        figure
        for figure, item in current_main.items()
        if not all(artifact["exists"] for artifact in item["artifacts"].values())
        or not item.get("generator_artifact", {}).get("exists", False)
    ]
    delegation_failures = [
        figure
        for figure, item in current_main.items()
        if not item.get("entry_point_delegates_to_audited_generator", False)
    ]
    index_points_to_legacy = all(
        f"figure{number}_{stem}_publication.png" in figure_index_text
        for number, stem in (
            (1, "neuron"),
            (2, "hybrid"),
            (3, "phase_synergy"),
            (4, "ews"),
            (5, "spatial"),
            (6, "disease"),
        )
    )

    return {
        "run_id": "R050",
        "status": "complete_prefigure_asset_audit",
        "claim_boundary_input": {
            "path": str(R049.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(R049),
            "absolute_calibration_allowed": r049["claim_gate_snapshot"][
                "absolute_calibration_allowed"
            ],
            "external_validation_claim_allowed": r049["claim_gate_snapshot"][
                "external_validation_claim_allowed"
            ],
        },
        "current_main_candidates": current_main,
        "legacy_main_assets": legacy_main,
        "supplementary_assets": supplementary,
        "stale_or_blocked_tables": {
            path: {"status": status, "artifact": _artifact(path)}
            for path, status in STALE_TABLES.items()
        },
        "qc": {
            "missing_current_main_artifacts": missing_current,
            "entry_point_delegation_failures": delegation_failures,
            "figure_index_points_to_legacy_publication_set": index_points_to_legacy,
            "all_current_main_artifacts_exist": not missing_current,
            "all_current_entry_points_delegate": not delegation_failures,
        },
        "active_set_decision": {
            "submission_ready": False,
            "retain_now": ["Figure 2", "Figure 3", "Figure 4", "Figure 5", "Figure 6"],
            "rebuild_before_active": ["Figure 1"],
            "active_supplementary_figures": [],
            "legacy_publication_assets_active": False,
            "reason": (
                "Figure 1 must be rebuilt around R047/R048 and the supplementary "
                "set requires claim-by-claim re-audit. The existing FIGURE_INDEX "
                "still identifies legacy publication files as active."
            ),
        },
        "next_runs": [
            {
                "run_id": "R051",
                "purpose": (
                    "Rebuild Figure 1 from audited R033/R039 maximal/spare ratios, "
                    "R046 formula reference, and R048 diagnostic mapping."
                ),
            },
            {
                "run_id": "R052",
                "purpose": (
                    "Rebuild only the supplementary figures that directly support "
                    "audited computational claims; keep all blocked assets inactive."
                ),
            },
        ],
        "manuscript_modified": False,
        "figures_regenerated": False,
    }


def main():
    payload = build_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

