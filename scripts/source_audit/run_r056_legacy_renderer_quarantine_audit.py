"""R056 legacy renderer quarantine audit.

R054 and R055 verified the active figure assets and their public CLI entry
points. R056 does not delete the historical exploratory renderers; it checks
that they remain quarantined behind the audited active wrappers and aliases.
The audit is static and claim-boundary oriented: no manuscript files are
modified, and the active entry points must not resolve to legacy renderers.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R056" / "legacy_renderer_quarantine_audit.json"
FIGURE_INDEX = ROOT / "FIGURE_INDEX.md"
R054 = RUNS / "R054" / "active_asset_regeneration_manifest.json"
R055 = RUNS / "R055" / "cli_entrypoint_smoke_manifest.json"


MODULES = {
    "Figure 1": {
        "path": "module1/figure1_neuron_comparison.py",
        "entrypoint": "make_figure1",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure1_neuron_comparison_verified",
            "return str(Path(png))",
        ],
        "legacy_markers": ["_make_legacy_", "Legacy exploratory"],
        "legacy_entrypoint_pattern": r"make_figure1\s*=\s*_make_legacy",
    },
    "Figure 2": {
        "path": "module2/figure2_hybrid_ml.py",
        "entrypoint": "make_figure2",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure2_hybrid_verified",
            "return generate()",
        ],
        "legacy_markers": ["_make_legacy_figure2_unverified", "Legacy exploratory"],
        "legacy_entrypoint_pattern": r"make_figure2\s*=\s*_make_legacy",
    },
    "Figure 3": {
        "path": "module3/figure3_phase_synergy.py",
        "entrypoint": "make_figure3",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure3_phase_synergy_verified",
            "make_figure3 = _make_verified_figure3",
        ],
        "legacy_markers": [
            "The former functions above are retained for reference only",
            "Legacy exploratory",
        ],
        "legacy_entrypoint_pattern": r"make_figure3\s*=\s*_make_legacy",
    },
    "Figure 4": {
        "path": "module4/figure4_ews_complete.py",
        "entrypoint": "make_figure4",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure4_ews_verified",
            "make_figure4 = _generate_verified_figure4",
        ],
        "legacy_markers": ["Legacy exploratory", "successful early intervention"],
        "legacy_entrypoint_pattern": r"make_figure4\s*=\s*_make_legacy",
    },
    "Figure 5": {
        "path": "module5/figure5_spatial_heterogeneity.py",
        "entrypoint": "make_figure5",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure5_spatial_verified",
            "return generate()",
        ],
        "legacy_markers": ["_make_legacy_figure5_unverified", "Legacy exploratory"],
        "legacy_entrypoint_pattern": r"make_figure5\s*=\s*_make_legacy",
    },
    "Figure 6": {
        "path": "module5/figure6_disease_applications.py",
        "entrypoint": "make_figure6",
        "verified_generator_markers": [
            "scripts.publication_figures.main.figure6_disease_verified",
            "return generate()",
        ],
        "legacy_markers": ["_make_legacy_figure6_unverified", "Legacy exploratory"],
        "legacy_entrypoint_pattern": r"make_figure6\s*=\s*_make_legacy",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact(relative_path: str) -> dict:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": _sha256(path) if path.exists() else None,
    }


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


def _publication_hits(text: str) -> list:
    return sorted(set(re.findall(r"[A-Za-z0-9_]*publication[A-Za-z0-9_]*", text)))


def _publication_hits_in_json(value) -> list:
    hits = set()
    pattern = re.compile(r"(?:figures|scripts|module|publication_figures|sfigure|figure)[A-Za-z0-9_./-]*publication[A-Za-z0-9_./-]*")

    def walk(item):
        if isinstance(item, dict):
            for sub in item.values():
                walk(sub)
        elif isinstance(item, list):
            for sub in item:
                walk(sub)
        elif isinstance(item, str):
            for hit in pattern.findall(item):
                hits.add(hit)

    walk(value)
    return sorted(hits)


def _main_block_calls_public_entrypoint(text: str, entrypoint: str) -> bool:
    tail = _main_block_tail(text)
    if tail is None:
        return False
    return f"{entrypoint}()" in tail


def _main_block_tail(text: str):
    for marker in ("if __name__ == '__main__':", 'if __name__ == "__main__":'):
        if marker in text:
            return text.split(marker, 1)[1]
    return None


def _module_audit(label: str, spec: dict) -> dict:
    path = ROOT / spec["path"]
    text = _read_text(path)
    legacy_markers_present = any(marker in text for marker in spec["legacy_markers"])
    legacy_binding = bool(re.search(spec["legacy_entrypoint_pattern"], text))
    verified_markers_present = all(marker in text for marker in spec["verified_generator_markers"])
    main_block_calls_public_entrypoint = _main_block_calls_public_entrypoint(
        text, spec["entrypoint"]
    )
    tail = _main_block_tail(text)
    main_block_calls_legacy_renderer = tail is not None and "_make_legacy_" in tail

    if label == "Figure 1":
        classification = "clean_wrapper"
        active_entrypoint_delegates = verified_markers_present and not legacy_markers_present
    else:
        classification = "legacy_retained_quarantined"
        active_entrypoint_delegates = verified_markers_present and not legacy_binding

    return {
        "path": spec["path"],
        "classification": classification,
        "legacy_markers_present": legacy_markers_present,
        "verified_generator_markers_present": verified_markers_present,
        "active_entrypoint_delegates_to_verified_generator": active_entrypoint_delegates,
        "main_block_calls_public_entrypoint": main_block_calls_public_entrypoint,
        "main_block_calls_legacy_renderer": main_block_calls_legacy_renderer,
        "active_entrypoint_resolves_to_legacy": legacy_binding,
        "public_entrypoint": spec["entrypoint"],
    }


def _read_prior_manifest(path: Path) -> dict:
    payload = _read_json(path)
    qc = payload.get("qc", {})
    publication_hits = _publication_hits_in_json(payload)
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha256(path),
        "qc_passed": qc.get("passed") is True,
        "publication_asset_references": publication_hits,
    }


def build_audit() -> dict:
    index_text = _read_text(FIGURE_INDEX)
    active_section = _active_index_section(index_text)
    inactive_section = _inactive_index_section(index_text)

    module_entrypoints = {
        label: _module_audit(label, spec) for label, spec in MODULES.items()
    }
    active_entrypoints_resolve_to_legacy = [
        label
        for label, item in module_entrypoints.items()
        if item["active_entrypoint_resolves_to_legacy"]
    ]
    module_quarantine_failures = [
        label
        for label, item in module_entrypoints.items()
        if not item["verified_generator_markers_present"]
        or not item["main_block_calls_public_entrypoint"]
        or item["main_block_calls_legacy_renderer"]
    ]

    active_section_publication_hits = _publication_hits(active_section)
    inactive_publication_hits = _publication_hits(inactive_section)
    inactive_section_publication_script_count = len(inactive_publication_hits)

    prior_manifests = {
        "R054": _read_prior_manifest(R054),
        "R055": _read_prior_manifest(R055),
    }
    active_manifests_reference_publication_assets = sorted(
        set(prior_manifests["R054"]["publication_asset_references"])
        | set(prior_manifests["R055"]["publication_asset_references"])
    )

    qc = {
        "module_quarantine_failures": module_quarantine_failures,
        "active_entrypoints_resolve_to_legacy": active_entrypoints_resolve_to_legacy,
        "active_manifests_reference_publication_assets": active_manifests_reference_publication_assets,
        "active_section_publication_hits": active_section_publication_hits,
        "inactive_section_publication_hits": inactive_publication_hits,
        "inactive_section_publication_script_count": inactive_section_publication_script_count,
        "manuscript_modified": False,
    }
    qc["passed"] = (
        not module_quarantine_failures
        and not active_entrypoints_resolve_to_legacy
        and not active_manifests_reference_publication_assets
        and not active_section_publication_hits
        and inactive_section_publication_script_count >= 20
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R056",
        "status": "complete_legacy_renderer_quarantine_audit",
        "module_entrypoints": module_entrypoints,
        "prior_manifests": prior_manifests,
        "figure_index": {
            "path": "FIGURE_INDEX.md",
            "active_section_publication_hits": active_section_publication_hits,
            "inactive_section_publication_hits": inactive_publication_hits,
            "inactive_section_publication_script_count": inactive_section_publication_script_count,
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

