"""
Module 3 — Stress Combination Experiments
Systematically sample multi-dimensional stress space

Stress dimensions:
- Rotenone (Complex I inhibitor): 0 - 0.9 fractional inhibition
- Paraquat (ROS generator): 0 - 20 μM
- Hypoxia (O2 limitation): 1.0 - 0.1 (relative)
- Pesticides (mixture effects): 0 - 5 μM

Outputs:
- Phase diagrams (2D slices)
- Critical surfaces (3D)
- Damage landscapes
"""

import numpy as np
from tqdm import tqdm
import concurrent.futures

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import simulate, IDX, CARDIAC_IC


# ── Stress space definition ───────────────────────────────────────────────────

STRESS_DIMENSIONS = {
    'rotenone': {
        'range': np.linspace(0.0, 0.9, 30),
        'type': 'inhibitor',
        'target': 'Vmax_C1',
        'description': 'Fractional Complex I inhibition',
    },
    'paraquat': {
        'range': np.logspace(-2, 1.3, 30),  # 0.01 to 20 μM
        'type': 'ROS_generator',
        'target': 'k_ROS_C1',
        'description': 'ROS amplification',
    },
    'hypoxia': {
        'range': np.array([1.0, 0.8, 0.6, 0.4, 0.2, 0.1]),
        'type': 'resource_limitation',
        'target': 'O2',
        'description': 'O2 availability',
    },
    'pesticides': {
        'range': np.logspace(-2, 0.7, 20),  # 0.01 to 5 μM
        'type': 'mixture',
        'target': 'Vmax_C1',  # Inhibition of multiple complexes
        'description': 'Pesticide mixture',
    },
}


# ── Apply stress to parameters ───────────────────────────────────────────────

def apply_stress(params, stress_condition):
    """
    Apply a stress condition to model parameters.

    Parameters
    ----------
    params : dict
        Base parameters
    stress_condition : dict
        e.g., {'rotenone': 0.5, 'paraquat': 10.0, 'hypoxia': 0.8}

    Returns
    -------
    params_stressed : dict
        Modified parameters
    """
    params_stressed = params.copy()

    # Rotenone: inhibit Complex I
    if 'rotenone' in stress_condition:
        inhibition = np.clip(float(stress_condition['rotenone']), 0.0, 1.0)
        params_stressed['Vmax_C1'] *= 1.0 - inhibition

    # Paraquat: increase ROS production
    if 'paraquat' in stress_condition:
        concentration = max(float(stress_condition['paraquat']), 0.0)
        params_stressed['k_ROS_C1'] *= 1.0 + 2.0 * concentration
        params_stressed['k_ROS_C3'] *= 1.0 + concentration

    # Hypoxia: reduce O2 availability
    if 'hypoxia' in stress_condition:
        hyp = stress_condition['hypoxia']
        params_stressed['O2_ext'] = DEFAULT_PARAMS['O2_ext'] * hyp

    # Pesticides: inhibit multiple complexes
    if 'pesticides' in stress_condition:
        pest = stress_condition['pesticides']
        # Simplified: general inhibition
        params_stressed['Vmax_C1'] *= (1 - 0.2 * pest)
        params_stressed['Vmax_C3'] *= (1 - 0.15 * pest)

    return params_stressed


# ── Run single stress simulation ───────────────────────────────────────────

def run_stress_simulation(params, stress_condition, t_span=(0, 300),
                       n_points=1000):
    """
    Run a single stress simulation.

    Returns
    -------
    sol : OdeResult
        Solution object
    summary : dict
        Key metrics (DPsi, ATP, ROS, etc.)
    """
    params_stressed = apply_stress(params, stress_condition)
    t_eval = np.linspace(*t_span, n_points)

    # The stress has already been applied to params_stressed. Passing it to
    # simulate again would apply rotenone/paraquat/hypoxia twice.
    sol = simulate(t_span, t_eval, y0=CARDIAC_IC.copy(),
                 params=params_stressed, stress=None)

    if not sol.success:
        return None, None

    # Extract steady-state metrics
    y_ss = sol.y[:, -1]

    summary = {
        'DPsi': y_ss[IDX['DPsi']],
        'ATP_m': y_ss[IDX['ATP_m']],
        'ADP_m': y_ss[IDX['ADP_m']],
        'ATP_ADP_ratio': y_ss[IDX['ATP_m']] / (y_ss[IDX['ADP_m']] + 1e-10),
        'H2O2_m': y_ss[IDX['H2O2_m']],
        'GSH': y_ss[IDX['GSH']],
        'GSSG': (DEFAULT_PARAMS['GSH_total'] - y_ss[IDX['GSH']]) / 2.0,
        'GSH_GSSG_ratio': y_ss[IDX['GSH']] / (DEFAULT_PARAMS['GSH_total'] - y_ss[IDX['GSH']] + 1e-10),
        'success': sol.success,
    }

    return sol, summary


# ── Run stress combinations ───────────────────────────────────────────────

