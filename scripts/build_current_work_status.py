"""Write the live current-work queue as Markdown/CSV."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from build_live_training_dashboard import queue_status_rows


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "outputs/reports/live"
OUT_MD = LIVE / "current_work_status.md"
OUT_CSV = LIVE / "current_work_status.csv"


def status_label(status: str) -> str:
    labels = {
        "done": "done",
        "running": "running",
        "ready": "ready",
        "waiting": "waiting",
        "monitoring": "monitoring",
    }
    return labels.get(status, status or "unknown")


def main() -> None:
    LIVE.mkdir(parents=True, exist_ok=True)
    rows = queue_status_rows()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["queue", "status", "detail", "event"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Current Work Status",
        "",
        f"Updated: `{now}`",
        "",
        "This file mirrors the active work shown in `training_dashboard.png`. Active work now focuses on the VisDrone detector claim, MarineCity simulation, neural-3D validation metrics, AeroGraph reasoner replication, and paper cleanup.",
        "",
        "| Work Item | Status | Detail | Latest Event |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('queue', '-')} | `{status_label(row.get('status', ''))}` | "
            f"{row.get('detail', '-')} | {row.get('event', '-')} |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
