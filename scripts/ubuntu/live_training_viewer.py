"""Small localhost viewer for live tmux training panes and dashboard images."""

from __future__ import annotations

import argparse
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.live_metrics_report import build_html_report, build_text_report


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


def latest_training_metrics(project_dir: Path) -> str:
    return build_text_report(project_dir=project_dir)


def latest_training_metrics_html(project_dir: Path) -> str:
    return build_html_report(project_dir=project_dir)


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
                "metrics_html": latest_training_metrics_html(self.project_dir),
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
    .metric-panel {{ padding: 10px 12px 14px; overflow: auto; max-height: 56vh; }}
    .metric-panel h3 {{ margin: 12px 0 8px; font-size: 14px; color: #eef2f7; }}
    .note {{ margin: 2px 0 10px; color: #c6d0df; font-size: 13px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #30343d; padding: 6px 8px; text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    th {{ position: sticky; top: 0; background: #252933; color: #e9eef7; z-index: 1; }}
    tbody tr:nth-child(even) {{ background: #1d2027; }}
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
        <div class="metric-panel" id="metrics-html"></div>
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
      document.getElementById("metrics-html").innerHTML = fields.metrics_html || "";
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
