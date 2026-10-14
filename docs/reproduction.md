# Local execution

Install the environment and run the test suite from the repository root:

```bash
conda env create -f environment.yml
conda activate neurmito-r071
python -m pytest -q
```

## R071 full-rebuild prerequisite

The R071 builders require the locked `inputs/audit_runs/` directory. The
current candidate package contains the 24 files used by the active builders,
including the two implicit dependencies `R009/final_dpsi_by_variant_matrix.csv`
and `R021/split_manifest.csv`. A clean checkout should verify them with
`python scripts/r071/audit_r071_archive.py --json` before rebuilding.

Before running a full rebuild, confirm that these directories exist and are
complete: `R009`, `R010`, `R014B`, `R021`, `R023`, `R025`, `R042`, `R047`,
`R048`, `R060`, `R060B`, and `R062`. Do not substitute legacy figure outputs or
unverified synthetic files for the locked inputs.

The scripts in `analysis/` and `scripts/` are supplied as code. Generators
write requested figures, tables, or manifests to local `results/`
subdirectories. `results/` is ignored by Git and must not be committed. The
public release must retain the locked audit-run inputs or state the approved
reviewer-access route that supplies them.
