"""Check whether neural-3D runner dependencies are available locally."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
COMMANDS = ["ns-train", "ns-process-data", "colmap", "instant-ngp"]
MODULES = ["nerfstudio", "open3d", "plyfile", "trimesh", "cv2", "numpy", "PIL"]


def module_status_current() -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for module in MODULES:
        try:
            __import__(module)
            status[module] = {"available": True, "error": ""}
        except Exception as exc:  # noqa: BLE001 - report environment import failures.
            status[module] = {"available": False, "error": f"{type(exc).__name__}: {str(exc)[:180]}"}
    return status


def command_status() -> dict[str, str | None]:
    return {command: shutil.which(command) for command in COMMANDS}


def conda_module_status(env_name: str) -> dict[str, Any]:
    code = (
        "import json, shutil\n"
        f"commands={COMMANDS!r}\n"
        f"modules={MODULES!r}\n"
        "out={'commands':{c:shutil.which(c) for c in commands},'modules':{}}\n"
        "for m in modules:\n"
        "    try:\n"
        "        __import__(m); out['modules'][m]={'available':True,'error':''}\n"
        "    except Exception as e:\n"
        "        out['modules'][m]={'available':False,'error':type(e).__name__+': '+str(e)[:180]}\n"
        "print(json.dumps(out))\n"
    )
    try:
        proc = subprocess.run(
            ["conda", "run", "--no-capture-output", "-n", env_name, "python", "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"{type(exc).__name__}: {exc}", "commands": {}, "modules": {}}
    if proc.returncode != 0:
        return {"available": False, "error": (proc.stderr or proc.stdout).strip()[-800:], "commands": {}, "modules": {}}
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"parse_error: {exc}; stdout={proc.stdout[-500:]}", "commands": {}, "modules": {}}
    payload["available"] = True
    payload["error"] = ""
    return payload


def build(args: argparse.Namespace) -> dict[str, Any]:
    current = {"commands": command_status(), "modules": module_status_current()}
    conda = conda_module_status(args.conda_env) if args.conda_env else {}
    conda_commands = conda.get("commands", {}) if conda else {}
    conda_modules = conda.get("modules", {}) if conda else {}
    neural_runner_available = bool(
        current["commands"].get("ns-train")
        or current["commands"].get("instant-ngp")
        or conda_commands.get("ns-train")
        or conda_commands.get("instant-ngp")
    )
    geometry_smoke_available = bool(
        current["modules"].get("numpy", {}).get("available")
        and current["modules"].get("PIL", {}).get("available")
    )
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": "marinecity_3d_runner_preflight_ready",
        "neural_runner_available": neural_runner_available,
        "geometry_smoke_available": geometry_smoke_available,
        "current_python": sys.executable,
        "current_env": current,
        "conda_env": args.conda_env,
        "conda_env_status": conda,
        "claiming_rule": (
            "No local neural 3D runner is considered available unless ns-train, instant-ngp, "
            "or an equivalent upstream command is found. The depth point-cloud smoke only verifies geometry handoff."
        ),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# MarineCity 3D Runner Preflight",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        f"Neural runner available: `{report['neural_runner_available']}`",
        f"Geometry smoke available: `{report['geometry_smoke_available']}`",
        "",
        "## Current Python",
        "",
        f"- Executable: `{report['current_python']}`",
        "",
        "| Command | Path |",
        "|---|---|",
    ]
    for command, found in report["current_env"]["commands"].items():
        lines.append(f"| {command} | `{found}` |")
    lines.extend(["", "| Module | Available | Error |", "|---|---|---|"])
    for module, payload in report["current_env"]["modules"].items():
        lines.append(f"| {module} | `{payload['available']}` | `{payload['error']}` |")
    if report.get("conda_env"):
        conda = report.get("conda_env_status", {})
        lines.extend(["", f"## Conda Env `{report['conda_env']}`", ""])
        if not conda.get("available"):
            lines.append(f"- Error: `{conda.get('error')}`")
        lines.extend(["", "| Command | Path |", "|---|---|"])
        for command, found in (conda.get("commands", {}) or {}).items():
            lines.append(f"| {command} | `{found}` |")
        lines.extend(["", "| Module | Available | Error |", "|---|---|---|"])
        for module, payload in (conda.get("modules", {}) or {}).items():
            lines.append(f"| {module} | `{payload['available']}` | `{payload['error']}` |")
    lines.extend(["", f"Claiming rule: {report['claiming_rule']}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conda-env", default="com3d-ace")
    parser.add_argument("--out-json", default=str(LIVE_DIR / "marinecity_3d_runner_preflight.json"))
    parser.add_argument("--out-md", default=str(LIVE_DIR / "marinecity_3d_runner_preflight.md"))
    args = parser.parse_args()
    report = build(args)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    print(json.dumps({"json": str(out_json), "markdown": str(out_md), "neural_runner_available": report["neural_runner_available"]}, indent=2))


if __name__ == "__main__":
    main()
