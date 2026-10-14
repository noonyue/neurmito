"""
Hybrid Neural-ODE Model for NeurMito-DT
Combines the Bazil-inspired reduced mechanistic ODE with neural network flexibility.
"""

import torch
import torch.nn as nn
import torchdiffeq

# ── Neural ODE Cell ───────────────────────────────────────────────────────────

class NeuralODECell(nn.Module):
    """
    Neural network that learns unknown dynamics.
    Replaces poorly-characterized rate laws in the mechanistic model.

    Learns:
    1. f_Neural(ROS, ΔΨm, Ca²⁺, ...) → ROS production rate
    2. g_Neural(ΔΨm, ATP, Ca²⁺) → Damage accumulation rate
    """

    def __init__(self, input_dim=4, hidden_dim=32, output_dim=1):
        super(NeuralODECell, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
        )

        # Initialize weights small to start near mechanistic model
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0, std=0.1)
                nn.init.normal_(m.bias, mean=0, std=0.01)

    def forward(self, t, y):
        """
        Compute dy/dt from neural network.

        Parameters
        ----------
        t : float
            Time (not used, for ODE solver compatibility)
        y : tensor (batch_size, input_dim)
            State variables [H2O2, DPsi, ATP, Ca]

        Returns
        -------
        dydt : tensor (batch_size, output_dim)
            Time derivatives
        """
        return self.net(y)


# ── Hybrid Mechanistic-Neural ODE ───────────────────────────────────────────────

class HybridNeuralODE(nn.Module):
    """
    Hybrid model combining:
    1. Mechanistic ODE for well-characterized processes
    2. Neural ODE for poorly-characterized processes

    Structure:
    - States y = [y_mech, y_neural]
    - dy_mech/dt = f_mech(y, params)
    - dy_neural/dt = f_neural(y) + g_mech(y, params)
    """

    def __init__(
        self,
        mechanistic_model,
        neural_ode,
        mech_indices,
        neural_indices,
        feature_indices=None,
    ):
        """
        Parameters
        ----------
        mechanistic_model : callable
            Function that computes mechanistic derivatives
        neural_ode : NeuralODECell
            Neural network for unknown dynamics
        mech_indices : list
            Indices of mechanistic states
        neural_indices : list
            Indices of neural-augmented states
        feature_indices : list, optional
            State indices used as neural network inputs. If omitted, features are
            selected from neural states, then mechanistic states, then remaining
            states until the neural network input dimension is reached.
        """
        super(HybridNeuralODE, self).__init__()
        self.mechanistic_model = mechanistic_model
        self.neural_ode = neural_ode
        self.mech_indices = list(mech_indices)
        self.neural_indices = list(neural_indices)
        self.feature_indices = None if feature_indices is None else list(feature_indices)

    @property
    def neural_input_dim(self):
        return self.neural_ode.net[0].in_features

    def _select_feature_indices(self, n_states):
        if self.feature_indices is not None:
            return [idx for idx in self.feature_indices if 0 <= idx < n_states]

        ordered = list(self.neural_indices) + list(self.mech_indices) + list(range(n_states))
        selected = []
        for idx in ordered:
            if 0 <= idx < n_states and idx not in selected:
                selected.append(idx)
            if len(selected) == self.neural_input_dim:
                break
        return selected

    def _neural_features(self, y):
        indices = self._select_feature_indices(y.shape[1])
        if indices:
            index_tensor = torch.as_tensor(indices, device=y.device, dtype=torch.long)
            features = y.index_select(1, index_tensor)
        else:
            features = y.new_zeros((y.shape[0], 0))

        if features.shape[1] < self.neural_input_dim:
            pad_width = self.neural_input_dim - features.shape[1]
            padding = y.new_zeros((y.shape[0], pad_width))
            features = torch.cat([features, padding], dim=1)
        return features[:, :self.neural_input_dim]

    def forward(self, t, y):
        if (
            isinstance(t, torch.Tensor)
            and isinstance(y, torch.Tensor)
            and t.dim() >= 1
            and y.dim() == 1
        ):
            return self.integrate(t, y)

        return self.rhs(t, y)

    def rhs(self, t, y):
        """
        Compute hybrid derivatives.

        Parameters
        ----------
        t : float
            Time
        y : tensor (batch_size, n_states)
            Full state vector

        Returns
        -------
        dydt : tensor (batch_size, n_states)
            Time derivatives
        """
        was_unbatched = y.dim() == 1
        y_batch = y.unsqueeze(0) if was_unbatched else y
        dydt = torch.zeros_like(y_batch)

        # Mechanistic derivatives
        dy_mech = self.mechanistic_model(t, y_batch)
        if dy_mech.dim() == 1:
            dy_mech = dy_mech.unsqueeze(0)
        dy_mech = dy_mech.to(device=y_batch.device, dtype=y_batch.dtype)

        valid_mech_indices = [
            idx for idx in self.mech_indices if 0 <= idx < y_batch.shape[1]
        ]
        if valid_mech_indices:
            dydt[:, valid_mech_indices] = dy_mech[:, valid_mech_indices]

        # Neural derivatives (for selected states)
        if self.neural_indices:
            features = self._neural_features(y_batch)
            dy_neural = self.neural_ode(t, features)
            if dy_neural.dim() == 1:
                dy_neural = dy_neural.unsqueeze(1)
            if dy_neural.shape[1] < len(self.neural_indices):
                raise ValueError(
                    "Neural ODE output dimension must cover neural_indices."
                )

            # Add neural correction to mechanistic derivative.
            for i, idx in enumerate(self.neural_indices):
                if 0 <= idx < y_batch.shape[1]:
                    dydt[:, idx] = dy_mech[:, idx] + 0.1 * dy_neural[:, i]

        return dydt.squeeze(0) if was_unbatched else dydt

    def integrate(self, y0, t_eval):
        """Compute batched trajectories using torchdiffeq."""
        was_unbatched = y0.dim() == 1
        y0_batch = y0.unsqueeze(0) if was_unbatched else y0

        solution = torchdiffeq.odeint(
            self.rhs,
            y0_batch,
            t_eval,
            method='dopri5',
            rtol=1e-5,
            atol=1e-8,
        )
        solution = solution.permute(1, 0, 2)
        return solution.squeeze(0) if was_unbatched else solution

    def trajectory(self, y0, t_eval):
        """
        Compute trajectory using Neural ODE solver.

        Parameters
        ----------
        y0 : tensor (n_states,)
            Initial conditions
        t_eval : tensor (n_times,)
            Time points to evaluate

        Returns
        -------
        y : tensor (n_times, n_states)
            State trajectories
        """
        return self.integrate(y0, t_eval)


