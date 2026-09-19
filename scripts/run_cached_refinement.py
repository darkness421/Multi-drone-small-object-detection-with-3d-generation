#!/usr/bin/env python3
"""Run the public REGR cache-replay CLI from a source checkout."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from regr.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
