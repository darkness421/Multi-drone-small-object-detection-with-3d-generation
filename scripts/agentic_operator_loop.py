"""24/7 local operator loop for guarded ACCV experiment automation.

The loop is intentionally conservative. It can monitor, summarize, start the
existing orchestrator when explicitly allowed, and ask an optional OpenAI
analyst for high-level recommendations. It does not edit model code.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "outputs" / "automation"
STATUS_JSON = OUT_DIR / "agentic_operator_status.json"
STATUS_MD = OUT_DIR / "agentic_operator_status.md"
LOCAL_SUMMARY_MD = OUT_DIR / "local_operator_summary.md"
OPENAI_ANALYSIS_MD = OUT_DIR / "openai_analyst_report.md"
CODE_REQUESTS_MD = OUT_DIR / "code_change_requests.md"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # noqa: BLE001 - status loop should keep breathing.
        return {"ok": False, "returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def read_text(path: Path, limit: int = 8000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-limit:]


def tmux_sessions() -> dict[str, Any]:
    result = run(["tmux", "ls"])
    sessions: list[str] = []
    if result["ok"]:
        sessions = [line.split(":", 1)[0] for line in result["stdout"].splitlines() if line.strip()]
    return {"raw": result, "sessions": sessions}


def gpu_status() -> dict[str, Any]:
    return run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )


def collect_status() -> dict[str, Any]:
    tmux = tmux_sessions()
    sessions = set(tmux["sessions"])
    status = {
        "generated_at": now(),
        "tmux": tmux,
        "gpu": gpu_status(),
        "git_status": run(["git", "status", "--short"], timeout=30),
        "important_sessions": {
            "orchestrator": "server-24h-orchestrator" in sessions,
            "large_comparison": "server-large-comparison" in sessions,
            "top3_pending": "server-top3-proposed-pending" in sessions,
            "top3_screening": "server-top3-proposed-screening" in sessions,
            "uavdt_pending": "server-uavdt-comparisons-pending" in sessions,
            "required_related_work": "required-related-work-models-gpu0" in sessions,
            "uavdet_inspired_after_required": "uavdet-inspired-after-required-gpu0" in sessions,
            "tinyperson_640_after_2d": "tinyperson-640-after-2d-gpu0" in sessions,
            "marinecity_viewer160_pipeline": "marinecity-viewer160-pipeline" in sessions,
            "agentic_operator": "server-agentic-operator" in sessions,
        },
        "files": {
            "auto_research_agenda": "outputs/research/auto_research_agenda.md",
            "proposed_gate": "outputs/experiments/ours_vs_comparison_gate.md",
            "legacy_proposed_gate": "outputs/experiments/proposed_overwhelm_gate.md",
            "combined_summary": "outputs/experiments/server_with_proposed/server_with_proposed_summary.csv",
            "legacy_combined_summary": "outputs/experiments/server_with_proposed_summary.csv",
            "large_live_summary": "outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv",
            "marinecity_sim_dashboard": "outputs/reports/live/marinecity_simulation_dashboard.png",
            "marinecity_viewer160_status": "outputs/experiments/marinecity_viewer160_pipeline_status.md",
            "marinecity_viewer160_queue": "outputs/logs/marinecity_viewer160_pipeline/queue.log",
            "required_related_work_queue": "outputs/logs/required_related_work_models/queue.log",
            "uavdet_queue": "outputs/logs/required_related_work_models/uavdet_inspired_after_required.log",
            "tinyperson_queue": "outputs/logs/tinyperson_640/queue.log",
            "marinecity_capture_quality": "outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_top8.png",
            "marinecity_crop_candidates": "outputs/reports/live/marinecity_real_capture_crops/marinecity_real_capture_crop_top12.png",
            "marinecity_system_test_bundle": "outputs/reports/live/marinecity_system_test_10plus/manifest.json",
        },
    }
    for key, rel_path in list(status["files"].items()):
        path = REPO / rel_path
        status["files"][key] = {
            "path": rel_path,
            "exists": path.exists(),
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "",
        }
    return status


def write_status(status: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sessions = status["tmux"]["sessions"]
    gpu = status["gpu"]
    lines = [
        "# Agentic Operator Status",
        "",
        f"Generated: {status['generated_at']}",
        "",
        "## Sessions",
        "",
        *(f"- `{session}`" for session in sessions),
        "",
        "## Important Flags",
        "",
        *(f"- {key}: `{value}`" for key, value in status["important_sessions"].items()),
        "",
        "## GPU",
        "",
        "```text",
        gpu["stdout"] if gpu["stdout"] else gpu["stderr"],
        "```",
        "",
        "## Files",
        "",
        *(f"- {item['path']}: `{item['exists']}` mtime `{item['mtime']}`" for item in status["files"].values()),
    ]
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def start_orchestrator_if_allowed(status: dict[str, Any], args: argparse.Namespace) -> None:
    if not args.enable_orchestrator_start:
        return
    if status["important_sessions"]["orchestrator"]:
        return
    env = os.environ.copy()
    env.update(
        {
            "START_IN_TMUX": "1",
            "ENABLE_AUTO_RESEARCH": "1" if args.enable_auto_research else "0",
            "ENABLE_PUBLISH": "1" if args.enable_publish else "0",
            "ENABLE_NOTION": "1" if args.enable_notion else "0",
        }
    )
    export_parts = [
        f"{key}={shlex.quote(value)}"
        for key, value in env.items()
        if key
        in {
            "CONDA_ENV",
            "ENABLE_AUTO_RESEARCH",
            "ENABLE_NOTION",
            "ENABLE_PUBLISH",
            "NOTION_FOCUS",
            "NOTION_PAGE_ID",
            "NOTION_TARGET",
            "NOTION_TOKEN",
            "OPENAI_API_KEY",
            "START_IN_TMUX",
        }
    ]
    command = (
        f"cd {shlex.quote(str(REPO))} && "
        + " ".join(export_parts)
        + " START_IN_TMUX=0 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh"
    )
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", "server-24h-orchestrator", "-n", "orchestrator", command],
        cwd=REPO,
        check=False,
    )


def ollama_generate(prompt: str, model: str, host: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - localhost/operator configured endpoint.
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", "")).strip()


def openai_analyze(prompt: str, model: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "OPENAI_API_KEY is not set; analyst skipped."
    payload = json.dumps(
        {
            "model": model,
            "input": [
                {
                    "role": "developer",
                    "content": "You are the advanced analyst for an ACCV experiment automation stack. Give concise, actionable recommendations. Do not request direct code edits unless the evidence is strong.",
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - official HTTPS API endpoint.
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return f"OpenAI analyst request failed: {exc}"
    if data.get("output_text"):
        return str(data["output_text"])
    chunks: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(str(content.get("text", "")))
    return "\n".join(chunks).strip() or json.dumps(data, indent=2)[:4000]


def build_prompt(status: dict[str, Any]) -> str:
    agenda = read_text(REPO / "outputs" / "research" / "auto_research_agenda.md", 7000)
    proposed_gate = read_text(REPO / "outputs" / "experiments" / "ours_vs_comparison_gate.md", 3000)
    status_brief = json.dumps(
        {
            "generated_at": status["generated_at"],
            "important_sessions": status["important_sessions"],
            "tmux_sessions": status["tmux"]["sessions"],
            "files": status["files"],
        },
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Review this experiment automation status. Return: current risk, next queue action, "
        "whether OpenAI-level analysis is needed, and any code-change request for Codex/OpenCode.\n\n"
        f"STATUS:\n{status_brief}\n\nAUTO_RESEARCH_AGENDA:\n{agenda}\n\nPROPOSED_GATE:\n{proposed_gate}"
    )


def write_code_request(analysis: str) -> None:
    CODE_REQUESTS_MD.write_text(
        "\n".join(
            [
                "# Code Change Requests",
                "",
                "These requests are generated for Codex/OpenCode review. They are not applied automatically.",
                "",
                "## Latest Analyst Notes",
                "",
                analysis.strip() or "No analyst notes.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_once(args: argparse.Namespace) -> None:
    status = collect_status()
    write_status(status)
    start_orchestrator_if_allowed(status, args)
    prompt = build_prompt(status)

    if args.enable_ollama and args.ollama_model:
        try:
            local_summary = ollama_generate(prompt, args.ollama_model, args.ollama_host)
        except Exception as exc:  # noqa: BLE001 - optional local summary.
            local_summary = f"Ollama summary failed: {type(exc).__name__}: {exc}"
        LOCAL_SUMMARY_MD.write_text(local_summary + "\n", encoding="utf-8")

    if args.enable_openai:
        analysis = openai_analyze(prompt, args.openai_model)
        OPENAI_ANALYSIS_MD.write_text(analysis + "\n", encoding="utf-8")
        write_code_request(analysis)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=int(os.environ.get("OPERATOR_INTERVAL", "900")))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--enable-orchestrator-start", action="store_true")
    parser.add_argument("--enable-auto-research", action="store_true")
    parser.add_argument("--enable-publish", action="store_true")
    parser.add_argument("--enable-notion", action="store_true")
    parser.add_argument("--enable-ollama", action="store_true", default=os.environ.get("ENABLE_OLLAMA_OPERATOR", "0") == "1")
    parser.add_argument("--ollama-model", default=os.environ.get("OLLAMA_MODEL", ""))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--enable-openai", action="store_true", default=os.environ.get("ENABLE_OPENAI_ANALYST", "0") == "1")
    parser.add_argument("--openai-model", default=os.environ.get("OPENAI_ANALYST_MODEL", "gpt-5.2"))
    args = parser.parse_args()

    while True:
        run_once(args)
        if args.once:
            break
        time.sleep(max(args.interval, 60))


if __name__ == "__main__":
    main()
