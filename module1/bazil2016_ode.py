"""
Bazil-inspired reduced OXPHOS-ROS-ATP ODE model.

This module is not a line-by-line reproduction of the Bazil 2016 DAE model.
It keeps a reduced state space and phenomenological rate laws for NeurMito-DT.
The model identity and deviations are documented in
``refine-logs/R004A_BAZIL_MODEL_AUDIT.md``.

Reference: Bazil JN et al., Biophys J 2016;110(4):962-971.

State variables exposed by ``neurmito_system`` (25 total):
  Bioenergetics: NADH, QH2, Cred, O2, DPsi, ATP_m, ADP_m, Pi_m
  ROS: H2O2_m, GSH, GSSG
  Calcium: Ca_m
  TCA intermediates: ISOC, AKG, SCoA, SUC, FUM, MAL, OAA
  Cofactors/reporters: FADH2
  Cytosol: ATP_c, ADP_c, Pi_c, Ca_c, H2O2_c, NADPH_m
"""

from typing import Dict, Tuple
import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp


# These are reduced-model defaults. Values that differ from the Bazil
# supplement must not be described as direct Bazil parameters.

# Type alias for parameter dictionary
ParamDict = Dict[str, float]

DEFAULT_PARAMS: ParamDict = {
    # Respiratory chain
    'Vmax_C1':    9.0e-2,   # Complex I max rate (mM/s)
    'Km_NADH':    1.0e-2,   # NADH Km for C1 (mM)
    'Km_Q_C1':    1.0e-1,   # Q Km for C1 (mM)
    'Ki_H2O2':    1.0e-2,   # H2O2 inhibition of C1 (mM)

    'Vmax_C3':    4.5e-2,   # Complex III max rate (mM/s)
    'Km_QH2':     5.0e-2,   # QH2 Km for C3 (mM)
    'Km_Cox_C3':  2.0e-3,   # Cyt c (ox) Km for C3 (mM)

    'Vmax_C4':    6.0e-2,   # Complex IV max rate (mM/s)
    'Km_Cred':    1.62e-1,  # Cyt c (red) Km for C4 (mM)
    'Km_O2':      1.2e-4,   # O2 Km for C4 (mM)

    # Effective thermodynamic backpressure for the reduced ETC rates.
    'DPsi_ETC_half': 165.0, # 50% ETC activity under backpressure (mV)
    'DPsi_ETC_slope': 12.0, # Backpressure transition width (mV)

    # ATP synthase (Complex V)
    'Vmax_CV':    3.0e-2,   # Max ATP synthesis rate (mM/s)
    'Km_ADP_CV':  2.0e-1,   # ADP Km (mM)
    'Km_Pi_CV':   5.0e-1,   # Pi Km (mM)
    'n_H_CV':     2.7,      # H+/ATP stoichiometry
    'DPsi_CV_half': 120.0,  # 50% ATP synthase activation (mV)
    'DPsi_CV_slope': 10.0,  # ATP synthase activation width (mV)

    # Proton leak
    'g_H':        2.0e-4,   # Proton conductance (mM/s/mV)
    'DPsi_0':     0.0,      # Reference potential (mV)
    'ROS_leak_gain': 1.0,   # Maximum fractional ROS-induced leak increase
    'Km_ROS_leak': 5.0e-5,  # H2O2 midpoint for leak activation (mM)

    # ANT (adenine nucleotide translocator)
    'Vmax_ANT':   5.0e-2,   # Max ANT rate (mM/s)
    'Km_ADP_ANT': 1.0e-1,   # ADP_c Km (mM)
    'Km_ATP_ANT': 5.0e-1,   # ATP_m Km (mM)
    'DPsi_ANT_half': 100.0, # 50% ANT activation (mV)
    'DPsi_ANT_slope': 12.0, # ANT activation width (mV)

    # Cytosolic ATP demand closes the ATP/ADP/Pi cycle.
    'Vmax_ATPase':  2.0e-2, # Cytosolic ATP hydrolysis (mM/s)
    'Km_ATPase':    5.0e-1, # ATP Km for demand (mM)

    # TCA cycle
    'Vmax_IDH':   2.0e-2,   # Isocitrate dehydrogenase (mM/s)
    'Vmax_KGDH':  1.5e-2,   # alpha-KG dehydrogenase (mM/s)
    'Vmax_SDH':   1.0e-2,   # Succinate dehydrogenase (mM/s)
    'Vmax_MDH':   3.0e-2,   # Malate dehydrogenase (mM/s)
    'Vmax_CS':    2.5e-2,   # Citrate synthase (mM/s)
    'Vmax_SCS':   1.5e-2,   # Succinyl-CoA synthetase (mM/s)
    'Vmax_FH':    2.0e-2,   # Fumarase (mM/s)
    'Km_TCA':     1.0e-1,   # Shared reduced-model TCA Km (mM)

    # ROS production and scavenging
    'k_ROS_C1':   1.0e-4,   # ROS production rate at C1 (fraction of C1 flux)
    'k_ROS_C3':   5.0e-5,   # ROS production rate at C3
    'Vmax_GPx':   1.0e-3,   # Glutathione peroxidase (mM/s)
    'Km_H2O2_GPx':1.0e-3,   # H2O2 Km for GPx (mM)
    'Km_GSH_GPx': 5.0e-1,   # GSH Km for GPx (mM)
    'Vmax_GR':    5.0e-3,   # Glutathione reductase (mM/s)
    'Km_GSSG':    5.0e-2,   # GSSG Km for GR (mM)
    'Km_NADPH_GR':5.0e-2,   # NADPH Km for GR (mM)
    'NADPH_target': 5.0e-1, # Reduced-model NADPH set point (mM)
    'k_NADPH_regen': 2.0e-2,# NADPH regeneration rate (s^-1)

    # Calcium uniporter (MCU)
    'Vmax_MCU':   1.0e-3,   # Max Ca2+ uptake (mM/s)
    'Km_Ca_MCU':  5.0e-3,   # Ca2+ Km for MCU (mM)
    'n_MCU':      2.0,      # Hill coefficient

    # NCLX (Na+/Ca2+ exchanger)
    'Vmax_NCLX':  5.0e-4,   # Max Ca2+ efflux (mM/s)
    'Km_Ca_NCLX': 1.0e-2,   # Ca2+ Km for NCLX (mM)

    # Fixed concentrations
    'O2_ext':     2.56e-2,  # Extracellular O2 (mM, ~5% O2)
    'k_O2_in':    2.0,      # O2 exchange with the external reservoir (s^-1)
    'NAD_total':  2.97,     # Total NAD pool (mM)
    'Q_total':    1.35,     # Reduced-model ubiquinone pool (mM)
    'Cc_total':   2.7,      # Total cytochrome c pool (mM)
    'GSH_total':  5.0,      # Total glutathione pool (mM)
    'FAD_total':  1.0e-1,   # Reduced-model FAD reporter pool (mM)
    'k_FAD_redox':1.0e-1,   # FAD reporter relaxation rate (s^-1)

    # Membrane capacitance
    'C_m':        6.76e-3,  # IMM capacitance after M-to-mM conversion

    # Volume ratios
    'Vm_Vc':      0.153,    # Mitochondrial/cytosolic volume ratio
}


