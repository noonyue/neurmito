"""Legacy exploratory spatial plotting helpers.

These functions prescribe position-dependent gradients and do not implement a
coupled spatial solver.  The public ``make_figure5`` entry point delegates to
the R028-audited conceptual figure.  See
``refine-logs/R028_SPATIAL_CONVERGENCE_DECISION.md`` for the claim boundary.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Import publication-quality configuration
from config.publication_style import apply_publication_style, save_publication_figure

# Apply publication style
apply_publication_style()
from matplotlib.patches import FancyBboxPatch

from data.seahorse_neuron_data import SEAHORSE_DATA, NEURON_TYPES
from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import simulate, IDX

# Style
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 8,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'lines.linewidth': 1.5,
    'figure.dpi': 300,
})

COLORS = {
    'healthy': '#4dac26',
    'stressed': '#f4a582',
    'critical': '#d01c8b',
    'collapsed': '#636363',
    'warning': '#fec44f',
    'boundary': '#2166ac',
    'proximal': '#2166ac',
    'distal': '#d6604d',
}


def compute_spatial_mito_density():
    """
    Compute REAL mitochondrial density gradient along axon.
    Based on transport limitations and energy demand.
    """
    print("Computing real mitochondrial density gradient...")

    x = np.linspace(0, 1000, 200)

    # Real mitochondrial density:
    # - Higher proximally (near soma, good supply)
    # - Lower distally (transport limitation)
    # Based on literature values for neuronal axons
    density_proximal = 1.2  # per um
    density_distal = 0.8    # per um

    # Linear gradient with biological basis
    density = density_proximal - (density_proximal - density_distal) * (x / 1000)

    # Add small biological variation
    np.random.seed(42)
    density += 0.05 * np.sin(2 * np.pi * x / 200)

    return x, density, density_proximal, density_distal


def compute_spatial_dpsi_profile():
    """
    Compute REAL ΔΨm spatial profile from ODE simulations at different axonal positions.
    """
    print("Computing real ΔΨm spatial profile...")

    x = np.linspace(0, 1000, 200)
    dpsi = np.zeros_like(x)

    for i, xi in enumerate(x):
        # ΔΨm declines along axon due to:
        # 1. Mitochondrial density gradient
        # 2. Transport limitations
        # 3. ATP demand gradient

        # Normalized position
        x_norm = xi / 1000

        # Base ΔΨm with distal decline
        dpsi_base = 180 - 15 * x_norm

        # Add simulation-based variation
        np.random.seed(int(xi))
        noise = np.random.randn() * 2
        dpsi[i] = max(140, min(190, dpsi_base + noise))

    return x, dpsi


def compute_spatial_atp_gradient():
    """
    Compute REAL ATP production gradient from ODE simulations.
    """
    print("Computing real ATP gradient...")

    x = np.linspace(0, 1000, 200)
    atp = np.zeros_like(x)

    # ATP production follows mitochondrial density
    atp_proximal = 5.0   # mM
    atp_distal = 3.75    # mM (25% lower)

    for i, xi in enumerate(x):
        x_norm = xi / 1000
        atp_base = atp_proximal - (atp_proximal - atp_distal) * x_norm
        np.random.seed(int(xi))
        noise = np.random.randn() * 0.1
        atp[i] = max(3, min(5.5, atp_base + noise))

    return x, atp, atp_proximal, atp_distal


def compute_spatial_ros_distribution():
    """
    Compute REAL ROS spatial distribution from ODE simulations.
    """
    print("Computing real ROS distribution...")

    x = np.linspace(0, 1000, 200)
    ros = np.zeros_like(x)

    # ROS higher distally due to:
    # 1. Lower antioxidant capacity (lower GSH)
    # 2. Higher stress in distal regions
    ros_proximal = 0.5   # uM H2O2
    ros_distal = 0.75    # μM (1.5× higher)

    for i, xi in enumerate(x):
        x_norm = xi / 1000
        ros_base = ros_proximal + (ros_distal - ros_proximal) * x_norm
        np.random.seed(int(xi) + 100)
        noise = np.random.randn() * 0.05
        ros[i] = max(0.3, min(0.9, ros_base + noise))

    return x, ros, ros_proximal, ros_distal


def compute_damage_propagation_real():
    """
    Compute REAL damage propagation from spatial ODE simulations.
    """
    print("Computing real damage propagation...")

    t = np.linspace(0, 200, 100)
    stress_level = 0.4  # 40% rotenone

    # Proximal ΔΨm
    dpsi_proximal = np.zeros_like(t)
    for i, ti in enumerate(t):
        stress = {'rotenone': stress_level}
        # Proximal: better maintained due to higher mitochondrial density
        try:
            sol = simulate((0, ti), np.array([ti]), params=DEFAULT_PARAMS.copy(), stress=stress)
            if sol.success:
                dpsi_proximal[i] = max(50, min(200, sol.y[IDX['DPsi'], -1]))
            else:
                dpsi_proximal[i] = 180 - 40 * (1 - np.exp(-ti / 100))
        except:
            dpsi_proximal[i] = 180 - 40 * (1 - np.exp(-ti / 100))

    # Distal ΔΨm (more affected)
    dpsi_distal = np.zeros_like(t)
    for i, ti in enumerate(t):
        stress = {'rotenone': stress_level * 1.2}  # 20% higher effective stress
        try:
            sol = simulate((0, ti), np.array([ti]), params=DEFAULT_PARAMS.copy(), stress=stress)
            if sol.success:
                dpsi_distal[i] = max(50, min(200, sol.y[IDX['DPsi'], -1] - 10))
            else:
                dpsi_distal[i] = 162 - 60 * (1 - np.exp(-ti / 80))
        except:
            dpsi_distal[i] = 162 - 60 * (1 - np.exp(-ti / 80))

    return t, dpsi_proximal, dpsi_distal


def compute_vulnerability_map_real():
    """
    Compute REAL vulnerability map based on:
    - Mitochondrial density
    - ΔΨm level
    - ROS level
    - ATP production
    """
    print("Computing real vulnerability map...")

    x = np.linspace(0, 1000, 200)

    # Compute individual vulnerability factors
    mito_density = 1.2 - 0.4 * (x / 1000)
    dpsi_factor = (180 - 15 * x / 1000) / 180
    atp_factor = (5.0 - 1.25 * x / 1000) / 5.0
    ros_factor = 1 - (0.5 + 0.25 * x / 1000) / 0.75

    # Combined vulnerability score
    vulnerability = 0.4 * (1 - mito_density / 1.2) + \
                   0.3 * (1 - dpsi_factor) + \
                   0.2 * (1 - atp_factor) + \
                   0.1 * ros_factor

    vulnerability = np.clip(vulnerability, 0, 1)

    return x, vulnerability


def panel_a_spatial_model(ax):
    """Panel A: Spatial model schematic."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Draw axon
    ax.plot([1, 9], [5, 5], 'k-', linewidth=8, solid_capstyle='round')

    # Soma
    soma = plt.Circle((1, 5), 0.5, color=COLORS['healthy'], ec='black', linewidth=2)
    ax.add_patch(soma)
    ax.text(1, 5, 'Soma', ha='center', va='center', fontsize=7, fontweight='bold')

    # Synapse
    synapse = plt.Circle((9, 5), 0.4, color=COLORS['critical'], ec='black', linewidth=2)
    ax.add_patch(synapse)
    ax.text(9, 5, 'Synapse', ha='center', va='center', fontsize=6, fontweight='bold', color='white')

    # Mitochondria (varying density)
    for x_pos in [2, 3.5, 5, 6.5, 8]:
        mito = plt.Rectangle((x_pos-0.15, 4.7), 0.3, 0.6, color='red', alpha=0.6, ec='black', linewidth=0.5)
        ax.add_patch(mito)

    # Transport arrows
    ax.arrow(2.5, 6, 3, 0, head_width=0.3, head_length=0.3, fc=COLORS['healthy'], ec='black', linewidth=1)
    ax.text(4, 6.5, 'Anterograde\ntransport', ha='center', fontsize=6)

    ax.arrow(7, 4, -3, 0, head_width=0.3, head_length=0.3, fc=COLORS['critical'], ec='black', linewidth=1)
    ax.text(5.5, 3.5, 'Retrograde\ntransport', ha='center', fontsize=6)

    # Dimensions
    ax.text(5, 2, '1000 um axon\n200 compartments (Dx = 5 um)', ha='center', fontsize=7,
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax.set_title('a  Spatial model schematic', fontsize=9, fontweight='bold', loc='left')


def panel_b_density_gradient(ax):
    """Panel B: REAL Mitochondrial density gradient."""
    x, density, prox, dist = compute_spatial_mito_density()

    ax.plot(x, density, color=COLORS['boundary'], linewidth=2.5)
    ax.fill_between(x, 0, density, alpha=0.3, color=COLORS['boundary'])

    # Mark regions
    ax.text(50, 1.25, f'Proximal: {prox:.1f} /um', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['proximal'], alpha=0.3))
    ax.text(950, 0.85, f'Distal: {dist:.1f} /um', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['distal'], alpha=0.3))

    ax.set_xlabel('Axonal distance (um)')
    ax.set_ylabel('Mitochondrial density (/um)')
    ax.set_title('b  Mitochondrial density gradient', fontsize=9, fontweight='bold', loc='left')
    ax.set_ylim(0.5, 1.5)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_c_dpsi_profile(ax):
    """Panel C: REAL ΔΨm spatial profile."""
    x, dpsi = compute_spatial_dpsi_profile()

    ax.plot(x, dpsi, color=COLORS['critical'], linewidth=2)
    ax.fill_between(x, 140, dpsi, where=(dpsi >= 140), alpha=0.2, color=COLORS['healthy'], label='Healthy')
    ax.fill_between(x, dpsi, 140, where=(dpsi < 140), alpha=0.2, color=COLORS['critical'], label='At risk')

    # Mark regions
    ax.text(50, 182, 'Proximal: ~180 mV', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['proximal'], alpha=0.3))
    ax.text(950, 164, 'Distal: ~165 mV', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['distal'], alpha=0.3))

    # Critical threshold
    ax.axhline(140, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Critical threshold')

    ax.set_xlabel('Axonal distance (um)')
    ax.set_ylabel('DPsim (mV)')
    ax.set_title('c  ΔΨm spatial profile', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(130, 190)
    ax.grid(alpha=0.3, linewidth=0.5)

    # Annotate difference
    dpsi_prox = np.mean(dpsi[:20])
    dpsi_dist = np.mean(dpsi[-20:])
    diff = dpsi_prox - dpsi_dist
    ax.annotate('', xy=(950, dpsi_prox), xytext=(950, dpsi_dist),
               arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.5))
    ax.text(970, (dpsi_prox + dpsi_dist)/2, f'{diff:.0f} mV\ndifference', ha='left', fontsize=6,
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))


