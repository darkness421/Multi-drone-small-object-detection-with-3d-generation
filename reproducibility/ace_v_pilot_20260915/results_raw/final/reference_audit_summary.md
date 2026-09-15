# Temporal-refinement bibliography audit

This audit measures citation coverage; it does not assert a journal minimum.

## Version reconciliation

| Snapshot | Compiled references | Source-tree cite keys | Evidence |
| --- | ---: | ---: | --- |
| 20260913 broad manuscript | 38 | 38 | `f68bb489` and reviewed PDF |
| 20260915 narrowed pre-repair | 22 | 26 | `da05de1` source topology |
| Final temporal-refinement source | 34 | 37 | reachable inputs from `main.tex` |

The 38-to-22 drop is therefore real at the compiled-PDF level. The four-key
source/PDF gap in the pre-repair snapshot came from citations that existed only
in TeX files not included by `main.tex`. The final gap is three keys because the
VisDrone-DET2019 source citation is now reachable from the Fig. 1 caption.

## Decisions

- Keep: 22
- Restore: 1
- Add: 11
- Remove from compiled scope: 15
- `nocite{*}` or bibliography-only padding: none
- Duplicate DOI entries in current `main.bib`: none

## Added and restored claim linkage

| Key | Decision | Section | Supported claim | Metadata source |
| --- | --- | --- | --- | --- |
| `aharon2022botsort` | add | Related Work: online tracking | BoT-SORT combines motion, appearance, and camera-motion compensation. | https://arxiv.org/abs/2206.14651 |
| `bergmann2019tracktor` | add | Related Work: online tracking | Tracktor provides a detector-regression tracking route and failure analysis. | https://openaccess.thecvf.com/content_ICCV_2019/html/Bergmann_Tracking_Without_Bells_and_Whistles_ICCV_2019_paper.html |
| `bewley2016sort` | add | Related Work: online tracking | SORT establishes the Kalman-prediction and linear-assignment baseline. | https://ieeexplore.ieee.org/document/7533003/ |
| `du2018uavdt` | add | Related Work: aerial tracking | UAVDT provides moving-camera and small-target aerial tracking context. | https://openaccess.thecvf.com/content_ECCV_2018/html/Dawei_Du_The_Unmanned_Aerial_ECCV_2018_paper.html |
| `du2019visdrone` | restore | Introduction, Fig. 1 caption | VisDrone-DET2019 is the source of the real aerial detection example. | https://openaccess.thecvf.com/content_ICCVW_2019/html/VISDrone/Du_VisDrone-DET2019_The_Vision_Meets_Drone_Object_Detection_in_Image_Challenge_ICCVW_2019_paper.html |
| `gao2023memotr` | add | Related Work: learned association | MeMOTR represents learned long-term track memory. | https://openaccess.thecvf.com/content/ICCV2023/html/Gao_MeMOTR_Long-Term_Memory-Augmented_Transformer_for_Multi-Object_Tracking_ICCV_2023_paper.html |
| `gao2025motip` | add | Related Work: learned association | MOTIP contrasts in-context ID prediction with frozen post-linking. | https://openaccess.thecvf.com/content/CVPR2025/html/Gao_Multiple_Object_Tracking_as_ID_Prediction_CVPR_2025_paper.html |
| `pirsiavash2011global` | add | Related Work: global association | Network-flow optimization is a classical global MOT formulation. | https://vision.ics.uci.edu/papers/globally-optimal-greedy-algorithms-for-tracking-a-variable-2011/ |
| `sun2025gta` | add | Related Work: post-tracking linking | GTA is a plug-and-play global tracklet association method. | https://link.springer.com/chapter/10.1007/978-981-96-2644-1_6 |
| `wang2019trackletnet` | add | Related Work: tracklet graphs | TrackletNet models tracklets as graph vertices with learned connectivity. | https://haotian-zhang.github.io/publication/tnt/ |
| `wen2019visdronemot` | add | Related Work: aerial tracking | VisDrone-MOT2019 is the drone temporal-MOT challenge citation. | https://doi.org/10.1109/ICCVW.2019.00028 |
| `wojke2017deepsort` | add | Related Work: online tracking | Deep SORT adds a learned appearance association metric. | https://arxiv.org/abs/1703.07402 |

