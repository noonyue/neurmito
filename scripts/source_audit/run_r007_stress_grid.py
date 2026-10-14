"""Run the R007 stress-grid qualification experiment.

This is a pre-registration/sanity run.  It records continuous endpoints and
solver QC without assigning a collapse label or fitting a critical boundary.
"""

import argparse
import csv
import hashlib
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
from module1.neurmito_system import IDX, odes, simulate


DEFAULT_ROTENONE = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
DEFAULT_PARAQUAT = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0]


def _parameter_hash(params):
    payload = json.dumps(params, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('ascii')).hexdigest()


def _simulate_condition(rotenone, paraquat, duration, n_points):
    stress = {'rotenone': rotenone, 'paraquat': paraquat}
    t_eval = np.linspace(0.0, duration, n_points)
    sol = simulate((0.0, duration), t_eval, params=DEFAULT_PARAMS.copy(),
                   stress=stress)

    row = {
        'rotenone_inhibition': rotenone,
        'paraquat_index': paraquat,
        'solver_success': bool(sol.success),
        'solver_message': str(sol.message),
    }
    if not sol.success or sol.y.shape[1] == 0:
        return row

    final = sol.y[:, -1]
    final_derivative = odes(duration, final, DEFAULT_PARAMS.copy(),
                            stress=stress)
    row.update({
        'final_dpsi_mv': final[IDX['DPsi']],
        'min_dpsi_mv': np.min(sol.y[IDX['DPsi']]),
        'max_dpsi_mv': np.max(sol.y[IDX['DPsi']]),
        'final_atp_m_mm': final[IDX['ATP_m']],
        'final_adp_m_mm': final[IDX['ADP_m']],
        'final_h2o2_m_mm': final[IDX['H2O2_m']],
        'max_h2o2_m_mm': np.max(sol.y[IDX['H2O2_m']]),
        'minimum_state_value': np.min(sol.y),
        'final_derivative_max_abs': np.max(np.abs(final_derivative)),
        'n_function_evaluations': sol.nfev,
    })
    return row


def run_grid(output_dir, duration=1000.0, n_points=201):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for rotenone in DEFAULT_ROTENONE:
        for paraquat in DEFAULT_PARAQUAT:
            rows.append(_simulate_condition(
                rotenone, paraquat, duration, n_points
            ))

    baseline = next(
        row for row in rows
        if row['rotenone_inhibition'] == 0.0 and row['paraquat_index'] == 0.0
    )
    for row in rows:
        if not row['solver_success']:
            continue
        row['dpsi_loss_fraction'] = (
            (baseline['final_dpsi_mv'] - row['final_dpsi_mv'])
            / baseline['final_dpsi_mv']
        )
        row['atp_loss_fraction'] = (
            (baseline['final_atp_m_mm'] - row['final_atp_m_mm'])
            / baseline['final_atp_m_mm']
        )
        row['h2o2_fold_change'] = (
            row['final_h2o2_m_mm'] / baseline['final_h2o2_m_mm']
        )

    csv_path = output_dir / 'stress_grid.csv'
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        'run_id': 'R007',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'stress-grid dynamic-range and solver-QC pre-run',
        'model_name': MODEL_NAME,
        'model_reference': MODEL_REFERENCE,
        'parameter_sha256': _parameter_hash(DEFAULT_PARAMS),
        'duration_s': duration,
        'n_output_points': n_points,
        'rotenone_inhibition_grid': DEFAULT_ROTENONE,
        'paraquat_index_grid': DEFAULT_PARAQUAT,
        'collapse_threshold_defined': False,
        'python_version': platform.python_version(),
        'numpy_version': np.__version__,
        'scipy_version': scipy.__version__,
        'output_csv': csv_path.name,
    }
    metadata_path = output_dir / 'metadata.json'
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding='utf-8',
    )
    return csv_path, metadata_path, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('inputs/audit_runs/R007'),
    )
    parser.add_argument('--duration', type=float, default=1000.0)
    parser.add_argument('--n-points', type=int, default=201)
    args = parser.parse_args()

    csv_path, metadata_path, rows = run_grid(
        args.output_dir,
        duration=args.duration,
        n_points=args.n_points,
    )
    successful = sum(row['solver_success'] for row in rows)
    print('conditions:', len(rows))
    print('successful:', successful)
    print('csv:', csv_path)
    print('metadata:', metadata_path)


if __name__ == '__main__':
    main()