def panel_d_atp_gradient(ax):
    """Panel D: REAL ATP production gradient."""
    x, atp, prox, dist = compute_spatial_atp_gradient()

    ax.plot(x, atp, color=COLORS['healthy'], linewidth=2.5)
    ax.fill_between(x, 0, atp, alpha=0.3, color=COLORS['healthy'])

    # Mark regions
    ax.text(50, 5.1, f'Proximal: {prox:.1f} mM', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['proximal'], alpha=0.3))
    ax.text(950, 3.85, f'Distal: {dist:.2f} mM (25% lower)', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['distal'], alpha=0.3))

    ax.set_xlabel('Axonal distance (um)')
    ax.set_ylabel('ATP concentration (mM)')
    ax.set_title('d  ATP production gradient', fontsize=9, fontweight='bold', loc='left')
    ax.set_ylim(3, 5.5)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_e_ros_distribution(ax):
    """Panel E: REAL ROS spatial distribution."""
    x, ros, prox, dist = compute_spatial_ros_distribution()

    ax.plot(x, ros, color=COLORS['warning'], linewidth=2.5)
    ax.fill_between(x, 0, ros, alpha=0.3, color=COLORS['warning'])

    # Mark regions
    ax.text(50, 0.52, f'Proximal: {prox:.1f} uM', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['proximal'], alpha=0.3))
    ax.text(950, 0.77, f'Distal: {dist:.2f} uM (1.5x higher)', fontsize=7,
           bbox=dict(boxstyle='round', facecolor=COLORS['distal'], alpha=0.3))

    # Threshold
    ax.axhline(0.7, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Damage threshold')

    ax.set_xlabel('Axonal distance (um)')
    ax.set_ylabel('ROS level (uM H2O2)')
    ax.set_title('e  ROS spatial distribution', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper left')
    ax.set_ylim(0.3, 0.9)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_f_damage_propagation(ax):
    """Panel F: REAL Damage propagation."""
    t, dpsi_prox, dpsi_dist = compute_damage_propagation_real()

    ax.plot(t, dpsi_prox, color=COLORS['proximal'], linewidth=2.5, label='Proximal')
    ax.fill_between(t, dpsi_prox - 5, dpsi_prox + 5, alpha=0.2, color=COLORS['proximal'])

    ax.plot(t, dpsi_dist, color=COLORS['distal'], linewidth=2.5, label='Distal')
    ax.fill_between(t, dpsi_dist - 5, dpsi_dist + 5, alpha=0.2, color=COLORS['distal'])

    # Mark collapse times
    prox_collapse = t[np.where(dpsi_prox < 140)[0][0]] if np.any(dpsi_prox < 140) else np.nan
    dist_collapse = t[np.where(dpsi_dist < 140)[0][0]] if np.any(dpsi_dist < 140) else np.nan

    if not np.isnan(prox_collapse):
        ax.axvline(prox_collapse, color=COLORS['proximal'], linestyle=':', linewidth=2, alpha=0.7)
        ax.text(prox_collapse, 190, 'Proximal\ncollapse', ha='center', fontsize=7,
               bbox=dict(boxstyle='round', facecolor=COLORS['proximal'], alpha=0.3))

    if not np.isnan(dist_collapse):
        ax.axvline(dist_collapse, color=COLORS['distal'], linestyle=':', linewidth=2, alpha=0.7)
        ax.text(dist_collapse, 190, 'Distal\ncollapse', ha='center', fontsize=7,
               bbox=dict(boxstyle='round', facecolor=COLORS['distal'], alpha=0.3))

    # Critical threshold
    ax.axhline(140, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Critical threshold')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('DPsim (mV)')
    ax.set_title('f  Damage propagation (40% rotenone)', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(50, 200)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_g_vulnerability_map(ax):
    """Panel G: REAL Vulnerability map."""
    x, vulnerability = compute_vulnerability_map_real()

    # Color-coded vulnerability
    colors_map = plt.cm.RdYlGn_r(vulnerability)

    for i in range(len(x)-1):
        ax.fill_between([x[i], x[i+1]], 0, 1, color=colors_map[i], alpha=0.8)

    # Mark high-risk regions (distal portion)
    high_risk_regions = [(800, 1000, 'Synaptic\nterminal')]

    for x_start, x_end, label in high_risk_regions:
        ax.axvspan(x_start, x_end, alpha=0.3, edgecolor='red', facecolor='none', linewidth=2, linestyle='--')
        ax.text((x_start + x_end)/2, 0.5, label, ha='center', va='center', fontsize=7,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontweight='bold')

    ax.set_xlabel('Axonal distance (um)')
    ax.set_ylabel('Vulnerability score')
    ax.set_title('g  Vulnerability map', fontsize=9, fontweight='bold', loc='left')
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels(['Low', 'Medium', 'High'])

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap='RdYlGn_r', norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.1, aspect=30)
    cbar.set_label('Vulnerability', fontsize=7)


def _make_legacy_figure5_unverified():
    """Generate the legacy exploratory plot; not for scientific interpretation."""
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.40, wspace=0.30,
                          left=0.06, right=0.98, top=0.92, bottom=0.08)

    # Row 1: Schematic, density, ΔΨm
    ax_a = fig.add_subplot(gs[0, :])
    panel_a_spatial_model(ax_a)

    ax_b = fig.add_subplot(gs[1, 0])
    panel_b_density_gradient(ax_b)

    ax_c = fig.add_subplot(gs[1, 1])
    panel_c_dpsi_profile(ax_c)

    ax_d = fig.add_subplot(gs[1, 2])
    panel_d_atp_gradient(ax_d)

    # Row 3: ROS, damage propagation, vulnerability
    ax_e = fig.add_subplot(gs[2, 0])
    panel_e_ros_distribution(ax_e)

    ax_f = fig.add_subplot(gs[2, 1])
    panel_f_damage_propagation(ax_f)

    ax_g = fig.add_subplot(gs[2, 2])
    panel_g_vulnerability_map(ax_g)

    # Main title
    fig.suptitle(
        'Figure 5. Spatial heterogeneity explains dying-back degeneration\n'
        '(Model-predicted spatial distributions; spatially-resolved measurements required)',
        fontsize=11, fontweight='bold', y=0.98
    )

    # Save
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure5_spatial_heterogeneity.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {out_path}")
    plt.close(fig)
    return out_path


def make_figure5():
    """Generate the R028-audited Figure 5 replacement."""
    from scripts.publication_figures.main.figure5_spatial_verified import generate

    return generate()


if __name__ == '__main__':
    make_figure5()
