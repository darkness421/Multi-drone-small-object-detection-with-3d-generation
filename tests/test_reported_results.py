from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_released_result_claims_recompute():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_reported_results.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
