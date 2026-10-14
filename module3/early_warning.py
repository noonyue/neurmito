"""
Module 3 — Early Warning Signal Detection
Detect critical slowing down and other early warning signals of mitochondrial failure

CSD metrics:
1. Increasing variance
2. Increasing autocorrelation
3. Spatial correlation
4. Flickering
"""

import numpy as np
import pandas as pd
from scipy.signal import hilbert, find_peaks
from scipy.stats import autocorrelation
from scipy.ndimage import gaussian_filter1d
from scipy.stats import kurtosis, skew

from .bistability_analysis import detect_critical_slowing_down


# ─── Early warning signals based on trajectory analysis ───────────────────────

def compute_csd_metrics(sol, window_size=50):
    """
    Compute multiple CSD metrics.

    Parameters
    ----------
    sol : OdeResult
        Trajectory solution
    window_size : int
        Rolling window size

    Returns
    -------
    csd_metrics : dict
        All CSD metrics
    """
    if not sol.success:
        return None

    # Extract key variables
    t = sol.t
    dp = sol.y[IDX['DPsi'], :]
    atp = sol.y[IDX['ATP_m'], :]
    h2o2 = sol.y[IDX['H2O2_m'], :]

    n_points = len(t)

    # Initialize arrays
    dp_variance = np.zeros(n_points)
    dp_autocorr = np.zeros(n_points)
    atp_variance = np.zeros(n_points)
    h2o2_variance = np.zeros(n_points)

    # Rolling window calculations
    for i in range(window_size, n_points):
        dp_window = dp[i - window_size:i]
        atp_window = atp[i - window_size:i]
        h2o2_window = h2o2[i - window_size:i]

        # Variance
        dp_variance[i] = np.var(dp_window)
        atp_variance[i] = np.var(atp_window)
        h2o2_variance[i] = np.var(h2o2_window)

        # Autocorrelation (lag-1)
        dp_autocorr[i] = np.corrcoef(dp_window[1:], dp_window[:-1])[0, 1]

    # Normalize
    dp_variance_norm = dp_variance / (np.max(dp_variance) + 1e-10)
    atp_variance_norm = atp_variance / (np.max(atp_variance) + 1e-10)
    h2o2_variance_norm = h2o2_variance / (np.max(h2o2_variance) + 1e-10)

    # Combined CSD metric
    combined_csd = dp_variance_norm * dp_autocorr

    # Compute trends (slope of last 100 points)
    slope_dp = np.polyfit(t[-100:], dp_variance[-100:], 1)[0]
    slope_atp = np.polyfit(t[-100:], atp_variance[-100:], 1)[0]
    slope_h2o2 = np.polyfit(t[-100:], h2o2_variance[-100:], 1)[0]

    # Normalize trends
    slope_dp_norm = slope_dp / (np.mean(dp_variance) + 1e-10)
    slope_atp_norm = slope_atp / (np.mean(atp_variance) + 1e-10)
    slope_h2o2_norm = slope_h2o2 / (np.mean(h2o2_variance) + 1e-10)

    return {
        'dp_variance': dp_variance_norm,
        'atp_variance': atp_variance_norm,
        'h2o2_variance': h2o2_variance_norm,
        'dp_autocorr': dp_autocorr,
        'combined_csd': combined_csd,
        'slope_dp': slope_dp_norm,
        'slope_atp': slope_atp_norm,
        'slope_h2o2': slope_h2o2_norm,
        'dp_autocorr_final': dp_autocorr[-100:].mean(),
        'variance_final': dp_variance_norm[-100:].mean(),
    }


# ─── Spatial early warning signals ───────────────────────────────────────────

def compute_spatial_ews(trajectory_2d):
    """
    Compute spatial EWS for 2D trajectory (e.g., ATP vs DPsi).

    Parameters
    ----------
    trajectory_2d : array (n_points, 2)
        2D trajectory (e.g., [DPsi, ATP])

    Returns
    -------
    spatial_ews : dict
        Spatial early warning signals
    """
    n_points = trajectory_2d.shape[0]

    # Distance from center
    center = np.mean(trajectory_2d, axis=0)
    distances = np.linalg.norm(trajectory_2d - center, axis=1)

    # Distance variance
    distance_variance = np.zeros(n_points)
    for i in range(50, n_points):
        window = distances[i - 50:i]
        distance_variance[i] = np.var(window)

    # Spatial correlation
    correlation = np.zeros(n_points)
    for i in range(50, n_points):
        window = trajectory_2d[i - 50:i]
        corr_matrix = np.corrcoef(window.T)
        correlation[i] = corr_matrix[0, 1]

    # Spatial coverage (radius of gyration)
    centroid_window = np.zeros(n_points)
    for i in range(50, n_points):
        window = trajectory_2d[i - 50:i]
        centroid = np.mean(window, axis=0)
        distances = np.linalg.norm(window - centroid, axis=1)
        centroid_window[i] = np.sqrt(np.mean(distances**2))

    return {
        'distance_variance': distance_variance,
        'spatial_correlation': correlation,
        'centroid_radius': centroid_window,
    }


# ─── Flickering detection ───────────────────────────────────────────────

