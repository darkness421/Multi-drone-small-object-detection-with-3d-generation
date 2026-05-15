"""Stage VisDrone DET downloads into the repository raw-data layout.

The script is conservative by default: without --apply it only reports what it
would do. With --apply it can extract official zip files or copy already
extracted split folders into data/raw/VisDrone2019-DET.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SPLIT_DIRS = [
    "VisDrone2019-DET-train",
    "VisDrone2019-DET-val",
    "VisDrone2019-DET-test-dev",
]


@dataclass(slots=True)
class StageAction:
    split: str
    source: str
    target: str
    action: str
    applied: bool


def _candidate_dirs(source: Path, split: str) -> list[Path]:
    if not source.exists():
        return []
    candidates = []
    for path in source.rglob(split):
        if path.is_dir():
            candidates.append(path)
    return sorted(candidates, key=lambda path: len(path.parts))


def _candidate_zips(source: Path, split: str) -> list[Path]:
    if not source.exists():
        return []
    return sorted(path for path in source.rglob("*.zip") if split.lower() in path.name.lower())


def _copy_split(source_dir: Path, target_dir: Path) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)


def _extract_zip(zip_path: Path, raw_root: Path) -> None:
    raw_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(raw_root)


def _split_file_count(split_dir: Path) -> int:
    if not split_dir.exists():
        return 0
    return sum(1 for path in split_dir.rglob("*") if path.is_file())


def stage_visdrone(source: str | Path, raw_root: str | Path, *, apply: bool = False) -> list[StageAction]:
    source = Path(source).resolve()
    raw_root = Path(raw_root).resolve()
    actions: list[StageAction] = []

    for split in SPLIT_DIRS:
        target_dir = raw_root / split
        existing_ready = (target_dir / "images").exists() and (target_dir / "annotations").exists() and _split_file_count(target_dir) > 0
        if existing_ready:
            actions.append(StageAction(split, str(target_dir), str(target_dir), "already-ready", False))
            continue

        dirs = _candidate_dirs(source, split)
        zips = _candidate_zips(source, split)
        if dirs:
            chosen = dirs[0]
            if apply:
                _copy_split(chosen, target_dir)
            actions.append(StageAction(split, str(chosen), str(target_dir), "copy-dir", apply))
            continue
        if zips:
            chosen = zips[0]
            if apply:
                _extract_zip(chosen, raw_root)
            actions.append(StageAction(split, str(chosen), str(raw_root), "extract-zip", apply))
            continue
        actions.append(StageAction(split, str(source), str(target_dir), "missing-source", False))

    return actions


def print_actions(actions: list[StageAction]) -> None:
    print("VisDrone staging plan")
    print("-" * 80)
    for action in actions:
        marker = "APPLIED" if action.applied else "DRY-RUN"
        print(f"{marker:8s} {action.split:26s} {action.action}")
        print(f"  source: {action.source}")
        print(f"  target: {action.target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage VisDrone DET downloads into data/raw/VisDrone2019-DET.")
    parser.add_argument("--source", default=str(Path.home() / "Downloads"))
    parser.add_argument("--raw-root", default="data/raw/VisDrone2019-DET")
    parser.add_argument("--apply", action="store_true", help="Actually copy/extract files. Omit for dry-run.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    actions = stage_visdrone(args.source, args.raw_root, apply=args.apply)
    if args.json:
        print(json.dumps([asdict(action) for action in actions], indent=2))
    else:
        print_actions(actions)
        if not args.apply:
            print()
            print("Dry-run only. Add --apply to copy/extract matching downloads.")


if __name__ == "__main__":
    main()
