# Current Experiment Execution Order

Updated: 2026-06-26 02:30 KST

This is the current official order for detector/system experiments.

## Order

1. Finish the active 2D detector ablation queue. **Done.**
   - Current gate marker:
     `outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log`
   - Required marker:
     `QUEUE_FINISHED final P2P4-SelfAttnFR ablation`

2. Finish cited related-work detector comparisons at 1280. **Done for the current paper-facing table.**
   - Completed paper-facing cited/reimplemented rows:
     `CSFPR-RTDETR [11]`, `MFFSODNet [2]`, `SFFEF-YOLO [4]`,
     `BPD-YOLO [7]`, `HF-D-FINE [12]`, and `UAVDet [16]`.
   - UAVDet [16] is now included in the final detector preview as a cited
     related-work 1280 3-seed row. Current aggregate: AP `0.3812`, AP50
     `0.6005`, F1 `0.6203`, Params `33.55M`.
   - Ours remains rank 1 in the paper-facing table: AP `0.3822`, AP50
     `0.6052`, F1 `0.6273`, Params `20.82M`.
   - Removed from paper-facing comparison:
     LEAF-YOLO rows are not used unless they are explicitly cited in the final
     manuscript.

3. Prepare final detector heatmap and qualitative evidence. **Done for first supplementary pass.**
   - Queue session:
     `final-detector-heatmaps-after-related-work`
   - Core models:
     `YOLOv11l`, `YOLOv9c`, `Ours: P2P4-SelfAttnFR`
   - Output:
     `outputs/qualitative/gradcam/final_detector/gradcam_run_plan.json`
   - Rendered sheet:
     `outputs/qualitative/gradcam/final_detector/feature_activation_contact_sheet.png`
   - Paper/live copy:
     `outputs/reports/live/paper_fig11_final_detector_feature_activation_heatmap.png`
   - Required marker:
     `QUEUE_FINISHED final detector heatmaps`

4. Split GPUs for cross-dataset and system experiments. **Done for current queues; GPU0 is available.**
   - GPU0 current:
     no active detector run detected after UAVDet and TinyPerson finished.
   - GPU0 next:
     keep free unless the paper review finds a missing detector row or a
     targeted re-run is needed.
   - TinyPerson queue session:
     `tinyperson-640-after-2d-gpu0` completed the planned top-model 640 stress
     check.
   - GPU1 now:
     Isaac / MarineCity / 3D evidence / AeroGraph reasoner experiments.

5. Improve MarineCity visual evidence. **Smoke complete; final visual review pending.**
   - Real-Cesium viewer160 smoke outputs are complete for S0/S1/S2.
   - Current system-test bundle:
     `outputs/reports/live/marinecity_system_test_10plus`
   - Current visual QA ranking:
     `outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_top8.png`
   - Current crop-only framing candidates:
     `outputs/reports/live/marinecity_real_capture_crops/marinecity_real_capture_crop_top12.png`
   - Clean full-frame recapture runbook:
     `docs/marinecity_clean_recapture_plan.md`
   - Latest viewer160 recapture uses real Cesium MarineCity with UAV camera
     altitudes in the 140--160 m band (`uav_01=140`, `uav_02=150`,
     `uav_03=160`). Use the generated panels for review, then decide whether a
     cleaner live-GUI recapture is needed for the main-paper qualitative figure.
   - Current main full-frame gate is passed: best full-frame black/void ratio
     is `0.017828`, and mean top-3 black/void ratio is `0.087552`.

6. Run AeroGraph external-provider reasoner validation. **Pending provider responses.**
   - Prompt pack:
     `outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl`
   - Prompt count: `49`
   - Current valid-schema coverage: `0/49` external-provider responses.
   - Web batches:
     `outputs/reports/live/aerograph_prompt_pack/web_batches`
   - Import template:
     `outputs/reports/live/aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl`
   - Paper table remains `PENDING` until all reviewed responses are imported.

7. Promote final paper artifacts after the two system gates above. **Pending.**
   - Detector tables and ablation artifacts are paper-ready for the current
     detector claim.
   - MarineCity rows can use the clean full-frame visual candidate, while
     AeroGraph rows should remain pending until all external-provider responses are
     valid-schema complete.
   - Run `python scripts/check_paper_artifact_readiness.py` and
     `python scripts/check_latex_patch_integrity.py` before manuscript export.

## TinyPerson Scope

TinyPerson is a supplementary stress test, not the main detector gate.

Default corrected TinyPerson corner/original-window models after current 1280
comparison queue:

- `YOLOv9m`
- `Ours`

Default TinyPerson setting is corrected crop-window materialization, collapsed
single `person` class, 1280 input, and seed `42` first. Expand to seeds `42`,
`123`, and `2026` only if the corrected result is strong enough to support a
supplementary generalization claim. Do not run broad TinyPerson ablations or
related-work TinyPerson rows by default.

## Active Waiting Queues

- MarineCity external-provider AeroGraph provider test: waiting for `OPENAI_API_KEY` or
  a working local CLI command.
- Current AeroGraph prompt-pack dry-run is healthy for all 49 prompts, but it is
  not a external-provider result.
- Final MarineCity qualitative figure: clean real-Cesium full-frame gate is
  passed; keep the figure as a candidate until final paper layout review.
- No active detector GPU queue is required by the current plan unless paper
  review identifies a missing cited row or a targeted rerun.

These waiting queues should not consume GPU until their required markers are
available.
