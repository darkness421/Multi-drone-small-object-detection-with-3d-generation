# Paper Figure Assets

This folder stores the current paper figure assets and editable figure sources
that are safe to keep in Git. Large simulator captures, raw render dumps, model
weights, and dataset images should stay outside Git and be copied into the final
paper package only after selection.

Current Overleaf-ready PNG exports:

| File | Paper slot |
| --- | --- |
| `fig01_com3d_ace_overall_framework.png` | Main Fig. 1, overall CoM3D-ACE framework |
| `fig02_p2p4_safr_yolo.png` | Main Fig. 2, SAFR-YOLO / P2P4-SelfAttnFR detector |
| `fig03_3d_evidence_reasoner.png` | Main Fig. 3, 3D evidence completion and ACE-Reasoner |
| `figS1_selfattnfr_module.png` | Supplementary Fig. S1, SelfAttnFR module |
| `figS2_tinyfrelu_activation.png` | Supplementary Fig. S2, TinyFReLU activation |
| `figS3_overlap_aware_nms.png` | Supplementary Fig. S3, overlap-aware NMS |

Editable/source draft figures:

| File | Purpose |
| --- | --- |
| `fig01_overall_framework.svg` | Overall CoM3D-ACE pipeline and contribution map |
| `fig02_detector_module.svg` | Working schematic for the selected SAFR-YOLO detector; `P2P4-SelfAttnFR` is the current implementation label |
| `fig03_isaac_multiuav_benchmark.svg` | Isaac Sim MarineCity multi-UAV benchmark setup |
| `fig04_3d_weather_reconstruction.svg` | Weather restoration and 3D reconstruction comparison |
| `fig05_llm_reobservation_policy.svg` | LLM reasoner and active re-observation policy |

Recommended main-paper flow:

1. Use Figure 1 in the introduction/method overview.
2. Add an evidence-graph and ambiguity-diagnosis figure before the detector module.
3. Use the main quantitative result figure after the method/experiment setup.
4. Use a qualitative multi-view before/after figure to show ambiguity resolution.
5. Move the detector module, benchmark details, extra result charts, and LLM prompt details to the supplementary material unless page budget and results justify keeping them in the main paper.

Current detector-figure rule:

- Use `fig02_detector_module.svg` as the current structure guide for
  SAFR-YOLO.
- Do not mix earlier single-seed search candidates such as P2-CBAM-FR, DCT-FR,
  or wavelet variants into the final detector figure unless they become part of
  the selected model.
- If the final detector changes, keep the same figure slot but update the
  module labels and metrics.

See `figure_and_canva_guide.md` for the full source, Canva, and export guide.
Use `figure_generation_briefs_gpt55_pro.md` when asking GPT-5.5 Pro, a
specialist figure-generation model, or a Canva artist to redraw the final method
figures.
