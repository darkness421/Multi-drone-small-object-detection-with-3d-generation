# LLM Reasoner Final Adjudicator Plan

## Goal

Add `AeroGraph Reasoner`, a drone-specialized final decision layer after the
detector, 3D geometry, ambiguity scoring, and optional VLM/LLM verification.
The goal is not to call an LLM for every object, but to evaluate whether
selective multi-UAV semantic reasoning improves hard-case decisions enough to
justify latency and cost.

Naming rule: do not use the previous non-drone-specific label for this paper. `AeroGraph
Reasoner` denotes the aerial multi-UAV evidence-graph reasoner used for
ambiguity resolution, targeted re-observation, and verified object-state
decisions.

## Inputs

- object hypotheses from the 3D evidence graph
- detector class posterior and confidence
- geometry residual / cross-view consistency
- ambiguity score and reason tags
- optional LLM response for selected hard cases

## Methods To Compare

- detector only
- detector + geometry + ambiguity
- AeroGraph Reasoner-assisted final adjudicator
- AeroGraph Reasoner-assisted final adjudicator + re-observation request policy

The LLM/VLM reasoner is a system-level ablation, not a detector baseline. It
should be evaluated after detector/proposed-module checkpoints and MarineCity
multi-view evidence are available.

## Metrics

- final object classification accuracy
- ambiguity resolution rate
- re-observation rate
- LLM call rate
- latency
- cost proxy
- failure taxonomy
- delta over detector-only and detector+3D baselines

## Advantages

- semantic/contextual disambiguation
- explanation of disagreements
- better final decision on occluded or tiny objects when visual evidence is
  incomplete

## Risks

- latency and cost
- prompt sensitivity
- hallucination under poor evidence
- privacy/deployment constraints
- harder reproducibility unless prompts and responses are cached

## Implementation

Core module:

- `reasoning/final_adjudicator.py`

Evaluation:

- `evaluation/reasoner_ablation.py`

Example:

```bash
python -m reasoning.final_adjudicator \
  --hypotheses outputs/graph/hypotheses.json \
  --ambiguity outputs/ambiguity/scores.json \
  --llm outputs/reasoning/llm_responses.json \
  --out outputs/reasoning/final_decisions.json

python -m evaluation.reasoner_ablation \
  --hypotheses outputs/graph/hypotheses.json \
  --ambiguity outputs/ambiguity/scores.json \
  --llm outputs/reasoning/llm_responses.json \
  --labels outputs/reasoning/final_labels.json \
  --out outputs/experiments/llm_reasoner_ablation.csv
```
