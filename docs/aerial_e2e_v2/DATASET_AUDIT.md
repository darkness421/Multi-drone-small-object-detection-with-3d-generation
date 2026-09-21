# Dataset Audit

## VisDrone2019-DET

- Local raw images: train 6,471; validation 548; test-dev 1,610.
- Local format: RGB image plus AABB annotations.
- Completed detector protocol: validation, image size 1280, seeds 42/123/2026.
- Identity and temporal labels are absent, so this dataset alone cannot measure
  HOTA, AssA, IDF1, IDSW, Frag, or reappearance behavior.
- OBB mAP and orientation error are not defined for the current labels.

## MMOT

- Official release description: 125 multispectral UAV sequences, eight bands,
  eight classes, frame-wise quadrilateral OBB and identity labels.
- Locally verified frame shape: `900 x 1200 x 8`, `uint8`.
- Local evaluated test split: 50 sequences, divided into the historical 12 and
  an additional 38; 5,466 frames in the official-detector run.
- The frozen detector input uses zero-based bands `[1,2,4]` as BGR, equivalent
  to spectral bands 5/3/2 after the official convention.
- Only test sequences are locally complete for this audit. They may be used for
  reproduction and infrastructure smoke, but not to select B2/V2 settings.

## M3OT

- RGB and IR streams, OBB/identity annotations, and frozen tracker/descriptor
  caches are available for prior temporal diagnostics.
- Existing development scene 08 and held-out/confirmation material have already
  been analyzed in the REGR line. They are not automatically an untouched
  confirmation set for this new method.
- The current B2 smoke does not use M3OT.

## Other local data

- UAVDT conversion artifacts exist for detector work, but the complete
  identity-tracking protocol required by this study is not locked here.
- TinyPerson is detector-only supplementary material and does not provide the
  required aerial identity-tracking protocol.
- MarineCity committed directories are schemas/placeholders; simulation outputs
  must not be presented as a public real-UAV benchmark.

## Split policy for the new study

1. Do not tune on the MMOT official test 50.
2. Acquire or reconstruct the official MMOT training split before B2/V2
   scientific training.
3. Freeze development settings before any independent confirmation evaluation.
4. Keep scene groups together across splits; do not split camera streams from
   the same scene into different roles.
5. Record whether each metric uses detector predictions, oracle boxes, or an
   adapter such as OBB-to-AABB envelope.
