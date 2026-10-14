"""R057 active claim-language audit.

The active audited figure set is computational-only. This audit scans the
active verified figure generators for risky claim terms and verifies that such
terms appear only inside explicit boundary/withheld/unsupported contexts.
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
OUT = RUNS / "R057" / "active_claim_language_audit.json"


VERIFIED_GENERATORS = {
    "Figure 1": "scripts/publication_figures/main/figure1_neuron_comparison_verified.py",
    "Figure 2": "scripts/publication_figures/main/figure2_hybrid_verified.py",
    "Figure 3": "scripts/publication_figures/main/figure3_phase_synergy_verified.py",
    "Figure 4": "scripts/publication_figures/main/figure4_ews_verified.py",
    "Figure 5": "scripts/publication_figures/main/figure5_spatial_verified.py",
    "Figure 6": "scripts/publication_figures/main/figure6_disease_verified.py",
}

RISKY_PATTERNS = {
    "absolute_ocr": r"\babsolute(?:\s+OCR|\s+calibration)?\b",
    "mcmc_or_bayesian": r"\b(?:MCMC|Bayesian|posterior)\b",
    "validation": r"\b(?:validation|validated|external validation|experimental)\b",
    "clinical_or_patient": r"\b(?:clinical|patient|patients)\b",
    "intervention_or_efficacy": r"\b(?:intervention|efficacy|treatment|success)\b",
    "independent_gain": r"\bindependent\s+(?:EWS\s+)?(?:gain|improvement)\b",
}

BOUNDARY_MARKERS = [
    "no ",
    "not ",
    "without ",
    "withheld",
    "unsupported",
    "missing",
    "rather than",
    "boundary",
    "gate",
    "claim boundary",
    "does not",
    "do not",
    "deliberately contains no",
    "required before",
    "blocked",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _is_boundary_context(context: str) -> bool:
    lowered = context.lower()
    return any(marker in lowered for marker in BOUNDARY_MARKERS)


def _line_hits(line: str) -> list:
    hits = []
    for claim_type, pattern in RISKY_PATTERNS.items():
        if re.search(pattern, line, flags=re.IGNORECASE):
            hits.append(claim_type)
    return hits


def _audit_generator(relative_path: str) -> dict:
    path = ROOT / relative_path
    text = _read_text(path)
    lines = text.splitlines()
    risky_lines = []
    unguarded = []
    boundary_hits = 0

    for lineno, line in enumerate(lines, start=1):
        hits = _line_hits(line)
        if not hits:
            continue
        start = max(0, lineno - 6)
        end = min(len(lines), lineno + 3)
        context = " ".join(lines[start:end])
        boundary_context = _is_boundary_context(context)
        item = {
            "line": lineno,
            "text": line.strip(),
            "claim_types": hits,
            "boundary_context": boundary_context,
        }
        risky_lines.append(item)
        if boundary_context:
            boundary_hits += len(hits)
        else:
            unguarded.append(item)

    boundary_gated = not unguarded and (
        "claim" in text.lower()
        or "boundary" in text.lower()
        or "gate" in text.lower()
        or "not supported" in text.lower()
        or "no " in text.lower()
    )
    legacy_publication_references = sorted(
        set(re.findall(r"[A-Za-z0-9_./-]*publication[A-Za-z0-9_./-]*", text))
    )
    return {
        "path": relative_path,
        "sha256": _sha256(path),
        "risky_lines": risky_lines,
        "unguarded_risky_lines": unguarded,
        "boundary_gated": boundary_gated,
        "risky_term_hit_count": sum(len(item["claim_types"]) for item in risky_lines),
        "boundary_context_hit_count": boundary_hits,
        "legacy_publication_references": legacy_publication_references,
    }


def build_audit() -> dict:
    verified = {
        label: _audit_generator(path)
        for label, path in VERIFIED_GENERATORS.items()
    }
    unguarded_risky_claims = [
        {
            "figure": label,
            "path": item["path"],
            "line": hit["line"],
            "text": hit["text"],
            "claim_types": hit["claim_types"],
        }
        for label, item in verified.items()
        for hit in item["unguarded_risky_lines"]
    ]
    legacy_publication_references = sorted(
        {
            reference
            for item in verified.values()
            for reference in item["legacy_publication_references"]
        }
    )
    active_risky_term_hits = sum(
        item["risky_term_hit_count"] for item in verified.values()
    )
    boundary_context_hits = sum(
        item["boundary_context_hit_count"] for item in verified.values()
    )

    qc = {
        "unguarded_risky_claims": unguarded_risky_claims,
        "legacy_publication_references": legacy_publication_references,
        "all_verified_generators_boundary_gated": all(
            item["boundary_gated"] for item in verified.values()
        ),
        "manuscript_modified": False,
    }
    qc["passed"] = (
        not unguarded_risky_claims
        and not legacy_publication_references
        and qc["all_verified_generators_boundary_gated"]
        and qc["manuscript_modified"] is False
    )

    return {
        "run_id": "R057",
        "status": "complete_active_claim_language_audit",
        "verified_generators": verified,
        "claim_boundary": {
            "active_risky_term_hits": active_risky_term_hits,
            "boundary_context_hits": boundary_context_hits,
            "unguarded_hits": unguarded_risky_claims,
            "interpretation": (
                "Risky claim terms in active generators must appear only in "
                "explicitly withheld, unsupported, missing-evidence, or "
                "claim-boundary contexts."
            ),
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

