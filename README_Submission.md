# Submission reproducibility scope

This public release contains the 24 frozen audit inputs and the code required to
regenerate the derived analysis views, Source Data, six main figures, and six
supplementary figures. Generated outputs are written locally to `results/` and
are not included in the repository or release archive.

The release excludes manuscript files, submitted figures and tables, the
internal recovered-history archive, complete historical 25-state trajectories,
original solver checkpoints, and historical pre-test access records. These
exclusions preserve the manuscript's stated evidence boundaries and do not
change the frozen scientific inputs.

Run:

```bash
python analysis/reproduce_r071.py --only all
python -m pytest -q
```

The repository is publicly downloadable without authentication. No
open-source license is granted, and use, execution, modification, or
redistribution requires prior written authorization. No Zenodo DOI has been
assigned. See `README.md`, `PUBLIC_DATA_SOURCES.md`, `LICENSE`, and
`inputs/locked_audit_hashes.json`.
