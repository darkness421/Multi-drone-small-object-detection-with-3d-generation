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

The professor-review status pack in `results_raw/review_response_20260916/`
links each requested strong-linker contrast to the committed sequence rows. It
also records component controls, post-filter versus reassignment, cached
`V_off` equivalence, the exact scope of the M3OT direct-crop control, and the
absence of historical scheduler/stdout logs. The Appendix table source is
generated directly from the aggregate contrast CSV as
`paper_table_ace_v_strong_linker.tex`. Generate the pack without rerunning an
experiment with:

```bash
python reproducibility/ace_v_pilot_20260915/scripts/build_review_response.py
```

The Table D.16 forensic pack in
`results_raw/d16_forensic_audit_20260916/` expands the compact table into
absolute tracker-level and sequence-level IDF1, AssA, and IDSW results. It also
audits verifier edge transitions, M3OT descriptor admission, `V_off`
equivalence, and the final ID partitions produced by the distinct greedy
controls. Generate it from the immutable caches without rerunning an experiment
with:

```bash
python reproducibility/ace_v_pilot_20260915/scripts/build_d16_forensic_audit.py
```

The audit establishes that D.16's controlled-cost path-constrained greedy
control (`P-G`) is not Table 4's cosine-ranked component-merging
`Geo.+ReID-G`; the names must remain distinct.

The manuscript reference reconciliation is recorded by title and DOI in
`results_raw/final/reference_audit.csv`; its version counts, inclusion
decisions, and claim-level citation links are summarized in
`results_raw/final/reference_audit_summary.md`.
