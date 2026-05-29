# Live Training Reports

Last organized: `2026-05-30`

This folder is refreshed by active server experiments. Use it to watch training
progress, but do not treat it as the final paper report.

Current live bundle:

- `large_20260524_140922_server_baseline_dashboard.png`: combined live dashboard.
- `large_20260524_140922_figures/`: separated live plots for AP/AP50,
  precision/recall/F1, parameters, GFLOPs, speed, and seed spread.

After a queue finishes, promote a clean snapshot with:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```
