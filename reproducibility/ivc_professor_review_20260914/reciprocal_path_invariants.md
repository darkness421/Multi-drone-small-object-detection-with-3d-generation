# Reciprocal path invariant audit

## Result

Status: **PASS** over 1,989 released
sequence/class/tracker/input instances.

- Strict-time violations: 0
- Maximum observed indegree/outdegree: 1/1
- Cyclic proposal graphs: 0
- Duplicate-frame input tracklets: 0
- Component-guard rejections: 0
- Guard/no-guard output differences: 0

## Structural conclusion

The implementation constructs one candidate/proposal graph and does not regenerate
proposals after union operations. Every accepted proposal has strict forward time,
and reciprocal predecessor/successor choice limits indegree and outdegree to one.
With duplicate-free input tracklets, each connected component is therefore a
time-ordered directed path whose frame supports cannot overlap. Under the evaluated
algorithm, the component-overlap check is structurally unable to reject an
otherwise reciprocal proposal. It remains useful as a defensive assertion and
output validator, but it is not an independently active performance module.

Raw property results: `results_raw/mmot_cached_solver_audit_v1/property_test_results.json`.
