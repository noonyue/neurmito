# Changelog

## v0.1.1 — 2026-10-14

- Identified the four public respiratory-data sources by PMID, DOI, PMCID,
  exact extracted panels, preparation, normalization, and source rights.
- Confirmed public distribution of all 24 SHA-256-locked audit inputs.
- Limited the repository and release archive to reproducibility code, frozen
  inputs, tests, environments, and necessary root metadata; generated results,
  submission files, article images, and the internal historical-evidence
  archive are excluded.
- Added confirmed citation authors and release metadata to `CITATION.cff`.
- Replaced the pending license notice with an explicit no-license/all-rights-
  reserved notice. Public access remains unrestricted, but no permission to
  use, execute, modify, or redistribute is granted.
- Recorded that no Zenodo DOI has been assigned.


## Release-preparation audit (2026-10-14)

- Validated the full asset rebuild and all 45 tests in the pinned Python 3.11 environment.
- Added the missing `scikit-learn` test dependency and replaced the removed NumPy 2.x `ndarray.ptp` call with `numpy.ptp` in the two mirrored builders.
- Removed six literature-derived JPGs from the distribution candidate because redistribution permission was not established for every image; the verified rebuild does not use them.
- Replaced the inherited license assertion with an author-action status notice and retained explicit authorship, ownership, license and DOI release gates.

## Unreleased (R071 preparation, 2026-08-31)

- Added an explicit preflight for all 24 locked R071 audit-run inputs (the original 22 plus two builder dependencies).
- Copied the locked audit-run inputs into the local candidate and verified a clean full rebuild of main figures, supplementary figures, and Source Data.
- Clarified that the public release still requires an approved visibility/access policy, immutable version, and license metadata.
- Added repository-root pytest path configuration for clean test execution.
- Lowered the package Python declaration to `>=3.8` to match the recorded R071 environment.

## R071-v1.0 (submission candidate)

- Reorganized the reproducibility package into model, audit, source, output, and test directories.
- Added one-command R071 main/supplementary builders and SHA-256 manifests.
- Documented dry-lab evidence boundaries and the excluded large R021 trajectory artifact.