## Excluded prior-scope citations

| Key | Title | Reason |
| --- | --- | --- |
| `bai2025sffefyolo` | {SFFEF-YOLO}: Small Object Detection Network Based on Fine-Grained Feature Extraction and Fusion for Unmanned Aerial Images | Detector-only SFFEF-YOLO work is outside the narrowed temporal paper. |
| `bodla2017softnms` | Soft-{NMS}: Improving Object Detection with One Line of Code | Soft-NMS is cited only by the detector source file excluded from main.tex. |
| `cai2025neusis` | {NEUSIS}: A Compositional Neuro-Symbolic Framework for Autonomous Perception, Reasoning, and Planning in Complex {UAV} Search Missions | Cross-view scene integration is outside within-stream post-linking. |
| `chao2025bpdyolo` | A Lightweight Small Object Detection Model for {UAV} Images Based on Deep Semantic Integration | Detector-only comparison is outside the narrowed temporal paper. |
| `ding2024adatrack` | {ADA-Track}: End-to-End Multi-Camera {3D} Multi-Object Tracking with Alternating Detection and Association | End-to-end multi-camera 3D tracking is not the evaluated task. |
| `emami2026frsicl` | {FRSICL}: {LLM}-Enabled In-Context Learning Flight Resource Allocation for Fresh Data Collection in {UAV}-Assisted Wildfire Monitoring | Flight-cost and active re-observation are not evaluated. |
| `hou2024selectviews` | Learning to Select Views for Efficient Multi-View Understanding | Active view selection is not evaluated. |
| `hu2025csfprrtdetr` | {CSFPR-RTDETR}: Real-Time Small Object Detection Network for {UAV} Images Based on Cross-Spatial-Frequency Domain and Position Relation | Detector-only comparison is outside the narrowed temporal paper. |
| `johns2016activemultiview` | Pairwise Decomposition of Image Sequences for Active Multi-View Recognition | Active multi-view recognition is not evaluated. |
| `ma2020frelu` | Funnel Activation for Visual Recognition | FReLU is cited only by the detector source file excluded from main.tex. |
| `naik2024bucktales` | {BuckTales}: A Multi-{UAV} Dataset for Multi-Object Tracking and Re-Identification of Wild Antelopes | BuckTales cross-video evaluation is outside the compiled temporal scope. |
| `sadeghibakhi2025comparison` | Comparison of Small Object Detection Approaches in Unmanned Aerial Vehicle ({UAV}) Images | Detector survey/comparison does not support a compiled claim. |
| `yang2026uavdet` | {UAVDet}: A {CNN}--{Mamba} Hybrid Network for Efficient Small Object Detection in {UAV} Imagery | Detector-only comparison is outside the narrowed temporal paper. |
| `zhang2024attention4align` | {Attention4Align}: Align Multi-View Parts Via Part2Part Hierarchical Attention Maps for Fine-Grained {3D} Object Classification | Cross-view alignment is outside within-stream post-linking. |
| `zhen2026gmt` | {GMT}: Effective Global Framework for Multi-Camera Multi-Target Tracking | Global multi-camera identity assignment is not the evaluated task. |

## BibTeX preservation

- Original `main.bib`: Git `f68bb489`, SHA-256 `ece0cb4571e4f1485d1f54ce618f2d55f4b9ab9cca37a6745ae5bd29eca414a6`
- Current `main.bib`: SHA-256 `4d560d9a37967755617f04f294d6e443d0c176949f054a97ed62751df2269352`
- Physical entries: old 66, current 77
- Physical keys added since old snapshot: aharon2022botsort, bergmann2019tracktor, bewley2016sort, du2018uavdt, gao2023memotr, gao2025motip, pirsiavash2011global, sun2025gta, wang2019trackletnet, wen2019visdronemot, wojke2017deepsort
- Physical keys removed since old snapshot: none

The original bibliography is preserved in Git history. Entries excluded from the
compiled scope were not erased from the historical snapshot.
