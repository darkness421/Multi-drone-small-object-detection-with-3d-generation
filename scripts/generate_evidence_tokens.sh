#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Generate EvidenceToken JSON with config: ${CONFIG}"
python -m pipelines.run_dummy_evidence_pipeline

