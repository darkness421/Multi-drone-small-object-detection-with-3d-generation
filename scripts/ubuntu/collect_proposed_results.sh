#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
DETECTOR_ROOTS=${DETECTOR_ROOTS:-outputs/detectors/server_fresh_baselines/fresh_20260519_131739,outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713,outputs/detectors/server_proposed_ablation}
DEDUP_KEY=${DEDUP_KEY:-dataset,model,seed,ablation,proposed_module}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/server_with_proposed_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_with_proposed_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/server_with_proposed_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/server_with_proposed/figures/server_baseline_dashboard.png}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_with_proposed}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/server_with_proposed_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/server_with_proposed_stage_gate.md}
STAGE_GATE_DATASET=${STAGE_GATE_DATASET:-VisDrone2019-DET}

cd "$(dirname "$0")/../.."

DETECTOR_ROOTS="$DETECTOR_ROOTS" \
DEDUPE_KEY="$DEDUP_KEY" \
RESULTS_CSV="$RESULTS_CSV" \
SUMMARY_CSV="$SUMMARY_CSV" \
PVALUES_CSV="$PVALUES_CSV" \
DASHBOARD="$DASHBOARD" \
REPORT_DIR="$REPORT_DIR" \
STAGE_GATE_JSON="$STAGE_GATE_JSON" \
STAGE_GATE_MD="$STAGE_GATE_MD" \
STAGE_GATE_DATASET="$STAGE_GATE_DATASET" \
CONDA_ENV="$CONDA_ENV" \
bash scripts/ubuntu/collect_server_results.sh
