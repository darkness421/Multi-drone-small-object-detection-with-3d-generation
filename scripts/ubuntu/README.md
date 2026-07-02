# Ubuntu Experiment Scripts

Active entrypoints for the current ACCV detector phase.

## Active Lanes

| Lane | Script | Purpose |
| --- | --- | --- |
| Proposed GPU0 | `run_under_param_target_queue.sh` | Continuous under-parameter proposed detector search. |
| Proposed single job | `start_yolov11_p2_balanced_search.sh` | Launch one P2-balanced proposed variant. Defaults to GPU0. |
| Related-work GPU1 | `start_related_work_detector_queue.sh` | Start runnable GitHub-backed comparison models. |
| Related-work queue | `run_related_work_detector_queue.sh` | CSFPR/LEAF/comparison policy and execution order. |
| CSFPR eval | `run_csfpr_rtdetr_eval.sh` | Evaluate staged CSFPR-RTDETR checkpoint. |
| LEAF eval | `run_leaf_yolo_eval.sh` | Evaluate staged LEAF-YOLO-N and LEAF-YOLO-S checkpoints. |
| Dashboard | `live_training_dashboard_png.sh` | Refresh `outputs/reports/live/training_dashboard.png`. |
| Scoreboard | `watch_live_training_scoreboard.sh` | Terminal scoreboard for baseline/proposed ranking. |

## GPU Policy

- GPU0: proposed detector search.
- GPU1: related-work comparison and lightweight external evaluations.
- `start_yolov11_p2_balanced_search.sh` defaults to `LOCK_PROPOSED_TO_GPU0=1`.
- `train_visdrone_baselines_tmux.sh` accepts `GPU_LIST`, for example `GPU_LIST=1`.

## Legacy Scripts

Older baseline, weekend, NMS, and large-model scripts remain here for
reproducibility, but they are not the active development path unless a current
plan explicitly references them.
