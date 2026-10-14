"""
单元测试：混合神经-ODE 模型

测试 module2/neural_ode_model.py 的核心功能：
- NeuralODECell 前向传播
- HybridNeuralODE 模型集成
- 训练流程
- 模型保存和加载
"""

import pytest
import torch
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from module2.neural_ode_model import NeuralODECell, HybridNeuralODE


class TestNeuralODECell:
    """测试 NeuralODECell 类"""

    def test_initialization(self):
        """测试模型初始化"""
        model = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        assert model is not None
        assert hasattr(model, 'net')
        assert isinstance(model.net, torch.nn.Sequential)

    def test_forward_shape(self):
        """测试前向传播输出形状"""
        model = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        batch_size = 8
        t = torch.tensor(0.0)
        y = torch.randn(batch_size, 4)

        output = model(t, y)

        assert output.shape == (batch_size, 1)

    def test_forward_no_nan(self):
        """测试前向传播不产生 NaN"""
        model = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.randn(10, 4)

        output = model(t, y)

        assert not torch.isnan(output).any(), "Output should not contain NaN"

    def test_forward_no_inf(self):
        """测试前向传播不产生无穷大"""
        model = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.randn(10, 4)

        output = model(t, y)

        assert not torch.isinf(output).any(), "Output should not contain Inf"

    def test_gradient_flow(self):
        """测试梯度能够反向传播"""
        model = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.randn(5, 4, requires_grad=True)

        output = model(t, y)
        loss = output.sum()
        loss.backward()

        # 检查输入的梯度
        assert y.grad is not None
        assert not torch.isnan(y.grad).any()

    def test_parameter_count(self):
        """测试参数数量合理"""
        input_dim = 4
        hidden_dim = 32
        output_dim = 1

        model = NeuralODECell(input_dim, hidden_dim, output_dim)

        total_params = sum(p.numel() for p in model.parameters())

        # 预期参数数量：
        # Layer 1: input_dim * hidden_dim + hidden_dim
        # Layer 2: hidden_dim * hidden_dim + hidden_dim
        # Layer 3: hidden_dim * output_dim + output_dim
        expected = (input_dim * hidden_dim + hidden_dim) + \
                   (hidden_dim * hidden_dim + hidden_dim) + \
                   (hidden_dim * output_dim + output_dim)

        assert total_params == expected, f"Expected {expected} params, got {total_params}"


class TestHybridNeuralODE:
    """测试 HybridNeuralODE 模型"""

    def test_initialization(self):
        """测试混合模型初始化"""
        neural_cell = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=1)

        def dummy_mechanistic(t, y):
            return torch.zeros_like(y)

        hybrid = HybridNeuralODE(
            mechanistic_model=dummy_mechanistic,
            neural_ode=neural_cell,
            mech_indices=[0, 1, 2, 3],
            neural_indices=[4]
        )

        assert hybrid is not None
        assert hybrid.mechanistic_model is not None
        assert hybrid.neural_ode is not None

    def test_forward_integration(self):
        """测试前向积分"""
        neural_cell = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        def dummy_mechanistic(t, y):
            # 简单的线性动力学
            return -0.1 * y

        hybrid = HybridNeuralODE(
            mechanistic_model=dummy_mechanistic,
            neural_ode=neural_cell,
            mech_indices=[0, 1, 2, 3],
            neural_indices=[4]
        )

        batch_size = 2
        state_dim = 5
        y0 = torch.randn(batch_size, state_dim)
        t = torch.linspace(0, 10, 50)

        # 执行前向传播
        y_pred = hybrid(y0, t)

        assert y_pred.shape == (batch_size, 50, state_dim)
        assert not torch.isnan(y_pred).any()

    def test_mechanistic_only_mode(self):
        """测试仅机制性模型模式"""
        neural_cell = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        def mechanistic_decay(t, y):
            return -0.5 * y

        hybrid = HybridNeuralODE(
            mechanistic_model=mechanistic_decay,
            neural_ode=neural_cell,
            mech_indices=[0, 1, 2, 3, 4],  # 所有状态都用机制性模型
            neural_indices=[]  # 无神经网络状态
        )

        y0 = torch.ones(1, 5)
        t = torch.linspace(0, 2, 20)

        y_pred = hybrid(y0, t)

        # 应该呈指数衰减
        assert y_pred[0, -1, 0] < y_pred[0, 0, 0]

    @pytest.mark.slow
    def test_training_step(self):
        """测试训练步骤"""
        neural_cell = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        def dummy_mechanistic(t, y):
            return -0.1 * y

        hybrid = HybridNeuralODE(
            mechanistic_model=dummy_mechanistic,
            neural_ode=neural_cell,
            mech_indices=[0, 1, 2, 3],
            neural_indices=[4]
        )

        optimizer = torch.optim.Adam(hybrid.parameters(), lr=0.001)

        # 模拟训练数据
        y0 = torch.randn(4, 5)
        t = torch.linspace(0, 5, 25)
        y_true = torch.randn(4, 25, 5)

        # 训练一步
        optimizer.zero_grad()
        y_pred = hybrid(y0, t)
        loss = torch.nn.functional.mse_loss(y_pred, y_true)
        loss.backward()
        optimizer.step()

        # 确保损失是有限的
        assert torch.isfinite(loss)


class TestModelPersistence:
    """测试模型保存和加载"""

    def test_save_and_load_state_dict(self, tmp_path):
        """测试模型状态字典保存和加载"""
        # 创建模型
        model1 = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        # 保存
        save_path = tmp_path / "model.pt"
        torch.save(model1.state_dict(), save_path)

        # 加载到新模型
        model2 = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)
        model2.load_state_dict(torch.load(save_path))

        # 测试输出一致
        test_input = torch.randn(5, 4)
        t = torch.tensor(0.0)

        with torch.no_grad():
            out1 = model1(t, test_input)
            out2 = model2(t, test_input)

        assert torch.allclose(out1, out2, atol=1e-6)

    def test_model_reproducibility(self):
        """测试模型输出的可重复性"""
        torch.manual_seed(42)
        model = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        t = torch.tensor(0.0)
        test_input = torch.randn(3, 4)

        # 两次前向传播应该产生相同结果
        with torch.no_grad():
            out1 = model(t, test_input)
            out2 = model(t, test_input)

        assert torch.allclose(out1, out2)


class TestEdgeCases:
    """测试边界情况"""

    def test_single_sample_batch(self):
        """测试单样本批次"""
        model = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.randn(1, 4)  # batch_size = 1

        output = model(t, y)

        assert output.shape == (1, 1)
        assert not torch.isnan(output).any()

    def test_large_batch(self):
        """测试大批次"""
        model = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.randn(1000, 4)  # 大批次

        output = model(t, y)

        assert output.shape == (1000, 1)

    def test_zero_input(self):
        """测试零输入"""
        model = NeuralODECell(input_dim=4, hidden_dim=16, output_dim=1)

        t = torch.tensor(0.0)
        y = torch.zeros(5, 4)

        output = model(t, y)

        # 由于初始化了偏置，输出不应该全为零
        assert not torch.allclose(output, torch.zeros_like(output))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
