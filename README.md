# NeurMito-DT reproducibility release v0.1.1

This repository contains the project-created analysis and figure-generation
code, environment specifications, tests, and the 24 SHA-256-locked audit inputs
used by the NeurMito-DT submission. It does not contain generated figures,
result tables, Source Data workbooks, manuscript files, internal historical
evidence archives, or article images.

## Public data sources

The only external public measurements used for the respiratory-reserve evidence
layer were digitized from four primary articles. Persistent DOI and PubMed
Central access links, the exact panels, preparations, and extraction scope are
listed in [PUBLIC_DATA_SOURCES.md](PUBLIC_DATA_SOURCES.md).

The 24 project-generated frozen inputs are under `inputs/audit_runs/`. Their
expected SHA-256 values are recorded in `inputs/locked_audit_hashes.json`.
They are publicly downloadable without authentication or an access request.
The internal recovered-history archive is not included and is not required to
regenerate the submitted figures or Source Data from the frozen inputs.

## Repository scope

Included:

- `analysis/`, `module1/`–`module5/`, and `scripts/`: analysis and regeneration code;
- `inputs/audit_runs/`: 24 frozen CSV/JSON inputs;
- `inputs/source_records/`: source-screening and provenance records without article images;
- `tests/`: reproducibility and consistency tests;
- `environment.yml` and `requirements-lock.txt`: Python 3.11 environment;
- root citation, rights, change, and integrity metadata.

Excluded:

- generated `results/` content, figures, spreadsheets, and tables;
- manuscript, cover letter, supplementary information, and submission forms;
- literature-derived JPG/PDF files;
- `NeurMito_Recovered_Historical_Evidence.zip` and other internal audit archives;
- Zenodo metadata or DOI, because no Zenodo deposition has been published.

## Reproduce locally

```bash
conda env create -f environment.yml
conda activate neurmito-r071
python analysis/reproduce_r071.py --only all
python -m pytest -q
```

The regeneration command writes derived files under a local `results/`
directory. Those generated outputs are intentionally not tracked or distributed
in the GitHub repository. The validated Python 3.11 environment previously
regenerated Source Data, six main figures and six supplementary figures and
passed 45 tests.

## Evidence boundaries

- R033/R039 use algebraic spare/basal; R060/R060B retain independently
  reported spare/basal endpoints.
- R014B is a 91-condition transition scan; R021 is a distinct 441-condition
  diagnostic cohort.
- EWS results are retrospective and event-aligned. Prescribed lead intervals
  are not prospectively learned warning horizons.
- Figure 6 scenario weights, ROS offsets, and ±0.08 ranges are prescribed
  computational objects, not patient measurements or confidence intervals.
- Complete historical 25-state trajectories, original solver checkpoints, and
  historical pre-test locking chronology are not asserted by this release.

## Access and rights

The repository is publicly accessible without technical access restrictions.
No open-source or data-reuse license is granted. Use, execution, modification,
and redistribution are not permitted without prior written authorization from
the applicable rights holder. See [LICENSE](LICENSE).

## Release identity

- Repository: https://github.com/noonyue/neurmito
- Release: `v0.1.1`
- Zenodo DOI: not assigned
- File integrity: `repository-sha256.txt`
