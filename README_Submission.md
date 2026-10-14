# Corrected submission asset workflow

This candidate supersedes the historical R071 asset generators for the accompanying corrected manuscript. Original records are preserved, not re-estimated.

## Reproduce the supplied asset layer

From this directory:

```
python analysis/reproduce_r071.py --only all
python -m pytest tests/test_submission_consistency.py tests/test_r071_smoke.py tests/test_r071_archive_audit.py
```

Order: unchanged inputs → derived analysis views → Source Data/tables → main figures → supplementary figures. Outputs are under `results/`. Historical CLI entry points delegate to the corrected builders; historical helper code is retained for traceability and is not an alternative submission pipeline.

## Installation and demonstration

The validated release environment is `environment.yml` (Python 3.11) with pinned packages in `requirements-lock.txt`:

```
conda env create -f environment.yml
conda activate neurmito-r071
python analysis/reproduce_r071.py --only all
```

The demo uses the 24 supplied audit inputs and writes Source Data, six main figures and six supplementary figures under `results/`; no network data fetch is required. A fresh Windows installation of the declared Python 3.11 lock completed the full rebuild without GPU use and passed all 45 tests. The validated direct stack includes NumPy 2.2.6, SciPy 1.15.3, Matplotlib 3.10.3, pandas 2.2.3, openpyxl 3.1.5, torch 2.7.0 and scikit-learn 1.6.1. This validates the supplied asset workflow; it is not evidence for the original simulation or training environment. The supplied asset demo does not rerun absent original trajectory/training records.

Figures: 1 reserve; 2 resolved transition; 3 independent synthetic benchmark; 4 retrospective diagnostic; 5 prescribed spatial scenario; 6 prescribed disease-axis scenario. Mapping covers 56 main and 33 supplementary panels (89 total). Supplementary Tables S1–S10 come exclusively from `scripts/r071/build_submission_source_data.py`.

## Evidence boundaries

- Reserve spare is algebraic for R033/R039 and independently source-reported for R060/R060B. The frozen R048/R062 mapping assumes a common contract and remains conditional. No observations or frozen mapping outputs are overwritten.
- R014B is a 91-condition scan. R021 is a distinct 441-group diagnostic cohort. Coarse ablation/robustness grids have 49 conditions each.
- EWS uses observed-event anchors. Lead intervals are prescribed. Effective n and window settings differ across configurations. Metrics are recomputed from saved probabilities; the original full feature/fit pipeline cannot be verified from these inputs alone.
- Figure 4a–c is a deterministic illustration with 12-s rolling descriptors and separate 20-s shading, not a selected 5-s EWS cohort trajectory.
- Figure 6 preserves every scenario weight and original ROS offset. Derived CSVs separately expose weights, offsets and plotted coordinates. These are uncalibrated assumptions; ±0.08 is not statistical uncertainty and coverage is not literature validation.

## Inputs and missing original artifacts

`inputs/locked_audit_hashes.json` verifies all 24 audit CSV/JSON inputs against checkpoint `before_submission_fix`, commit `a683c7d01c49aa3e33272684df78f416a69976e6`. Asset regeneration does not reproduce absent R021 full trajectories, R022 development/locking artifacts, or upstream long-tail scan histories. The original software environment is not asserted from the current validation runtime.

The source code contains simulation and training implementations, but running them anew would generate new results rather than certify the original locked experiment. Supply the original missing artifacts before claiming end-to-end reproduction.

## Author-confirmation gates

This is a reviewer-preparation archive, not a verified public release. Software authors in CITATION.cff remain unconfirmed. Repository ownership, release identity, copyright ownership, software license and permission to redistribute literature-derived image assets must be confirmed. Run `python scripts/r071/audit_r071_archive.py --json` to expose the citation-metadata gate; a nonzero exit is expected while authors are unresolved. Do not label it a failed scientific-data test or hide it by inserting invented metadata.
