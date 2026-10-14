"""
NeurMito-DT Module 2: Hybrid Neural-ODE Framework
Combines mechanistic ODE constraints with neural network flexibility

Core idea: Use Neural ODE to learn unknown dynamics in:
1. ROS damage kinetics (nonlinear, poorly characterized)
2. Calcium-dependent regulation (complex feedback)
3. Stress interaction effects (combinatorial toxicity)

While preserving mechanistic constraints in:
1. Mass balance (ATP, NADH pools)
2. Thermodynamics (membrane potential, proton gradient)
3. Conservation laws (redox balance)
"""

# Lazy imports to avoid torch dependency
# from .neural_ode_model import HybridNeuralODE, NeuralODECell
# from .training import train_hybrid_model, generate_training_data
# from .figure3_hybrid import make_figure3
# from .figure4_validation import make_figure4

__all__ = [
    'HybridNeuralODE',
    'NeuralODECell',
    'train_hybrid_model',
    'generate_training_data',
    'make_figure3',
    'make_figure4',
]