# ── Mechanistic ODE wrapper (for integration) ───────────────────────────────────

def mechanistic_ode_wrapper(params_dict):
    """
    Create a callable mechanistic ODE function from the reduced NeurMito-DT model.
    """
    from module1.bazil2016_ode import DEFAULT_PARAMS
    from module1.neurmito_system import IDX

    params = DEFAULT_PARAMS.copy()
    params.update(params_dict)

    def mechanistic_derivatives(t, y):
        """Compute dy/dt from mechanistic model."""
        # Convert tensor to numpy for scipy solver compatibility
        # This is a simplified version — for full integration,
        # would need to reimplement ODE in PyTorch

        batch_size = y.shape[0]
        dydt = torch.zeros(batch_size, 25)  # 25 states

        # TODO: Implement full mechanistic derivatives in PyTorch
        # For now, return placeholder

        return dydt

    return mechanistic_derivatives


# ── Example usage ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Create neural ODE cell
    neural_ode = NeuralODECell(input_dim=4, hidden_dim=32, output_dim=3)

    # Create hybrid model
    # mechanistic_fn = mechanistic_ode_wrapper({})
    # hybrid_model = HybridNeuralODE(
    #     mechanistic_fn,
    #     neural_ode,
    #     mech_indices=[0, 1, 2, 3, 5, 6, 7],  # Well-characterized states
    #     neural_indices=[8, 4, 5],            # ROS, DPsi, ATP (neural-augmented)
    # )

    print("Hybrid Neural-ODE model initialized")
    print(f"Neural ODE parameters: {sum(p.numel() for p in neural_ode.parameters())}")
