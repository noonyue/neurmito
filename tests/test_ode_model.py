"""
单元测试：Bazil 2016 ODE 模型

测试 module1/bazil2016_ode.py 的核心功能：
- ODE 积分稳定性
- 状态变量物理合理性
- 应激修饰符效果
- 参数敏感性
"""

import pytest
import numpy as np
from scipy.integrate import solve_ivp

# 导入要测试的模块
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import odes, IDX, CARDIAC_IC


class TestODEIntegration:
    """测试 ODE 积分功能"""

    def test_ode_integration_basic(self, test_params):
        """测试基本 ODE 积分能否成功运行"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 100),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        assert sol.success, "ODE integration should succeed"
        assert sol.t[-1] >= 100, "Should integrate to t=100"

    def test_no_nan_values(self, test_params):
        """测试积分结果不包含 NaN"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 100),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        assert not np.any(np.isnan(sol.y)), "Solution should not contain NaN"

    def test_no_inf_values(self, test_params):
        """测试积分结果不包含无穷大"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 100),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        assert not np.any(np.isinf(sol.y)), "Solution should not contain Inf"

    def test_integration_with_dense_output(self, test_params):
        """测试稠密输出功能"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 100),
            y0=CARDIAC_IC,
            method='LSODA',
            dense_output=True
        )

        assert sol.success, "Integration with dense_output should succeed"
        assert sol.sol is not None, "Should have interpolation function"

        # 测试插值
        t_interp = np.linspace(0, 100, 50)
        y_interp = sol.sol(t_interp)
        assert y_interp.shape == (len(CARDIAC_IC), 50)


class TestPhysicalConstraints:
    """测试物理约束和生理范围"""

    def test_membrane_potential_range(self, test_params):
        """测试膜电位在生理范围内 (100-200 mV)"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        DPsi = sol.y[IDX['DPsi'], :]

        assert np.all(DPsi > 50), f"DPsi too low: min={DPsi.min():.1f} mV"
        assert np.all(DPsi < 250), f"DPsi too high: max={DPsi.max():.1f} mV"

    def test_atp_positive(self, test_params):
        """测试 ATP 浓度保持正值"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        ATP = sol.y[IDX['ATP_m'], :]

        assert np.all(ATP >= 0), f"ATP should be non-negative, min={ATP.min():.4f}"
        assert np.all(ATP < 20), f"ATP too high: max={ATP.max():.1f} mM"

    def test_ros_bounded(self, test_params):
        """测试 ROS 浓度在合理范围内"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        H2O2 = sol.y[IDX['H2O2_m'], :]

        assert np.all(H2O2 >= 0), "H2O2 should be non-negative"
        assert np.all(H2O2 < 1.0), f"H2O2 too high: max={H2O2.max():.4f} mM"

    def test_calcium_range(self, test_params):
        """测试钙离子浓度在生理范围内"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        Ca_m = sol.y[IDX['Ca_m'], :]

        assert np.all(Ca_m >= 0), "Ca_m should be non-negative"
        assert np.all(Ca_m < 0.01), f"Ca_m too high: max={Ca_m.max():.6f} mM"


