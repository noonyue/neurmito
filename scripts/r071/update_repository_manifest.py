"""Regenerate the tracked-file SHA-256 manifest for the R071 repository."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "repository-sha256.txt"


def main() -> int:
    # Scope is this archive tree, independent of any enclosing project Git repo.
    excluded_dirs = {"results", ".pytest_cache", ".ruff_cache", "__pycache__", ".git"}
    relative_paths = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != MANIFEST.name
        and not any(part in excluded_dirs for part in path.relative_to(ROOT).parts)
        and path.suffix not in {".pyc", ".zip"}
    ]
    rows = []
    for relative in sorted(path for path in relative_paths if path and path != MANIFEST.name):
        path = ROOT / relative
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(f"{digest}  {relative}")
    MANIFEST.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"updated={MANIFEST} files={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
