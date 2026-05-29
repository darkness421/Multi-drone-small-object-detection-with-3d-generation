# ACCV Paper Revision and Additional Experiment Update

Updated: 2026-05-30

This note tracks the ACCV paper revisions and new experiment ideas derived from the recent UAV small-object survey papers [24]-[37]. It is intended as a GitHub-facing checklist for the paper and codebase.

## Paper structure updates

- Add a dataset composition table to the Experimental Setup section.
- Add a dataset/evaluation protocol figure showing how public 2D datasets connect to the synchronized CoM3D multi-UAV layer.
- Replace the broad placeholder detector table with a comparison matrix that separates detector-level metrics from graph-level downstream checks.
- Keep ACCV review submission anonymous; camera-ready author metadata should be restored only after acceptance or final submission instructions.
- Keep references limited to the final cited set: 34 cited BibTeX entries, 0 unused entries.

## Dataset composition to report

The paper now separates datasets into two layers.

1. Public 2D front-end datasets
   - VisDrone2019-DET and UAVDT for always-on detector training and dense traffic evaluation.
   - AI-TOD and TinyPerson for tiny-object stress testing.
   - HIT-UAV and DroneVehicle for low-light, thermal/RGB, and domain-shift testing.
   - DOTA, UAVOD-10, RO-UAV, and PhenoBench for oriented boxes, weak-context objects, masks, boundary evidence, and rotated footprints.

2. CoM3D synchronized multi-UAV layer
   - Multi-UAV RGB images, optional depth or IR, camera intrinsics/extrinsics, UAV poses, timestamps, 2D boxes, 3D object IDs, visibility, occlusion labels, view angle, and ambiguity labels.
   - Used for cross-view association, 2D-to-3D lifting, graph updates, ambiguity diagnosis, targeted re-observation, VLM verification, and communication-aware cost.

## Improved comparison table design

The comparison table should not only report 2D AP. It should include:

- General detectors: YOLOv8/v10/v11, RT-DETR, D-FINE.
- High-resolution/FPN detectors: Universal YOLO, MFFSODNet, SFFEF-YOLO, FMFN-YOLO, BPD-YOLO, LRDS-YOLO.
- Density/crop refinement: DS-YOLOv5s, DG-TSOD.
- Frequency/DETR/Former detectors: D2A, CSFPR-RTDETR, UFO-DETR, CFIA, HF-D-FINE, DFFormer.
- Context/mask/oriented/multimodal detectors: CSADet, FG-UNet, GLF-Net, AFFNet.
- Proposal/adaptive-branch detectors: Keypoint-Mask R-CNN, Hydra-Mask R-CNN.
- Ours: CoM3D-ACE evidence generator plus 3D evidence graph.

For each group, report both detector-level metrics and downstream graph checks.

## Additional experiments to add

### E1. Dataset composition and protocol validation

Show which public datasets are used for detector training, which are used for stress testing, and which synchronized CoM3D fields support 3D graph evaluation.

Metrics:
- dataset coverage by object size, density, modality, orientation, and annotation type
- missing-label or ignore-region statistics when available

### E2. Front-end detector family comparison

Compare representative detector families under a shared evaluation protocol.

Metrics:
- AP, AP50, AP75, APsmall/APtiny, recall-small/tiny
- FPS, latency, Params, GFLOPs, memory
- box jitter, background false positive rate, verified precision

### E3. Detector-to-graph transfer

Measure whether a better 2D detector actually improves 3D evidence quality.

Metrics:
- 2D APsmall versus 3D center error
- association F1
- false merge and false split
- wrong high-confidence rate

### E4. Evidence descriptor ablation

Test which detector-side descriptors help graph association.

Variants:
- bbox only
- bbox + crop feature
- bbox + boundary/mask
- bbox + frequency/high-frequency descriptor
- bbox + rotated footprint
- bbox + modality/reliability descriptor

### E5. Cross-resolution and cross-domain robustness

Inspired by DCO-CRSA, evaluate near/far UAV views and domain shifts.

Conditions:
- low altitude versus high altitude
- day versus night
- clear versus fog/rain/glare
- RGB versus thermal/RGB-T
- synthetic-to-real transfer

Metrics:
- APtiny, association F1, ambiguity trigger rate, re-observation gain

### E6. Density-guided crop versus active re-observation

Inspired by DG-TSOD, compare image-level crop refinement with new-view evidence acquisition.

Methods:
- detector-only
- dense crop refinement
- multi-view fusion without new capture
- CoM3D-ACE targeted re-observation

Metrics:
- APsmall, 3D error, ambiguity resolution, flight cost, VLM calls, communication cost

### E7. Annotation incompleteness stress test