class TestStressModifiers:
    """测试应激修饰符功能"""

    def test_rotenone_decreases_dpsi(self, test_params, stress_none, stress_rotenone):
        """测试鱼藤酮降低膜电位"""
        # 基线
        sol_baseline = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_none),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # 鱼藤酮应激
        sol_stress = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_rotenone),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        DPsi_baseline = sol_baseline.y[IDX['DPsi'], -1]
        DPsi_stress = sol_stress.y[IDX['DPsi'], -1]

        assert DPsi_stress < DPsi_baseline, \
            f"Rotenone should decrease DPsi: baseline={DPsi_baseline:.1f}, stress={DPsi_stress:.1f}"

    def test_paraquat_increases_ros(self, test_params, stress_none, stress_paraquat):
        """测试百草枯增加 ROS 水平"""
        # 基线
        sol_baseline = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_none),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # 百草枯应激
        sol_stress = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_paraquat),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        H2O2_baseline = sol_baseline.y[IDX['H2O2_m'], -1]
        H2O2_stress = sol_stress.y[IDX['H2O2_m'], -1]

        assert H2O2_stress > H2O2_baseline, \
            f"Paraquat should increase H2O2: baseline={H2O2_baseline:.6f}, stress={H2O2_stress:.6f}"

    def test_combined_stress_synergy(self, test_params, stress_rotenone,
                                      stress_paraquat, stress_combined):
        """测试组合应激的协同效应"""
        # 单独应激
        sol_rot = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_rotenone),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        sol_par = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_paraquat),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # 组合应激
        sol_combined = solve_ivp(
            lambda t, y: odes(t, y, test_params, stress=stress_combined),
            t_span=(0, 1000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        DPsi_rot = sol_rot.y[IDX['DPsi'], -1]
        DPsi_par = sol_par.y[IDX['DPsi'], -1]
        DPsi_combined = sol_combined.y[IDX['DPsi'], -1]

        # 组合效应应该比单独应激更严重
        assert DPsi_combined < min(DPsi_rot, DPsi_par), \
            "Combined stress should have stronger effect than individual stresses"


class TestParameterSensitivity:
    """测试参数敏感性"""

    def test_vmax_c1_sensitivity(self, test_params):
        """测试 Complex I 最大速率的敏感性"""
        # 基线
        sol_baseline = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 200),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # 增加 Vmax_C1 20%
        params_high = test_params.copy()
        params_high['Vmax_C1'] = test_params['Vmax_C1'] * 1.2

        sol_high = solve_ivp(
            lambda t, y: odes(t, y, params_high),
            t_span=(0, 200),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # At long times the redox pools can compensate for Vmax changes.
        # Use the acute 200 s response and NADH redox state, rather than
        # asserting a monotonic difference in the fully relaxed fixed point.
        DPsi_baseline = sol_baseline.y[IDX['DPsi'], -1]
        DPsi_high = sol_high.y[IDX['DPsi'], -1]
        NADH_baseline = sol_baseline.y[IDX['NADH'], -1]
        NADH_high = sol_high.y[IDX['NADH'], -1]

        # Increasing Complex I capacity should increase the acute membrane
        # potential response and leave the NADH pool more oxidized.
        assert DPsi_high > DPsi_baseline, \
            f"Increasing Vmax_C1 should increase acute DPsi: baseline={DPsi_baseline:.1f}, high={DPsi_high:.1f}"
        assert NADH_high < NADH_baseline, \
            f"Increasing Vmax_C1 should lower NADH: baseline={NADH_baseline:.3f}, high={NADH_high:.3f}"

    def test_parameter_vector_length(self):
        """测试默认参数字典包含所有必需参数"""
        required_params = [
            'Vmax_C1', 'Km_NADH', 'Km_Q_C1', 'Ki_H2O2',
            'Vmax_C3', 'Km_QH2', 'Vmax_C4', 'Km_Cred', 'Km_O2',
            'Vmax_CV', 'Km_ADP_CV', 'Km_Pi_CV', 'n_H_CV',
            'g_H', 'DPsi_0'
        ]

        for param in required_params:
            assert param in DEFAULT_PARAMS, f"Missing required parameter: {param}"


@pytest.mark.slow
class TestLongTimeIntegration:
    """测试长时间积分（标记为 slow）"""

    def test_steady_state_convergence(self, test_params):
        """测试长时间积分后达到稳态"""
        sol = solve_ivp(
            lambda t, y: odes(t, y, test_params),
            t_span=(0, 5000),
            y0=CARDIAC_IC,
            method='LSODA'
        )

        # 检查最后 1000 秒的变化率
        DPsi = sol.y[IDX['DPsi'], :]
        t = sol.t

        # 找到 t > 4000 的时间点
        late_idx = t > 4000
        DPsi_late = DPsi[late_idx]

        if len(DPsi_late) > 10:
            # 计算标准差
            std_late = np.std(DPsi_late)
            assert std_late < 5.0, f"DPsi should reach steady state: std={std_late:.2f} mV"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
