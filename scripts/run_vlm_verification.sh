#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run selective SAGE VLM verification with config: ${CONFIG}"
echo "TODO: call configured VLM only for high-ambiguity graph nodes."

