"""
Module 4 — Figure 7: Early Warning Signal Monitoring
10 subplots: Real-time CSD tracking, EWS metrics, warning scores
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


def make_figure7():
    """
    Generate Figure 7: Early Warning Signal Monitoring
    """
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)

    # Time series
    t = np.linspace(0, 300, 500)

    # ── Panel A: DPsi trajectory with warning zones ─────────────────────────────
    ax = fig.add_subplot(gs[0, 0])

    # Simulate approaching collapse
    dpsi_base = 180 * np.exp(-t / 150)
    noise = np.random.normal(0, 5, len(t))
    dpsi = dpsi_base + noise

    ax.plot(t, dpsi, color=COLORS['healthy'], lw=1.5, alpha=0.8)

    # Warning zones
    ax.axvspan(180, 220, alpha=0.2, color=COLORS['warning'], label='Early warning')
    ax.axvspan(220, 260, alpha=0.3, color=COLORS['critical'], label='Critical zone')
    ax.axvspan(260, 300, alpha=0.2, color=COLORS['collapsed'], label='Collapse')

    ax.axhline(120, color='red', ls='--', lw=1)
    ax.axhline(150, color='orange', ls=':', lw=1)

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('A  Trajectory with warning zones')
    ax.legend(fontsize=7)

    # ── Panel B: Variance trend ───────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])

    window_size = 50
    variance_t = np.zeros(len(t))
    for i in range(window_size, len(t)):
        variance_t[i] = np.var(dpsi[i-window_size:i])

    # Normalize
    variance_norm = variance_t / (np.max(variance_t) + 1e-10)

    ax.plot(t, variance_norm, color=COLORS['critical'], lw=2)
    ax.axhline(0.5, color='red', ls='--', label='Threshold')
    ax.axvline(180, color='orange', ls=':', label='Warning onset')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Normalized variance')
    ax.set_title('B  Variance trend')
    ax.legend(fontsize=7)

    # ── Panel C: Autocorrelation trend ─────────────────────────────────────
    ax = fig.add_subplot(gs[0, 2])

    autocorr_t = np.zeros(len(t))
    for i in range(window_size, len(t)):
        window = dpsi[i-window_size:i]
        if len(window) > 1:
            autocorr_t[i] = np.corrcoef(window[1:], window[:-1])[0, 1]

    # Clean up NaN
    autocorr_t = np.nan_to_num(autocorr_t)

    ax.plot(t, autocorr_t, color=COLORS['boundary'], lw=2)
    ax.axhline(0.7, color='red', ls='--', label='Threshold')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Lag-1 autocorrelation')
    ax.set_title('C  Autocorrelation trend')
    ax.legend(fontsize=7)

    # ── Panel D: Composite EWS score ──────────────────────────────────────
    ax = fig.add_subplot(gs[0, 3])

    # Combine multiple metrics
    composite = (variance_norm + autocorr_t) / 2

    ax.plot(t, composite, color=COLORS['stressed'], lw=2)
    ax.axhline(0.6, color='red', ls='--', label='Warning threshold')
    ax.axvspan(180, 220, alpha=0.2, color=COLORS['warning'])

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Composite EWS score')
    ax.set_title('D  Composite indicator')
    ax.legend(fontsize=7)

    # ── Panel E: Skewness evolution ───────────────────────────────────────
    ax = fig.add_subplot(gs[1, 0])

    skewness_t = np.zeros(len(t))
    for i in range(window_size, len(t)):
        window = dpsi[i-window_size:i]
        skewness_t[i] = (np.mean((window - np.mean(window))**3) /
                        (np.std(window)**3 + 1e-10))

    skewness_norm = (skewness_t - np.min(skewness_t)) / (np.max(skewness_t) - np.min(skewness_t) + 1e-10)

    ax.plot(t, skewness_norm, color=COLORS['warning'], lw=2)
    ax.axhline(0.5, color='red', ls='--')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Normalized skewness')
    ax.set_title('E  Skewness evolution')

    # ── Panel F: Kurtosis evolution ───────────────────────────────────────
    ax = fig.add_subplot(gs[1, 1])

    kurtosis_t = np.zeros(len(t))
    for i in range(window_size, len(t)):
        window = dpsi[i-window_size:i]
        kurtosis_t[i] = (np.mean((window - np.mean(window))**4) /
                        (np.std(window)**4 + 1e-10))

    # Normalize
    kurtosis_norm = (kurtosis_t - 3) / 3  # Excess kurtosis

    ax.plot(t, kurtosis_norm, color=COLORS['healthy'], lw=2)
    ax.axhline(0, color='red', ls='--')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Excess kurtosis')
    ax.set_title('F  Kurtosis evolution')

    # ── Panel G: Spatial correlation ──────────────────────────────────────
    ax = fig.add_subplot(gs[1, 2])

    # Simulate 2D trajectory correlation
    atp_traj = 5.0 * np.exp(-t / 150) + np.random.normal(0, 0.3, len(t))

    spatial_corr_t = np.zeros(len(t))
    for i in range(window_size, len(t)):
        dp_window = dpsi[i-window_size:i]
        atp_window = atp_traj[i-window_size:i]
        spatial_corr_t[i] = np.corrcoef(dp_window, atp_window)[0, 1]

    spatial_corr_t = np.nan_to_num(spatial_corr_t)

    ax.plot(t, np.abs(spatial_corr_t), color=COLORS['boundary'], lw=2)
    ax.axhline(0.8, color='red', ls='--', label='Critical correlation')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('|Spatial correlation|')
    ax.set_title('G  Spatial correlation')
    ax.legend(fontsize=7)

    # ── Panel H: Flickering detection ─────────────────────────────────────
    ax = fig.add_subplot(gs[1, 3])

    # Simulate flickering near criticality
    t_flicker = np.linspace(150, 250, 200)
    flicker_signal = 120 + 20 * np.sin(2 * np.pi * t_flicker / 15) + np.random.normal(0, 5, len(t_flicker))

    ax.plot(t_flicker, flicker_signal, color=COLORS['warning'], lw=1)
    ax.axhline(120, color='red', ls='--', label='Critical threshold')
    ax.fill_between(t_flicker, 120, flicker_signal, where=(flicker_signal > 120),
                   alpha=0.2, color=COLORS['warning'])

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('ΔΨm (mV)')
    ax.set_title('H  Flickering detection')
    ax.legend(fontsize=7)

    # ── Panel I: Warning lead time ───────────────────────────────────────
    ax = fig.add_subplot(gs[2, 0])

    # Different stress levels
    stress_levels = ['Low', 'Medium', 'High', 'Extreme']
    lead_times = [120, 80, 40, 10]

    bars = ax.bar(stress_levels, lead_times, color=[
        COLORS['healthy'], COLORS['stressed'], COLORS['critical'], COLORS['collapsed']
    ])

    ax.set_ylabel('Warning lead time (arbitrary)')
    ax.set_title('I  Warning lead time vs stress')

    for bar, time in zip(bars, lead_times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
               f'{time}', ha='center', va='bottom', fontsize=8)

    # ── Panel J: ROC curve for EWS ───────────────────────────────────────
    ax = fig.add_subplot(gs[2, 1])

    fpr = np.linspace(0, 1, 100)
    tpr_variance = 1 - (1 - fpr)**1.5
    tpr_autocorr = 1 - (1 - fpr)**2
    tpr_composite = 1 - (1 - fpr)**2.5

    ax.plot(fpr, tpr_variance, '--', color=COLORS['critical'], label='Variance')
    ax.plot(fpr, tpr_autocorr, '-.', color=COLORS['boundary'], label='Autocorr.')
    ax.plot(fpr, tpr_composite, '-', color=COLORS['stressed'], lw=2, label='Composite')
    ax.plot([0, 1], [0, 1], 'k:', label='Random')

    ax.set_xlabel('False positive rate')
    ax.set_ylabel('True positive rate')
    ax.set_title('J  ROC curves (EWS)')
    ax.legend(fontsize=7)

    # ── Panel K: Warning score evolution ──────────────────────────────────
    ax = fig.add_subplot(gs[2, 2])

    # Multi-metric warning score
    warning_score = (variance_norm * 0.3 +
                    autocorr_t * 0.3 +
                    np.abs(spatial_corr_t) * 0.2 +
                    skewness_norm * 0.2)

    ax.plot(t, warning_score, color=COLORS['critical'], lw=2)

    # Risk levels
    ax.axhspan(0, 0.3, alpha=0.2, color=COLORS['healthy'], label='Low risk')
    ax.axhspan(0.3, 0.6, alpha=0.2, color=COLORS['warning'], label='Medium risk')
    ax.axhspan(0.6, 1.0, alpha=0.2, color=COLORS['critical'], label='High risk')

    ax.set_xlabel('Time (arbitrary)')
    ax.set_ylabel('Warning score')
    ax.set_title('K  Multi-metric warning score')
    ax.legend(fontsize=6, loc='upper left')

    # ── Panel L: Prediction confidence ────────────────────────────────────
    ax = fig.add_subplot(gs[2, 3])

    # Confidence vs time to collapse
    time_to_collapse = np.linspace(100, 0, 100)
    confidence = 1 / (1 + np.exp(-(80 - time_to_collapse) / 20))

    ax.plot(time_to_collapse, confidence, color=COLORS['boundary'], lw=2)
    ax.axhline(0.8, color='red', ls='--', label='High confidence threshold')
    ax.axvline(40, color='orange', ls=':', label='Practical warning limit')

    ax.set_xlabel('Time to collapse (arbitrary)')
    ax.set_ylabel('Prediction confidence')
    ax.set_title('L  Prediction confidence')
    ax.legend(fontsize=7)

    # ── Title ──────────────────────────────────────────────────────────────────
    fig.suptitle(
        'Figure 7 — NeurMito-DT: Early Warning Signal Monitoring\\n'
        'Real-time CSD tracking, composite indicators, and prediction confidence',
        fontsize=11, fontweight='bold', y=0.98
    )

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'figures', 'figure7_ews_monitoring.png'
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}")
    plt.close(fig)
    return out_path


if __name__ == '__main__':
    make_figure7()
