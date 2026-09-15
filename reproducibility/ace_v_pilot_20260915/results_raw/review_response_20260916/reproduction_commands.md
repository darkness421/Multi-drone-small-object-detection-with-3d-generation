# Reproduction commands

The exact historical shell strings and scheduler IDs were not logged. The commands below are reconstructed from the COMPLETE manifests and current CLI contracts. They write to new directories and must not target the committed result directories.

## M3OT development selection and exposed held-out retest

```bash
python reproducibility/ace_v_pilot_20260915/scripts/run_ace_v_m3ot.py \
  --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal \
  --diagnostic-script reproducibility/ivc_professor_review_20260914/scripts/run_m3ot_linker_diagnostic.py \
  --ace-core reproducibility/ace_v_pilot_20260915/scripts/ace_v_core.py \
  --development-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/val_development_manifest.json \
  --held-out-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/test_final_manifest.json \
  --checkpoint /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal/assets/reid_r50_6e_mot17-4bf6b63d.pth \
  --device cpu --threads 8 \
  --output-dir reproducibility/ace_v_pilot_20260915/results_raw/rerun_m3ot_NEW
```

## MMOT exposed 50-sequence retest

```bash
python reproducibility/ace_v_pilot_20260915/scripts/run_ace_v_mmot.py \
  --benchmark-script reproducibility/ivc_temporal_meta_review_20260914/scripts/run_full50_linker_benchmark.py \
  --audit-script reproducibility/ivc_professor_review_20260914/scripts/run_cached_solver_audit.py \
  --ace-core reproducibility/ace_v_pilot_20260915/scripts/ace_v_core.py \
  --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal \
  --oracle-cache /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e1_direct_full50_v1 \
  --detector-cache /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e3_temporal_full50_v1 \
  --family-root legacy12 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/legacy12 \
  --family-root confirmation38 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/confirmation38 \
  --selected-config reproducibility/ace_v_pilot_20260915/results_raw/m3ot_direct_crop_v1/selected_config.json \
  --output-dir reproducibility/ace_v_pilot_20260915/results_raw/rerun_mmot_NEW
```

## This review pack

```bash
python reproducibility/ace_v_pilot_20260915/scripts/build_review_response.py
```
