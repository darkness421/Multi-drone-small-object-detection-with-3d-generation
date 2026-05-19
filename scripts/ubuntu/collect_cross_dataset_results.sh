#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
DETECTOR_ROOTS=${DETECTOR_ROOTS:-outputs/detectors/server_baselines,outputs/detectors/server_uavdt_baselines}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/server_cross_dataset_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_cross_dataset_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/server_cross_dataset_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/server_cross_dataset_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/server_cross_dataset_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/server_cross_dataset_stage_gate.md}
STAGE_GATE_DATASET=${STAGE_GATE_DATASET:-VisDrone2019-DET}

cd "$(dirname "$0")/../.."

DETECTOR_ROOTS="$DETECTOR_ROOTS" \
RESULTS_CSV="$RESULTS_CSV" \
SUMMARY_CSV="$SUMMARY_CSV" \
PVALUES_CSV="$PVALUES_CSV" \
DASHBOARD="$DASHBOARD" \
STAGE_GATE_JSON="$STAGE_GATE_JSON" \
STAGE_GATE_MD="$STAGE_GATE_MD" \
STAGE_GATE_DATASET="$STAGE_GATE_DATASET" \
CONDA_ENV="$CONDA_ENV" \
bash scripts/ubuntu/collect_server_results.sh