Inspired by UAV-S/VisDrone annotation inconsistency analysis, test whether graph consistency and verification metrics remain meaningful when labels are incomplete.

Settings:
- full labels
- missing tiny labels
- ignore-region overlap
- noisy boxes/classes

Metrics:
- mAP degradation
- recall-oriented score
- unlabeled detection ratio
- human/VLM verified precision
- graph consistency score

### E8. Efficiency-aware reasoning

Compare always-on detectors with event-triggered VLM/LLM verification.

Methods:
- detector-only
- always-on VLM
- periodic VLM
- event-triggered CoM3D-ACE

Metrics:
- detector FPS
- graph latency
- VLM call count
- token cost
- end-to-end latency
- final object accuracy

## Implementation TODO mapping

- `detectors/`: add wrapper metadata for descriptor output, tiny-head score, frequency score, mask/rotated outputs, and latency.
- `evidence/`: extend EvidenceToken fields for dataset/domain tags, descriptor reliability, localization uncertainty, and modality reliability.
- `alignment/` and `graph/`: add ablations for visual, frequency, geometry, uncertainty, and time costs.
- `policy/`: implement top-K re-observation policy with expected information gain and flight/communication cost.
- `evaluation/`: add metrics for false merge, false split, association F1, box jitter, unlabeled detection ratio, verified precision, and re-observation gain.
- `paper/accv2026/`: keep dataset table, dataset protocol figure, comparison matrix, and compact ablation plan synchronized with experiments.

## Immediate next actions

1. Compile the updated ACCV paper and check that the new dataset table and figure fit within the 14-page limit.
2. Decide which public detector baselines are feasible to actually run versus cite as reported comparison.
3. Implement the detector-to-graph transfer experiment first, because it directly supports the main CoM3D-ACE claim.
4. Add annotation incompleteness and active re-observation ablations after the basic graph pipeline is stable.

## Detector baseline execution scope for Codex development

The detector comparison should be split into three practical tiers so Codex can implement the experiments without trying to reproduce every surveyed paper at once.

### Tier 1. Directly runnable baselines

These models should be trained or evaluated directly in this repository first.

- YOLOv8n
- YOLOv11n / YOLOv11s
- RT-DETR
- YOLOv10, if the training wrapper is stable
- D-FINE, if setup time is acceptable

Purpose:
- establish reproducible public 2D detector baselines
- produce AP/AP50/AP75/APsmall, recall, FPS, latency, Params, and GFLOPs
- generate EvidenceToken outputs for downstream 3D graph tests

### Tier 2. Strong UAV detector comparison

These are strong reference models that should be added as reported-comparison baselines first, and implemented only if code/checkpoints are practical.

- LRDS-YOLO
- BPD-YOLO
- UAVDet
- CSFPR-RTDETR
- HF-D-FINE

Purpose:
- compare against recent UAV-specific detector designs
- evaluate whether high-quality 2D small-object detection improves graph-level 3D association
- prioritize models with public code or easily reproducible YOLO/DETR-style modifications

### Tier 3. Idea-level ablation references

These papers should inform ablation design rather than all being fully reproduced.

- DG-TSOD: density-guided crop refinement versus active re-observation
- FG-UNet: mask, boundary, and fine-grained crop evidence
- GLF-Net: rotated footprints and orientation uncertainty
- Keypoint-Mask R-CNN / Hydra-Mask R-CNN: proposal source, keypoint cues, and scale-specific branches
- AFFNet: RGB/thermal or modality-aware evidence reliability

Purpose:
- translate paper ideas into EvidenceToken fields and graph ablations
- avoid overloading the ACCV experiments with too many full detector implementations
- keep the central claim focused on detector-to-graph transfer

### Main comparison question

The main experiment should not be a detector AP leaderboard only. The key question is:

> Does a stronger 2D small-object detector produce evidence that improves multi-UAV 3D graph association, ambiguity diagnosis, and targeted re-observation?

Therefore, every important detector family should be evaluated along two axes:

1. 2D front-end quality
   - APsmall/APtiny
   - recall-small/tiny
   - AP75 or localization stability
   - FPS and compute cost

2. Downstream CoM3D value
   - 3D center error
   - association F1
   - false merge / false split
   - ambiguity resolution rate
   - re-observation gain
   - final object accuracy

### Suggested implementation order

1. Finish Tier 1 baselines and EvidenceToken export.
2. Add detector-to-graph transfer table using Tier 1 outputs.
3. Add LRDS-YOLO and BPD-YOLO as first Tier 2 references because they are closest to lightweight YOLO/FPN implementation.
4. Add CSFPR-RTDETR or HF-D-FINE if DETR/D-FINE code integration is practical.
5. Implement Tier 3 ideas as graph/evidence ablations, not full detector replications.
