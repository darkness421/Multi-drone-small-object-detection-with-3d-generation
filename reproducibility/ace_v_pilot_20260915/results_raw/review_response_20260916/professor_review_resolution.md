# Professor-review resolution

| Review requirement | Disposition | Evidence |
| --- | --- | --- |
| H+V minus H on identical inputs | 해결 | Sequence and summary CSVs; result is mixed/negative |
| Greedy+same verifier minus greedy | 해결 | Sequence and summary CSVs; no robust gain |
| Same-information simple controls | 해결 | Margin-only, motion-only, and soft-cost contrasts |
| Post-filter versus reassignment | 해결 | Direct contrast from committed per-sequence rows |
| Verifier disabled reproduces base linker | 해결 | Cached pair-level equivalence for both solvers |
| M3OT crop admission without GT | 부분해결 | Direct tracker-box crops are GT-free, but upstream tracker detections are oracle boxes |
| Development/test separation | 해결 | M3OT development selects tau; held-out and MMOT are explicitly exposed retests |
| Fresh independent confirmation | 미해결 | No unexposed dataset is available |
| Solver-agnostic evidence-verifier advantage | 미해결 | Frozen success rule failed; negative results retained |
| Manuscript performance claim/table | 미반영 | Evidence does not justify a new performance claim or table |

No experiment row was removed because it was unfavorable. No threshold was selected on MMOT or M3OT held-out.
