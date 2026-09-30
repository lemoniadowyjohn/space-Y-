"""Run the three recruiter-facing scenarios locally."""

from pathlib import Path
import subprocess
import sys


for scenario in ("success", "fallback", "approval"):
    print(f"\n=== {scenario.upper()} ===")
    subprocess.run(
        [sys.executable, "-m", "governed_agent.demo", "--scenario", scenario, "--workspace", str(Path("artifacts") / scenario)],
        check=True,
    )
