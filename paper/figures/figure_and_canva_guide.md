# ACCV Figure, Asset, And Canva Guide

Updated: 2026-06-16 KST

This guide defines what figures we need, where their source data should come
from, which figures belong in the main paper vs supplementary material, and how
to redraw them cleanly in Canva or another vector editor.

## Core Rule

The main paper figures should prove the system story, not just decorate it.
Every main figure should answer one reviewer question:

- What is the proposed system?
- What is technically new?
- Does it improve the important metric?
- Can I visually understand why it helps?

Detector graphs, full per-seed charts, hyperparameters, and large result
dashboards are better placed in the supplementary material unless the proposed
detector becomes a clear main contribution.

## Current Figure Sources

| Source | Current Path | Use |
| --- | --- | --- |
| Overall framework draft | `paper/figures/fig01_overall_framework.svg` | Starting point for Main Fig. 1 |
| Detector module draft | `paper/figures/fig02_detector_module.svg` | Working schematic for the selected SAFR-YOLO detector; `P2P4-SelfAttnFR` remains the current implementation label |
| MarineCity benchmark draft | `paper/figures/fig03_isaac_multiuav_benchmark.svg` | Main or supplement dataset figure |
| 3D/weather reconstruction draft | `paper/figures/fig04_3d_weather_reconstruction.svg` | Candidate qualitative/system figure |
| LLM re-observation draft | `paper/figures/fig05_llm_reobservation_policy.svg` | Candidate method subfigure or supplement |
| Detector summary charts | `outputs/reports/server_with_proposed/figures/*.png` | Supplement detector result figures |
| Large detector live charts | `outputs/reports/live/large_20260524_140922_figures/*.png` | Supplement or final detector appendix |
| Main system tables | `paper/tables/system_level_comparison_filled.csv` | Main result table after metric verification |
| Detector front-end tables | `paper/tables/detector_frontend_comparison_filled.csv` | Main compressed table after final values |
| MarineCity metadata | `outputs/experiments/marinecity_multiview_benchmark.json` | Dataset/scene/camera figure source |
| Pose metadata | `outputs/experiments/poses/*/*.json` | Evidence graph and camera-layout figure source |

## Main Paper Figure Plan

| Figure | Main Message | Source | Final Format | Canva Role |
| --- | --- | --- | --- | --- |
| Fig. 1: CoM3D-ACE Pipeline | Multi-UAV images become 3D evidence, ambiguity diagnosis, completion, and re-observation | `fig01_overall_framework.svg`, method text | PDF export, PNG preview | Redraw as clean pipeline |
| Fig. 2: Proposed YOLO Evidence Generator | Shows the detector-side module without overclaiming final results | `fig02_detector_module.svg`, method text, final detector table | PDF export, PNG preview | Draw with SAFR-YOLO labels |
| Fig. 3: 3D Evidence Graph And Ambiguity | Nodes/edges/uncertainty explain the technical novelty | pose JSON, method equations, graph sketch | PDF export, PNG preview | Build graph diagram and ambiguity callouts |
| Fig. 4: Dataset/Protocol Or Main Quantitative Result | Shows MarineCity protocol or the key system-level metric | MarineCity metadata or final CSV | PDF export, PNG preview | Use script-generated plots for numeric panels |
| Fig. 5: Qualitative Multi-View / 3D Case | Show before/after ambiguity resolution, restoration, or re-observation | selected simulator/detector frames | PDF/PNG panels | Compose clean panel with callouts |

## Supplementary Figure Plan

| Figure | Content | Source |
| --- | --- | --- |
| S1 | Full detector AP/AP50 chart | `outputs/reports/server_with_proposed/figures/ap_ap50_by_model.png` |
| S2 | Params-vs-AP and GFLOPs-vs-AP | `outputs/reports/server_with_proposed/figures/params_vs_ap.png`, `gflops_vs_ap.png` |
| S3 | Seed AP distribution | `outputs/reports/server_with_proposed/figures/seed_ap_distribution_by_model.png` |
| S4 | Proposed detector ablation curves/tables | `outputs/experiments/top3_proposed_ablation_commands.csv`, final summaries |
| S5 | MarineCity scene and camera layout | `outputs/experiments/marinecity_multiview_benchmark.json`, `outputs/experiments/poses/*/*.json` |
| S6 | Evidence graph examples | selected graph/association debug outputs |
| S7 | Ambiguity diagnosis examples | selected false merge/split/occlusion cases |
| S8 | Re-observation before/after | selected re-observation outputs |
| S9 | VLM prompt input/output schema | prompt text and JSON schema |
| S10 | Failure case gallery | selected failure frames |

## Recommended Visual Style

Use a restrained research-paper style:

