"""NeurMito-DT Bazil-inspired reduced ODE and initial conditions."""

import numpy as np
from scipy.integrate import solve_ivp
from .bazil2016_ode import (
    DEFAULT_PARAMS, get_conserved,
    rate_C1, rate_C3, rate_C4, rate_CV, rate_leak,
    rate_ANT, rate_MCU, rate_NCLX, rate_GPx, rate_GR
)


# ── State vector indices ───────────────────────────────────────────────────────
IDX = {
    'NADH':   0,
    'QH2':    1,
    'Cred':   2,
    'O2':     3,
    'DPsi':   4,
    'ATP_m':  5,
    'ADP_m':  6,
    'Pi_m':   7,
    'H2O2_m': 8,
    'GSH':    9,
    'Ca_m':   10,
    # TCA intermediates (simplified, 8 vars)
    'ISOC':   11,
    'AKG':    12,
    'SCoA':   13,
    'SUC':    14,
    'FUM':    15,
    'MAL':    16,
    'OAA':    17,
    # Cytosolic
    'ATP_c':  18,
    'ADP_c':  19,
    'Pi_c':   20,
    'Ca_c':   21,
    'H2O2_c': 22,
    # Additional
    'NADPH_m':23,
    'FADH2':  24,
}
N_STATES = 25


# Reduced-model baseline initial conditions. Units are mM for concentrations
# and mV for DPsi; these are not a direct copy of Bazil 2016 Table 2.

CARDIAC_IC = np.zeros(N_STATES)
CARDIAC_IC[IDX['NADH']]    = 0.2970   # mM
CARDIAC_IC[IDX['QH2']]     = 0.6750   # mM (50% of reduced-model Q pool)
CARDIAC_IC[IDX['Cred']]    = 1.35     # mM (50% of cytochrome c pool)
CARDIAC_IC[IDX['O2']]      = 2.56e-2  # mM
CARDIAC_IC[IDX['DPsi']]    = 180.0    # mV
CARDIAC_IC[IDX['ATP_m']]   = 9.0      # mM
CARDIAC_IC[IDX['ADP_m']]   = 0.9      # mM
CARDIAC_IC[IDX['Pi_m']]    = 2.0      # mM
CARDIAC_IC[IDX['H2O2_m']]  = 1.0e-4  # mM
CARDIAC_IC[IDX['GSH']]     = 4.5      # mM
CARDIAC_IC[IDX['Ca_m']]    = 1.0e-4  # mM
CARDIAC_IC[IDX['ISOC']]    = 0.12     # mM
CARDIAC_IC[IDX['AKG']]     = 0.30     # mM
CARDIAC_IC[IDX['SCoA']]    = 0.05     # mM
CARDIAC_IC[IDX['SUC']]     = 0.50     # mM
CARDIAC_IC[IDX['FUM']]     = 0.10     # mM
CARDIAC_IC[IDX['MAL']]     = 0.20     # mM
CARDIAC_IC[IDX['OAA']]     = 0.01     # mM
CARDIAC_IC[IDX['ATP_c']]   = 8.0      # mM
CARDIAC_IC[IDX['ADP_c']]   = 0.8      # mM
CARDIAC_IC[IDX['Pi_c']]    = 5.0      # mM
CARDIAC_IC[IDX['Ca_c']]    = 1.0e-4  # mM
CARDIAC_IC[IDX['H2O2_c']]  = 5.0e-5  # mM
CARDIAC_IC[IDX['NADPH_m']] = 0.50     # mM
CARDIAC_IC[IDX['FADH2']]   = 0.05     # mM


