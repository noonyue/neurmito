import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_r071_builder_help():
    result = subprocess.run(
        [sys.executable, "analysis/reproduce_r071.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--only" in result.stdout


def test_r071_locked_inputs_exist():
    required = [
        ROOT / "inputs" / "source_records" / "README.md",
        ROOT / "inputs" / "input_manifest.json",
        ROOT / "inputs" / "parameter_manifest.json",
    ]
    assert all(path.is_file() for path in required)


def test_result_artifacts_are_not_tracked():
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "results"],
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_results = result.stdout.splitlines()
    else:
        manifest = (ROOT / "repository-sha256.txt").read_text(encoding="utf-8")
        tracked_results = [line for line in manifest.splitlines() if "  results/" in line]
    assert tracked_results == []
