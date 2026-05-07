#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run graph fusion with config: ${CONFIG}"
python -m pipelines.run_dummy_evidence_pipeline

