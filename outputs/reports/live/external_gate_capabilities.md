# External Gate Capabilities

Updated: `2026-06-27 13:34:57 KST`
Status: `external_gates_missing_provider_and_3d_runner`

This report checks whether the remaining external gates can be executed from the current shell. Secret values are never printed.

## Summary

- AeroGraph provider configured: `False`; modes `[]`
- Provider candidates without runnable command: `False`; candidates `{'ollama': False, 'openai_cli': False}`
- Neural 3D runner configured: `False`
- Neural 3D source capture ready: `True`
- Neural 3D dataset ready: `True`
- Neural 3D metric rows: `0`

## Current Gate Reports

| Gate | Value |
|---|---|
| `aerograph_final_status` | `aerograph_reviewed_candidate_ready_external_pending` |
| `aerograph_final_external_ready` | `False` |
| `aerograph_final_valid_direct_responses` | `0` |
| `aerograph_final_prompt_count` | `49` |
| `aerograph_compact_smoke_status` | `aerograph_real_capture_nonmock_smoke_complete` |
| `marinecity_3d_completion_status` | `marinecity_3d_input_dataset_ready_metrics_pending` |
| `marinecity_3d_runner_available` | `False` |
| `marinecity_3d_metric_rows` | `0` |

## Environment Flags

| Variable | Set | Readable |
|---|---|---|
| `OPENAI_API_KEY` | `False` | `` |
| `AEROGRAPH_COMMAND` | `False` | `` |
| `AEROGRAPH_ENV_FILE` | `False` | `` |
| `OLLAMA_HOST` | `False` | `` |
| `AEROGRAPH_OPENAI_MODEL` | `False` | `` |

## Commands

| Command | Available | Path |
|---|---|---|
| `ollama` | `False` | `` |
| `openai` | `False` | `` |
| `ns-train` | `False` | `` |
| `ns-process-data` | `False` | `` |
| `colmap` | `False` | `` |
| `instant-ngp` | `False` | `` |

## Next Commands

### AeroGraph manual web fallback

```bash
python scripts/import_aerograph_external_responses.py --mode final49 --input reasoning/aerograph_web_raw_batches/*.md --provider-label "ChatGPT/Codex web"
```

### AeroGraph compact manual fallback

```bash
python scripts/import_aerograph_external_responses.py --mode compact23 --input reasoning/aerograph_real_capture_web_raw_batches/*.md --provider-label "ChatGPT/Codex web compact"
```

### Neural 3D fallback/import path

```bash
Install/connect Nerfstudio, Instant-NGP, or 3DGS, then run python scripts/import_marinecity_3d_metrics.py PATH_TO_RUNNER_METRICS.json --overwrite
```

## Claiming Rule

This report only indicates whether external execution is configured. It does not promote AeroGraph or neural-3D results unless the corresponding readiness reports contain complete, non-placeholder outputs.
