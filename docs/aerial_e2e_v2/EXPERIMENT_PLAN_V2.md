# V2 Experiment Plan

## Gate before V2-01

V2-01 does not start until all of the following hold:

1. NVIDIA driver and CUDA visibility are restored.
2. An MMOT development/training split is locally complete and scene-disjoint.
3. The official OBB detector checkpoint or a reproducibly trained replacement
   is available.
4. B0 and B1 use the same declared dataset/input/evaluator conditions.
5. B2 completes a short real-data training run and frozen validation run.
6. OBB mAP, angle error, HOTA/DetA/AssA/IDF1/MOTA/IDSW/Frag, runtime, memory,
   parameters, and FLOPs all write to the registry.

## V2-01 execution

Run DOS-0 through DOS-4 with identical data, seed, backbone, optimizer, and
association implementation. Use a periodic orientation likelihood; reject a
naive unbounded Gaussian angle model. Report localization NLL and calibration
only when the predicted distribution is probabilistically defined.

Advance a DOS variant only if its gain is repeatable globally or on a locked
target subset without unacceptable detection/tracking regression. Do not move
to V2-02 until the V2-01 report recommends KEEP, MODIFY, or DROP from evidence.

## Subsequent order

ETFA, ECMS, OISF, MCG, CAR, FLRA, RCIF, CTEE, and finally AAC. Independent
ablations precede combinations. Future frames are forbidden in online rows;
fixed-lag rows must state their latency. The final architecture is selected
from complementary surviving modules, not from the number of proposed ideas.

## Hard subsets

Subset generation must be deterministic and saved before comparison:
tiny/small area, heavy occlusion, crossing, high ego-motion, camera rotation,
large orientation change, low confidence, reappearance, and crowding. Every
subset report includes its denominator and missing-label policy.
