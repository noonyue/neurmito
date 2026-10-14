# NeurMito-DT

**Corrected submission candidate:** follow [README_Submission.md](README_Submission.md)
for the authoritative 89-panel asset pipeline, evidence boundaries and unresolved
author gates. The historical R071 notes below are retained for provenance and
do not certify the corrected public release or end-to-end training reproduction.

Code-availability repository for the NeurMito-DT computational framework.
This repository intentionally contains method source code and reproducibility
configuration only. Generated result figures, result tables, source-data
workbooks, manuscript text, and submission files are not distributed here.

## Quick start

```bash
conda env create -f environment.yml
conda activate neurmito-r071
python analysis/reproduce_r071.py --only all
python -m pytest -q
```

The current R071 candidate checkout includes the 24 locked `inputs/audit_runs/`
artifacts required by the active builders. The audit-run files are copied from
the project-local source-audit records and are checked by
`scripts/r071/audit_r071_archive.py` before release. A public or anonymous
review archive must preserve these files or provide an approved equivalent
access route; do not substitute legacy figures or synthetic inputs.

```bash
python scripts/r071/build_r071_all.py
python scripts/r071/build_r071_supplementary.py
python scripts/r071/build_r071_source_data.py
```

These commands generate local files under `results/` for verification only.
The `results/` directory, caches, and archives are excluded from the method
repository and must not be included in a public or reviewer upload.

The release candidate completed a full rebuild and the full test suite in a
fresh Python 3.11 environment created from `environment.yml` and
`requirements-lock.txt`. The final public or reviewer release still requires repository-owner
confirmation of visibility, authorship metadata, an immutable tag/commit, and
an archive or reviewer-access record before it is cited as the final
reproducibility location.

Model implementations are in `module1`-`module5`; analysis and figure
generation entry points are in `analysis/` and `scripts/`. A generator may
create local files under `results/`; that directory is ignored by Git and must
not be committed.

Literature-derived source records are kept under `inputs/source_records/`.
This is dry-lab computational work: no new wet-lab, imaging, animal, clinical,
or person-level data are included.

See `docs/REPOSITORY_SCOPE.md` and `docs/reproduction.md` for the public scope.
See `docs/PRE_RELEASE_CHECKLIST.md` for the remaining release actions.

## License status

No public software license has been approved for this release candidate. The
repository owner and copyright holders must approve the license before public
release or reviewer distribution. See `LICENSE` for the current status notice.
