"""
Module 3 — Phase Diagram Construction
Build multi-dimensional stress phase diagrams and critical surfaces
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

from .stress_combination import (
    run_stress_combinations,
    run_stress_landscape_3d,
    calculate_damage_metrics,
    STRESS_DIMENSIONS,
)


# ── Construct 2D phase diagram ───────────────────────────────────────────

def construct_2d_phase_diagram(results, stress1_name='rotenone',
                            stress2_name='paraquat',
                            n_grid=20):
    """
    Construct 2D phase diagram from stress combination results.

    Parameters
    ----------
    results : list of dict
        Stress combination results
    stress1_name : str
        First stress dimension
    stress2_name : str
        Second stress dimension
    n_grid : int
        Grid resolution

    Returns
    -------
    phase_diagram : dict
        2D phase diagram data
    """
    # Create grid
    stress1_grid = STRESS_DIMENSIONS[stress1_name]['range'][:n_grid]
    stress2_grid = STRESS_DIMENSIONS[stress2_name]['range'][:n_grid]

    # Organize results into grid
    dp_grid = np.zeros((n_grid, n_grid))
    damage_grid = np.zeros((n_grid, n_grid))

    for result in results:
        stress = result['stress']

        # Find grid indices
        idx1 = np.argmin(np.abs(stress1_grid - stress[stress1_name]))
        idx2 = np.argmin(np.abs(stress2_grid - stress[stress2_name]))

        dp_grid[idx1, idx2] = result['DPsi']
        damage_grid[idx1, idx2] = result.get('overall_damage', 0.5)

    return {
        'stress1_grid': stress1_grid,
        'stress2_grid': stress2_grid,
        'DPsi_grid': dp_grid,
        'damage_grid': damage_grid,
    }


# ── Construct 3D phase surface ─────────────────────────────────────────────

def construct_3d_phase_surface(results_3d):
    """
    Construct 3D stress phase surface.

    Parameters
    ----------
    results_3d : dict
        3D stress landscape results

    Returns
    -------
    phase_surface : dict
        3D phase surface data
    """
    # Extract grid data
    S1, S2, S3 = results_3d['stress1_values'], \
                     results_3d['stress2_values'], \
                     results_3d['stress3_values']

    # Organize into unique grid
    S1_unique = np.unique(S1)
    S2_unique = np.unique(S2)
    S3_unique = np.unique(S3)

    # Create meshgrid
    S1_mesh, S2_mesh, S3_mesh = np.meshgrid(S1_unique, S2_unique, S3_unique)

    # Interpolate DPsi
    from scipy.interpolate import griddata
    DPsi_surface = griddata(
        (S1, S2, S3),
        results_3d['DPsi'],
        (S1_mesh, S2_mesh, S3_mesh),
        method='linear',
    )

    return {
        'S1_mesh': S1_mesh,
        'S2_mesh': S2_mesh,
        'S3_mesh': S3_mesh,
        'DPsi_surface': DPsi_surface,
    }


# ── Identify critical boundaries ───────────────────────────────────────────────

def identify_critical_boundaries(phase_diagram, dp_threshold=120.0,
                                 damage_threshold=0.6):
    """
    Identify critical boundaries in phase diagram.

    Parameters
    ----------
    phase_diagram : dict
        Phase diagram data
    dp_threshold : float
        DPsi threshold for criticality
    damage_threshold : float
        Damage threshold for criticality

    Returns
    -------
    boundaries : dict
        Critical boundary information
    """
    dp_grid = phase_diagram['DPsi_grid']
    damage_grid = phase_diagram['damage_grid']

    # Find boundary where DPsi = threshold
    dp_boundary = None
    dp_boundary_points = []

    for i in range(dp_grid.shape[0]):
        for j in range(dp_grid.shape[1]):
            if abs(dp_grid[i, j] - dp_threshold) < 10.0:
                dp_boundary_points.append((i, j))

    if len(dp_boundary_points) > 0:
        dp_boundary = np.array(dp_boundary_points)

    # Find damage boundary
    damage_boundary_points = []
    for i in range(damage_grid.shape[0]):
        for j in range(damage_grid.shape[1]):
            if abs(damage_grid[i, j] - damage_threshold) < 0.1:
                damage_boundary_points.append((i, j))

    if len(damage_boundary_points) > 0:
        damage_boundary = np.array(damage_boundary_points)
    else:
        damage_boundary = None

    return {
        'dp_boundary': dp_boundary,
        'damage_boundary': damage_boundary,
        'critical_region': damage_grid > damage_threshold,
    }


# ── Plot 2D phase diagram ───────────────────────────────────────────────

def plot_2d_phase_diagram(phase_diagram, ax,
                           stress1_label='Rotenone (μM)',
                           stress2_label='Paraquat (μM)'):
    """
    Plot 2D phase diagram.

    Parameters
    ----------
    phase_diagram : dict
        Phase diagram data
    ax : matplotlib Axes
        Axes to plot on
    stress1_label, stress2_label : str
        Axis labels
    """
    stress1 = phase_diagram['stress1_grid']
    stress2 = phase_diagram['stress2_grid']
    dp = phase_diagram['DPsi_grid']
    damage = phase_diagram['damage_grid']

    # Contour plot
    contour_levels = np.linspace(dp.min(), dp.max(), 20)

    # Plot contours
    cs1 = ax.contour(stress1, stress2, dp, levels=contour_levels,
                     colors='k', linewidths=0.5, alpha=0.5)
    ax.clabel(cs1, inline=True, fontsize=7)

    # Highlight critical regions
    critical_mask = damage > 0.6
    ax.contourf(stress1, stress2, critical_mask,
                levels=[0.5, 1.0], colors=['none', 'red'],
                alpha=0.3)

    # Add colorbar
    cbar = plt.colorbar(cs1, ax=ax)
    cbar.set_label('ΔΨm (mV)')

    ax.set_xlabel(stress1_label)
    ax.set_ylabel(stress2_label)
    ax.set_xscale('log')
    ax.set_yscale('log')


# ── Plot 3D phase surface ───────────────────────────────────────────────

def plot_3d_phase_surface(phase_surface, ax):
    """
    Plot 3D stress phase surface.

    Parameters
    ----------
    phase_surface : dict
        3D phase surface data
    ax : matplotlib Axes 3D
        3D axes to plot on
    """
    S1 = phase_surface['S1_mesh']
    S2 = phase_surface['S2_mesh']
    S3 = phase_surface['S3_mesh']
    DPsi = phase_surface['DPsi_surface']

    # Plot surface
    surf = ax.plot_surface(S1, S2, S3, DPsi, cmap='RdYlBu_r',
                              alpha=0.8, linewidth=0, antialiased=False)

    ax.set_xlabel('Rotenone (μM)')
    ax.set_ylabel('Paraquat (μM)')
    ax.set_zlabel('ΔΨm (mV)')


def construct_phase_diagram(params):
    """
    Main function to construct phase diagram.

    Parameters
    ----------
    params : dict
        Model parameters

    Returns
    -------
    phase_diagram : dict
        Phase diagram data
    """
    # Run 2D stress combinations
    results = run_stress_combinations(params, n_samples_per_dim=15,
                                     n_workers=2)

    # Extract DPsi and damage
    dp_values = np.array([r['DPsi'] for r in results])
    damage_values = np.array([r.get('overall_damage', 0.5) for r in results])

    # Identify critical region
    critical_mask = damage_values > 0.6

    # Estimate boundary (simplified)
    stress1 = np.array([r['stress']['rotenone'] for r in results])
    stress2 = np.array([r['stress']['paraquat'] for r in results])

    return {
        'stress1': stress1,
        'stress2': stress2,
        'DPsi': dp_values,
        'damage': damage_values,
        'critical_mask': critical_mask,
        'results': results,
    }


if __name__ == '__main__':
    print("Constructing phase diagram...")
    phase_diagram = construct_phase_diagram(DEFAULT_PARAMS.copy())
    print(f"Phase diagram constructed with {len(phase_diagram['DPsi'])} points")
