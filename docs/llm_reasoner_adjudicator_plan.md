# LLM Reasoner Final Adjudicator Plan

## Goal

Add a final decision layer after detector, 3D geometry, ambiguity scoring, and
optional VLM/LLM verification. The goal is not to call an LLM for every object,
but to evaluate whether selective semantic reasoning improves hard-case
decisions enough to justify latency and cost.

## Inputs

- object hypotheses from the 3D evidence graph
- detector class posterior and confidence
- geometry residual / cross-view consistency
- ambiguity score and reason tags
- optional LLM response for selected hard cases

## Methods To Compare

- detector only
- detector + geometry + ambiguity
- LLM-assisted final adjudicator

## Metrics

- final object classification accuracy
- ambiguity resolution rate
- re-observation rate
- LLM call rate
- latency
- cost proxy
- failure taxonomy

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