def odes(t, y, p, Ca_c_input=None, stress=None):
    """
    Full ODE right-hand side for NeurMito-DT.

    Parameters
    ----------
    t : float
        Time (s)
    y : array (N_STATES,)
        State vector
    p : dict
        Parameters
    Ca_c_input : callable or None
        Time-varying cytosolic Ca2+ input function Ca_c(t)
    stress : dict or None
        Stress modifiers, e.g.:
          {'rotenone': 0.5}   -> 50% C1 inhibition
          {'paraquat': 10.0}  -> concentration-indexed ROS amplification
          {'hypoxia': 0.2}    -> O2_ext *= 0.2
          {'oligomycin': 0.5} -> 50% ATP synthase inhibition
          {'fccp': 0.5}       -> increased proton conductance
    """
    # Unpack state
    NADH   = max(y[IDX['NADH']],   1e-10)
    QH2    = max(y[IDX['QH2']],    1e-10)
    Cred   = max(y[IDX['Cred']],   1e-10)
    O2     = max(y[IDX['O2']],     1e-10)
    DPsi   = y[IDX['DPsi']]
    ATP_m  = max(y[IDX['ATP_m']],  1e-10)
    ADP_m  = max(y[IDX['ADP_m']],  1e-10)
    Pi_m   = max(y[IDX['Pi_m']],   1e-10)
    H2O2_m = max(y[IDX['H2O2_m']], 1e-10)
    GSH    = max(y[IDX['GSH']],    1e-10)
    Ca_m   = max(y[IDX['Ca_m']],   1e-10)
    OAA    = max(y[IDX['OAA']],    1e-10)
    MAL    = max(y[IDX['MAL']],    1e-10)
    ATP_c  = max(y[IDX['ATP_c']],  1e-10)
    ADP_c  = max(y[IDX['ADP_c']],  1e-10)
    Pi_c   = max(y[IDX['Pi_c']],   1e-10)
    H2O2_c = max(y[IDX['H2O2_c']], 1e-10)
    NADPH_m = max(y[IDX['NADPH_m']], 1e-10)

    # Cytosolic Ca2+ (can be externally driven)
    if Ca_c_input is not None:
        Ca_c = Ca_c_input(t)
    else:
        Ca_c = max(y[IDX['Ca_c']], 1e-10)

    # Apply stress modifiers
    p_eff = dict(p)
    if stress:
        if 'rotenone' in stress:
            inhibition = np.clip(float(stress['rotenone']), 0.0, 1.0)
            p_eff['Vmax_C1'] *= 1.0 - inhibition
        if 'paraquat' in stress:
            concentration = max(float(stress['paraquat']), 0.0)
            p_eff['k_ROS_C1'] *= 1.0 + 2.0 * concentration
            p_eff['k_ROS_C3'] *= 1.0 + 1.0 * concentration
        if 'hypoxia' in stress:
            fraction = np.clip(float(stress['hypoxia']), 0.0, 1.0)
            p_eff['O2_ext'] *= fraction
        if 'oligomycin' in stress:
            inhibition = np.clip(float(stress['oligomycin']), 0.0, 1.0)
            p_eff['Vmax_CV'] *= 1.0 - inhibition
        if 'fccp' in stress:
            activation = max(float(stress['fccp']), 0.0)
            p_eff['g_H'] *= 1.0 + 20.0 * activation

    # ── Reaction fluxes ──────────────────────────────────────────────────────
    J_C1   = rate_C1(NADH, QH2, DPsi, H2O2_m, p_eff)
    J_C3   = rate_C3(QH2, Cred, DPsi, p_eff)
    J_C4   = rate_C4(Cred, O2, DPsi, p_eff)
    J_CV   = rate_CV(ADP_m, Pi_m, DPsi, p_eff)
    basal_leak = rate_leak(DPsi, p_eff)
    ros_leak = (p_eff['ROS_leak_gain'] * H2O2_m
                / (H2O2_m + p_eff['Km_ROS_leak']))
    J_leak = basal_leak * (1.0 + ros_leak)
    J_ANT  = rate_ANT(ATP_m, ADP_c, p_eff, DPsi=DPsi)
    J_MCU  = rate_MCU(Ca_c, DPsi, p_eff)
    J_NCLX = rate_NCLX(Ca_m, p_eff)
    J_GPx  = rate_GPx(H2O2_m, GSH, p_eff)
    J_GR   = rate_GR(
        (p_eff['GSH_total'] - GSH) / 2.0,
        p_eff,
        NADPH=NADPH_m,
    )
    J_ATPase = (p_eff['Vmax_ATPase'] * ATP_c
                / (ATP_c + p_eff['Km_ATPase']))

    # Closed reduced TCA cycle. Each intermediate appears once as a
    # substrate and once as a product, so their total is conserved.
    Km_tca = p_eff['Km_TCA']
    NAD = max(p_eff['NAD_total'] - NADH, 0.0)
    redox_acceptor = NAD / (NAD + 0.1)
    Q = max(p_eff['Q_total'] - QH2, 0.0)
    q_acceptor = Q / (Q + p_eff['Km_Q_C1'])

    ISOC = max(y[IDX['ISOC']], 0.0)
    AKG = max(y[IDX['AKG']], 0.0)
    SCoA = max(y[IDX['SCoA']], 0.0)
    SUC = max(y[IDX['SUC']], 0.0)
    FUM = max(y[IDX['FUM']], 0.0)

    J_CS = p_eff['Vmax_CS'] * OAA / (OAA + 0.05)
    J_IDH = (p_eff['Vmax_IDH'] * ISOC / (ISOC + Km_tca)
             * redox_acceptor)
    J_KGDH = (p_eff['Vmax_KGDH'] * AKG / (AKG + Km_tca)
              * redox_acceptor)
    J_SCS = p_eff['Vmax_SCS'] * SCoA / (SCoA + Km_tca)
    J_SDH = (p_eff['Vmax_SDH'] * SUC / (SUC + 0.5)
             * q_acceptor)
    J_FH = p_eff['Vmax_FH'] * FUM / (FUM + Km_tca)
    J_MDH = (p_eff['Vmax_MDH'] * MAL / (MAL + Km_tca)
             * redox_acceptor)
    J_NADH_prod = J_IDH + J_KGDH + J_MDH

    # ROS production (fraction of electron flux)
    J_ROS_C1 = p_eff['k_ROS_C1'] * J_C1
    J_ROS_C3 = p_eff['k_ROS_C3'] * J_C3

    # H2O2 diffusion matrix→cytosol
    k_diff_H2O2 = 0.01  # s^-1
    J_H2O2_diff = k_diff_H2O2 * (H2O2_m - H2O2_c)

    # Effective charge balance follows the Bazil convention: C1 and C4
    # contribute four charges per turnover, C3 contributes two, while ATP
    # synthase, ANT, leak and MCU dissipate the gradient.
    n_H = p_eff['n_H_CV']

    # ── ODEs ─────────────────────────────────────────────────────────────────
    dy = np.zeros(N_STATES)

    # NADH: produced by TCA, consumed by C1
    dy[IDX['NADH']]   = J_NADH_prod - J_C1

    # QH2: produced by C1 and C2/SDH, consumed by C3.
    dy[IDX['QH2']]    = J_C1 + J_SDH - J_C3

    # C3 produces two reduced cytochrome c per turnover; C4 consumes four.
    dy[IDX['Cred']]   = 2.0 * J_C3 - 4.0 * J_C4

    # O2: consumed by C4, replenished from extracellular
    k_O2_in = p_eff['k_O2_in']
    dy[IDX['O2']]     = -J_C4 + k_O2_in * (p_eff['O2_ext'] - O2)
    # Keep the extracellularly supplied O2 pool non-negative at the numerical
    # boundary.  Without this guard, an O2_ext=0 stress can overshoot into
    # negative concentration values during stiff integration.
    if y[IDX['O2']] <= 0.0 and dy[IDX['O2']] < 0.0:
        dy[IDX['O2']] = 0.0

    # Membrane potential
    dy[IDX['DPsi']]   = (1.0 / p_eff['C_m']) * (
        4.0 * J_C1 + 2.0 * J_C3 + 4.0 * J_C4
        - n_H * J_CV - J_ANT - J_leak
        - 2.0 * J_MCU  # Ca2+ uniporter (electrogenic)
    )

    # Matrix ATP/ADP
    dy[IDX['ATP_m']]  = J_CV - J_ANT
    dy[IDX['ADP_m']]  = J_ANT - J_CV

    # Matrix Pi (simplified: Pi consumed by CV, replenished by Pi_c)
    k_Pi_in = 0.01
    dy[IDX['Pi_m']]   = -J_CV + k_Pi_in * (Pi_c - Pi_m)

    # Matrix H2O2
    dy[IDX['H2O2_m']] = J_ROS_C1 + J_ROS_C3 - J_GPx - J_H2O2_diff

    # GSH (reduced glutathione)
    dy[IDX['GSH']]    = 2.0 * J_GR - 2.0 * J_GPx

    # Matrix Ca2+
    dy[IDX['Ca_m']]   = J_MCU - J_NCLX

    dy[IDX['ISOC']]   = J_CS - J_IDH
    dy[IDX['AKG']]    = J_IDH - J_KGDH
    dy[IDX['SCoA']]   = J_KGDH - J_SCS
    dy[IDX['SUC']]    = J_SCS - J_SDH
    dy[IDX['FUM']]    = J_SDH - J_FH
    dy[IDX['MAL']]    = J_FH - J_MDH
    dy[IDX['OAA']]    = J_MDH - J_CS

    # Cytosolic ATP demand closes the adenine-nucleotide cycle and prevents
    # the model from drifting to a zero-workload state with depleted ADP.
    dy[IDX['ATP_c']]  = J_ANT - J_ATPase
    dy[IDX['ADP_c']]  = -J_ANT + J_ATPase
    dy[IDX['Pi_c']]   = -k_Pi_in * (Pi_c - Pi_m) + J_ATPase

    # Cytosolic Ca2+ (if not externally driven)
    if Ca_c_input is None:
        dy[IDX['Ca_c']] = -(J_MCU - J_NCLX) / p_eff['Vm_Vc']

    # Cytosolic H2O2
    k_GPx_c = 5e-3
    dy[IDX['H2O2_c']] = J_H2O2_diff - k_GPx_c * H2O2_c

    # NADPH reporter with a finite regeneration capacity.
    dy[IDX['NADPH_m']] = (
        p_eff['k_NADPH_regen'] * (p_eff['NADPH_target'] - NADPH_m)
        - J_GR
    )

    # FADH2 is retained as a bounded redox reporter rather than an
    # independent mass-producing pathway.
    fad_target = p_eff['FAD_total'] * SUC / (SUC + 0.5)
    dy[IDX['FADH2']] = p_eff['k_FAD_redox'] * (
        fad_target - max(y[IDX['FADH2']], 0.0)
    )

    return dy


def simulate(t_span, t_eval, y0=None, params=None, Ca_c_input=None, stress=None):
    """
    Run NeurMito-DT simulation.

    Returns
    -------
    sol : OdeResult
        scipy solve_ivp result with .t and .y attributes
    """
    if y0 is None:
        y0 = CARDIAC_IC.copy()
    if params is None:
        params = DEFAULT_PARAMS.copy()

    sol = solve_ivp(
        fun=lambda t, y: odes(t, y, params, Ca_c_input, stress),
        t_span=t_span,
        y0=y0,
        t_eval=t_eval,
        method='LSODA',       # stiff solver
        rtol=1e-6,
        atol=1e-9,
        max_step=0.5,
    )
    return sol
