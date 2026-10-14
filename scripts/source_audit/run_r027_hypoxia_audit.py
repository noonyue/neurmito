"""Audit hypoxia units, directionality, boundary behavior, and solver QC."""

import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from module1.bazil2016_ode import DEFAULT_PARAMS, MODEL_NAME, MODEL_REFERENCE
from module1.neurmito_system import CARDIAC_IC, IDX, simulate


HYPOXIA_GRID = (1.0, 0.8, 0.6, 0.4, 0.2, 0.1)
BOUNDARY_PROBE = 0.0


def run_audit(output_dir, duration=2000.0, n_points=401):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for hypoxia in HYPOXIA_GRID + (BOUNDARY_PROBE,):
        t_eval = np.linspace(0.0, duration, n_points)
        sol = simulate(
            (0.0, duration),
            t_eval,
            y0=CARDIAC_IC.copy(),
            params=DEFAULT_PARAMS.copy(),
            stress={"hypoxia": hypoxia},
        )
        y = sol.y
        rows.append(
            {
                "hypoxia_fraction": hypoxia,
                "o2_ext_m_m": DEFAULT_PARAMS["O2_ext"] * hypoxia,
                "solver_success": bool(sol.success),
                "min_o2_m_m": float(np.min(y[IDX["O2"]])),
                "final_o2_m_m": float(y[IDX["O2"], -1]),
                "final_dpsi_mv": float(y[IDX["DPsi"], -1]),
                "final_atp_m_mm": float(y[IDX["ATP_m"], -1]),
                "final_h2o2_m_mm": float(y[IDX["H2O2_m"], -1]),
                "min_state_value": float(np.min(y)),
                "n_function_evaluations": int(sol.nfev),
            }
        )
    fields = list(rows[0])
    with (output_dir / "hypoxia_audit.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    o2_monotone = all(
        rows[i]["final_o2_m_m"] >= rows[i + 1]["final_o2_m_m"]
        for i in range(len(rows) - 1)
    )
    metadata = {
        "run_id": "R027",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": MODEL_NAME,
        "model_reference": MODEL_REFERENCE,
        "hypoxia_definition": "fraction of DEFAULT_PARAMS['O2_ext']",
        "hypoxia_grid": list(HYPOXIA_GRID),
        "boundary_probe": BOUNDARY_PROBE,
        "duration_s": duration,
        "n_output_points": n_points,
        "o2_nonnegative_in_formal_grid": all(
            row["min_o2_m_m"] >= -1e-12
            for row in rows
            if row["hypoxia_fraction"] in HYPOXIA_GRID
        ),
        "o2_direction_monotone_in_formal_grid": o2_monotone,
        "boundary_probe_status": (
            "invalid_for_formal_extension_due_to_zero_O2_depletion"
        ),
        "dp_validity": (
            "Hypoxia fractions 0.2-0.8 lower O2 but have negligible DPsi/ATP "
            "effect at this parameterization; only 0.1 reaches energetic failure."
        ),
        "main_claim_scope": "extension audit only; does not modify C1/C2",
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return rows, metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/audit_runs/R027"))
    parser.add_argument("--duration", type=float, default=2000.0)
    parser.add_argument("--n-points", type=int, default=401)
    args = parser.parse_args()
    rows, metadata = run_audit(
        args.output_dir, duration=args.duration, n_points=args.n_points
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

