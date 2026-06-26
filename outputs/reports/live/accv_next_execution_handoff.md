# ACCV Next Execution Handoff

Updated: `2026-06-26T19:59:42+09:00`

This file lists only the next actions needed to move the research package closer to paper-ready completion. It intentionally separates paper-ready evidence from blocked external gates.

## External Capability Snapshot

- Current shell capability status: `external_gates_missing_provider_and_3d_runner`.
- AeroGraph provider configured: `False`; modes `[]`.
- Neural-3D runner configured: `False`; metric rows `0`.
- Capability report: `outputs/reports/live/external_gate_capabilities.md`.

## Already Paper-Ready

- Detector main claim: `Ours`, AP/AP50/F1 `0.382163`/`0.605173`/`0.627275`, params `20.82M`, seeds `42,123,2026`.
- TinyPerson: corrected original-window/1280 diagnostic is complete, but Ours is below YOLOv9m; keep it as a supplementary limitation only.
- Paper artifact audit: `paper_artifact_audit_ok_with_pending_gates`.

## Gate 1: Neural 3D Completion Metrics

- Current status: `marinecity_3d_input_dataset_ready_metrics_pending`.
- Source capture ready: `True`; dataset ready: `True`; neural runner available: `False`.
- Transforms input: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/transforms.json`.
- Missing metric rows: `0`; missing methods: `['nerf', 'instant_ngp', 'mip_nerf_360', 'gaussian_splatting']`.

Next executable options:

```bash
python scripts/check_marinecity_3d_runner_preflight.py
python scripts/check_marinecity_3d_completion_readiness.py
```

After an upstream runner finishes, import its verified JSON/CSV metrics with:

```bash
python scripts/import_marinecity_3d_metrics.py PATH_TO_RUNNER_METRICS.json --overwrite
python scripts/build_marinecity_3d_results_table.py
python scripts/check_marinecity_3d_completion_readiness.py
```

To complete this gate, attach an actual upstream runner such as Nerfstudio, Instant-NGP, or a 3DGS implementation to the exported MarineCity transforms and write non-placeholder PSNR/SSIM/LPIPS/FPS/runtime rows to `outputs/experiments/3d_generation_comparison.csv`.

## Gate 2: AeroGraph External Non-Mock Reasoner

- Current status: `aerograph_reviewed_candidate_ready_external_pending`.
- Prompt-pack integrity: `aerograph_prompt_pack_integrity_ok`, prompts `49`.
- Manual/direct valid responses: `0/49`.
- External-provider replication ready: `False`.

Fast smoke path:

```bash
OPENAI_API_KEY=... AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh
# or
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' AEROGRAPH_PROVIDER=command bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh
# FACTORY_COMMAND can be used instead of AEROGRAPH_COMMAND when the Factory/local command reads stdin and returns AeroGraph JSON.
```

Final 49-prompt path:

```bash
OPENAI_API_KEY=... AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
# or
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' AEROGRAPH_PROVIDER=command bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
# FACTORY_COMMAND can be used instead of AEROGRAPH_COMMAND when the Factory/local command reads stdin and returns AeroGraph JSON.
```

Manual web fallback:

- Start with batch: `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md`.
- Save JSONL answers into `outputs/reasoning/aerograph_manual_responses.jsonl`.
- Or save raw Factory/ChatGPT answers as `.md`, `.txt`, `.json`, or `.jsonl` and run the one-command importer:

```bash
python scripts/import_aerograph_external_responses.py \
  --mode final49 \
  --input reasoning/aerograph_web_raw_batches/*.md \
  --provider-label "Factory/ChatGPT web"

python scripts/import_aerograph_external_responses.py \
  --mode compact23 \
  --input reasoning/aerograph_real_capture_web_raw_batches/*.md \
  --provider-label "Factory/ChatGPT web compact"
```

```bash
python scripts/import_aerograph_manual_responses.py \
  --responses outputs/reasoning/aerograph_manual_responses.jsonl \
  --provider-label "Factory/ChatGPT web" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_paper_artifact_readiness.py
```

## Safe Rebuild After Any New Result

```bash
python scripts/build_accv_remaining_gates_queue.py
python scripts/build_accv_status_snapshot.py
python scripts/build_live_training_dashboard.py
python scripts/check_latex_patch_integrity.py
```