MODEL_NAME = 'NeurMito-DT Bazil-inspired reduced OXPHOS model'
MODEL_REFERENCE = 'Bazil et al., Biophys J 2016;110:962-971'


def _positive(value: float) -> float:
    """Return a non-negative substrate value for kinetic expressions."""
    return max(float(value), 0.0)


def _sigmoid(value: float) -> float:
    """Numerically stable logistic function."""
    value = float(np.clip(value, -60.0, 60.0))
    return 1.0 / (1.0 + np.exp(-value))


def voltage_backpressure(DPsi: float, p: ParamDict) -> float:
    """Effective ETC activity remaining at a given membrane potential."""
    return _sigmoid(
        (p['DPsi_ETC_half'] - DPsi) / p['DPsi_ETC_slope']
    )


# ── Conserved quantities ───────────────────────────────────────────────────────

def get_conserved(
    y: NDArray[np.float64],
    p: ParamDict
) -> Tuple[float, float, float, float]:
    """
    Compute conserved pool complements.

    Parameters
    ----------
    y : ndarray
        State vector (29 elements)
    p : dict
        Parameter dictionary

    Returns
    -------
    NAD : float
        Oxidized NAD concentration (mM)
    Q : float
        Oxidized ubiquinone concentration (mM)
    Cox : float
        Oxidized cytochrome c concentration (mM)
    GSSG : float
        Oxidized glutathione concentration (mM)
    """
    NADH = _positive(y[0])
    QH2  = _positive(y[1])
    Cred = _positive(y[2])
    GSH  = _positive(y[9])

    NAD   = max(p['NAD_total'] - NADH, 0.0)
    Q     = max(p['Q_total']   - QH2, 0.0)
    Cox   = max(p['Cc_total']  - Cred, 0.0)
    GSSG  = max((p['GSH_total'] - GSH) / 2.0, 0.0)

    return NAD, Q, Cox, GSSG


