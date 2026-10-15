# DOVE-WM and CoM3D-ACE Research Boundary

Date: 2026-10-15

The two projects may share the MarineCity simulator, detector wrappers, capture
utilities, and evaluation infrastructure. Shared infrastructure is not a shared
method contribution.

## DOVE-WM

- Predicts detector-facing future outcomes for candidate camera actions.
- Uses geometry transport plus learned residual outcome prediction.
- Ranks candidate viewpoints under pixel, motion, or capture budgets.
- Primary evidence: counterfactual prediction quality, calibration, ranking,
  and closed-loop perception utility.

## CoM3D-ACE

- Diagnoses ambiguity in current multi-view evidence.
- Builds and reasons over current 3D evidence and requests re-observation.
- Primary evidence: present-view fusion, ambiguity diagnosis, evidence
  completion, and re-observation routing.

## Prohibited Overlap

- Do not describe CoM3D-ACE's current-evidence routing as the DOVE-WM future
  outcome model.
- Do not claim DOVE-WM results from CoM3D-ACE captures without training and
  evaluating the stated predictor.
- Do not submit substantially overlapping method text, figures, or empirical
  claims to concurrent venues.
- Record shared code and data-generation infrastructure explicitly in both
  reproducibility statements.
