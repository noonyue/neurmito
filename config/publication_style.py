"""
Nature Communications 级别图表配置
专业科学出版标准

应用于所有 NeurMito-DT 图表
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 基础字体配置（Nature Communications 标准）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FONT_CONFIG = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 9,           # 基础字体（增加到9pt）
    'axes.labelsize': 10,     # 轴标签（增加到10pt）
    'axes.titlesize': 11,     # 标题（增加到11pt）
    'xtick.labelsize': 8,     # x轴刻度
    'ytick.labelsize': 8,     # y轴刻度
    'legend.fontsize': 8,     # 图例
    'figure.titlesize': 12,   # 主标题
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 线条和边框配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LINE_CONFIG = {
    'lines.linewidth': 2.0,       # 数据线加粗
    'axes.linewidth': 1.5,        # 轴线加粗
    'grid.linewidth': 0.8,        # 网格线
    'xtick.major.width': 1.5,     # x轴主刻度
    'ytick.major.width': 1.5,     # y轴主刻度
    'xtick.minor.width': 1.0,     # x轴次刻度
    'ytick.minor.width': 1.0,     # y轴次刻度
    'patch.linewidth': 1.5,       # 补丁边框
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 色盲友好配色（Wong 2011 + ColorBrewer）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Wong 色盲友好色板（Nature 推荐）
WONG_COLORS = {
    'orange': '#E69F00',      # 橙色
    'sky_blue': '#56B4E9',    # 天蓝
    'green': '#009E73',       # 蓝绿
    'yellow': '#F0E442',      # 黄色
    'blue': '#0072B2',        # 蓝色
    'vermillion': '#D55E00',  # 朱红
    'purple': '#CC79A7',      # 紫红
    'black': '#000000',       # 黑色
}

# 神经元类型配色（色盲友好版本）
NEURON_COLORS_OPTIMIZED = {
    'cortical': '#0072B2',        # 深蓝（Wong blue）
    'hippocampal': '#56B4E9',     # 天蓝（Wong sky blue）
    'dopaminergic': '#D55E00',    # 朱红（Wong vermillion）
    'motor': '#E69F00',           # 橙色（Wong orange）
    'gabaergic': '#009E73',       # 蓝绿（Wong green）
    'cholinergic': '#CC79A7',     # 紫红（Wong purple）
    'cerebellar': '#F0E442',      # 黄色（Wong yellow）
    'sensory': '#B47846',         # 棕色
    'sh-sy5y': '#AA4499',         # 深紫
    'SH-SY5Y': '#AA4499',         # 深紫（大写）
}

# 状态/类型配色
STATUS_COLORS = {
    'prior': '#999999',       # 灰色（先验）
    'posterior': '#D55E00',   # 朱红（后验）
    'control': '#56B4E9',     # 天蓝（对照）
    'stress': '#D55E00',      # 朱红（应激）
    'healthy': '#009E73',     # 绿色（健康）
    'diseased': '#D55E00',    # 红色（疾病）
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 图表布局配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LAYOUT_CONFIG = {
    'figure.figsize': (17.2, 11.6),  # A4 宽度（单栏）
    'figure.dpi': 100,                # 屏幕显示DPI
    'savefig.dpi': 600,               # 保存时DPI（提高到600）
    'savefig.bbox': 'tight',          # 紧凑裁剪
    'savefig.pad_inches': 0.1,        # 边距
    'savefig.transparent': False,     # 白色背景
    'figure.constrained_layout.use': False,  # 禁用自动布局（手动控制）
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 其他优化配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OTHER_CONFIG = {
    'axes.spines.top': False,         # 去除顶部边框
    'axes.spines.right': False,       # 去除右侧边框
    'axes.grid': False,               # 默认不显示网格
    'grid.alpha': 0.3,                # 网格透明度
    'legend.frameon': False,          # 图例无边框
    'legend.loc': 'best',             # 自动最佳位置
    'axes.axisbelow': True,           # 网格在数据下方
    'pdf.fonttype': 42,               # TrueType字体（编辑友好）
    'ps.fonttype': 42,                # PostScript字体
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 应用所有配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def apply_publication_style():
    """应用所有出版级配置"""
    config = {}
    config.update(FONT_CONFIG)
    config.update(LINE_CONFIG)
    config.update(LAYOUT_CONFIG)
    config.update(OTHER_CONFIG)

    plt.rcParams.update(config)

    # 设置默认色彩循环（使用Wong色板）
    plt.rcParams['axes.prop_cycle'] = plt.cycler(
        color=[
            WONG_COLORS['blue'],
            WONG_COLORS['orange'],
            WONG_COLORS['green'],
            WONG_COLORS['vermillion'],
            WONG_COLORS['sky_blue'],
            WONG_COLORS['purple'],
            WONG_COLORS['yellow'],
        ]
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 辅助函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_panel_label(ax, label, x=-0.15, y=1.05):
    """添加面板标签（a, b, c...）"""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=12, fontweight='bold', va='top', ha='right')

def save_publication_figure(fig, filepath, dpi=600):
    """保存出版级图表"""
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"✓ Saved publication-quality figure: {filepath}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 使用示例
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    # 在每个figure脚本开头导入并应用
    # from config.publication_style import apply_publication_style, NEURON_COLORS_OPTIMIZED
    # apply_publication_style()

    print("Publication style configuration loaded successfully!")
    print("Applied settings:")
    print(f"  - Font size: {FONT_CONFIG['font.size']} pt")
    print(f"  - Line width: {LINE_CONFIG['lines.linewidth']} pt")
    print(f"  - DPI: {LAYOUT_CONFIG['savefig.dpi']}")
    print(f"  - Color palette: Wong (color-blind friendly)")
