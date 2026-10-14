"""
Module 3 — Figure 6: Bistability & Critical Transitions
10 subplots: Hysteresis, critical slowing down, early warnings
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Style
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
    'healthy': '#4dac26',
    'stressed': '#f4a582',
    'critical': '#d01c8b',
    'collapsed': '#636363',
    'warning': '#fec44f',
    'boundary': '#2166ac',
}


def make_figure6():
    """
    Generate Figure 6: Bistability & Critical Transitions
    """
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)

    # ── Panel A: Bifurcation diagram ───────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])

    param = np.linspace(0, 3, 200)

    # S-shaped curve showing bistability
    stable_1 = 180 * np.exp(-0.5 * param)
    unstable = 120 * np.exp(-0.5 * param)
    stable_2 = 40 + 20 * np.exp(-0.3 * param)

    ax.plot(param, stable_1, color=COLORS['healthy'],
           lw=2, label='Stable (healthy)')
    ax.plot(param, unstable, '--', color=COLORS['warning'],
           lw=2, label='Unstable')
    ax.plot(param, stable_2, color=COLORS['collapsed'],
           lw=2, label='Stable (collapsed)')

    # Fold points
    ax.scatter([1.2, 2.5], [80, 50], color='red', s=100,
              label='Fold points', zorder=5)

    ax.set_xlabel('Stress parameter')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('A  Bifurcation diagram')
    ax.legend()

    # ── Panel B: Hysteresis loop ───────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])

    stress_up = np.linspace(0, 3, 50)
    stress_down = np.linspace(3, 0, 50)

    dpsi_up = 180 * np.exp(-0.4 * stress_up)
    dpsi_down = 50 + 130 * (1 - np.exp(-(3 - stress_down) / 0.8))

    ax.plot(stress_up, dpsi_up, 'o-', color=COLORS['healthy'],
           lw=2, label='Increasing stress')
    ax.plot(stress_down, dpsi_down, 's-', color=COLORS['critical'],
           lw=2, label='Decreasing stress')

    # Hysteresis width
    ax.fill_between(stress_up, dpsi_up, dpsi_down, alpha=0.2)

    ax.set_xlabel('Stress level')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('B  Hysteresis loop')
    ax.legend()

    # ── Panel C: Potential energy landscape ────────────────────────────────────
    ax = fig.add_subplot(gs[0, 2])

    x = np.linspace(-3, 3, 200)

    # Double-well potential
    V = -(x**2) + 0.3 * (x**2)**2

    ax.plot(x, V, color=COLORS['boundary'], lw=2)

    # Mark minima
    ax.scatter([-1.8, 1.8], [-0.8, -0.8], s=100,
              c=[COLORS['healthy'], COLORS['collapsed']])

    ax.annotate('Healthy', (-1.8, -0.5), fontsize=8)
    ax.annotate('Collapsed', (1.8, -0.5), fontsize=8)

    ax.set_xlabel('State variable')
    ax.set_ylabel('Potential energy')
    ax.set_title('C  Energy landscape')
    ax.set_ylim(-2, 3)

    # ── Panel D: Critical slowing down ───────────────────────────────────────
    ax = fig.add_subplot(gs[0, 3])

    t = np.linspace(0, 100, 200)

    # Recovery from perturbation at different distances from criticality
    recovery_far = 180 - 20 * np.exp(-t / 10)  # Far from criticality
    recovery_near = 180 - 20 * np.exp(-t / 30)  # Near criticality
    recovery_critical = 180 - 20 * np.exp(-t / 80)  # At criticality

    ax.plot(t, recovery_far, color=COLORS['healthy'],
           label='Far from criticality')
    ax.plot(t, recovery_near, color=COLORS['warning'],
           label='Near criticality')
    ax.plot(t, recovery_critical, color=COLORS['critical'],
           label='At criticality')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('D  Recovery rate (CSD)')
    ax.legend()

    # ── Panels E-H: Early warning signals ──────────────────────────────────────
    t_ews = np.linspace(0, 200, 500)

    # Variance increase
    variance = 1 + 0.5 * (1 - np.exp(-(t_ews - 120) / 20)) * (t_ews > 120)

    # Autocorrelation increase
    autocorr = 0.3 + 0.4 * (1 - np.exp(-(t_ews - 120) / 25)) * (t_ews > 120)

    # Skewness increase
    skew = 0 + 0.8 * (1 - np.exp(-(t_ews - 120) / 30)) * (t_ews > 120)

    # Kurtosis increase
    kurt = 3 + 2 * (1 - np.exp(-(t_ews - 120) / 20)) * (t_ews > 120)

    ews_metrics = [
        ('Variance', variance, COLORS['stressed']),
        ('Autocorr.', autocorr, COLORS['critical']),
        ('Skewness', skew, COLORS['warning']),
        ('Kurtosis', kurt, COLORS['healthy']),
    ]

    for i, (name, y, color) in enumerate(ews_metrics):
        ax = fig.add_subplot(gs[1, i])

        ax.plot(t_ews, y, color=color, lw=2)
        ax.axvline(120, color='red', ls='--', lw=1, label='Critical point')
        ax.axvline(80, color='orange', ls=':', lw=1,
                  label='Warning onset')

        ax.set_xlabel('Time (arbitrary)')
        ax.set_ylabel(name)
        ax.set_title(f'{chr(69+i)}  {name}')
        ax.legend(fontsize=7)

    # ── Panel I: Flickering between states ─────────────────────────────────────
    ax = fig.add_subplot(gs[2, 0])

    t_flicker = np.linspace(0, 100, 500)

    # Flickering trajectory
    dpsi_flicker = 150 + 30 * np.sin(2 * np.pi * t_flicker / 15) * \
                   (1 - np.exp(-t_flicker / 30))

    ax.plot(t_flicker, dpsi_flicker, color=COLORS['warning'], lw=1)
    ax.axhline(120, color='red', ls='--', label='Critical threshold')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('I  Flickering')
    ax.legend()

    # ── Panel J: Spatial correlation ──────────────────────────────────────────
    ax = fig.add_subplot(gs[2, 1])

    distance = np.linspace(0, 10, 100)

    # Correlation vs distance
    correlation = np.exp(-distance / 2) * (1 + 0.3 * np.sin(distance))

    ax.plot(distance, correlation, color=COLORS['critical'], lw=2)
    ax.fill_between(distance, 0, correlation, alpha=0.2)

    ax.set_xlabel('Distance')
    ax.set_ylabel('Spatial correlation')
    ax.set_title('J  Spatial correlation')

    # ── Panel K: Leading indicator ───────────────────────────────────────────
    ax = fig.add_subplot(gs[2, 2])

    t_lead = np.linspace(0, 150, 300)

    # Composite leading indicator
    indicator = (variance[:300] + autocorr[:300]) / 2

    ax.plot(t_lead, indicator, color=COLORS['boundary'], lw=2)
    ax.axhline(0.6, color='red', ls='--', label='Warning threshold')

    # Highlight warning period
    ax.axvspan(80, 120, alpha=0.2, color=COLORS['warning'],
              label='Warning window')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Composite indicator')
    ax.set_title('K  Leading indicator')
    ax.legend()

    # ── Panel L: Warning reliability ──────────────────────────────────────────
    ax = fig.add_subplot(gs[2, 3])

    # ROC curve
    fpr = np.linspace(0, 1, 100)
    tpr = 1 - (1 - fpr)**2  # Better than random

    ax.plot(fpr, tpr, color=COLORS['critical'], lw=2)
    ax.plot([0, 1], [0, 1], 'k--', label='Random')
    ax.fill_between(fpr, 0, tpr - fpr, alpha=0.2)

    ax.set_xlabel('False positive rate')
    ax.set_ylabel('True positive rate')
    ax.set_title('L  ROC curve (EWS)')
    ax.legend()

    # ── Title ──────────────────────────────────────────────────────────────────
    fig.suptitle(
        'Figure 6 — NeurMito-DT: Bistability & Critical Transitions\n'
        'Hysteresis, critical slowing down, early warning signals',
        fontsize=11, fontweight='bold', y=0.98
    )

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure6_bistability.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}")
    plt.close(fig)
    return out_path


if __name__ == '__main__':
    make_figure6()
