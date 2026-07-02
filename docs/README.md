# Documentation Index

Updated: `2026-07-02 KST`

This directory keeps implementation, experiment, dataset, and simulation documentation. It should describe how the code works and how to reproduce the compact results, not internal writing notes or tool-specific sync procedures.

## Start Here

| File | Use |
| --- | --- |
| `dataset_setup.md` | Dataset roots, conversion expectations, and readiness checks |
| `UBUNTU_SERVER_SETUP.md` | Ubuntu server environment and paths |
| `WINDOWS_MARINECITY_ISAAC_SETUP.md` | Windows/Isaac setup for MarineCity simulation |
| `visible_execution_workflow.md` | tmux/live monitoring workflow |
| `server_gpu_allocation.md` | GPU lane policy for detector and 3D jobs |
| `current_workspace_layout.md` | Current folder policy and tracked artifact scope |

## Detector Implementation

| File | Use |
| --- | --- |
| `server_training_plan.md` | Detector training protocol and queue structure |
| `server_progress.md` | Server-side detector experiment log |
| `proposed_perception_module_plan.md` | SAFR-YOLO/P2P4-SelfAttnFR detector design and ablation protocol |
| `proposed_detector_three_core_modules.md` | Detector module implementation details |
| `system_ablation_evaluation_plan.md` | Ablation and evaluation checklist |
| `supplementary_small_object_analysis_plan.md` | Additional small-object analysis protocol |
| `uav_small_object_same_dataset_comparison_models.md` | Same-dataset comparison model matrix |

## 3D, Simulation, And Reasoning

| File | Use |
| --- | --- |
| `3d_generation_experiment_plan.md` | MarineCity neural-3D comparison protocol |
| `isaac_3d_reasoner_readiness_2026-06-16.md` | Isaac, 3D, and reasoner readiness status |
| `llm_reasoner_adjudicator_plan.md` | Evidence graph reasoning and re-observation policy |
| `qualitative_gradcam_plan.md` | Detector qualitative and activation analysis |
| `uavmarine_multiuav_scenarios.md` | Multi-UAV MarineCity scenario definitions |

## Result Summaries

| File | Use |
| --- | --- |
| `current_experiment_steps.md` | Active experiment checklist |
| `current_experiment_execution_order.md` | Execution order for remaining jobs |
| `experiment_steps_and_progress_summary.md` | Compact project progress summary |
| `accv_final_submission_readiness_2026-06-30.md` | Final claim and artifact readiness summary |
| `accv_supplementary_cleanup_audit_2026-06-30.md` | Supplementary artifact cleanup audit |

## Archive Policy

Keep only reproducibility and implementation documents in the main docs index. Superseded planning notes, prompt drafts, and editor-specific sync notes should be removed or kept outside the public repository.
