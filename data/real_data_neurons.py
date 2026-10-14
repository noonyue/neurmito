"""
真实数据神经元类型常量
仅包含有真实文献发表的实验数据的神经元类型
"""

# 有真实文献数据的神经元类型（4种）
# No source in the current repository passed the R026 primary-source audit.
# Keep this list empty so downstream code cannot silently treat provisional
# numbers as verified experimental observations.
REAL_DATA_NEURON_TYPES = []
UNVERIFIED_SOURCE_NEURON_TYPES = [
    'cortical',
    'hippocampal',
    'dopaminergic',
    'SH-SY5Y',
]

# 估计数据的神经元类型（5种，暂不使用）
ESTIMATED_NEURON_TYPES = [
    'motor',
    'GABAergic',
    'cholinergic',
    'cerebellar',
    'sensory',
]

# 文献来源详细信息
LITERATURE_SOURCES = {
    'cortical': {
        'citation': 'Cheng et al., 2012, ASN Neuro',
        'title': 'Mitochondrial KATP channels: an essential component of cardioprotection',
        'pmid': '22313347',
        'sample_type': 'Rat primary cortical neurons',
        'culture_condition': 'DIV 7-10',
        'n': 12,
        'assay': 'Seahorse XF24 Mito Stress Test',
    },
    'hippocampal': {
        'citation': 'Ferreira et al., 2015, BBA',
        'title': 'Mitochondrial dysfunction and oxidative stress in Alzheimer\'s disease',
        'pmid': '25633543',
        'sample_type': 'Rat primary hippocampal neurons',
        'culture_condition': 'DIV 14',
        'n': 6,
        'assay': 'Seahorse XF Analyzer',
    },
    'dopaminergic': {
        'citation': 'Requejo-Aguilar et al., 2014, Sci Rep',
        'title': 'PINK1 deficiency sustains cell proliferation by reprogramming glucose metabolism',
        'pmid': '24670369',
        'sample_type': 'Mouse primary midbrain dopaminergic neurons',
        'culture_condition': 'DIV 7',
        'n': 4,
        'assay': 'Seahorse XF24 Extracellular Flux Analyzer',
    },
    'SH-SY5Y': {
        'citation': 'Connolly et al., 2018, Neurotoxicology',
        'title': 'Characterization of the bioenergetic profile of human neuroblastoma SH-SY5Y cells',
        'pmid': '29462712',
        'sample_type': 'SH-SY5Y cells differentiated with RA+BDNF',
        'culture_condition': 'DIV 14 post-differentiation',
        'n': 5,
        'assay': 'Seahorse XF96 Mito Stress Test',
    },
}
