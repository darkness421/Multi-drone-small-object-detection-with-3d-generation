# Live Report Index

This folder keeps compact, current implementation reports that are useful for reproducing detector, MarineCity, neural-3D, and reasoner checks. It should not contain raw training runs, datasets, weights, or tool-specific sync notes.

## Detector

- `training_dashboard.png`: current training/queue dashboard.
- `final_input_resolution_summary.md`: input-resolution sweep summary.
- `final_nms_robustness_summary.md`: NMS robustness sweep summary.
- `paper_detector_figures_manifest.md`: detector figure export manifest for LaTeX manuscript assets.

## MarineCity And 3D

- `marinecity_system_integration_check.md`: object, camera, detector, graph, 3D, and reasoner integration gate.
- `marinecity_simulation_dashboard.png`: compact MarineCity scenario dashboard.
- `marinecity_neural3d_dataset_export.md`: RGB/depth/pose export summary for neural 3D runners.
- `marinecity_depth_pointcloud_smoke.md`: depth-fused geometry validation summary.
- `marinecity_depth_view_consistency_sanity.md`: multi-view depth/geometry consistency check.
- `marinecity_3d_completion_readiness.md`: neural 3D runner-family readiness and metric row status.

## Reasoner

- `aerograph_nonmock_readiness_status.md`: external-provider/local-model readiness for AeroGraph validation.
- `aerograph_reasoner_table_manifest.json`: compact table source manifest.
- `aerograph_prompt_pack/`: prompt pack and validation checklist.
- `aerograph_real_capture_prompt_pack/`: compact real-capture prompt pack.

## Current Workflow

- `current_work_status.md`: current local workflow snapshot.
- `accv_workflow_status_snapshot.md`: detector, MarineCity, 3D, and reasoner status snapshot.
- `accv_remaining_gates_queue.md`: concise remaining implementation gates.

Keep this directory small. Move stale dashboards, historical logs, and old generated reports to `outputs/reports/archive/` or leave them untracked.
