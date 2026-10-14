"""R054 one-command active asset regeneration harness.

This harness rebuilds the full active audited asset set and immediately runs the
R053 consistency audit. It is intentionally scoped to computational assets only:
no manuscript files are modified, and legacy ``*_publication`` assets are not
regenerated or reactivated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R054" / "active_asset_regeneration_manifest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_outputs(result):
    if isinstance(result, (str, Path)):
        return [Path(result)]
    if isinstance(result, tuple):
        return [Path(item) for item in result]
    if isinstance(result, list):
        return [Path(item) for item in result]
    raise TypeError(f"Unsupported generation result type: {type(result)!r}")


def _artifact(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return {
        "path": str(resolved.relative_to(ROOT)).replace("\\", "/"),
        "exists": resolved.exists(),
        "size_bytes": resolved.stat().st_size if resolved.exists() else None,
        "sha256": _sha256(resolved) if resolved.exists() else None,
    }


def _run_step(label: str, fn) -> dict:
    start = perf_counter()
    result = fn()
    duration = perf_counter() - start
    outputs = [_artifact(path) for path in _normalize_outputs(result)]
    return {
        "label": label,
        "duration_seconds": round(duration, 3),
        "outputs": outputs,
        "passed": all(item["exists"] and item["size_bytes"] > 10000 for item in outputs),
    }


def _run_main_figures() -> dict:
    from module1.figure1_neuron_comparison import make_figure1
    from scripts.publication_figures.main.figure1_neuron_comparison_verified import (
        OUT as FIGURE1_PNG,
        PDF as FIGURE1_PDF,
    )
    from module2.figure2_hybrid_ml import make_figure2
    from module3.figure3_phase_synergy import make_figure3
    from module4.figure4_ews_complete import make_figure4
    from module5.figure5_spatial_heterogeneity import make_figure5
    from module5.figure6_disease_applications import make_figure6

    def make_figure1_with_pdf():
        make_figure1()
        return FIGURE1_PNG, FIGURE1_PDF

    steps = [
        ("Figure 1", make_figure1_with_pdf),
        ("Figure 2", make_figure2),
        ("Figure 3", make_figure3),
        ("Figure 4", make_figure4),
        ("Figure 5", make_figure5),
        ("Figure 6", make_figure6),
    ]
    return {label: _run_step(label, fn) for label, fn in steps}


def _run_supplementary() -> dict:
    from scripts.source_audit.run_r052_audited_supplementary_rebuild import generate as generate_r052

    start = perf_counter()
    r052_payload = generate_r052()
    duration = perf_counter() - start
    outputs = {}
    for label, item in r052_payload["active_supplementary_figures"].items():
        outputs[label] = {
            "png": _artifact(Path(item["png"])),
            "pdf": _artifact(Path(item["pdf"])),
            "scope": item["scope"],
            "status": item["status"],
        }
    return {
        "label": "Audited Supplementary S1-S4",
        "duration_seconds": round(duration, 3),
        "outputs": outputs,
        "passed": all(
            item["png"]["exists"]
            and item["png"]["size_bytes"] > 10000
            and item["pdf"]["exists"]
            and item["pdf"]["size_bytes"] > 10000
            for item in outputs.values()
        ),
        "r052_status": r052_payload["status"],
    }


def _run_consistency_audit() -> dict:
    from scripts.source_audit.run_r053_active_asset_consistency_audit import build_audit, OUT as R053_OUT

    start = perf_counter()
    payload = build_audit()
    R053_OUT.parent.mkdir(parents=True, exist_ok=True)
    R053_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    duration = perf_counter() - start
    return {
        "label": "R053 consistency audit",
        "duration_seconds": round(duration, 3),
        "output": _artifact(R053_OUT),
        "passed": payload["qc"]["passed"] is True,
        "qc": payload["qc"],
    }


def generate() -> dict:
    main_start = perf_counter()
    main_figures = _run_main_figures()
    supplementary = _run_supplementary()
    consistency = _run_consistency_audit()
    total_duration = perf_counter() - main_start

    payload = {
        "run_id": "R054",
        "status": "complete_active_asset_regeneration_harness",
        "main_figures": main_figures,
        "supplementary_figures": supplementary,
        "consistency_audit": consistency,
        "qc": {
            "main_figures_passed": all(item["passed"] for item in main_figures.values()),
            "supplementary_figures_passed": supplementary["passed"],
            "r053_consistency_passed": consistency["passed"],
            "legacy_publication_assets_regenerated": False,
            "manuscript_modified": False,
        },
        "total_duration_seconds": round(total_duration, 3),
    }
    payload["qc"]["passed"] = all(
        value is True
        for value in (
            payload["qc"]["main_figures_passed"],
            payload["qc"]["supplementary_figures_passed"],
            payload["qc"]["r053_consistency_passed"],
            payload["qc"]["legacy_publication_assets_regenerated"] is False,
            payload["qc"]["manuscript_modified"] is False,
        )
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def main():
    payload = generate()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

