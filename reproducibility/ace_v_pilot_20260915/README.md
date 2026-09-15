# ACE-V bounded pilot

This directory contains a separated, auditable pilot for testing whether
multi-frame evidence can improve existing temporal link solvers. It does not
modify or overwrite the published CoM3D-ACE v1 outputs.

The frozen protocol is in `protocol_freeze.yaml`. All ground-truth access is
restricted to evaluation and post-hoc audits. The current MMOT 50 sequences
and M3OT held-out split are explicitly treated as exposed exploratory sets,
not as fresh confirmation data.

Run the unit tests with:

```bash
python -m unittest discover reproducibility/ace_v_pilot_20260915/tests
```

Run the final consistency checks with:

```bash
python reproducibility/ace_v_pilot_20260915/scripts/build_inventory.py
python reproducibility/ace_v_pilot_20260915/scripts/build_results_decision.py
```

The frozen success rule was not met. Therefore no manuscript figure was
generated or replaced. This is intentional: generating only a favorable panel
would misrepresent the trajectory-level result. The source CSVs remain under
`results_raw/` for inspection and any later manual diagnostic drawing.

The concise scientific interpretation is in `experiment_report.md`; the
machine-checkable decision and primary contrasts are in
`results_raw/final/results_decision.json` and
`results_raw/final/paired_comparisons.csv`.

The manuscript reference reconciliation is recorded by title and DOI in
`results_raw/final/reference_audit.csv`; its version counts, inclusion
decisions, and claim-level citation links are summarized in
`results_raw/final/reference_audit_summary.md`.
