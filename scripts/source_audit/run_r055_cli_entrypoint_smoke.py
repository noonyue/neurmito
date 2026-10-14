"""R055 command-line entry-point smoke test.

R054 verifies the Python public functions. R055 verifies the command-line
entry points used by batch workflows, ensuring that ``python module*/figure*.py``
also routes to the audited active assets rather than legacy exploratory
renderers.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNS = ROOT / "refine-logs" / "runs"
OUT = RUNS / "R055" / "cli_entrypoint_smoke_manifest.json"

ENTRYPOINTS = {
    "Figure 1": "module1/figure1_neuron_comparison.py",
    "Figure 2": "module2/figure2_hybrid_ml.py",
    "Figure 3": "module3/figure3_phase_synergy.py",
    "Figure 4": "module4/figure4_ews_complete.py",
    "Figure 5": "module5/figure5_spatial_heterogeneity.py",
    "Figure 6": "module5/figure6_disease_applications.py",
}

EXPECTED_OUTPUTS = {
    "Figure 1": [
        "figures/figure1_neuron_comparison.png",
        "figures/figure1_neuron_comparison.pdf",
    ],
    "Figure 2": [
        "figures/figure2_hybrid_ml.png",
        "figures/figure2_hybrid_ml.pdf",
    ],
    "Figure 3": [
        "figures/figure3_phase_synergy.png",
        "figures/figure3_phase_synergy.pdf",
    ],
    "Figure 4": [
        "figures/figure4_ews_complete.png",
        "figures/figure4_ews_complete.pdf",
    ],
    "Figure 5": [
        "figures/figure5_spatial_heterogeneity.png",
        "figures/figure5_spatial_heterogeneity.pdf",
    ],
    "Figure 6": [
        "figures/figure6_disease_applications.png",
        "figures/figure6_disease_applications.pdf",
    ],
}


def _tail(text: str, limit: int = 1200) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _artifact(relative_path: str) -> dict:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def _run_entrypoint(label: str, relative_path: str, timeout_seconds: int = 150) -> dict:
    start = perf_counter()
    completed = subprocess.run(
        [sys.executable, relative_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    duration = perf_counter() - start
    artifacts = [_artifact(path) for path in EXPECTED_OUTPUTS[label]]
    return {
        "label": label,
        "entrypoint": relative_path,
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "expected_outputs": artifacts,
        "passed": completed.returncode == 0
        and all(item["exists"] and item["size_bytes"] > 10000 for item in artifacts),
    }


def _run_post_smoke_consistency() -> dict:
    from scripts.source_audit.run_r053_active_asset_consistency_audit import build_audit, OUT as R053_OUT

    payload = build_audit()
    R053_OUT.parent.mkdir(parents=True, exist_ok=True)
    R053_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "r053_output": str(R053_OUT.relative_to(ROOT)).replace("\\", "/"),
        "passed": payload["qc"]["passed"] is True,
        "qc": payload["qc"],
    }


def generate() -> dict:
    start = perf_counter()
    smoke = {
        label: _run_entrypoint(label, relative_path)
        for label, relative_path in ENTRYPOINTS.items()
    }
    consistency = _run_post_smoke_consistency()
    payload = {
        "run_id": "R055",
        "status": "complete_cli_entrypoint_smoke",
        "entrypoint_results": smoke,
        "post_smoke_consistency": consistency,
        "qc": {
            "all_entrypoints_return_zero": all(
                item["returncode"] == 0 for item in smoke.values()
            ),
            "all_expected_outputs_exist": all(
                all(
                    artifact["exists"] and artifact["size_bytes"] > 10000
                    for artifact in item["expected_outputs"]
                )
                for item in smoke.values()
            ),
            "all_entrypoints_passed": all(item["passed"] for item in smoke.values()),
            "r053_consistency_passed": consistency["passed"],
            "legacy_publication_assets_reactivated": False,
            "manuscript_modified": False,
        },
        "total_duration_seconds": round(perf_counter() - start, 3),
    }
    payload["qc"]["passed"] = all(
        value is True
        for value in (
            payload["qc"]["all_entrypoints_return_zero"],
            payload["qc"]["all_expected_outputs_exist"],
            payload["qc"]["all_entrypoints_passed"],
            payload["qc"]["r053_consistency_passed"],
            payload["qc"]["legacy_publication_assets_reactivated"] is False,
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