def detect_flickering(sol, threshold_window=50, min_flicker_duration=5):
    """
    Detect flickering between states.

    Parameters
    ----------
    sol : OdeResult
        Trajectory solution
    threshold_window : int
        Window for flickering detection
    min_flicker_duration : int
        Minimum duration for flickering

    Returns
    -------
    flickering : dict
        Flickering detection results
    """
    if not sol.success:
        return None

    # Extract DPsi
    dp = sol.y[IDX['DPsi'], :]
    dp_mean = np.mean(dp[-100:])  # Recent mean
    dp_std = np.std(dp[-100:])

    # Define states
    threshold = dp_mean + dp_std
    critical_threshold = 100.0

    # Detect flickering: crossing threshold repeatedly
    flickering_states = []
    in_flicker = False
    flicker_start = 0

    for i in range(len(dp) - threshold_window):
        # Average over window
        window_avg = np.mean(dp[i:i + threshold_window])

        # Check if crossing threshold
        if window_avg > threshold and not in_flicker:
            in_flicker = True
            flicker_start = i
        elif window_avg <= threshold and in_flicker:
            in_flicker = False
            flicker_duration = i - flicker_start

            if flicker_duration >= min_flicker_duration:
                flickering_states.append({
                    'start': i,
                    'end': i + threshold_window,
                    'duration': flicker_duration,
                    'depth': np.max(dp[flicker_start:i + threshold_window]) - threshold,
                })

    # Flickering frequency and amplitude
    if len(flickering_states) > 1:
        intervals = []
        for i in range(1, len(flickering_states)):
            intervals.append(flickering_states[i]['start'] - flickering_states[i-1]['end'])

        avg_interval = np.mean(intervals)
        avg_amplitude = np.mean([f['depth'] for f in flickering_states])

        return {
            'flickering_detected': True,
            'flicker_count': len(flickering_states),
            'avg_interval': avg_interval,
            'avg_amplitude': avg_amplitude,
            'flicker_states': flickering_states,
        }
    else:
        return {
            'flickering_detected': False,
            'flicker_count': 0,
            'avg_interval': None,
            'avg_amplitude': None,
            'flicker_states': [],
        }


# ─── Run early warning analysis ─────────────────────────────────────────────

def run_early_warning_analysis(params, stress_conditions,
                            t_span=(0, 500), n_points=5000):
    """
    Run complete early warning analysis.

    Parameters
    ----------
    params : dict
        Model parameters
    stress_conditions : dict
        Stress conditions
    t_span : tuple
        Time span
    n_points : int
        Number of time points

    Returns
    -------
    ews_analysis : dict
        Complete early warning analysis
    """
    from module1.neurmito_system import simulate, CARDIAC_IC

    # Run simulation
    t_eval = np.linspace(*t_span, n_points)
    sol = simulate(t_span, t_eval, y0=CARDIAC_IC,
                 params=params, stress=stress_conditions)

    if not sol.success:
        return None

    # Compute CSD metrics
    csd_metrics = compute_csd_metrics(sol)

    # Compute spatial EWS
    trajectory_2d = np.column_stack([
        sol.y[IDX['DPsi'], :],
        sol.y[IDX['ATP_m'], :]
    ])
    spatial_ews = compute_spatial_ews(trajectory_2d)

    # Detect flickering
    flickering = detect_flickering(sol)

    # Run original CSD detection
    original_csd = detect_critical_slowing_down(sol)

    # Combine all metrics
    ews_analysis = {
        'csd_metrics': csd_metrics,
        'spatial_ews': spatial_ews,
        'flickering': flickering,
        'original_csd': original_csd,
        'trajectory': {
            't': sol.t,
            'DPsi': sol.y[IDX['DPsi'], :],
            'ATP': sol.y[IDX['ATP_m'], :],
            'H2O2': sol.y[IDX['H2O2_m'], :],
        }
    }

    return ews_analysis


# ─── Warning time estimation ───────────────────────────────────────────────

def estimate_warning_time(params, stress_conditions):
    """
    Estimate time to failure based on early warning signals.

    Parameters
    ----------
    params : dict
        Model parameters
    stress_conditions : dict
        Stress conditions

    Returns
    -------
    warning_time : dict
        Warning time estimation
    """
    # Run analysis
    ews_analysis = run_early_warning_analysis(params, stress_conditions)

    if ews_analysis is None:
        return None

    # Extract key metrics
    csd = ews_analysis['csd_metrics']
    flickering = ews_analysis['flickering']

    # Estimate warning time based on CSD slope
    # Higher slope = faster approaching critical point
    if csd['slope_dp'] > 0.01:
        # Using exponential relationship
        warning_time = 1.0 / csd['slope_dp']  # Approximate
    else:
        warning_time = None

    # Estimate based on flickering
    if flickering['flickering_detected']:
        # Flickering near criticality
        flickering_factor = flickering['avg_amplitude'] * 10
        if warning_time is None:
            warning_time = flickering_factor
        else:
            warning_time = min(warning_time, flickering_factor)

    # Confidence score
    confidence = 0.0

    if csd['slope_dp'] > 0.01:
        confidence += 0.4
    if csd['variance_final'] > 0.5:
        confidence += 0.3
    if flickering['flickering_detected']:
        confidence += 0.3

    confidence = min(confidence, 1.0)

    return {
        'warning_time': warning_time,
        'confidence': confidence,
        'csd_slope': csd['slope_dp'],
        'variance_final': csd['variance_final'],
        'flickering_detected': flickering['flickering_detected'],
        'metrics': ews_analysis,
    }


if __name__ == '__main__':
    from module1.bazil2016_ode import DEFAULT_PARAMS

    print("Testing early warning signal detection...")
    ews = run_early_warning_analysis(DEFAULT_PARAMS.copy(),
                                   {'rotenone': 5e-3},
                                   t_span=(0, 300))
    print(f"Warning time: {ews['csd_metrics']['slope_dp']:.4f} /s")
    print(f"Variance trend: {ews['csd_metrics']['slope_dp']:.4f} /s")
    print(f"Flickering detected: {ews['flickering']['flickering_detected']}")
