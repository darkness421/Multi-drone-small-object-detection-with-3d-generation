# ACE-V results decision

## Verdict

**NO-GO for manuscript performance claims and figure replacement.**

The frozen ACE-V verifier lowers conditional link error in several conditions, but the accompanying coverage loss reduces final trajectory IDF1. It therefore fails the predeclared rule that both H+V and G+V improve their standalone solvers by at least 0.30 percentage points without coverage collapse.

No existing manuscript figure was replaced. No favorable-only result panel was generated. The CSV outputs retain all positive, tied, and negative conditions for manual inspection.

## Protocol checks

- Frozen configuration selected on M3OT val before held-out loading: `tau_a=0.10`, `tau_m=4.0`.
- Existing baseline reproduction: PASS (420/420 aggregate values exact).
- MMOT 50 and M3OT held-out were already exposed and are reported as exploratory retests, not fresh confirmation.
- All evaluated refiners preserved the frame/box/score/class multiset and produced no duplicate same-frame identities.

## Primary contrasts

| Dataset/input | H+V - H IDF1 | G+V - G IDF1 | Interpretation |
|---|---:|---:|---|
| M3OT development | +0.067 pp | +0.152 pp | 1/2/1 improved/tied/worsened for H+V |
| M3OT exposed held-out | +0.995 pp | +0.000 pp | 1/3/0 improved/tied/worsened for H+V |
| MMOT oracle AABB | -0.210 pp | -0.160 pp | 9/4/37 improved/tied/worsened for H+V |
| MMOT official detector | -0.066 pp | -0.020 pp | 13/13/24 improved/tied/worsened for H+V |

## What the experiment establishes

1. **The current verified strength remains detector-preserving temporal refinement.** On official-detector MMOT, ACE-v1 improves IDF1 over unchanged ByteTrack, OC-SORT, and Deep OC-SORT outputs, but stronger standalone linkers remain more accurate in the all-50 mean.
2. **Motion is diagnostically informative but insufficient as a verifier.** Correct candidate edges have lower median motion disagreement than false edges, yet the fixed hard verifier does not convert that separation into robust trajectory gains.
3. **The failure is mainly a precision-coverage trade-off.** H+V generally lowers conditional edge error while discarding links needed for identity continuity; this is not acceptable as a claimed improvement.
4. **M3OT remains candidate-limited.** The direct-crop held-out audit retains only 3/8 correct fragment opportunities; 5 are rejected by the fixed 55-pixel geometry gate before any solver or verifier acts.
5. **The simple information control also does not explain a hidden gain.** It is mixed or negative across the main MMOT conditions, so neither a verifier claim nor a new soft-cost claim is supported.

## Manuscript and figure action

Do not add ACE-V as a validated method, do not replace the current result figure, and do not claim solver-agnostic improvement. If the experiment is discussed internally, describe it as a bounded negative pilot showing that hard evidence filtering reduces link errors but sacrifices trajectory coverage. Existing verified Figures 1, 3, and 4 remain untouched.

## Fresh confirmation

No fresh independent confirmation set was available. New seeds, filenames, or bootstrap draws were not treated as independent data.
