"""Small localhost viewer for live tmux training panes and dashboard images."""

from __future__ import annotations

import argparse
import csv
import html
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]


def run_text(args: list[str]) -> str:
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=5, check=False)
    except Exception as exc:
        return str(exc)
    return (result.stdout + result.stderr).strip()


def capture_pane(target: str, lines: int = 80) -> str:
    return run_text(["tmux", "capture-pane", "-p", "-S", f"-{lines}", "-t", target])


def latest_log(log_dir: Path) -> tuple[Path | None, str]:
    logs = sorted(log_dir.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not logs:
        return None, "No logs yet."
    path = logs[0]
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
    return path, "\n".join(lines)


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def latest_training_metrics(project_dir: Path) -> str:
    rows: list[list[str]] = [
        [
            "run",
            "epoch",
            "precision",
            "recall",
            "F1",
            "mAP50",
            "mAP50-95",
        ]
    ]
    csv_paths = sorted(
        project_dir.glob("*/ultralytics/results.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in csv_paths[:12]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                result_rows = list(csv.DictReader(handle))
        except OSError:
            continue
        if not result_rows:
            continue
        last = result_rows[-1]
        precision = as_float(last.get("metrics/precision(B)"))
        recall = as_float(last.get("metrics/recall(B)"))
        f1 = None
        if precision is not None and recall is not None and precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        rows.append(
            [
                path.parents[1].name,
                last.get("epoch", ""),
                format_metric(precision),
                format_metric(recall),
                format_metric(f1),
                format_metric(as_float(last.get("metrics/mAP50(B)"))),
                format_metric(as_float(last.get("metrics/mAP50-95(B)"))),
            ]
        )
    if len(rows) == 1:
        return "No live results.csv rows yet.\nDetector accuracy is not a standard detection metric; use mAP50, mAP50-95, precision, recall, and F1."
    widths = [max(len(row[idx]) for row in rows) for idx in range(len(rows[0]))]
    rendered = []
    for row_idx, row in enumerate(rows):
        rendered.append("  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
        if row_idx == 0:
            rendered.append("  ".join("-" * width for width in widths))
    rendered.append("")
    rendered.append("accuracy: N/A for detector baselines; report mAP/precision/recall/F1 instead.")
    return "\n".join(rendered)


def format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


class LiveHandler(BaseHTTPRequestHandler):
    training_session = "server-visdrone-baselines"
    monitor_session = "server-baseline-monitor"
    log_dir = ROOT / "outputs" / "logs" / "server_baselines"
    project_dir = ROOT / "outputs" / "detectors" / "server_baselines"
    dashboard = ROOT / "outputs" / "reports" / "server_baseline_dashboard.png"
    live_dashboard = ROOT / "outputs" / "reports" / "live" / "server_baseline_dashboard.png"

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_bytes(self, payload: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/dashboard.png":
            dashboard = self.live_dashboard if self.live_dashboard.exists() else self.dashboard
            if dashboard.exists():
                self.send_bytes(dashboard.read_bytes(), "image/png")
            else:
                self.send_error(404, "dashboard not found")
            return
        if parsed.path == "/api":
            query = parse_qs(parsed.query)
            window = query.get("window", ["0"])[0]
            pane = f"{self.training_session}:{window}.0"
            log_path, log_text = latest_log(self.log_dir)
            payload = {
                "tmux": capture_pane(pane, 100),
                "sessions": run_text(["tmux", "ls"]),
                "gpu": run_text(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
                        "--format=csv",
                    ]
                ),
                "metrics": latest_training_metrics(self.project_dir),
                "log_name": str(log_path.relative_to(ROOT)) if log_path else "",
                "log": log_text,
            }
            body = "\n---FIELD---\n".join(
                f"{key}\n{value}" for key, value in payload.items()
            ).encode("utf-8", errors="replace")
            self.send_bytes(body, "text/plain; charset=utf-8")
            return
        self.send_bytes(self.page().encode("utf-8"), "text/html; charset=utf-8")

    def page(self) -> str:
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CoM3D-ACE Live Training</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #101114; color: #f2f2f2; }}
    header {{ display: flex; gap: 12px; align-items: center; padding: 12px 16px; background: #1b1d22; position: sticky; top: 0; z-index: 2; }}
    button {{ background: #2e7dd7; color: white; border: 0; padding: 8px 12px; border-radius: 6px; cursor: pointer; }}
    button.secondary {{ background: #363a43; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(420px, .85fr); gap: 12px; padding: 12px; }}
    section {{ background: #181a1f; border: 1px solid #30343d; border-radius: 8px; overflow: hidden; }}
    h2 {{ font-size: 14px; margin: 0; padding: 10px 12px; background: #20232a; }}
    pre {{ margin: 0; padding: 12px; white-space: pre-wrap; font: 13px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; max-height: 58vh; overflow: auto; }}
    img {{ display: block; width: 100%; background: #fff; }}
    .stack {{ display: grid; gap: 12px; }}
    .muted {{ color: #a9b0bd; }}
  </style>
</head>
<body>
  <header>
    <strong>CoM3D-ACE Live Training</strong>
    <button onclick="setWindow('0')">GPU0 pane</button>
    <button onclick="setWindow('1')">GPU1 pane</button>
    <button class="secondary" onclick="refresh()">Refresh now</button>
    <span class="muted" id="status">starting...</span>
  </header>
  <main>
    <section>
      <h2 id="pane-title">Training pane</h2>
      <pre id="tmux"></pre>
    </section>
    <div class="stack">
      <section>
        <h2>GPU</h2>
        <pre id="gpu"></pre>
      </section>
      <section>
        <h2>Live Metrics</h2>
        <pre id="metrics"></pre>
      </section>
      <section>
        <h2 id="log-title">Latest log</h2>
        <pre id="log"></pre>
      </section>
      <section>
        <h2>Dashboard</h2>
        <img id="dashboard" src="/dashboard.png" alt="server baseline dashboard">
      </section>
    </div>
  </main>
  <script>
    let windowId = "0";
    function setWindow(id) {{ windowId = id; refresh(); }}
    async function refresh() {{
      const res = await fetch(`/api?window=${{windowId}}&t=${{Date.now()}}`);
      const text = await res.text();
      const fields = Object.fromEntries(text.split("\\n---FIELD---\\n").map(part => {{
        const idx = part.indexOf("\\n");
        return [part.slice(0, idx), part.slice(idx + 1)];
      }}));
      document.getElementById("pane-title").textContent = `Training pane GPU${{windowId}}`;
      document.getElementById("tmux").textContent = fields.tmux || "";
      document.getElementById("gpu").textContent = fields.gpu || "";
      document.getElementById("metrics").textContent = fields.metrics || "";
      document.getElementById("log-title").textContent = fields.log_name ? `Latest log: ${{fields.log_name}}` : "Latest log";
      document.getElementById("log").textContent = fields.log || "";
      document.getElementById("dashboard").src = `/dashboard.png?t=${{Date.now()}}`;
      document.getElementById("status").textContent = `updated ${{new Date().toLocaleTimeString()}}`;
    }}
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a live training viewer.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--training-session", default="server-visdrone-baselines")
    parser.add_argument("--monitor-session", default="server-baseline-monitor")
    args = parser.parse_args()
    LiveHandler.training_session = args.training_session
    LiveHandler.monitor_session = args.monitor_session
    server = ThreadingHTTPServer((args.host, args.port), LiveHandler)
    print(f"Serving live training viewer at http://{args.host}:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
