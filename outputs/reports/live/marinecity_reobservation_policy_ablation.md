# MarineCity Re-observation Policy Ablation

Updated: `2026-06-29T22:59:56+09:00`

The ablation is computed from the viewer160 real-Cesium cross-view
evidence graph. It compares action allocation policies over the same
17 graph hypotheses and reports action load rather than external LLM
latency.

| Policy | Units | Avg. ambiguity | F/M/R/O | High-ambiguity handled | Action load |
| --- | ---: | ---: | --- | ---: | ---: |
| No active re-observation | 17 | 0.94 | 0/17/0/0 | 0.0% | 17 |
| Support only | 17 | 0.94 | 0/8/0/9 | 60.0% | 17 |
| Uncertainty only | 17 | 0.94 | 0/3/0/14 | 93.3% | 17 |
| Conflict/missing aware | 17 | 0.94 | 0/3/0/14 | 93.3% | 17 |
| Ours | 17 | 0.94 | 0/1/7/9 | 100.0% | 10 |

## Scenario evidence

- S0: hypotheses=6, avg_ambiguity=0.97, high=6, edges S/C/M=26/4/10
- S1: hypotheses=4, avg_ambiguity=0.93, high=3, edges S/C/M=22/1/6
- S2: hypotheses=7, avg_ambiguity=0.93, high=6, edges S/C/M=30/6/9
