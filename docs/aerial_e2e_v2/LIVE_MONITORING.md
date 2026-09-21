# Live Experiment Monitoring

Start the monitor from the repository root:

```bash
bash scripts/ubuntu/start_aerial_e2e_live_monitor.sh
tmux attach -t aerial-e2e-monitor
```

The terminal view refreshes GPU health and the latest row from
`experiments/results.csv`. The same snapshot is written to
`outputs/monitor/live_status.json` for editors or external dashboards.

For a foreground run with a fixed lifetime:

```bash
python tools/aerial_e2e_live_monitor.py --interval 2 --iterations 30
```

An unavailable GPU is reported as `unavailable` with the `nvidia-smi` error.
The monitor does not replace a failed measurement with CPU data or a zero-valued
GPU result. Blank scientific metrics in an infrastructure smoke row remain
blank.