def run_stress_combinations(params, n_samples_per_dim=15,
                         combinations=None,
                         n_workers=4):
    """
    Run multiple stress combinations in parallel.

    Parameters
    ----------
    params : dict
        Base parameters
    n_samples_per_dim : int
        Samples per stress dimension
    combinations : list or None
        Specific combinations to test (if None, use grid)
    n_workers : int
        Parallel workers

    Returns
    -------
    results : list of dict
        Results for each combination
    """
    # Define stress grid
    if combinations is None:
        # Create 2D grid for rotenone x paraquat
        rot_grid = STRESS_DIMENSIONS['rotenone']['range'][:n_samples_per_dim]
        pq_grid = STRESS_DIMENSIONS['paraquat']['range'][:n_samples_per_dim]

        # Generate all combinations
        combinations = []
        for rot in rot_grid:
            for pq in pq_grid:
                combinations.append({'rotenone': rot, 'paraquat': pq})

    print(f"Running {len(combinations)} stress combinations...")

    # Run simulations
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        for stress in combinations:
            future = executor.submit(run_stress_simulation, params, stress)
            futures.append(future)

        for i, future in enumerate(tqdm(concurrent.futures.as_completed(futures),
                                             total=len(futures))):
            sol, summary = future.result()
            if summary is not None:
                summary['stress'] = stress
                results.append(summary)

    print(f"Completed {len(results)} successful simulations")
    return results


# ── Run 3D stress landscape ───────────────────────────────────────────

def run_stress_landscape_3d(params, stress1_name='rotenone',
                              stress2_name='paraquat',
                              stress3_name='hypoxia',
                              n_points_per_dim=10):
    """
    Run 3D stress landscape (combinatorial stress).

    Returns
    -------
    results : dict
        Structured results for 3D grid
    """
    grid1 = STRESS_DIMENSIONS[stress1_name]['range'][:n_points_per_dim]
    grid2 = STRESS_DIMENSIONS[stress2_name]['range'][:n_points_per_dim]
    grid3 = STRESS_DIMENSIONS[stress3_name]['range']

    results = {
        'stress1_values': [],
        'stress2_values': [],
        'stress3_values': [],
        'DPsi': [],
        'ATP_ADP': [],
        'GSH_ratio': [],
    }

    print("Running 3D stress landscape...")
    for s1 in tqdm(grid1):
        for s2 in grid2:
            for s3 in grid3:
                stress = {
                    stress1_name: s1,
                    stress2_name: s2,
                    stress3_name: s3,
                }

                sol, summary = run_stress_simulation(params, stress,
                                                     t_span=(0, 200),
                                                     n_points=500)

                if summary is not None:
                    results['stress1_values'].append(s1)
                    results['stress2_values'].append(s2)
                    results['stress3_values'].append(s3)
                    results['DPsi'].append(summary['DPsi'])
                    results['ATP_ADP'].append(summary['ATP_ADP_ratio'])
                    results['GSH_ratio'].append(summary['GSH_GSSG_ratio'])

    # Convert to arrays
    for key in results:
        results[key] = np.array(results[key])

    print(f"Completed {len(results['DPsi'])} simulations")
    return results


# ── Calculate damage metrics ───────────────────────────────────────────────

def calculate_damage_metrics(summary):
    """
    Calculate damage metrics from simulation summary.

    Parameters
    ----------
    summary : dict
        Simulation summary

    Returns
    -------
    damage : dict
        Damage metrics
    """
    # Define thresholds
    DPsi_critical = 100.0  # mV
    ATP_ADP_critical = 2.0  # Below healthy
    GSH_critical = 0.2  # 20% GSH remaining

    # Damage score (0-1)
    dp = summary['DPsi']
    damage_score = 0.0

    # DPsi damage
    if dp < DPsi_critical:
        damage_score += 0.3 * (1 - dp / DPsi_critical)
    else:
        damage_score += 0.4 * (DPsi_critical - dp) / DPsi_critical

    # ATP damage
    atp_ratio = summary['ATP_ADP_ratio']
    if atp_ratio < ATP_ADP_critical:
        damage_score += 0.3

    # GSH damage
    gsh_ratio = summary['GSH_GSSG_ratio']
    if gsh_ratio < GSH_critical:
        damage_score += 0.2

    # H2O2 damage
    h2o2 = summary['H2O2_m'] * 1000  # μM
    if h2o2 > 1.0:  # 1 μM threshold
        damage_score += 0.2 * min(h2o2 / 10.0, 1.0)

    damage_score = min(damage_score, 1.0)

    damage = {
        'DPsi_damage': 1 - dp / 180.0 if dp < 180.0 else dp / 180.0,
        'ATP_damage': 1 - atp_ratio / 10.0,
        'ROS_damage': summary['H2O2_m'] / 1.0,  # Normalized
        'overall_damage': damage_score,
        'collapsed': damage_score > 0.6,
    }

    return damage


if __name__ == '__main__':
    # Example: run 2D stress combinations
    print("Running 2D stress combinations (rotenone x paraquat)...")
    results = run_stress_combinations(DEFAULT_PARAMS.copy(),
                                     n_samples_per_dim=10,
                                     n_workers=2)
    print(f"Generated {len(results)} stress response samples")
