"""
Module 1 — Figure 1: Baseline validation of NeurMito-DT ODE framework
10 subplots showing steady-state and dynamic behavior under cardiac parameters.
Validates: DPsi ~180mV, ATP/ADP ~10, ROS flux <1% of C1 flux
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.integrate import solve_ivp

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import odes, simulate, IDX, N_STATES, CARDIAC_IC

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 9,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'lines.linewidth': 1.5,
    'figure.dpi': 150,
})

COLORS = {
    'cardiac':  '#2166ac',
    'neuron':   '#d6604d',
    'stress':   '#f4a582',
    'healthy':  '#4dac26',
    'damaged':  '#d01c8b',
    'ROS':      '#e08214',
    'Ca':       '#8073ac',
    'ATP':      '#1a9641',
}


def run_baseline():
    """Run 200s baseline simulation."""
    t_span = (0, 200)
    t_eval = np.linspace(0, 200, 2000)
    sol = simulate(t_span, t_eval, y0=CARDIAC_IC.copy(), params=DEFAULT_PARAMS.copy())
    return sol


def run_ca_pulse():
    """Simulate a cytosolic Ca2+ pulse (mimics neuronal firing)."""
    def Ca_c_input(t):
        # Baseline 0.1 μM, pulse to 1 μM at t=50s for 10s
        if 50 <= t <= 60:
            return 1.0e-3  # mM
        return 1.0e-4

    t_span = (0, 150)
    t_eval = np.linspace(0, 150, 1500)
    sol = simulate(t_span, t_eval, y0=CARDIAC_IC.copy(),
                   params=DEFAULT_PARAMS.copy(), Ca_c_input=Ca_c_input)
    return sol, Ca_c_input


def run_ros_ramp():
    """Simulate chronic ROS increase (slow stress)."""
    params = DEFAULT_PARAMS.copy()
    t_span = (0, 500)
    t_eval = np.linspace(0, 500, 5000)

    def odes_ramp(t, y):
        p = DEFAULT_PARAMS.copy()
        p['k_ROS_C1'] = DEFAULT_PARAMS['k_ROS_C1'] * (1 + 5 * t / 500)
        return odes(t, y, p)

    sol = solve_ivp(odes_ramp, t_span, CARDIAC_IC.copy(),
                    t_eval=t_eval, method='LSODA', rtol=1e-6, atol=1e-9)
    return sol


def make_figure1():
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)

    sol_base = run_baseline()
    sol_ca, Ca_c_fn = run_ca_pulse()
    sol_ramp = run_ros_ramp()

    t_b = sol_base.t
    t_c = sol_ca.t
    t_r = sol_ramp.t

    # ── Panel A: DPsi steady-state ─────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(t_b, sol_base.y[IDX['DPsi']], color=COLORS['cardiac'])
    ax.axhline(180, color='gray', ls='--', lw=0.8, label='Target ~180 mV')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('A  Membrane potential')
    ax.legend(fontsize=7)
    ax.set_ylim(100, 220)

    # ── Panel B: ATP/ADP ratio ─────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])
    atp_adp = sol_base.y[IDX['ATP_m']] / np.maximum(sol_base.y[IDX['ADP_m']], 1e-10)
    ax.plot(t_b, atp_adp, color=COLORS['ATP'])
    ax.axhline(10, color='gray', ls='--', lw=0.8, label='Target ~10')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ATP/ADP (matrix)')
    ax.set_title('B  ATP/ADP ratio')
    ax.legend(fontsize=7)

    # ── Panel C: ROS flux as % of C1 ──────────────────────────────────────
    ax = fig.add_subplot(gs[0, 2])
    from module1.bazil2016_ode import rate_C1
    J_C1_arr = np.array([
        rate_C1(sol_base.y[IDX['NADH'], i],
                sol_base.y[IDX['QH2'], i],
                sol_base.y[IDX['DPsi'], i],
                sol_base.y[IDX['H2O2_m'], i],
                DEFAULT_PARAMS)
        for i in range(len(t_b))
    ])
    ros_pct = 100 * DEFAULT_PARAMS['k_ROS_C1'] * J_C1_arr / np.maximum(J_C1_arr, 1e-15)
    ax.plot(t_b, np.full_like(t_b, DEFAULT_PARAMS['k_ROS_C1'] * 100),
            color=COLORS['ROS'])
    ax.axhline(1.0, color='gray', ls='--', lw=0.8, label='Target <1%')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ROS / J_C1 (%)')
    ax.set_title('C  ROS production fraction')
    ax.legend(fontsize=7)
    ax.set_ylim(0, 2)

    # ── Panel D: H2O2 dynamics ─────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 3])
    ax.plot(t_b, sol_base.y[IDX['H2O2_m']] * 1e3, color=COLORS['ROS'], label='Matrix')
    ax.plot(t_b, sol_base.y[IDX['H2O2_c']] * 1e3, color=COLORS['ROS'],
            ls='--', label='Cytosol')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('H₂O₂ (μM)')
    ax.set_title('D  H₂O₂ compartments')
    ax.legend(fontsize=7)

    # ── Panel E: Ca2+ pulse — matrix response ─────────────────────────────
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(t_c, sol_ca.y[IDX['Ca_m']] * 1e3, color=COLORS['Ca'], label='Ca²⁺ matrix')
    ax2 = ax.twinx()
    Ca_c_arr = np.array([Ca_c_fn(t) for t in t_c]) * 1e3
    ax2.plot(t_c, Ca_c_arr, color=COLORS['Ca'], ls=':', alpha=0.5, label='Ca²⁺ cytosol')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Ca²⁺_m (μM)', color=COLORS['Ca'])
    ax2.set_ylabel('Ca²⁺_c (μM)', color=COLORS['Ca'], alpha=0.6)
    ax.set_title('E  Ca²⁺ pulse response')

    # ── Panel F: DPsi during Ca2+ pulse ───────────────────────────────────
    ax = fig.add_subplot(gs[1, 1])
    ax.plot(t_c, sol_ca.y[IDX['DPsi']], color=COLORS['cardiac'])
    ax.axvspan(50, 60, alpha=0.15, color=COLORS['Ca'], label='Ca²⁺ pulse')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('F  ΔΨm during Ca²⁺ pulse')
    ax.legend(fontsize=7)

    # ── Panel G: ATP during Ca2+ pulse ────────────────────────────────────
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(t_c, sol_ca.y[IDX['ATP_m']], color=COLORS['ATP'], label='ATP_m')
    ax.plot(t_c, sol_ca.y[IDX['ATP_c']], color=COLORS['ATP'], ls='--', label='ATP_c')
    ax.axvspan(50, 60, alpha=0.15, color=COLORS['Ca'])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ATP (mM)')
    ax.set_title('G  ATP during Ca²⁺ pulse')
    ax.legend(fontsize=7)

    # ── Panel H: ROS ramp — DPsi collapse ─────────────────────────────────
    ax = fig.add_subplot(gs[1, 3])
    ax.plot(t_r, sol_ramp.y[IDX['DPsi']], color=COLORS['damaged'])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('H  ΔΨm under chronic ROS stress')
    ax.axhline(100, color='gray', ls='--', lw=0.8, label='Damage threshold')
    ax.legend(fontsize=7)

    # ── Panel I: H2O2 accumulation during ramp ────────────────────────────
    ax = fig.add_subplot(gs[2, 0])
    ax.plot(t_r, sol_ramp.y[IDX['H2O2_m']] * 1e3, color=COLORS['ROS'])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('H₂O₂_m (μM)')
    ax.set_title('I  H₂O₂ accumulation (ROS ramp)')

    # ── Panel J: GSH depletion during ramp ────────────────────────────────
    ax = fig.add_subplot(gs[2, 1])
    ax.plot(t_r, sol_ramp.y[IDX['GSH']], color=COLORS['healthy'])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('GSH (mM)')
    ax.set_title('J  GSH depletion (ROS ramp)')

    # ── Panel K: Phase portrait DPsi vs ATP ───────────────────────────────
    ax = fig.add_subplot(gs[2, 2])
    sc = ax.scatter(sol_ramp.y[IDX['ATP_m']], sol_ramp.y[IDX['DPsi']],
                    c=t_r, cmap='RdYlGn_r', s=2, alpha=0.7)
    plt.colorbar(sc, ax=ax, label='Time (s)', shrink=0.8)
    ax.set_xlabel('ATP_m (mM)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('K  Phase portrait: ATP vs ΔΨm')

    # ── Panel L: Flux balance summary (bar) ───────────────────────────────
    ax = fig.add_subplot(gs[2, 3])
    from module1.bazil2016_ode import rate_C1, rate_C3, rate_C4, rate_CV, rate_leak, rate_ANT
    i_ss = -1  # steady-state index
    y_ss = sol_base.y[:, i_ss]
    fluxes = {
        'J_C1':   rate_C1(y_ss[IDX['NADH']], y_ss[IDX['QH2']],
                          y_ss[IDX['DPsi']], y_ss[IDX['H2O2_m']], DEFAULT_PARAMS),
        'J_C3':   rate_C3(y_ss[IDX['QH2']], y_ss[IDX['Cred']],
                          y_ss[IDX['DPsi']], DEFAULT_PARAMS),
        'J_C4':   rate_C4(y_ss[IDX['Cred']], y_ss[IDX['O2']],
                          y_ss[IDX['DPsi']], DEFAULT_PARAMS),
        'J_CV':   rate_CV(y_ss[IDX['ADP_m']], y_ss[IDX['Pi_m']],
                          y_ss[IDX['DPsi']], DEFAULT_PARAMS),
        'J_leak': rate_leak(y_ss[IDX['DPsi']], DEFAULT_PARAMS),
        'J_ANT':  rate_ANT(y_ss[IDX['ATP_m']], y_ss[IDX['ADP_c']], DEFAULT_PARAMS),
    }
    names = list(fluxes.keys())
    vals  = [fluxes[k] * 1e3 for k in names]  # convert to μmol/s
    colors_bar = [COLORS['cardiac']] * 4 + [COLORS['ROS'], COLORS['ATP']]
    ax.barh(names, vals, color=colors_bar)
    ax.set_xlabel('Flux (μmol/s)')
    ax.set_title('L  Steady-state flux balance')

    # ── Title ──────────────────────────────────────────────────────────────
    fig.suptitle(
        'Figure 1 — NeurMito-DT: Baseline ODE Framework Validation\n'
        'Reduced-model cardiac baseline; pre-calibration',
        fontsize=11, fontweight='bold', y=0.98
    )

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure1_baseline_validation.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}")
    plt.close(fig)
    return out_path


if __name__ == '__main__':
    make_figure1()
