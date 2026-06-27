"""Audit external execution capabilities for the remaining ACCV gates.

This check deliberately reports only whether secrets and provider commands are
configured. It never prints API keys or provider command strings.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"

ENV_VARS = [
    "OPENAI_API_KEY",
    "AEROGRAPH_COMMAND",
    "AEROGRAPH_ENV_FILE",
    "OLLAMA_HOST",
    "AEROGRAPH_OPENAI_MODEL",
]

COMMANDS = [
    "ollama",
    "openai",
    "ns-train",
    "ns-process-data",
    "colmap",
    "instant-ngp",
]


def rel(path: Path | str) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def env_status() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name in ENV_VARS:
        value = os.environ.get(name, "")
        rows[name] = {
            "set": bool(value.strip()),
            "value_redacted": bool(value.strip()),
        }
        if name == "AEROGRAPH_ENV_FILE" and value.strip():
            path = Path(value).expanduser()
            rows[name]["readable"] = path.is_file() and os.access(path, os.R_OK)
            rows[name]["path_hint"] = path.name
    return rows


def command_status() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for command in COMMANDS:
        found = shutil.which(command)
        rows[command] = {"available": bool(found), "path": found or ""}
    return rows


def aerograph_runnable(env: dict[str, dict[str, Any]], commands: dict[str, dict[str, Any]]) -> dict[str, Any]:
    env_file_ready = bool(env["AEROGRAPH_ENV_FILE"].get("readable"))
    openai_ready = bool(env["OPENAI_API_KEY"]["set"] or env_file_ready)
    command_ready = bool(env["AEROGRAPH_COMMAND"]["set"] or env_file_ready)
    provider_candidates = {
        "ollama": bool(commands["ollama"]["available"] or env["OLLAMA_HOST"]["set"]),
        "openai_cli": bool(commands["openai"]["available"]),
    }
    cli_ready = bool(commands["openai"]["available"] and env["OPENAI_API_KEY"]["set"])
    provider_modes: list[str] = []
    if openai_ready or cli_ready:
        provider_modes.append("openai")
    if command_ready:
        provider_modes.append("command_or_local")
    return {
        "ready": bool(provider_modes),
        "openai_ready": openai_ready or cli_ready,
        "command_or_local_ready": command_ready,
        "env_file_ready": env_file_ready,
        "provider_candidates": provider_candidates,
        "candidate_available_without_runnable_command": bool(any(provider_candidates.values()) and not command_ready),
        "provider_modes": provider_modes,
    }


def neural_3d_runnable(
    commands: dict[str, dict[str, Any]],
    preflight: dict[str, Any],
    completion: dict[str, Any],
) -> dict[str, Any]:
    command_ready = bool(commands["ns-train"]["available"] or commands["instant-ngp"]["available"])
    preflight_ready = bool(preflight.get("neural_runner_available"))
    dataset_ready = bool(completion.get("neural3d_dataset_ready"))
    source_ready = bool(completion.get("source_capture_ready"))
    metric_rows = int(completion.get("metric_result_row_count", 0) or 0)
    return {
        "ready": bool(command_ready or preflight_ready or metric_rows),
        "command_ready": command_ready,
        "preflight_ready": preflight_ready,
        "metric_row_ready": bool(metric_rows),
        "dataset_ready": dataset_ready,
        "source_capture_ready": source_ready,
        "metric_result_row_count": metric_rows,
        "completion_status": completion.get("status", "missing"),
    }


def status_label(aerograph: dict[str, Any], threed: dict[str, Any]) -> str:
    if aerograph["ready"] and threed["ready"]:
        return "external_gates_ready_to_execute"
    if aerograph["ready"] and not threed["ready"]:
        return "aerograph_provider_configured_3d_runner_missing"
    if threed["ready"] and not aerograph["ready"]:
        return "three_d_runner_available_aerograph_provider_missing"
    return "external_gates_missing_provider_and_3d_runner"


def next_commands(aerograph: dict[str, Any], threed: dict[str, Any]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    if aerograph["openai_ready"]:
        commands.append(
            {
                "gate": "AeroGraph compact smoke",
                "command": "AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh",
            }
        )
        commands.append(
            {
                "gate": "AeroGraph final 49-prompt run",
                "command": "AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_nonmock_queue.sh",
            }
        )
    elif aerograph["command_or_local_ready"]:
        command_prefix = (
            "AEROGRAPH_PROVIDER=command"
            if not aerograph.get("env_file_ready")
            else "AEROGRAPH_PROVIDER=command AEROGRAPH_ENV_FILE=/path/to/aerograph.env"
        )
        commands.append(
            {
                "gate": "AeroGraph compact smoke",
                "command": f"{command_prefix} bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh",
            }
        )
        commands.append(
            {
                "gate": "AeroGraph final 49-prompt run",
                "command": f"{command_prefix} bash scripts/ubuntu/start_aerograph_nonmock_queue.sh",
            }
        )
    else:
        commands.append(
            {
                "gate": "AeroGraph manual web fallback",
                "command": (
                    "python scripts/import_aerograph_external_responses.py "
                    "--mode final49 "
                    "--input reasoning/aerograph_web_raw_batches/*.md "
                    "--provider-label \"External web LLM\""
                ),
            }
        )
        commands.append(
            {
                "gate": "AeroGraph compact manual fallback",
                "command": (
                    "python scripts/import_aerograph_external_responses.py "
                    "--mode compact23 "
                    "--input reasoning/aerograph_real_capture_web_raw_batches/*.md "
                    "--provider-label \"External web LLM compact\""
                ),
            }
        )

    if threed["ready"]:
        commands.append(
            {
                "gate": "Neural 3D runner preflight",
                "command": "python scripts/check_marinecity_3d_runner_preflight.py",
            }
        )
        commands.append(
            {
                "gate": "Neural 3D metric import after runner finishes",
                "command": (
                    "python scripts/import_marinecity_3d_metrics.py "
                    "PATH_TO_RUNNER_METRICS.json --overwrite"
                ),
            }
        )
    else:
        commands.append(
            {
                "gate": "Neural 3D fallback/import path",
                "command": (
                    "Install/connect Nerfstudio, Instant-NGP, or 3DGS, then run "
                    "python scripts/import_marinecity_3d_metrics.py PATH_TO_RUNNER_METRICS.json --overwrite"
                ),
            }
        )
    return commands


def build_report() -> dict[str, Any]:
    env = env_status()
    commands = command_status()
    preflight = read_json(LIVE_DIR / "marinecity_3d_runner_preflight.json")
    completion = read_json(LIVE_DIR / "marinecity_3d_completion_readiness.json")
    aerograph_final = read_json(LIVE_DIR / "aerograph_nonmock_readiness_status.json")
    aerograph_smoke = read_json(LIVE_DIR / "aerograph_real_capture_nonmock_smoke_status.json")
    aerograph = aerograph_runnable(env, commands)
    threed = neural_3d_runnable(commands, preflight, completion)
    status = status_label(aerograph, threed)
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "env": env,
        "commands": commands,
        "aerograph_execution": aerograph,
        "neural_3d_execution": threed,
        "current_gate_reports": {
            "aerograph_final_status": aerograph_final.get("status", "missing"),
            "aerograph_final_external_ready": bool(aerograph_final.get("external_provider_replication_ready")),
            "aerograph_final_valid_direct_responses": (
                (aerograph_final.get("manual_response_coverage", {}) or {}).get("matched_valid_response_count")
            ),
            "aerograph_final_prompt_count": (
                (aerograph_final.get("manual_response_coverage", {}) or {}).get("prompt_count")
            ),
            "aerograph_compact_smoke_status": aerograph_smoke.get("status", "missing"),
            "marinecity_3d_completion_status": completion.get("status", "missing"),
            "marinecity_3d_runner_available": bool(preflight.get("neural_runner_available")),
            "marinecity_3d_metric_rows": int(completion.get("metric_result_row_count", 0) or 0),
        },
        "next_commands": next_commands(aerograph, threed),
        "claiming_rule": (
            "This report only indicates whether external execution is configured. "
            "It does not promote AeroGraph or neural-3D results unless the corresponding "
            "readiness reports contain complete, non-placeholder outputs."
        ),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# External Gate Capabilities",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "This report checks whether the remaining external gates can be executed from the current shell. Secret values are never printed.",
        "",
        "## Summary",
        "",
        f"- AeroGraph provider configured: `{report['aerograph_execution']['ready']}`; modes `{report['aerograph_execution']['provider_modes']}`",
        f"- Provider candidates without runnable command: `{report['aerograph_execution']['candidate_available_without_runnable_command']}`; candidates `{report['aerograph_execution']['provider_candidates']}`",
        f"- Neural 3D runner configured: `{report['neural_3d_execution']['ready']}`",
        f"- Neural 3D source capture ready: `{report['neural_3d_execution']['source_capture_ready']}`",
        f"- Neural 3D dataset ready: `{report['neural_3d_execution']['dataset_ready']}`",
        f"- Neural 3D metric rows: `{report['neural_3d_execution']['metric_result_row_count']}`",
        "",
        "## Current Gate Reports",
        "",
        "| Gate | Value |",
        "|---|---|",
    ]
    for key, value in report["current_gate_reports"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Environment Flags", "", "| Variable | Set | Readable |", "|---|---|---|"])
    for name, payload in report["env"].items():
        readable = payload.get("readable", "")
        lines.append(f"| `{name}` | `{payload['set']}` | `{readable}` |")

    lines.extend(["", "## Commands", "", "| Command | Available | Path |", "|---|---|---|"])
    for command, payload in report["commands"].items():
        lines.append(f"| `{command}` | `{payload['available']}` | `{payload['path']}` |")

    lines.extend(["", "## Next Commands", ""])
    for row in report["next_commands"]:
        lines.extend([f"### {row['gate']}", "", "```bash", row["command"], "```", ""])

    lines.extend(["## Claiming Rule", "", report["claiming_rule"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", default=str(LIVE_DIR / "external_gate_capabilities.json"))
    parser.add_argument("--out-md", default=str(LIVE_DIR / "external_gate_capabilities.md"))
    args = parser.parse_args()
    report = build_report()
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    print(json.dumps({"json": rel(out_json), "markdown": rel(out_md), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