- Background: white or very light neutral.
- Primary accent: deep teal or blue for CoM3D-ACE.
- Secondary accent: amber for uncertainty/ambiguity.
- Error/failure accent: muted red.
- Success/completed-evidence accent: green.
- Use consistent line weights, ideally 1.2-1.8 pt in final PDF.
- Avoid gradients, decorative blobs, brand-heavy visuals, and oversized logo marks.
- Use vector arrows and labels for method diagrams.
- Use actual image crops for qualitative examples.
- Use script-generated plots for numerical results, then polish labels if needed.

Suggested palette:

| Role | Hex |
| --- | --- |
| Evidence graph / proposed | `#2563EB` |
| 3D geometry / camera rays | `#0F766E` |
| Ambiguity / uncertainty | `#D97706` |
| Failure / unresolved | `#DC2626` |
| Completed / verified | `#16A34A` |
| Text | `#111827` |
| Light background | `#F8FAFC` |
| Border/grid | `#CBD5E1` |

## CoM3D-ACE Mark Guidance

For a double-blind submission, the mark must not reveal an institution, lab, or
personal identity. It should be used lightly, mainly as an internal visual label
inside figures, not as a branding element on the paper title page.

Safe mark concept:

- Three small UAV/camera nodes around a simple wireframe cube or city block.
- One highlighted uncertain object box in amber.
- A completed/verified 3D box in teal or blue.
- Text label: `CoM3D-ACE`.
- No university colors, lab names, location-specific skyline, or personal logos.

Canva prompt/brief:

```text
Create a clean academic vector mark for "CoM3D-ACE". The mark should show three
minimal UAV camera nodes observing a simple 3D evidence cube or city block. Use
thin vector lines, a white background, deep blue and teal as primary colors, and
amber only for uncertainty. The style should be suitable for a computer vision
conference paper figure, not a commercial logo. Do not include any institution,
author name, mascot, or real-world brand.
```

Export:

- Preferred: PDF for paper use.
- Backup: PNG at 300-600 dpi with transparent background.
- Remove metadata if possible before submission.

## Canva Briefs For Main Figures

### Fig. 1: CoM3D-ACE Pipeline

Canvas:

- Wide two-column paper figure.
- Preferred final aspect ratio: about 2.0:1.
- Must remain readable when printed at two-column width.

Layout:

1. Left: 3-4 UAV camera views.
2. Middle-left: detector/front-end evidence extraction.
3. Middle: 3D evidence graph with object nodes, camera nodes, uncertainty edges.
4. Middle-right: ambiguity diagnosis block.
5. Right: evidence completion, selective re-observation, optional VLM verification.

Labels:

- `Multi-UAV observations`
- `2D evidence extraction`
- `3D evidence graph`
- `Ambiguity diagnosis`
- `Evidence completion / re-observation`
- `Verified object state`

Avoid:

- Making the detector the visual center.
- Overloading the figure with every module name.
- Using a marketing-style hero graphic.

### Fig. 2: Proposed YOLO Evidence Generator

Canvas:

- One-column or compact two-column figure.
- Use the detector module draft as a starting point, but keep final claims
  blank until the detector gate is final.

Layout:

1. Input UAV crop with small/adjacent objects.
2. Selected YOLO backbone block with `YOLOv11l`.
3. High-resolution P2/P3/P4 detection path with `P2P4 heads`.
4. SelfAttnFR refinement and TinySpatialFReLU activation blocks with short
   formula labels only if space allows.
5. NMS policy block as a small eval-only side tag.
6. Output `EvidenceToken`: box, class, confidence, uncertainty, descriptor,
   pose/time.

Labeling rules:

- Use `Proposed Evidence Generator` for the selected detector module, but keep
  wording flexible enough to rename it if the final detector changes.
- For the current draft, use `SAFR-YOLO`; add `P2P4-SelfAttnFR implementation`
  only if the figure needs to match the experiment table.
- Show ablation-only modules as side tags, not as if all modules are active.
- Use only the final approved AP/AP50/F1 values from the normalized 1280
  three-seed table.

Avoid:

- Official YOLO logos.
- `SOTA`, `best`, or `outperforms all` labels before the final gate.
- Making the detector figure larger or more important than the full system
  pipeline.

### Fig. 3: Evidence Graph And Ambiguity

Canvas:

- Two-column width if possible; one-column if method section is tight.

Layout:

1. Left: camera rays from multiple UAVs to candidate object boxes.
2. Center: graph representation with node types and edge types.
3. Right: four ambiguity cases: false merge, false split, occlusion, missing-view evidence.

Visual encoding:

- Camera/view nodes: circles.
- Object hypotheses: squares or rounded boxes.
- Spatial association edges: solid lines.
- Uncertain/conflicting edges: dashed amber lines.
- Recovered/completed edge: teal or green line.

