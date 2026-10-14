"""R025 controlled in-silico misspecification benchmark.

This benchmark is deliberately independent of the biological ODE generator:
the reference system contains a hidden nonlinear residual, while the nominal
mechanistic baseline omits it. Results support only controlled recovery under
model misspecification, not biological predictive validity.
"""

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn


TRAIN_GAIN = (0.0, 0.5)
TEST_GAIN = (0.75, 1.0)
DT = 0.05
N_STEPS = 120
SEEDS = (0, 1, 2)


def base_rhs(x):
    return np.stack(
        (-0.8 * x[..., 0] + 0.6 * x[..., 1],
         -0.5 * x[..., 1] - 0.4 * x[..., 0]),
        axis=-1,
    )


def reference_rhs(x, hidden_gain):
    residual = hidden_gain * np.stack(
        (np.tanh(x[..., 0] * x[..., 1]),
         0.5 * np.sin(x[..., 0])),
        axis=-1,
    )
    return base_rhs(x) + residual


def rk4_rollout(x0, hidden_gain, n_steps=N_STEPS):
    trajectory = np.zeros((n_steps, 2), dtype=np.float32)
    trajectory[0] = x0
    for i in range(1, n_steps):
        x = trajectory[i - 1]
        k1 = reference_rhs(x, hidden_gain)
        k2 = reference_rhs(x + 0.5 * DT * k1, hidden_gain)
        k3 = reference_rhs(x + 0.5 * DT * k2, hidden_gain)
        k4 = reference_rhs(x + DT * k3, hidden_gain)
        trajectory[i] = x + DT * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
    return trajectory


class MLP(nn.Module):
    def __init__(self, hidden=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 2),
        )

    def forward(self, x):
        return self.net(x)


def generate_data(seed, n_train=40, n_test=24):
    rng = np.random.default_rng(seed)
    train = []
    test = []
    for i in range(n_train):
        gain = rng.uniform(*TRAIN_GAIN)
        x0 = rng.uniform(-1.5, 1.5, size=2).astype(np.float32)
        train.append((gain, rk4_rollout(x0, gain)))
    for i in range(n_test):
        gain = rng.uniform(*TEST_GAIN)
        x0 = rng.uniform(-1.5, 1.5, size=2).astype(np.float32)
        test.append((gain, rk4_rollout(x0, gain)))
    return train, test


def fit_model(kind, train, seed, epochs=250):
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    model = MLP()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)
    states = []
    targets = []
    for gain, trajectory in train:
        x = torch.tensor(trajectory[:-1])
        dx = torch.tensor(
            (trajectory[1:] - trajectory[:-1]) / DT,
            dtype=torch.float32,
        )
        states.append(x)
        if kind == "hybrid":
            targets.append(dx - torch.tensor(base_rhs(trajectory[:-1])))
        else:
            targets.append(dx)
    states = torch.cat(states)
    targets = torch.cat(targets)
    for _ in range(epochs):
        prediction = model(states)
        loss = torch.mean((prediction - targets) ** 2)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return model


def rollout_model(kind, model, x0, n_steps=N_STEPS):
    trajectory = np.zeros((n_steps, 2), dtype=np.float32)
    trajectory[0] = x0
    for i in range(1, n_steps):
        x = trajectory[i - 1]
        if kind == "ode":
            rhs = base_rhs(x)
        else:
            with torch.no_grad():
                correction = model(torch.tensor(x).unsqueeze(0)).numpy()[0]
            rhs = correction if kind == "neural" else base_rhs(x) + correction
        trajectory[i] = x + DT * rhs
    return trajectory


def rmse(prediction, target):
    return float(np.sqrt(np.mean((prediction - target) ** 2)))


def run_benchmark(output_dir, epochs=250):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    prediction_rows = []
    for seed in SEEDS:
        train, test = generate_data(seed)
        for kind in ("neural", "hybrid"):
            model = fit_model(kind, train, seed, epochs=epochs)
            errors = []
            endpoint_errors = []
            for case_index, (gain, target) in enumerate(test):
                prediction = rollout_model(kind, model, target[0])
                errors.append(rmse(prediction, target))
                endpoint_errors.append(rmse(prediction[-1:], target[-1:]))
                if seed == SEEDS[0] and case_index < 3:
                    for t in range(N_STEPS):
                        prediction_rows.append(
                            {
                                "model": kind,
                                "seed": seed,
                                "case_index": case_index,
                                "hidden_gain": gain,
                                "time_s": t * DT,
                                "target_x1": target[t, 0],
                                "target_x2": target[t, 1],
                                "pred_x1": prediction[t, 0],
                                "pred_x2": prediction[t, 1],
                            }
                        )
            all_metrics.append(
                {
                    "model": kind,
                    "seed": seed,
                    "test_region": "hidden_gain_0.75_1.0",
                    "trajectory_rmse": float(np.mean(errors)),
                    "endpoint_rmse": float(np.mean(endpoint_errors)),
                }
            )
        ode_errors = [
            rmse(rollout_model("ode", None, target[0]), target)
            for _gain, target in test
        ]
        ode_endpoint = [
            rmse(rollout_model("ode", None, target[0])[-1:], target[-1:])
            for _gain, target in test
        ]
        all_metrics.append(
            {
                "model": "ode",
                "seed": seed,
                "test_region": "hidden_gain_0.75_1.0",
                "trajectory_rmse": float(np.mean(ode_errors)),
                "endpoint_rmse": float(np.mean(ode_endpoint)),
            }
        )

    summary = []
    for model in ("ode", "neural", "hybrid"):
        rows = [row for row in all_metrics if row["model"] == model]
        values = np.asarray([row["trajectory_rmse"] for row in rows])
        summary.append(
            {
                "model": model,
                "n_seeds": len(rows),
                "trajectory_rmse_mean": float(values.mean()),
                "trajectory_rmse_sd": float(values.std(ddof=1)),
                "trajectory_rmse_min": float(values.min()),
                "trajectory_rmse_max": float(values.max()),
                "endpoint_rmse_mean": float(
                    np.mean([row["endpoint_rmse"] for row in rows])
                ),
            }
        )
    with (output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=all_metrics[0].keys())
        writer.writeheader()
        writer.writerows(all_metrics)
    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prediction_rows[0].keys())
        writer.writeheader()
        writer.writerows(prediction_rows)
    (output_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": "R025",
                "purpose": "controlled in-silico model-misspecification benchmark",
                "train_hidden_gain": TRAIN_GAIN,
                "test_hidden_gain": TEST_GAIN,
                "seeds": SEEDS,
                "dt": DT,
                "n_steps": N_STEPS,
                "epochs": epochs,
                "claim_boundary": (
                    "supports only controlled recovery under hidden nonlinear "
                    "residual misspecification; not biological validation"
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/audit_runs/R025"))
    parser.add_argument("--epochs", type=int, default=250)
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.output_dir, args.epochs), indent=2))


if __name__ == "__main__":
    main()

