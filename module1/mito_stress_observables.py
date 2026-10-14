"""Unit-free Mito Stress Test observables for the reduced ODE.

The reduced model has a mitochondrial oxygen-consumption proxy (Complex IV
flux, ``J_C4``) but no cell-number or protein-mass scale.  This module exposes
the same source-local ratios used by ``data.relative_ocr_constraints`` without
claiming an absolute Seahorse OCR conversion.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional

import numpy as np

from .bazil2016_ode import DEFAULT_PARAMS, rate_C4
from .neurmito_system import CARDIAC_IC, IDX, odes, simulate


def _effective_params(params: Mapping[str, float], stress: Mapping[str, float]):
    """Mirror the Mito Stress-relevant modifiers in ``neurmito_system.odes``."""

    effective = dict(params)
    if "oligomycin" in stress:
        inhibition = np.clip(float(stress["oligomycin"]), 0.0, 1.0)
        effective["Vmax_CV"] *= 1.0 - inhibition
    if "fccp" in stress:
        activation = max(float(stress["fccp"]), 0.0)
        effective["g_H"] *= 1.0 + 20.0 * activation
    return effective


def c4_oxygen_flux(y: np.ndarray, params: Mapping[str, float],
                   stress: Optional[Mapping[str, float]] = None) -> float:
    """Return Complex IV oxygen flux, the model's mitochondrial OCR proxy."""

    stress = stress or {}
    p_eff = _effective_params(params, stress)
    return float(rate_C4(
        max(float(y[IDX["Cred"]]), 1e-10),
        max(float(y[IDX["O2"]]), 1e-10),
        float(y[IDX["DPsi"]]),
        p_eff,
    ))


def _run_stage(
    y0: np.ndarray,
    params: Mapping[str, float],
    stress: Mapping[str, float],
    duration_s: float,
    sample_count: int,
):
    times = np.linspace(0.0, duration_s, sample_count)
    solution = simulate(
        (0.0, duration_s),
        times,
        y0=np.asarray(y0, dtype=float).copy(),
        params=dict(params),
        stress=dict(stress),
    )
    if not solution.success:
        raise RuntimeError(f"Mito Stress stage failed: {solution.message}")
    final_state = solution.y[:, -1]
    final_residual = odes(
        float(solution.t[-1]),
        final_state,
        dict(params),
        stress=dict(stress),
    )
    return {
        "state": final_state,
        "flux": c4_oxygen_flux(final_state, params, stress),
        "max_abs_derivative": float(np.max(np.abs(final_residual))),
        "duration_s": float(duration_s),
        "stress": dict(stress),
    }


def run_mito_stress_protocol(
    *,
    params: Optional[Mapping[str, float]] = None,
    y0: Optional[np.ndarray] = None,
    duration_s: float = 10000.0,
    sample_count: int = 201,
    oligomycin_inhibition: float = 0.9,
    fccp_activation: float = 0.5,
    stationarity_tolerance: float = 1e-6,
) -> Dict[str, object]:
    """Run a sequential, unit-free reduced-model Mito Stress protocol.

    The model contains only mitochondrial oxygen consumption through ``J_C4``;
    accordingly the non-mitochondrial OCR proxy is structurally zero. Oligomycin
    remains active during the FCCP stage, matching the sequential assay design.
    """

    params = dict(DEFAULT_PARAMS if params is None else params)
    initial = CARDIAC_IC.copy() if y0 is None else np.asarray(y0, dtype=float)
    if stationarity_tolerance <= 0:
        raise ValueError("stationarity_tolerance must be positive")
    basal = _run_stage(initial, params, {}, duration_s, sample_count)
    oligomycin_stress = {"oligomycin": float(oligomycin_inhibition)}
    oligomycin = _run_stage(
        basal["state"], params, oligomycin_stress, duration_s, sample_count
    )
    fccp_stress = {
        "oligomycin": float(oligomycin_inhibition),
        "fccp": float(fccp_activation),
    }
    fccp = _run_stage(
        oligomycin["state"], params, fccp_stress, duration_s, sample_count
    )

    basal_flux = float(basal["flux"])
    oligomycin_flux = float(oligomycin["flux"])
    maximal_flux = float(fccp["flux"])
    if min(basal_flux, oligomycin_flux, maximal_flux) <= 0.0:
        raise RuntimeError("Mito Stress OCR proxy must remain positive")

    atp_linked = basal_flux - oligomycin_flux
    proton_leak = oligomycin_flux
    spare = maximal_flux - basal_flux
    metrics = {
        "basal_ocr_proxy": basal_flux,
        "maximal_ocr_proxy": maximal_flux,
        "atp_linked_proxy": atp_linked,
        "proton_leak_proxy": proton_leak,
        "spare_proxy": spare,
        "non_mito_ocr_proxy": 0.0,
    }
    relative = {
        "maximal_to_basal": maximal_flux / basal_flux,
        "spare_to_basal": spare / basal_flux,
        "atp_linked_to_basal": atp_linked / basal_flux,
        "proton_leak_to_basal": proton_leak / basal_flux,
    }
    return {
        "protocol": {
            "duration_s": float(duration_s),
            "sample_count": int(sample_count),
            "oligomycin_inhibition": float(oligomycin_inhibition),
            "fccp_activation": float(fccp_activation),
            "stationarity_tolerance": float(stationarity_tolerance),
            "ocr_proxy": "Complex IV flux J_C4 (mM/s)",
            "stationary": all(
                stage["max_abs_derivative"] <= stationarity_tolerance
                for stage in (basal, oligomycin, fccp)
            ),
            "claim_boundary": (
                "unit-free reduced-model observable; not an absolute Seahorse "
                "OCR prediction"
            ),
        },
        "metrics": metrics,
        "relative_constraints": relative,
        "stages": {
            "basal": {key: value for key, value in basal.items() if key != "state"},
            "oligomycin": {
                key: value for key, value in oligomycin.items() if key != "state"
            },
            "fccp": {key: value for key, value in fccp.items() if key != "state"},
        },
    }
