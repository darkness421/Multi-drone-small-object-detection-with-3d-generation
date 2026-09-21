# Baseline Configurations

## B0: SAFR-YOLO + Deep OC-SORT

Verified detector training settings:

- task: AABB detection
- model: `yolo11l-p2p4-balanced-v1.yaml`
- patches: lightweight self-attention plus TinySpatialFReLU
- data: VisDrone2019-DET
- image size: 1280
- epochs: 100; early-stop patience in completed args: 20
- batch: 4
- seeds: 42, 123, 2026
- initialization: YOLO11l pretrained weights with custom P2/P3/P4 head
- optimizer request: `auto`; do not interpret stored `lr0`/momentum as the
  executed optimizer without the corresponding training-start log
- augmentation: HSV, translation 0.1, scale 0.5, horizontal flip 0.5, mosaic
  1.0, mosaic disabled for the final 10 epochs
- checkpoint used by local smoke assets: seed 123, SHA-256
  `57b43dc93c7d826ed379b77a1daa1bb398bca0cdf4b40c6c8df1bbaf2c7dd29e`

The tracking half is intentionally not declared complete; see
`TRACKING_PROTOCOL.md`.

## B1: official MMOT OBB detector + Deep OC-SORT

- checkpoint recorded SHA-256:
  `6d9f66ed17eb1e29a452d43f223a55efe83959f480c65e596fd288bc966f2b15`
- spectral input: zero-based `[1,2,4]` as BGR
- image size: 1280
- confidence: 0.1
- NMS IoU: 0.6
- OBB output: four corners; tracking adapter: AABB envelope
- Deep OC-SORT and BaseReID settings: `TRACKING_PROTOCOL.md`
- evaluation: MMOT official-test 50, TrackEval commit
  `12c8791b303e0a0b50f753af204249e622d0281a`

## B2: minimal shared-encoder scaffold

- config: `configs/e2e/b2_minimal_smoke.yaml`
- deterministic OBB state only
- shared convolutional encoder
- objectness, class, box, and identity heads
- no DOS, ETFA, ECMS, OISF, FLRA, CAR, AAC, CTEE, MCG, or RCIF
- smoke optimizer: one AdamW step at 0.001 on CPU
- smoke input: two real MMOT frames resized to 256
- status: infrastructure validation only
