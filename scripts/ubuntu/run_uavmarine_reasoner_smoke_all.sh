#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

for scenario in s0_locked_roi s1_adjacent_overlap s2_coastline_multiview; do
  python3 scripts/run_marinecity_3d_reasoner_smoke.py \
    --scenario "$scenario" \
    --provider rule_based \
    --out-dir "outputs/reasoning/marinecity_3d_reasoner_smoke_${scenario}"
done

echo "MarineCity 3D/reasoner smoke outputs:"
find outputs/reasoning -maxdepth 2 -name summary.json -path '*marinecity_3d_reasoner_smoke*' -print | sort
