"""Unit-invariant, source-local OCR constraints.

This module deliberately does not create observations.  It provides the
smallest safe interface for using future Seahorse records when studies report
incompatible absolute normalizations (for example, per-cell versus per-protein).

Only ratios within one source record are derived.  Values from different source
records must never be combined before this transformation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Dict, Mapping, Optional


METRICS = ("basal_ocr", "maximal_ocr", "atp_linked", "proton_leak")
VERIFIED_STATUS = "verified_primary_source"


@dataclass(frozen=True)
class RelativeOCRRecord:
    """One source-local Mito Stress Test record.

    ``normalization_basis`` is metadata only.  It is intentionally not
    converted across records.  A record may be used for relative constraints
    even when its absolute unit is not compatible with the project table.
    """

    source_id: str
    preparation: str
    normalization_basis: str
    metrics: Mapping[str, float]
    provenance_status: str = "unverified_source_provenance"
    absolute_calibration_eligible: bool = False


def validate_record(record: RelativeOCRRecord) -> None:
    """Raise ``ValueError`` if a record is unsafe for ratio construction."""

    if not record.source_id.strip():
        raise ValueError("source_id must be non-empty")
    if not record.preparation.strip():
        raise ValueError("preparation must be non-empty")
    if not record.normalization_basis.strip():
        raise ValueError("normalization_basis must be non-empty")
    missing = [metric for metric in METRICS if metric not in record.metrics]
    if missing:
        raise ValueError(f"missing OCR metrics: {', '.join(missing)}")
    for metric in METRICS:
        value = float(record.metrics[metric])
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{metric} must be a finite positive value")


def derive_relative_constraints(
    record: RelativeOCRRecord,
    *,
    non_mito_ocr: Optional[float] = None,
) -> Dict[str, float]:
    """Derive dimensionless within-record constraints.

    The reference is basal OCR.  ``non_mito_ocr`` is optional and must belong
    to the same source record; when supplied, coupling fractions are calculated
    after subtracting it from basal/maximal OCR.
    """

    validate_record(record)
    basal = float(record.metrics["basal_ocr"])
    maximal = float(record.metrics["maximal_ocr"])
    atp_linked = float(record.metrics["atp_linked"])
    proton_leak = float(record.metrics["proton_leak"])
    if non_mito_ocr is not None:
        non_mito_ocr = float(non_mito_ocr)
        if not isfinite(non_mito_ocr) or non_mito_ocr < 0:
            raise ValueError("non_mito_ocr must be finite and non-negative")
        if non_mito_ocr >= basal:
            raise ValueError("non_mito_ocr must be smaller than basal_ocr")
        basal_ref = basal - non_mito_ocr
        maximal_ref = maximal - non_mito_ocr
    else:
        basal_ref = basal
        maximal_ref = maximal

    if maximal_ref <= 0:
        raise ValueError("maximal OCR after normalization must be positive")
    ratios = {
        "maximal_to_basal": maximal_ref / basal_ref,
        "spare_to_basal": (maximal_ref - basal_ref) / basal_ref,
        "atp_linked_to_basal": atp_linked / basal_ref,
        "proton_leak_to_basal": proton_leak / basal_ref,
    }
    return ratios


def log_ratio_residual(
    predicted: Mapping[str, float],
    observed: Mapping[str, float],
) -> Dict[str, float]:
    """Return log-ratio residuals for a source-local comparison."""

    expected = ("maximal_to_basal", "spare_to_basal",
                "atp_linked_to_basal", "proton_leak_to_basal")
    missing = [key for key in expected if key not in predicted or key not in observed]
    if missing:
        raise ValueError(f"missing relative constraints: {', '.join(missing)}")
    residuals: Dict[str, float] = {}
    for key in expected:
        pred = float(predicted[key])
        obs = float(observed[key])
        if not isfinite(pred) or not isfinite(obs) or pred <= 0 or obs <= 0:
            raise ValueError(f"{key} must be finite and positive")
        residuals[key] = log(pred) - log(obs)
    return residuals


def source_local_constraint_loss(
    predicted: Mapping[str, float],
    observed: Mapping[str, float],
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """Calculate a weighted mean squared log-ratio residual."""

    residuals = log_ratio_residual(predicted, observed)
    weights = weights or {}
    total_weight = 0.0
    weighted_sum = 0.0
    for key, residual in residuals.items():
        weight = float(weights.get(key, 1.0))
        if not isfinite(weight) or weight <= 0:
            raise ValueError(f"weight for {key} must be finite and positive")
        weighted_sum += weight * residual * residual
        total_weight += weight
    return weighted_sum / total_weight


def absolute_calibration_allowed(record: RelativeOCRRecord) -> bool:
    """Return whether the record can enter absolute Figure 1 calibration."""

    return (
        record.provenance_status == VERIFIED_STATUS
        and record.normalization_basis == "pmol/min/ug_protein"
        and record.absolute_calibration_eligible
    )
