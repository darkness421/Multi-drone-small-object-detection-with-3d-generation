#!/usr/bin/env bash
set -uo pipefail
cd /home/oem/projects/multi-uav-marine-city
echo "Resume collector waiting for GPU workers at $(date -Is)"
while [[ ! -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/resume_20260522_190713/gpu0.done ]]; do echo "Waiting for gpu0 at $(date -Is)"; sleep 60; done
while [[ ! -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/resume_20260522_190713/gpu1.done ]]; do echo "Waiting for gpu1 at $(date -Is)"; sleep 60; done
echo "All resume GPU workers finished; collecting combined results at $(date -Is)"
DETECTOR_ROOTS=outputs/detectors/server_fresh_baselines/fresh_20260519_131739\,outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 DEDUPE_KEY=dataset\,model\,seed\,ablation\,proposed_module RESULTS_CSV=outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_results.csv SUMMARY_CSV=outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_summary.csv PVALUES_CSV=outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_pvalues.csv DASHBOARD=outputs/reports/server_fresh_baselines/fresh_20260519_131739/figures/server_baseline_dashboard.png REPORT_DIR=outputs/reports/server_fresh_baselines/fresh_20260519_131739 CONDA_ENV=com3d-ace bash scripts/ubuntu/collect_server_results.sh outputs/detectors/server_fresh_baselines/fresh_20260519_131739 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/final_collection.log
echo "Resume queue complete at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/final_collection.log