# ── Reaction rates ─────────────────────────────────────────────────────────────

def rate_C1(
    NADH: float,
    QH2: float,
    DPsi: float,
    H2O2: float,
    p: ParamDict
) -> float:
    """
    Complex I reaction rate: NADH + Q → NAD + QH2, pumps 4H+

    Parameters
    ----------
    NADH : float
        NADH concentration (mM)
    QH2 : float
        Reduced ubiquinone concentration (mM)
    DPsi : float
        Membrane potential (mV)
    H2O2 : float
        Hydrogen peroxide concentration (mM)
    p : dict
        Parameter dictionary

    Returns
    -------
    float
        Complex I flux (mM/s)
    """
    NAD, Q, _, _ = get_conserved(
        np.array([NADH, QH2, 0, 0, DPsi, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        p
    )
    NADH = _positive(NADH)
    H2O2 = _positive(H2O2)
    inh = 1.0 / (1.0 + H2O2 / p['Ki_H2O2'])
    v = (p['Vmax_C1']
         * (NADH / (NADH + p['Km_NADH']))
         * (Q    / (Q    + p['Km_Q_C1']))
         * inh
         * voltage_backpressure(DPsi, p))
    return v


def rate_C3(
    QH2: float,
    Cred: float,
    DPsi: float,
    p: ParamDict
) -> float:
    """
    Complex III reaction rate: QH2 + 2Cyt_c(ox) → Q + 2Cyt_c(red), pumps 4H+

    Parameters
    ----------
    QH2 : float
        Reduced ubiquinone concentration (mM)
    Cred : float
        Reduced cytochrome c concentration (mM)
    DPsi : float
        Membrane potential (mV)
    p : dict
        Parameter dictionary

    Returns
    -------
    float
        Complex III flux (mM/s)
    """
    _, _, Cox, _ = get_conserved(
        np.array([0, QH2, Cred, 0, DPsi, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        p
    )
    QH2 = _positive(QH2)
    v = (p['Vmax_C3']
         * (QH2 / (QH2 + p['Km_QH2']))
         * (Cox / (Cox + p['Km_Cox_C3']))
         * voltage_backpressure(DPsi, p))
    return v


def rate_C4(
    Cred: float,
    O2: float,
    DPsi: float,
    p: ParamDict
) -> float:
    """
    Complex IV reaction rate: 4Cyt_c(red) + O2 → 4Cyt_c(ox) + H2O, pumps 4H+

    Parameters
    ----------
    Cred : float
        Reduced cytochrome c concentration (mM)
    O2 : float
        Oxygen concentration (mM)
    DPsi : float
        Membrane potential (mV)
    p : dict
        Parameter dictionary

    Returns
    -------
    float
        Complex IV flux (mM/s)
    """
    Cred = _positive(Cred)
    O2 = _positive(O2)
    v = (p['Vmax_C4']
         * (Cred / (Cred + p['Km_Cred']))
         * (O2   / (O2   + p['Km_O2']))
         * voltage_backpressure(DPsi, p))
    return v


def rate_CV(
    ADP_m: float,
    Pi_m: float,
    DPsi: float,
    p: ParamDict
) -> float:
    """
    Complex V (ATP synthase) reaction rate: ADP + Pi → ATP

    Parameters
    ----------
    ADP_m : float
        Mitochondrial ADP concentration (mM)
    Pi_m : float
        Mitochondrial Pi concentration (mM)
    DPsi : float
        Membrane potential (mV)
    p : dict
        Parameter dictionary

    Returns
    -------
    float
        ATP synthase flux (mM/s)
    """
    ADP_m = _positive(ADP_m)
    Pi_m = _positive(Pi_m)
    voltage_activation = _sigmoid(
        (DPsi - p['DPsi_CV_half']) / p['DPsi_CV_slope']
    )
    v = (p['Vmax_CV']
         * (ADP_m / (ADP_m + p['Km_ADP_CV']))
         * (Pi_m  / (Pi_m  + p['Km_Pi_CV']))
         * voltage_activation)
    return v


def rate_leak(DPsi, p):
    """Proton leak across inner membrane."""
    return p['g_H'] * max(DPsi - p['DPsi_0'], 0.0)


def rate_ANT(ATP_m, ADP_c, p, DPsi=None):
    """ANT: exchanges matrix ATP for cytosolic ADP."""
    ATP_m = _positive(ATP_m)
    ADP_c = _positive(ADP_c)
    voltage_activation = 1.0
    if DPsi is not None:
        voltage_activation = _sigmoid(
            (DPsi - p['DPsi_ANT_half']) / p['DPsi_ANT_slope']
        )
    v = (p['Vmax_ANT']
         * (ADP_c / (ADP_c + p['Km_ADP_ANT']))
         * (ATP_m / (ATP_m + p['Km_ATP_ANT']))
         * voltage_activation)
    return v


def rate_MCU(Ca_c, DPsi, p):
    """Mitochondrial calcium uniporter."""
    Ca_c = _positive(Ca_c)
    voltage_activation = np.clip(DPsi / 180.0, 0.0, 1.5)
    v = (p['Vmax_MCU']
         * (Ca_c**p['n_MCU'])
         / (Ca_c**p['n_MCU'] + p['Km_Ca_MCU']**p['n_MCU'])
         * voltage_activation)
    return v


def rate_NCLX(Ca_m, p):
    """Na+/Ca2+ exchanger (Ca2+ efflux)."""
    Ca_m = _positive(Ca_m)
    v = p['Vmax_NCLX'] * Ca_m / (Ca_m + p['Km_Ca_NCLX'])
    return v


def rate_GPx(H2O2, GSH, p):
    """Glutathione peroxidase: H2O2 + 2GSH → GSSG + 2H2O"""
    H2O2 = _positive(H2O2)
    GSH = _positive(GSH)
    v = (p['Vmax_GPx']
         * H2O2 / (H2O2 + p['Km_H2O2_GPx'])
         * GSH / (GSH + p['Km_GSH_GPx']))
    return v


def rate_GR(GSSG, p, NADPH=None):
    """Glutathione reductase: GSSG + NADPH → 2GSH"""
    GSSG = _positive(GSSG)
    nadph_factor = 1.0
    if NADPH is not None:
        NADPH = _positive(NADPH)
        nadph_factor = NADPH / (NADPH + p['Km_NADPH_GR'])
    v = (p['Vmax_GR'] * GSSG / (GSSG + p['Km_GSSG'])
         * nadph_factor)
    return v


def rate_TCA(NADH, p):
    """Legacy lumped NADH-production helper retained for compatibility."""
    NAD = max(p['NAD_total'] - _positive(NADH), 0.0)
    v_tca = p['Vmax_IDH'] * NAD / (NAD + 0.1)
    return v_tca
