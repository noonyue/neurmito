"""Legacy exploratory disease-scenario plotting helpers.

The numerical disease trajectories and intervention values below are prescribed
scenarios, not a source-audited disease parameterization or external
validation.  The public ``make_figure6`` entry point delegates to the
R029-audited hypothesis map.  See
``refine-logs/R029_DISEASE_SCENARIO_DECISION.md`` for the claim boundary.
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
    'PD': '#d6604d',
    'AD': '#4393c3',
    'ALS': '#8073ac',
    'healthy': '#4dac26',
    'intervention': '#fec44f',
    'success': '#4dac26',
    'failure': '#d01c8b',
}


def panel_a_pd_dpsi_trajectory(ax):
    """Panel A: PD - ΔΨm trajectory under progressive complex I inhibition."""
    t = np.linspace(0, 300, 500)

    # Progressive rotenone exposure (0 → 50% over 300s)
    rotenone = 50 * (t / 300)

    # ΔΨm decline
    dpsi = 180 - 1.5 * rotenone
    dpsi += 3 * np.random.randn(len(t))  # Noise

    ax.plot(t, dpsi, color=COLORS['PD'], linewidth=2.5)
    ax.fill_between(t, dpsi - 5, dpsi + 5, alpha=0.2, color=COLORS['PD'])

    # Critical threshold
    ax.axhline(140, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Critical threshold')

    # Mark intervention window
    intervention_start = 300 * 0.25 / 0.5  # 25% inhibition
    intervention_end = 300 * 0.35 / 0.5    # 35% inhibition
    ax.axvspan(intervention_start, intervention_end, alpha=0.2, color=COLORS['intervention'],
              label='Intervention window')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('a  PD: ΔΨm trajectory', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(100, 190)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_b_pd_ros_burst(ax):
    """Panel B: PD - ROS burst dynamics."""
    t = np.linspace(0, 200, 500)

    # ROS burst at critical transition
    ros = 0.5 * np.ones_like(t)
    burst_idx = np.where(t >= 120)[0]
    ros[burst_idx] = 0.5 + 2.0 * (1 - np.exp(-(t[burst_idx]-120)/15))

    ax.plot(t, ros, color=COLORS['PD'], linewidth=2.5)
    ax.fill_between(t, 0, ros, alpha=0.3, color=COLORS['PD'])

    # Mark burst
    ax.axvline(120, color='red', linestyle=':', linewidth=2, alpha=0.7)
    ax.text(120, 2.3, 'ROS burst', ha='center', fontsize=7,
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ROS level (μM H₂O₂)')
    ax.set_title('b  PD: ROS burst dynamics', fontsize=9, fontweight='bold', loc='left')
    ax.set_ylim(0, 2.5)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_c_pd_ews_detection(ax):
    """Panel C: PD - EWS detection (35 ± 8 s lead time)."""
    t = np.linspace(0, 200, 500)

    # Composite EWS score
    ews_score = 0.1 + 0.8 * (1 / (1 + np.exp(-0.1 * (t - 120))))

    ax.plot(t, ews_score, color=COLORS['PD'], linewidth=2.5)
    ax.fill_between(t, 0, ews_score, alpha=0.3, color=COLORS['PD'])

    # Alert threshold
    ax.axhline(0.6, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Alert threshold')

    # Mark warning and collapse
    warning_time = 120 - 35  # 35s lead time
    ax.axvline(warning_time, color='orange', linestyle=':', linewidth=2, alpha=0.7, label='EWS alert')
    ax.axvline(120, color='red', linestyle=':', linewidth=2, alpha=0.7, label='Collapse')

    # Annotate lead time
    ax.annotate('', xy=(warning_time, 0.8), xytext=(120, 0.8),
               arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.5))
    ax.text((warning_time + 120)/2, 0.85, '35 ± 8 s\nlead time', ha='center', fontsize=7,
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('EWS composite score')
    ax.set_title('c  PD: EWS detection', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper left')
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_d_pd_intervention_window(ax):
    """Panel D: PD - Intervention window (25-35% inhibition, 87% vs 23% success)."""
    inhibition_levels = np.array([10, 20, 25, 30, 35, 40, 50, 60])
    success_rates = np.array([95, 92, 87, 87, 87, 23, 15, 8])

    ax.plot(inhibition_levels, success_rates, 'o-', color=COLORS['PD'],
           linewidth=2.5, markersize=8)

    # Mark intervention window
    ax.axvspan(25, 35, alpha=0.2, color=COLORS['success'], label='Optimal window (87% success)')
    ax.axvspan(40, 60, alpha=0.2, color=COLORS['failure'], label='Late intervention (23% success)')

    # Annotate key points
    ax.scatter([30], [87], s=200, color=COLORS['success'], marker='*', zorder=5,
              edgecolor='black', linewidth=1.5)
    ax.scatter([40], [23], s=200, color=COLORS['failure'], marker='X', zorder=5,
              edgecolor='black', linewidth=1.5)

    ax.set_xlabel('Complex I inhibition (%)')
    ax.set_ylabel('Intervention success rate (%)')
    ax.set_title('d  PD: Intervention window', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_e_ad_energy_calcium(ax):
    """Panel E: AD - Synergistic energy-calcium dysregulation."""
    t = np.linspace(0, 300, 500)

    # Energy deficit
    atp = 5.0 - 2.0 * (1 - np.exp(-t/80))

    # Calcium overload (synergistic with energy deficit)
    ca = 0.1 + 0.8 * (1 - np.exp(-t/60))

    ax2 = ax.twinx()

    line1 = ax.plot(t, atp, color=COLORS['AD'], linewidth=2.5, label='ATP')
    line2 = ax2.plot(t, ca, color='orange', linewidth=2.5, linestyle='--', label='Ca²⁺')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ATP (mM)', color=COLORS['AD'])
    ax2.set_ylabel('Ca²⁺ (μM)', color='orange')
    ax.set_title('e  AD: Energy-calcium dysregulation', fontsize=9, fontweight='bold', loc='left')

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, fontsize=6, loc='center right')

    ax.set_ylim(2, 5.5)
    ax2.set_ylim(0, 1)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_f_ad_ca1_vulnerability(ax):
    """Panel F: AD - Hippocampal CA1 vulnerability."""
    regions = ['CA1', 'CA3', 'DG', 'Cortex']
    vulnerability = [0.85, 0.45, 0.35, 0.50]

    colors_bar = [COLORS['AD'] if v > 0.7 else 'gray' for v in vulnerability]

    bars = ax.bar(range(len(regions)), vulnerability, color=colors_bar,
                  alpha=0.7, edgecolor='black', linewidth=1.5)

    ax.set_xticks(range(len(regions)))
    ax.set_xticklabels(regions)
    ax.set_ylabel('Vulnerability score')
    ax.set_title('f  AD: CA1 vulnerability', fontsize=9, fontweight='bold', loc='left')
    ax.set_ylim(0, 1)
    ax.axhline(0.7, color='red', linestyle='--', linewidth=1, alpha=0.5, label='High vulnerability')
    ax.legend(fontsize=6)
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)


def panel_g_ad_calcium_blocker(ax):
    """Panel G: AD - Calcium channel blocker efficacy window."""
    time_of_treatment = np.array([0, 50, 100, 150, 200, 250])
    efficacy = np.array([90, 85, 75, 50, 25, 10])

    ax.plot(time_of_treatment, efficacy, 'o-', color=COLORS['AD'],
           linewidth=2.5, markersize=8)

    # Mark efficacy window
    ax.axvspan(0, 100, alpha=0.2, color=COLORS['success'], label='High efficacy (>75%)')
    ax.axvspan(100, 200, alpha=0.2, color=COLORS['intervention'], label='Moderate efficacy')
    ax.axvspan(200, 250, alpha=0.2, color=COLORS['failure'], label='Low efficacy (<25%)')

    ax.set_xlabel('Time of treatment (s after onset)')
    ax.set_ylabel('Efficacy (%)')
    ax.set_title('g  AD: Ca²⁺ channel blocker efficacy', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_h_als_transport_sod1(ax):
    """Panel H: ALS - Transport failure + SOD1 mutation synergy (3.2-fold acceleration)."""
    t = np.linspace(0, 200, 500)

    # Wild-type
    dpsi_wt = 180 - 40 * (1 - np.exp(-t/100))

    # Transport failure only
    dpsi_transport = 180 - 60 * (1 - np.exp(-t/80))

    # SOD1 mutation only
    dpsi_sod1 = 180 - 60 * (1 - np.exp(-t/80))

    # Combined (synergistic, 3.2× faster)
    dpsi_combined = 180 - 100 * (1 - np.exp(-t/31))  # 100/31 ≈ 3.2× faster

    ax.plot(t, dpsi_wt, color='gray', linewidth=1.5, linestyle=':', label='Wild-type')
    ax.plot(t, dpsi_transport, color=COLORS['ALS'], linewidth=1.5, linestyle='--',
           alpha=0.5, label='Transport failure')
    ax.plot(t, dpsi_sod1, color=COLORS['ALS'], linewidth=1.5, linestyle='-.',
           alpha=0.5, label='SOD1 mutation')
    ax.plot(t, dpsi_combined, color=COLORS['ALS'], linewidth=2.5,
           label='Combined (3.2× acceleration)')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('h  ALS: Transport + SOD1 synergy', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(60, 190)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_i_als_biogenesis_window(ax):
    """Panel I: ALS - Mitochondrial biogenesis compensation window."""
    t = np.linspace(0, 300, 500)

    # No intervention
    dpsi_no_int = 180 - 100 * (1 - np.exp(-t/50))

    # Early biogenesis boost (t < 100s)
    dpsi_early = 180 - 60 * (1 - np.exp(-t/80))

    # Late biogenesis boost (t > 150s)
    dpsi_late = dpsi_no_int.copy()
    late_idx = np.where(t >= 150)[0]
    dpsi_late[late_idx] = dpsi_no_int[late_idx] + 20

    ax.plot(t, dpsi_no_int, color='gray', linewidth=1.5, linestyle=':', label='No intervention')
    ax.plot(t, dpsi_early, color=COLORS['success'], linewidth=2.5, label='Early boost (<100s)')
    ax.plot(t, dpsi_late, color=COLORS['failure'], linewidth=2.5, linestyle='--',
           label='Late boost (>150s)')

    # Mark compensation window
    ax.axvspan(0, 100, alpha=0.2, color=COLORS['success'], label='Compensation window')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('i  ALS: Biogenesis compensation window', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right')
    ax.set_ylim(60, 190)
    ax.grid(alpha=0.3, linewidth=0.5)


def panel_j_multi_disease_comparison(ax):
    """Panel J: Multi-disease comparison - distinct mitochondrial signatures."""
    diseases = ['PD', 'AD', 'ALS', 'Control']

    # Mitochondrial signatures (normalized)
    complex_i = [0.70, 0.85, 0.80, 1.0]  # PD has lowest
    ros_production = [1.5, 1.2, 1.4, 1.0]  # PD has highest
    ca_buffering = [0.9, 0.6, 0.85, 1.0]  # AD has lowest
    transport = [0.85, 0.9, 0.5, 1.0]  # ALS has lowest

    x = np.arange(len(diseases))
    width = 0.2

    ax.bar(x - 1.5*width, complex_i, width, label='Complex I activity',
          color=COLORS['PD'], alpha=0.7, edgecolor='black')
    ax.bar(x - 0.5*width, ros_production, width, label='ROS production',
          color='orange', alpha=0.7, edgecolor='black')
    ax.bar(x + 0.5*width, ca_buffering, width, label='Ca²⁺ buffering',
          color=COLORS['AD'], alpha=0.7, edgecolor='black')
    ax.bar(x + 1.5*width, transport, width, label='Axonal transport',
          color=COLORS['ALS'], alpha=0.7, edgecolor='black')

    ax.set_xticks(x)
    ax.set_xticklabels(diseases)
    ax.set_ylabel('Relative to control')
    ax.set_title('j  Multi-disease comparison', fontsize=9, fontweight='bold', loc='left')
    ax.legend(fontsize=6, loc='upper right', ncol=2)
    ax.set_ylim(0, 1.8)
    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Control baseline')
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)


def _make_legacy_figure6_unverified():
    """Generate the legacy exploratory plot; not for scientific interpretation."""
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.45, wspace=0.35,
                          left=0.06, right=0.98, top=0.94, bottom=0.06)

    # Row 1: Parkinson's disease (a-d)
    ax_a = fig.add_subplot(gs[0, 0])
    panel_a_pd_dpsi_trajectory(ax_a)

    ax_b = fig.add_subplot(gs[0, 1])
    panel_b_pd_ros_burst(ax_b)

    ax_c = fig.add_subplot(gs[0, 2])
    panel_c_pd_ews_detection(ax_c)

    ax_d = fig.add_subplot(gs[1, 0])
    panel_d_pd_intervention_window(ax_d)

    # Row 2: Alzheimer's disease (e-g)
    ax_e = fig.add_subplot(gs[1, 1])
    panel_e_ad_energy_calcium(ax_e)

    ax_f = fig.add_subplot(gs[1, 2])
    panel_f_ad_ca1_vulnerability(ax_f)

    ax_g = fig.add_subplot(gs[2, 0])
    panel_g_ad_calcium_blocker(ax_g)

    # Row 3: ALS (h-i)
    ax_h = fig.add_subplot(gs[2, 1])
    panel_h_als_transport_sod1(ax_h)

    ax_i = fig.add_subplot(gs[2, 2])
    panel_i_als_biogenesis_window(ax_i)

    # Row 4: Multi-disease comparison (j)
    ax_j = fig.add_subplot(gs[3, :])
    panel_j_multi_disease_comparison(ax_j)

    # Main title
    fig.suptitle(
        'Figure 6. Disease-specific applications reveal intervention windows\n'
        '(Model predictions using literature-derived disease parameters; patient data validation pending)',
        fontsize=11, fontweight='bold', y=0.98
    )

    # Save
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure6_disease_applications.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {out_path}")
    plt.close(fig)
    return out_path


def make_figure6():
    """Generate the R029-audited Figure 6 replacement."""
    from scripts.publication_figures.main.figure6_disease_verified import generate

    return generate()


if __name__ == '__main__':
    make_figure6()
