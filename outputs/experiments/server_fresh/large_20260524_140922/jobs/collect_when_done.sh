#!/usr/bin/env bash
set -uo pipefail
cd /home/oem/projects/multi-uav-marine-city
echo "Collector waiting for GPU workers at $(date -Is)"
while [[ ! -f outputs/experiments/server_fresh/large_20260524_140922/jobs/gpu0.done ]]; do echo "Waiting for gpu0 at $(date -Is)"; sleep 60; done
echo "All GPU workers finished; collecting results at $(date -Is)"
DETECTOR_ROOT=outputs/detectors/server_fresh_baselines/large_20260524_140922 RESULTS_CSV=outputs/experiments/server_fresh/large_20260524_140922/server_baseline_results.csv SUMMARY_CSV=outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv PVALUES_CSV=outputs/experiments/server_fresh/large_20260524_140922/server_baseline_pvalues.csv DASHBOARD=outputs/reports/server_fresh_baselines/large_20260524_140922/figures/server_baseline_dashboard.png REPORT_DIR=outputs/reports/server_fresh_baselines/large_20260524_140922 CONDA_ENV=com3d-ace bash scripts/ubuntu/collect_server_results.sh outputs/detectors/server_fresh_baselines/large_20260524_140922 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/final_collection.log
echo "Fresh queue complete at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/final_collection.log
