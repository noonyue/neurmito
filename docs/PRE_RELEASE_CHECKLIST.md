# Method-only repository pre-release checklist

This package is intentionally limited to the computational methods needed to
reproduce the study workflow. It does not distribute the manuscript, figures,
tables, Source Data workbooks, or generated result artifacts.

## Completed locally

- [x] Model implementations and analysis entry points are included.
- [x] Required locked audit-run inputs and public source records are included.
- [x] Conda and pip dependency specifications are included.
- [x] Tests pass in a fresh Python 3.11 environment (`45 passed`).
- [x] Main, supplementary, and Source Data builders run in a clean extraction.
- [x] Generated outputs are written only to local `results/` directories.
- [x] Final method-only archive contains no `results/`, figures, tables,
      manuscript files, caches, bytecode, or nested archives.

## Required before public or reviewer release

- [ ] Confirm whether the locked `inputs/audit_runs/` files are approved as
      reproducibility inputs rather than distributed result artifacts.
- [ ] Resolve redistribution permission for the six literature-derived image
      assets under `inputs/source_records/` or exclude assets that are not
      required by the verified rebuild.
- [ ] Approve the software license and identify the copyright holder(s).
- [ ] Add the final author list and ORCID identifiers to `CITATION.cff`.
- [ ] Create the approved public or anonymous reviewer-access Git repository.
- [ ] Commit the method-only tree and create an immutable version tag.
- [ ] Regenerate `repository-sha256.txt` from the final committed tree.
- [ ] Create an archive DOI or approved reviewer-access record.
- [ ] Replace the release-status note in `docs/code_availability.md` with the
      final URL/DOI.
- [ ] Update the manuscript and submission system with that exact URL/DOI.

## Release rule

Do not add generated `results/` files to the repository. Reproduction commands
may create them locally; they remain ignored and are not part of the release
archive.
