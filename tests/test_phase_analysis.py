"""Regression tests for stress semantics in the Module 3 pipeline."""

import numpy as np

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import simulate
from module3.stress_combination import apply_stress, run_stress_simulation


def test_apply_stress_uses_fractional_rotenone_and_paraquat_index():
    stressed = apply_stress(
        DEFAULT_PARAMS,
        {'rotenone': 0.5, 'paraquat': 10.0, 'hypoxia': 0.2},
    )

    assert stressed['Vmax_C1'] == DEFAULT_PARAMS['Vmax_C1'] * 0.5
    assert stressed['k_ROS_C1'] == DEFAULT_PARAMS['k_ROS_C1'] * 21.0
    assert stressed['k_ROS_C3'] == DEFAULT_PARAMS['k_ROS_C3'] * 11.0
    assert stressed['O2_ext'] == DEFAULT_PARAMS['O2_ext'] * 0.2


def test_stress_pipeline_applies_each_stressor_once():
    stress = {'rotenone': 0.5, 'paraquat': 10.0}
    wrapped, _ = run_stress_simulation(
        DEFAULT_PARAMS.copy(), stress, t_span=(0.0, 100.0), n_points=101
    )
    direct = simulate(
        (0.0, 100.0),
        np.linspace(0.0, 100.0, 101),
        params=DEFAULT_PARAMS.copy(),
        stress=stress,
    )

    assert wrapped.success and direct.success
    np.testing.assert_allclose(wrapped.y, direct.y, rtol=1e-7, atol=1e-9)
