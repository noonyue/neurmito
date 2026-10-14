"""
Training pipeline for Hybrid Neural-ODE model
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from tqdm import tqdm

from .neural_ode_model import HybridNeuralODE, NeuralODECell


def generate_training_data(n_samples=1000):
    """
    Generate training data by running mechanistic model
    with various stress conditions.

    Returns
    -------
    trajectories : list of arrays
        State trajectories under different stress levels
    conditions : list of dict
        Stress conditions for each trajectory
    """
    from module1.bazil2016_ode import DEFAULT_PARAMS
    from module1.neurmito_system import simulate, IDX, CARDIAC_IC

    trajectories = []
    conditions = []

    # Define stress combinations
    rotenone_levels = np.logspace(-3, -1, 5)  # 0.001 to 0.1 mM
    paraquat_levels = np.logspace(-2, 1, 5)    # 0.01 to 10 mM
    hypoxia_levels = [1.0, 0.5, 0.2, 0.1]     # 100% to 10% O2

    print("Generating training data...")
    for rot in rotenone_levels:
        for pq in paraquat_levels:
            for hyp in hypoxia_levels:
                # Skip extreme combinations
                if rot > 0.05 and pq > 5.0:
                    continue

                params = DEFAULT_PARAMS.copy()
                stress = {
                    'rotenone': rot,
                    'paraquat': pq,
                    'hypoxia': hyp,
                }

                try:
                    # Run simulation
                    t_span = (0, 200)
                    t_eval = np.linspace(0, 200, 500)
                    sol = simulate(t_span, t_eval,
                                 y0=CARDIAC_IC.copy(),
                                 params=params,
                                 stress=stress)

                    if sol.success:
                        trajectories.append(sol.y)
                        conditions.append(stress)

                except Exception as e:
                    continue

    print(f"Generated {len(trajectories)} training samples")
    return trajectories, conditions


def train_hybrid_model(model, train_data, val_data, n_epochs=100, lr=1e-3):
    """
    Train hybrid neural-ODE model.

    Parameters
    ----------
    model : HybridNeuralODE
        Hybrid model to train
    train_data : list of tuples
        Training data (y0, t_eval, y_true)
    val_data : list of tuples
        Validation data
    n_epochs : int
        Number of training epochs
    lr : float
        Learning rate

    Returns
    -------
    model : HybridNeuralODE
        Trained model
    history : dict
        Training history
    """
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=10
    )

    criterion = nn.MSELoss()

    history = {'train_loss': [], 'val_loss': []}

    print("Training hybrid model...")
    for epoch in range(n_epochs):
        # Training
        model.train()
        train_loss = 0.0

        for y0, t_eval, y_true in train_data:
            optimizer.zero_grad()

            # Forward pass
            y_pred = model.trajectory(y0, t_eval)

            # Compute loss
            loss = criterion(y_pred, y_true)

            # Backward pass
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_data)

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for y0, t_eval, y_true in val_data:
                y_pred = model.trajectory(y0, t_eval)
                loss = criterion(y_pred, y_true)
                val_loss += loss.item()

        val_loss /= len(val_data)

        # Update learning rate
        scheduler.step(val_loss)

        # Record history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)

        # Print progress
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{n_epochs}: "
                  f"Train Loss = {train_loss:.4f}, "
                  f"Val Loss = {val_loss:.4f}")

    return model, history


def prepare_data_splits(trajectories, conditions, train_ratio=0.8):
    """
    Split data into training and validation sets.

    Parameters
    ----------
    trajectories : list of arrays
        State trajectories
    conditions : list of dict
        Stress conditions
    train_ratio : float
        Fraction of data for training

    Returns
    -------
    train_data : list of tuples
    val_data : list of tuples
    """
    n_train = int(len(trajectories) * train_ratio)

    # Shuffle indices
    indices = np.random.permutation(len(trajectories))
    train_indices = indices[:n_train]
    val_indices = indices[n_train:]

    train_data = []
    val_data = []

    for idx in train_indices:
        traj = trajectories[idx]
        y0 = torch.tensor(traj[:, 0], dtype=torch.float32)
        t_eval = torch.linspace(0, 200, traj.shape[1], dtype=torch.float32)
        y_true = torch.tensor(traj.T, dtype=torch.float32)
        train_data.append((y0, t_eval, y_true))

    for idx in val_indices:
        traj = trajectories[idx]
        y0 = torch.tensor(traj[:, 0], dtype=torch.float32)
        t_eval = torch.linspace(0, 200, traj.shape[1], dtype=torch.float32)
        y_true = torch.tensor(traj.T, dtype=torch.float32)
        val_data.append((y0, t_eval, y_true))

    return train_data, val_data


if __name__ == '__main__':
    print("Generating training data...")
    trajectories, conditions = generate_training_data(n_samples=100)
    print(f"Generated {len(trajectories)} trajectories")

    train_data, val_data = prepare_data_splits(trajectories, conditions)
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
