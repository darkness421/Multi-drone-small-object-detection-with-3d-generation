#!/usr/bin/env python3
"""Audit the narrowed manuscript bibliography and record citation decisions."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAPER = Path(
    "/home/oem/projects/deepfake/Ourmethod/_checkpoint/meme_comparison/"
    "workspace/com3d_ace_ivc_overleaf_sync"
)

CURRENT_BEFORE_AUDIT = {
    "bodla2017softnms", "boxmot2023software", "braso2020neuralsolver",
    "cao2023ocsort", "du2019visdrone", "du2021giaotracker",
    "du2023strongsort", "geifman2019selectivenet", "guo2017calibration",
    "he2020cityscale", "hu2022where2comm", "hu2024universalyolo",
    "jiang2024mffsodnet", "li2025mmot", "liu2023mdmt",
    "luiten2021hota", "ma2020frelu", "maggiolino2023deepocsort",
    "naik2024bucktales", "nie2025m3ot", "ovadia2019uncertainty",
    "ristani2016performance", "tang2019cityflow", "tian2025ucdnet",
    "wu2025tsmmt", "zhang2022bytetrack",
}

ADDED = {
    "bewley2016sort": (
        "Related Work: aerial tracking",
        "SORT establishes the Kalman-prediction and linear-assignment baseline.",
        "https://ieeexplore.ieee.org/document/7533003/",
    ),
    "wojke2017deepsort": (
        "Related Work: aerial tracking",
        "Deep SORT adds a learned appearance association metric.",
        "https://arxiv.org/abs/1703.07402",
    ),
    "aharon2022botsort": (
        "Related Work: aerial tracking",
        "BoT-SORT combines motion, appearance, and camera-motion compensation.",
        "https://arxiv.org/abs/2206.14651",
    ),
    "sun2025gta": (
        "Related Work: post-tracking linking",
        "GTA is a plug-and-play global tracklet association method.",
        "https://link.springer.com/chapter/10.1007/978-981-96-2644-1_6",
    ),
}

PRIOR_ONLY = {
    "bai2025sffefyolo", "cai2025neusis", "chao2025bpdyolo",
    "ding2024adatrack", "emami2026frsicl", "hou2024selectviews",
    "hu2025csfprrtdetr", "johns2016activemultiview",
    "sadeghibakhi2025comparison", "yang2026uavdet",
    "zhang2024attention4align", "zhen2026gmt",
}

CATEGORY = {
    "bodla2017softnms": ("Detector frontend", "Soft-NMS context."),
    "ma2020frelu": ("Detector frontend", "Funnel activation context."),
    "hu2024universalyolo": ("Related Work: small objects", "Aerial small-object detection."),
    "jiang2024mffsodnet": ("Related Work: small objects", "Aerial small-object detection."),
    "hu2022where2comm": ("Related Work: cooperation", "Selective feature communication."),
    "tian2025ucdnet": ("Related Work: cooperation", "Cross-UAV feature mapping."),
    "du2019visdrone": ("Introduction and protocol", "Source of the VisDrone example and dataset."),
    "liu2023mdmt": ("Related Work: aerial tracking", "Multi-drone tracking benchmark context."),
    "wu2025tsmmt": ("Related Work: aerial tracking", "Temporal-spatial multi-drone tracking."),
    "li2025mmot": ("Protocol", "MMOT benchmark source."),
    "nie2025m3ot": ("Protocol", "M3OT benchmark source."),
    "naik2024bucktales": ("Protocol", "BuckTales benchmark source."),
    "zhang2022bytetrack": ("Method and protocol", "ByteTrack upstream tracker."),
    "cao2023ocsort": ("Method and protocol", "OC-SORT upstream tracker."),
    "maggiolino2023deepocsort": ("Method and protocol", "Deep OC-SORT upstream tracker."),
    "boxmot2023software": ("Implementation", "Frozen BoxMOT implementation provenance."),
    "du2023strongsort": ("Related Work and protocol", "StrongSORT and AFLink baseline."),
    "du2021giaotracker": ("Related Work: post-tracking linking", "Aerial global linking."),
    "braso2020neuralsolver": ("Related Work: graph MOT", "Graph-based learned association."),
    "tang2019cityflow": ("Related Work: graph MOT", "City-scale multi-camera association."),
    "he2020cityscale": ("Related Work: graph MOT", "Cross-camera tracklet matching."),
    "luiten2021hota": ("Evaluation", "HOTA metric definition."),
    "ristani2016performance": ("Evaluation", "IDF1 metric definition."),
    "geifman2019selectivenet": ("Related Work: selective association", "Reject-option motivation."),
    "guo2017calibration": ("Related Work: uncertainty", "Calibration limitation."),
    "ovadia2019uncertainty": ("Related Work: uncertainty", "Uncertainty under shift."),
}


def entry_blocks(text: str) -> dict[str, str]:
    """Return BibTeX entries keyed by citation key using balanced braces."""
    output: dict[str, str] = {}
    for match in re.finditer(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,", text):
        depth = 1
        cursor = match.end()
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        output[match.group(1)] = text[match.start():cursor]
    return output


def field(entry: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*=\s*", entry, flags=re.IGNORECASE)
    if not match:
        return ""
    cursor = match.end()
    if cursor >= len(entry):
        return ""
    if entry[cursor] == "{":
        depth, start, cursor = 1, cursor + 1, cursor + 1
        while cursor < len(entry) and depth:
            if entry[cursor] == "{":
                depth += 1
            elif entry[cursor] == "}":
                depth -= 1
            cursor += 1
        value = entry[start:cursor - 1]
    elif entry[cursor] == '"':
        start, cursor = cursor + 1, cursor + 1
        while cursor < len(entry) and entry[cursor] != '"':
            cursor += 1
        value = entry[start:cursor]
    else:
        value = entry[cursor:].split(",", 1)[0]
    return " ".join(value.replace("\n", " ").split())


def cited_keys(root: Path) -> set[str]:
    keys: set[str] = set()
    for path in root.rglob("*.tex"):
        for match in re.finditer(r"\\cite(?:t|p)?\{([^}]+)\}", path.read_text(errors="ignore")):
            keys.update(item.strip() for item in match.group(1).split(","))
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-root", type=Path, default=DEFAULT_PAPER)
    parser.add_argument(
        "--output", type=Path,
        default=ACE_ROOT / "results_raw/final/reference_audit.csv",
    )
    args = parser.parse_args()

    entries = entry_blocks((args.paper_root / "main.bib").read_text(encoding="utf-8"))
    current = cited_keys(args.paper_root)
    expected = CURRENT_BEFORE_AUDIT | set(ADDED)
    if current != expected:
        missing = sorted(expected - current)
        unexpected = sorted(current - expected)
        raise RuntimeError(f"citation set mismatch: missing={missing}, unexpected={unexpected}")

    rows = []
    for key in sorted(expected | PRIOR_ONLY):
        entry = entries.get(key, "")
        if key in ADDED:
            section, claim, source = ADDED[key]
            version, decision = "20260915_scope_audit", "add"
        elif key in CURRENT_BEFORE_AUDIT:
            section, claim = CATEGORY[key]
            source = "current LaTeX citation and main.bib metadata"
            version, decision = "current_before_audit", "keep"
        else:
            section = "Prior 54-page scope"
            claim = "Not required by the narrowed frozen-tracklet temporal-refinement narrative."
            source = "prior cited manuscript and retained main.bib metadata"
            version, decision = "prior_only", "remove"
        locator = field(entry, "doi") or field(entry, "url") or source
        rows.append({
            "key": key,
            "title": field(entry, "title"),
            "doi_or_url": locator,
            "version": version,
            "decision": decision,
            "relevant_section": section,
            "supported_claim": claim,
            "evidence_source": source,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.output}; cited references={len(current)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
