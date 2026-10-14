"""Run the controlled Hybrid Neural-ODE benchmark audit."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    return subprocess.run([sys.executable, str(ROOT / "analysis" / "reproduce_r071.py"), "--only", "main"], cwd=ROOT).returncode
if __name__ == "__main__":
    raise SystemExit(main())
