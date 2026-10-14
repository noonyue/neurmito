"""
测试配置文件

提供测试用的 fixtures 和配置
"""

import pytest
import numpy as np
from pathlib import Path

from module1.bazil2016_ode import DEFAULT_PARAMS
from module1.neurmito_system import CARDIAC_IC


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def test_params():
    """完整默认参数，避免测试夹具与 RHS 的参数 schema 分叉。"""
    return DEFAULT_PARAMS.copy()


@pytest.fixture
def test_initial_conditions():
    """与生产模型 IDX 顺序一致的初始状态。"""
    return CARDIAC_IC.copy()


@pytest.fixture
def stress_none():
    """无应激条件"""
    return {}


@pytest.fixture
def stress_rotenone():
    """鱼藤酮应激（50% Complex I 抑制）"""
    return {'rotenone': 0.5}


@pytest.fixture
def stress_paraquat():
    """百草枯应激（10 μM ROS 产生）"""
    return {'paraquat': 10.0}


@pytest.fixture
def stress_combined():
    """组合应激"""
    return {'rotenone': 0.5, 'paraquat': 10.0}


@pytest.fixture
def seahorse_cortical_data():
    """皮层神经元的 Seahorse 实验数据"""
    return {
        'basal_ocr': 100.0,
        'maximal_ocr': 250.0,
        'spare_capacity': 150.0,
        'atp_linked': 70.0,
        'proton_leak': 30.0,
    }


@pytest.fixture
def seahorse_dopaminergic_data():
    """多巴胺能神经元的 Seahorse 实验数据"""
    return {
        'basal_ocr': 90.0,
        'maximal_ocr': 180.0,
        'spare_capacity': 90.0,
        'atp_linked': 65.0,
        'proton_leak': 25.0,
    }