Source:

- `outputs/experiments/poses/*/*.json` for camera/view naming.
- Method equations for score terms.
- Selected qualitative cases once experiments finish.

### Fig. 4: Dataset / Protocol / Quantitative Result Summary

Do not manually draw the bars in Canva. Generate the plot from source CSV, then
use Canva only for layout/caption alignment if necessary.

Source:

- `paper/tables/system_level_comparison_filled.csv`
- Later final system result CSVs.

Recommended plot:

- Grouped bars for `Final_Acc`, `Assoc_F1`, and `Ambiguity_Res`.
- Secondary small panel for `Center_3D_Error` where lower is better.
- Mark `Full CoM3D-ACE` clearly but do not exaggerate if the value is not best.

Before final:

- Verify that every plotted value matches the CSV.
- If `Full CoM3D-ACE` is not best on a metric, explain the tradeoff or choose a
  better metric that reflects the actual system claim.

If used as dataset/protocol instead of a result plot, show MarineCity scene
types, multi-UAV synchronized capture, RGB/depth/pose/2D boxes/3D IDs, train/val
/test split, and evaluation tasks.

### Fig. 5: Qualitative Multi-View / 3D Case

Canvas:

- 2x3 or 3x3 panel.
- Each row should tell one mini-story.

Candidate row structure:

1. Input multi-UAV views.
2. Detector-only ambiguity or failure.
3. CoM3D-ACE evidence graph/completed result.

Good examples:

- Occluded car or pedestrian recovered from another view.
- False merge split into two object hypotheses.
- Low-confidence small object verified through re-observation.
- Weather-degraded view corrected by cross-view evidence.

Callouts:

- Use small numbered circles.
- Keep captions short.
- Use colored boxes consistently: baseline in red/amber, ours in blue/green.

## What To Avoid In Main Paper Figures

- Do not include too many detector leaderboard plots in the main paper.
- Do not include raw training curves unless they prove stability.
- Do not use decorative logos as if this were a product deck.
- Do not include institution-specific marks, filenames, usernames, or paths in
  submitted figures.
- Do not create a figure whose claim is stronger than the actual experiment.
- Do not place essential experimental details only in supplementary material.

## Figure Production Workflow

1. Keep editable sources in `paper/figures/`.
2. Keep generated plots in `outputs/reports/.../figures/`.
3. Move final selected assets into `paper/figures/final/`.
4. Export every final figure as PDF for LaTeX, plus PNG preview/backup.
5. For raster qualitative panels, export at least 300 dpi.
6. Check readability at final paper size.
7. Confirm anonymity: no usernames, lab names, absolute paths, or identifying
   metadata.
8. Confirm every numeric figure matches the final CSV/table source.

## File Naming Convention

Use stable names so LaTeX references do not break:

| File | Purpose |
| --- | --- |
| `fig01_pipeline_canva.pdf` | Main pipeline |
| `fig02_yolo_proposed_module_canva.pdf` | Proposed YOLO/evidence-generator module |
| `fig03_evidence_graph_canva.pdf` | Evidence graph and ambiguity |
| `fig04_dataset_protocol_canva.pdf` | MarineCity dataset/protocol |
| `fig04_main_results_canva.pdf` | Main quantitative result, if used |
| `fig05_qualitative_canva.pdf` | Main qualitative result |
| `fig05_3d_restoration_canva.pdf` | 3D/restoration qualitative result |
| `figS_llm_reasoner_canva.pdf` | Supplement LLM/VLM reasoner and prompt schema |
| `figS01_detector_ap_ap50.pdf` | Supplement detector chart |
| `figS02_efficiency_tradeoff.pdf` | Supplement efficiency chart |
| `figS03_seed_distribution.pdf` | Supplement seed distribution |
| `figS04_ablation.pdf` | Supplement proposed/module ablation |
| `figS05_dataset_layout.pdf` | Supplement MarineCity/camera layout |
| `figS06_failure_cases.pdf` | Supplement failure cases |

## Immediate Drawing Tasks

1. Draw Fig. 1 pipeline from `fig01_overall_framework.svg`.
2. Draw Fig. 2 proposed YOLO/evidence-generator module from
   `fig02_detector_module.svg`, with `Backbone: TBD`, `P2 branch: under test`,
   `TinyFReLU: under test`, and `NMS: TBD`.
3. Draw Fig. 3 evidence graph and ambiguity diagnosis.
4. Prepare a MarineCity dataset/protocol layout for Fig. 4, separate from the
   detector module.
5. Prepare an empty Fig. 5 qualitative layout; fill it after detector/3D outputs
   are selected.

Only copy final exported PDF/PNG assets into the Overleaf repository. Keep Canva
links, SVG sources, and drawing briefs here in the main project repository.
