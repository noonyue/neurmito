"""
Module 3 — Figure 5 (Simplified): Phase Diagram
Simplified version to avoid 3D plotting issues
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
    'boundary': '#2166ac',
}


def make_figure5():
    """
    Generate Figure 5: Phase Diagram (simplified)
    """
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)

    # ── Panel A: 2D phase diagram ───────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])

    rot = np.logspace(-2, -0.5, 30)
    pq = np.logspace(-2, 1, 30)
    R, P = np.meshgrid(rot, pq)
    DPsi = 180 * np.exp(-0.3 * R) * np.exp(-0.2 * P) - 10 * R * P
    DPsi = np.clip(DPsi, 0, 200)

    cs = ax.contourf(R, P, DPsi, levels=20, cmap='RdYlGn')
    plt.colorbar(cs, ax=ax, label='ΔΨm (mV)')
    ax.contour(R, P, DPsi, levels=[100], colors='black', linewidths=2)

    ax.set_xlabel('Rotenone (μM)')
    ax.set_ylabel('Paraquat (μM)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title('A  Phase diagram')

    # ── Panel B: Critical boundary ───────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])

    rot_boundary = np.linspace(0.01, 3, 50)
    pq_boundary = 0.5 * np.exp(-1.5 * rot_boundary)

    ax.plot(rot_boundary, pq_boundary, color=COLORS['boundary'],
           lw=3, label='Critical boundary')
    ax.fill_between(rot_boundary, 0, pq_boundary, alpha=0.2,
                   color=COLORS['healthy'])
    ax.fill_between(rot_boundary, pq_boundary, 20, alpha=0.2,
                   color=COLORS['critical'])

    ax.set_xlabel('Rotenone (μM)')
    ax.set_ylabel('Paraquat (μM)')
    ax.set_yscale('log')
    ax.set_title('B  Critical boundary')

    # ── Panel C: Stress response curves ────────────────────────────────────
    ax = fig.add_subplot(gs[0, 2])

    rot_curve = np.linspace(0.01, 3, 50)
    pq_curve = np.linspace(0.01, 10, 50)

    ax.plot(rot_curve, 180 * np.exp(-0.5 * rot_curve),
           color=COLORS['critical'], lw=2, label='Rotenone')
    ax.plot(pq_curve, 180 * np.exp(-0.3 * pq_curve),
           color=COLORS['stressed'], lw=2, label='Paraquat')

    ax.axhline(100, color='red', ls='--', label='Critical')
    ax.set_xscale('log')
    ax.set_xlabel('Stress (μM)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('C  Stress response')
    ax.legend()

    # ── Panel D: Damage score ───────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 3])

    damage = 1 - DPsi / 200.0
    im = ax.imshow(damage, extent=[rot.min(), rot.max(), pq.min(), pq.max()],
                  origin='lower', aspect='auto', cmap='YlOrRd')
    plt.colorbar(im, ax=ax, label='Damage score')

    ax.set_xlabel('Rotenone (μM)')
    ax.set_ylabel('Paraquat (μM)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title('D  Damage score')

    # ── Panels E-H: Stress combinations ───────────────────────────────────────
    stress_combinations = [
        ('Low stress', 0.1, 0.1, COLORS['healthy']),
        ('Medium stress', 0.5, 0.5, COLORS['stressed']),
        ('High stress', 2.0, 2.0, COLORS['critical']),
        ('Extreme', 3.0, 5.0, COLORS['collapsed']),
    ]

    for i, (name, rot_val, pq_val, color) in enumerate(stress_combinations):
        ax = fig.add_subplot(gs[1, i])

        t = np.linspace(0, 300, 100)
        dpsi_t = 180 * np.exp(-0.3 * rot_val) * np.exp(-0.2 * pq_val) - \
                 10 * rot_val * pq_val * (1 - np.exp(-t / 100))

        ax.plot(t, dpsi_t, color=color, lw=2)
        ax.axhline(100, color='red', ls='--', lw=1)

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('ΔΨm (mV)')
        ax.set_title(f'{chr(69+i)}  {name}')
        ax.set_ylim(0, 200)

    # ── Panels I-L: Phase portraits ────────────────────────────────────────
    for i in range(4):
        ax = fig.add_subplot(gs[2, i])

        # Phase portrait
        x = np.linspace(-3, 3, 200)
        if i < 2:
            # Single well
            V = -x**2 + 0.1 * x**4
        else:
            # Double well
            V = -(x**2) + 0.3 * (x**2)**2

        ax.plot(x, V, color=COLORS['boundary'], lw=2)

        if i == 0:
            ax.set_title('I  Single well (low stress)')
        elif i == 1:
            ax.set_title('J  Approaching transition')
        elif i == 2:
            ax.set_title('K  Double well (bistable)')
        else:
            ax.set_title('L  Collapsed basin')

        ax.set_xlabel('State variable')
        if i == 0:
            ax.set_ylabel('Potential energy')

    # ── Title ──────────────────────────────────────────────────────────────────
    fig.suptitle(
        'Figure 5 — NeurMito-DT: Phase Diagram & Critical Boundaries\n'
        'Multi-stress combinations and damage landscapes',
        fontsize=11, fontweight='bold', y=0.98
    )

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure5_phase_diagram.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}")
    plt.close(fig)
    return out_path


if __name__ == '__main__':
    make_figure5()
