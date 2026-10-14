"""
Module 3 — Bistability Analysis
Detect and characterize bistability in neuronal mitochondrial dynamics

Bistability metrics:
1. Basin of attraction analysis
2. Potential energy surfaces
3. Hysteresis loops
4. Critical slowing down (CSD)
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import odes, IDX, CARDIAC_IC


# ── Detect steady states ───────────────────────────────────────────────────

def find_steady_states(y_trajectory, threshold=1e-4):
    """
    Find steady states from trajectory.

    Parameters
    ----------
    y_trajectory : array (n_times, n_states)
        System trajectory
    threshold : float
        Convergence threshold

    Returns
    -------
    steady_states : list
        Indices where steady state is reached
    """
    # Check if last N points are within threshold
    y_last = y_trajectory[-100:]  # Last 100 points

    std_last = np.std(y_last, axis=0)
    mean_last = np.mean(y_last, axis=0)

    # Convergence criterion
    converged = np.all(std_last < threshold, axis=0)

    if converged:
        # Return the final steady state
        return [y_trajectory[-1]]
    else:
        # Return None if not converged
        return None


def run_to_steady_state(params, y0, max_time=1000, dt=0.1):
    """
    Run simulation to steady state.

    Parameters
    ----------
    params : dict
        Model parameters
    y0 : array
        Initial conditions
    max_time : float
        Maximum simulation time
    dt : float
        Time step

    Returns
    -------
    t : array
        Time points
    y : array
        State trajectory
    converged : bool
        Whether converged to steady state
    """
    n_steps = int(max_time / dt)
    t = np.linspace(0, max_time, n_steps)

    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0

    # Simple Euler integration (for steady state detection)
    for i in tqdm(range(n_steps), desc="Integrating to steady state"):
        dydt = odes(t[i], y[i], params)

        if dydt is None:
            return None, None, False

        y[i + 1] = y[i] + dydt * dt

    # Check convergence
    y_last = y[-100:]
    std_last = np.std(y_last, axis=0)

    converged = np.all(std_last < 1e-4, axis=0)

    return t, y, converged


# ── Bistability detection ─────────────────────────────────────────────────────

def detect_bistability(params, y0_1, y0_2, stress_conditions,
                   max_time=1000, dt=0.1):
    """
    Detect bistability by comparing final states from different initial conditions.

    Parameters
    ----------
    params : dict
        Model parameters
    y0_1, y0_2 : arrays
        Two different initial conditions
    stress_conditions : dict
        Stress conditions
    max_time : float
        Maximum simulation time
    dt : float
        Time step

    Returns
    -------
    result : dict
        Bistability analysis results
    """
    # Run from IC1
    print("Running from IC1...")
    t1, y1, converged1 = run_to_steady_state(params, y0_1, max_time, dt)

    if y1 is None or not converged1:
        return {
            'bistable': False,
            'y_ss1': None,
            'y_ss2': None,
            'basin_separation': None,
            'energy_surface': None,
        }

    # Run from IC2
    print("Running from IC2...")
    t2, y2, converged2 = run_to_steady_state(params, y0_2, max_time, dt)

    if y2 is None or not converged2:
        return {
            'bistable': False,
            'y_ss1': y1[-1] if converged1 else None,
            'y_ss2': None,
            'basin_separation': None,
            'energy_surface': None,
        }

    # Extract final states
    y_ss1 = y1[-1]
    y_ss2 = y2[-1]

    # Check if states are different (bistability)
    state_difference = np.linalg.norm(y_ss1 - y_ss2)
    normalized_diff = state_difference / (np.linalg.norm(y_ss1) + 1e-10)

    bistable = normalized_diff > 0.1  # States differ by >10%

    if not bistable:
        return {
            'bistable': False,
            'y_ss1': y_ss1,
            'y_ss2': y_ss2,
            'basin_separation': 0.0,
            'energy_surface': None,
        }

    # Calculate basin separation
    # Use DPsi and ATP as key indicators
    dpsi_1 = y_ss1[IDX['DPsi']]
    dpsi_2 = y_ss2[IDX['DPsi']]
    atp_1 = y_ss1[IDX['ATP_m']]
    atp_2 = y_ss2[IDX['ATP_m']]

    basin_separation = np.sqrt(
        (dpsi_1 - dpsi_2)**2 / 180.0**2 +
        (atp_1 - atp_2)**2 / 10.0**2
    )

    # Estimate energy surface (simplified)
    # Energy ∝ -(DPsi - DPsi_target)² - λ * (ATP - ATP_target)²
    dpsi_target = 180.0  # Healthy DPsi
    atp_target = 9.0  # Healthy ATP

    energy_1 = -(dpsi_1 - dpsi_target)**2 - 0.5 * (atp_1 - atp_target)**2
    energy_2 = -(dpsi_2 - dpsi_target)**2 - 0.5 * (atp_2 - atp_target)**2

    result = {
        'bistable': bistable,
        'y_ss1': y_ss1,
        'y_ss2': y_ss2,
        'basin_separation': basin_separation,
        'energy_surface': (energy_1, energy_2),
        'state_1_healthy': dpsi_1 > 150 and atp_1 > 7,
        'state_2_healthy': dpsi_2 > 150 and atp_2 > 7,
    }

    return result


# ── Hysteresis analysis ─────────────────────────────────────────────────────

def analyze_hysteresis(params, stress_path, y0, max_time=800, dt=0.1):
    """
    Analyze hysteresis: path dependence in stress recovery.

    Parameters
    ----------
    params : dict
        Base parameters
    stress_path : list of dict
        Stress conditions along a path (e.g., increase then decrease)
    y0 : array
        Initial condition
    max_time : float
        Maximum time per condition
    dt : float
        Time step

    Returns
    -------
    hysteresis : dict
        Hysteresis analysis results
    """
    current_time = 0
    y_current = y0.copy()

    trajectory_time = []
    trajectory_y = []
    stress_levels = []

    print("Analyzing hysteresis loop...")

    for i, stress in enumerate(tqdm(stress_path, desc="Hysteresis simulation")):
        t_span = (current_time, current_time + max_time)
        t_eval = np.linspace(*t_span, int(max_time / dt))

        sol = simulate(t_span, t_eval, y0=y_current,
                     params=params, stress=stress)

        if not sol.success:
            continue

        # Update
        current_time += max_time
        y_current = sol.y[:, -1]

        # Record trajectory
        trajectory_time.append(current_time)
        trajectory_y.append(y_current.copy())

        # Extract stress level
        if 'rotenone' in stress:
            stress_levels.append(stress['rotenone'])
        elif 'paraquat' in stress:
            stress_levels.append(stress['paraquat'])
        else:
            stress_levels.append(0.0)

    if len(trajectory_y) < 10:
        return None

    # Detect hysteresis
    # Forward vs reverse path comparison
    stress_array = np.array(stress_levels)

    # Find peaks in stress
    peaks, _ = find_peaks(stress_array)

    if len(peaks) < 2:
        return {
            'has_hysteresis': False,
            'hysteresis_width': 0.0,
            'forward_path': None,
            'reverse_path': None,
        }

    # Calculate hysteresis width
    # At a given stress level, compare forward and reverse responses
    forward_path = []
    reverse_path = []

    for stress_level in np.unique(stress_array):
        # Forward path responses at this stress level
        forward_vals = []
        reverse_vals = []

        for j, (t, y) in enumerate(zip(trajectory_time, trajectory_y)):
            idx = np.abs(stress_array[j] - stress_level) < 1e-6
            if idx:
                forward_vals.append(y[IDX['DPsi']])
                if j < len(trajectory_time) // 2:
                    break
                reverse_vals.append(y[IDX['DPsi']])

        if len(forward_vals) > 0 and len(reverse_vals) > 0:
            forward_path.append((stress_level, np.mean(forward_vals)))
            reverse_path.append((stress_level, np.mean(reverse_vals)))

    if len(forward_path) < 2:
        return {
            'has_hysteresis': False,
            'hysteresis_width': 0.0,
            'forward_path': forward_path,
            'reverse_path': reverse_path,
        }

    # Calculate hysteresis width
    forward_vals = np.array([y for x, y in forward_path])
    reverse_vals = np.array([y for x, y in reverse_path])

    hysteresis_width = np.mean(np.abs(forward_vals - reverse_vals))

    return {
        'has_hysteresis': hysteresis_width > 10.0,
        'hysteresis_width': hysteresis_width,
        'forward_path': forward_path,
        'reverse_path': reverse_path,
        'stress_trajectory': stress_array,
        'dpsi_trajectory': np.array([y[IDX['DPsi']] for y in trajectory_y]),
    }


# ── Critical slowing down detection ───────────────────────────────────────────

def detect_critical_slowing_down(sol, idx_dpsi=IDX['DPsi'],
                                  window_size=50):
    """
    Detect critical slowing down (CSD) as early warning signal.

    Parameters
    ----------
    sol : OdeResult
        Simulation solution
    idx_dpsi : int
        Index of DPsi in state vector
    window_size : int
        Window for autocorrelation/variance

    Returns
    -------
    csd : dict
        CSD metrics
    """
    if not sol.success:
        return None

    dpsi_trajectory = sol.y[idx_dpsi, :]
    n_points = len(dpsi_trajectory)

    # Calculate rolling variance
    variance = np.zeros(n_points)
    autocorr = np.zeros(n_points)

    for i in range(window_size, n_points):
        window = dpsi_trajectory[max(0, i - window_size):i]

        # Variance
        variance[i] = np.var(window)

        # Autocorrelation (lag-1)
        if i > window_size:
            lag_1 = window[:-1]
            lag_0 = window[1:]
            autocorr[i] = np.corrcoef(lag_0, lag_1)[0, 1]

    # Normalize
    variance_norm = variance / (np.max(variance) + 1e-10)
    autocorr_norm = autocorr / (np.max(np.abs(autocorr)) + 1e-10)

    # CSD detection: both increase
    csd_window = variance_norm * autocorr_norm
    csd_threshold = 0.3 * np.mean(csd_window[window_size:])

    # Find onset time
    csd_onset = None
    for i in range(window_size, n_points):
        if csd_window[i] > csd_threshold and csd_onset is None:
            csd_onset = sol.t[i]

    if csd_onset is None:
        csd_onset = sol.t[window_size]

    # Collapse time
    collapse_threshold = 100.0  # DPsi < 100 mV
    collapse_time = None
    for i in range(window_size, n_points):
        if dpsi_trajectory[i] < collapse_threshold:
            collapse_time = sol.t[i]
            break

    return {
        'variance_trajectory': variance_norm,
        'autocorr_trajectory': autocorr_norm,
        'csd_trajectory': csd_window,
        'csd_onset_time': csd_onset,
        'collapse_time': collapse_time,
        'warning_window': collapse_time - csd_onset if collapse_time else 0,
    }


if __name__ == '__main__':
    # Example: detect bistability with two different ICs
    print("Detecting bistability...")
    result = detect_bistability(
        DEFAULT_PARAMS.copy(),
        CARDIAC_IC.copy(),
        CARDIAC_IC.copy() * 1.2,  # Different IC
        {},
        max_time=500,
        dt=0.1
    )
    print(f"Bistable: {result['bistable']}")
    print(f"Basin separation: {result['basin_separation']:.3f}")
