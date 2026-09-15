# ACE-V experiment report

## Scope

This pilot asks whether a frozen, GT-free margin-and-motion verifier improves
two strong temporal solvers on the same atomic tracker tracklets. Candidate
gates, solver costs, verifier grid, development selection, effect floor, and
bootstrap unit were frozen before inspecting the exploratory test results.
Ground truth is used only for metrics and post-hoc edge labels.

## Confirmed current strength

The confirmed CoM3D-ACE result remains detector-preserving temporal identity
refinement: the historical v1 improves over unchanged MMOT tracker outputs and
the validated AFLink adapter while preserving every box, class, score, and
frame. The smoke audit exactly reproduced 420 of 420 stored aggregate values
and all output-invariance tests passed.

## ACE-V result

| Dataset and input | H+V minus H IDF1 | G+V minus G IDF1 | Decision |
|---|---:|---:|---|
| M3OT development | +0.067 pp | +0.152 pp | Below the frozen +0.30 pp floor |
| M3OT exposed held-out | +0.995 pp | +0.000 pp | No second-solver replication |
| MMOT oracle AABB | -0.210 pp | -0.160 pp | Both primary contrasts worsen |
| MMOT official detector | -0.066 pp | -0.020 pp | Both primary contrasts worsen |

ACE-V therefore does not establish an additional solver-agnostic contribution.
The same-information soft-cost control is also mixed or negative, so the pilot
does not support reframing the contribution as a new evidence cost.

## Observable help and failure conditions

Motion disagreement is lower for post-hoc correct edges than for false edges,
showing that it is a useful diagnostic signal. Hard verification nevertheless
removes identity-continuity links along with false links. Conditional link
error often falls while accepted-link coverage falls further, and final IDF1
does not improve robustly. On M3OT held-out, only 3 of 8 auditable correct
fragment opportunities enter the fixed candidate graph; 5 fail the 55-pixel
geometry gate before assignment or verification.

## Data status

M3OT development is the only configuration-selection split. M3OT held-out and
all 50 MMOT test sequences had already been inspected in earlier work and are
reported only as exposed exploratory retests. No independent fresh
confirmation set was available. New seeds or bootstrap draws were not counted
as new data.

## Critical-issue disposition

- **Resolved:** baseline equivalence, dummy/null assignment semantics, direct
  tracker-box M3OT crops without GT admission, output invariants, paired
  sequence bootstrap, and GT label-quality accounting.
- **Scope adjusted:** the verified manuscript contribution remains the v1
  engineering/refinement result and its controlled diagnostics.
- **Unresolved:** a verifier that consistently adds value above both H and G,
  independent fresh confirmation, and recovery of M3OT candidates outside the
  fixed pixel gate.

## Manuscript and figure action

Do not add ACE-V performance claims or replace a manuscript figure. Existing
verified figures remain unchanged. The complete negative outputs are retained
for reproducibility and future method design.

## Not executed

- Candidate-gate variants were not promoted after the frozen verifier failed;
  they would confound verifier and candidate-recall effects.
- No fresh confirmation evaluation was run because no independent, unexposed
  dataset was available.
- No detector or tracker was retrained.
- No GPU end-to-end timing claim was produced because CUDA was unavailable in
  the execution environment; CPU timings are not presented as GPU timings.
