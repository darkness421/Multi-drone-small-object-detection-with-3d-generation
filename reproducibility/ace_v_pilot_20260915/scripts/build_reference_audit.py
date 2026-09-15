#!/usr/bin/env python3
"""Build a title/DOI audit for the narrowed temporal-refinement bibliography."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path


ACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAPER = Path(
    "/home/oem/projects/deepfake/Ourmethod/_checkpoint/meme_comparison/"
    "workspace/com3d_ace_ivc_overleaf_sync"
)
OLD_COMMIT = "f68bb489"
PRE_REPAIR_COMMIT = "da05de1"

OLD_PDF_CITED = {
    "bai2025sffefyolo", "bodla2017softnms", "boxmot2023software",
    "braso2020neuralsolver", "cai2025neusis", "cao2023ocsort",
    "chao2025bpdyolo", "ding2024adatrack", "du2019visdrone",
    "du2021giaotracker", "du2023strongsort", "emami2026frsicl",
    "geifman2019selectivenet", "guo2017calibration", "he2020cityscale",
    "hou2024selectviews", "hu2022where2comm", "hu2024universalyolo",
    "hu2025csfprrtdetr", "jiang2024mffsodnet", "johns2016activemultiview",
    "li2025mmot", "liu2023mdmt", "luiten2021hota", "ma2020frelu",
    "maggiolino2023deepocsort", "naik2024bucktales", "nie2025m3ot",
    "ovadia2019uncertainty", "ristani2016performance",
    "sadeghibakhi2025comparison", "tang2019cityflow", "tian2025ucdnet",
    "wu2025tsmmt", "yang2026uavdet", "zhang2022bytetrack",
    "zhang2024attention4align", "zhen2026gmt",
}

PRE_REPAIR_SOURCE = {
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

# Four keys were cited only by source files not included by main.tex. VisDrone
# became compiled when its Fig. 1 source citation was restored.
PRE_REPAIR_PDF = PRE_REPAIR_SOURCE - {
    "bodla2017softnms", "du2019visdrone", "ma2020frelu", "naik2024bucktales",
}
SOURCE_ONLY_FINAL = {"bodla2017softnms", "ma2020frelu", "naik2024bucktales"}

RESTORED = {
    "du2019visdrone": (
        "Introduction, Fig. 1 caption",
        "VisDrone-DET2019 is the source of the real aerial detection example.",
        "https://openaccess.thecvf.com/content_ICCVW_2019/html/VISDrone/"
        "Du_VisDrone-DET2019_The_Vision_Meets_Drone_Object_Detection_in_"
        "Image_Challenge_ICCVW_2019_paper.html",
    ),
}

ADDED = {
    "bewley2016sort": (
        "Related Work: online tracking",
        "SORT establishes the Kalman-prediction and linear-assignment baseline.",
        "https://ieeexplore.ieee.org/document/7533003/",
    ),
    "wojke2017deepsort": (
        "Related Work: online tracking",
        "Deep SORT adds a learned appearance association metric.",
        "https://arxiv.org/abs/1703.07402",
    ),
    "aharon2022botsort": (
        "Related Work: online tracking",
        "BoT-SORT combines motion, appearance, and camera-motion compensation.",
        "https://arxiv.org/abs/2206.14651",
    ),
    "sun2025gta": (
        "Related Work: post-tracking linking",
        "GTA is a plug-and-play global tracklet association method.",
        "https://link.springer.com/chapter/10.1007/978-981-96-2644-1_6",
    ),
    "du2018uavdt": (
        "Related Work: aerial tracking",
        "UAVDT provides moving-camera and small-target aerial tracking context.",
        "https://openaccess.thecvf.com/content_ECCV_2018/html/"
        "Dawei_Du_The_Unmanned_Aerial_ECCV_2018_paper.html",
    ),
    "wen2019visdronemot": (
        "Related Work: aerial tracking",
        "VisDrone-MOT2019 is the drone temporal-MOT challenge citation.",
        "https://doi.org/10.1109/ICCVW.2019.00028",
    ),
    "bergmann2019tracktor": (
        "Related Work: online tracking",
        "Tracktor provides a detector-regression tracking route and failure analysis.",
        "https://openaccess.thecvf.com/content_ICCV_2019/html/"
        "Bergmann_Tracking_Without_Bells_and_Whistles_ICCV_2019_paper.html",
    ),
    "gao2023memotr": (
        "Related Work: learned association",
        "MeMOTR represents learned long-term track memory.",
        "https://openaccess.thecvf.com/content/ICCV2023/html/"
        "Gao_MeMOTR_Long-Term_Memory-Augmented_Transformer_for_Multi-Object_"
        "Tracking_ICCV_2023_paper.html",
    ),
    "gao2025motip": (
        "Related Work: learned association",
        "MOTIP contrasts in-context ID prediction with frozen post-linking.",
        "https://openaccess.thecvf.com/content/CVPR2025/html/"
        "Gao_Multiple_Object_Tracking_as_ID_Prediction_CVPR_2025_paper.html",
    ),
    "pirsiavash2011global": (
        "Related Work: global association",
        "Network-flow optimization is a classical global MOT formulation.",
        "https://vision.ics.uci.edu/papers/globally-optimal-greedy-algorithms-"
        "for-tracking-a-variable-2011/",
    ),
    "wang2019trackletnet": (
        "Related Work: tracklet graphs",
        "TrackletNet models tracklets as graph vertices with learned connectivity.",
        "https://haotian-zhang.github.io/publication/tnt/",
    ),
}

KEEP = {
    "boxmot2023software": ("Implementation", "BoxMOT implementation provenance."),
    "braso2020neuralsolver": ("Related Work: graph MOT", "Learned graph association."),
    "cao2023ocsort": ("Method and protocol", "Frozen OC-SORT upstream tracker."),
    "du2021giaotracker": ("Related Work: post-linking", "Aerial global tracklet linking."),
    "du2023strongsort": ("Protocol", "StrongSORT/AFLink comparison source."),
    "geifman2019selectivenet": ("Related Work: selective association", "Reject-option motivation."),
    "guo2017calibration": ("Related Work: uncertainty", "Confidence-calibration limitation."),
    "he2020cityscale": ("Related Work: multi-camera MOT", "Cross-camera tracklet matching."),
    "hu2022where2comm": ("Related Work: cooperation", "Selective feature communication context."),
    "hu2024universalyolo": ("Related Work: small objects", "Aerial small-object detection context."),
    "jiang2024mffsodnet": ("Related Work: small objects", "Aerial small-object detection context."),
    "li2025mmot": ("Protocol", "Primary MMOT benchmark source."),
    "liu2023mdmt": ("Related Work: aerial tracking", "Multi-drone tracking benchmark context."),
    "luiten2021hota": ("Evaluation", "HOTA metric definition."),
    "maggiolino2023deepocsort": ("Method and protocol", "Frozen Deep OC-SORT upstream tracker."),
    "nie2025m3ot": ("Protocol", "M3OT transfer diagnostic source."),
    "ovadia2019uncertainty": ("Related Work: uncertainty", "Uncertainty-under-shift caveat."),
    "ristani2016performance": ("Evaluation", "IDF1 metric definition."),
    "tang2019cityflow": ("Related Work: multi-camera MOT", "City-scale association context."),
    "tian2025ucdnet": ("Related Work: cooperation", "Cross-UAV feature mapping context."),
    "wu2025tsmmt": ("Related Work: aerial tracking", "Temporal-spatial multi-drone tracking."),
    "zhang2022bytetrack": ("Method and protocol", "Frozen ByteTrack upstream tracker."),
}

REMOVED = {
    "bai2025sffefyolo": "Detector-only SFFEF-YOLO work is outside the narrowed temporal paper.",
    "bodla2017softnms": "Soft-NMS is cited only by the detector source file excluded from main.tex.",
    "cai2025neusis": "Cross-view scene integration is outside within-stream post-linking.",
    "chao2025bpdyolo": "Detector-only comparison is outside the narrowed temporal paper.",
    "ding2024adatrack": "End-to-end multi-camera 3D tracking is not the evaluated task.",
    "emami2026frsicl": "Flight-cost and active re-observation are not evaluated.",
    "hou2024selectviews": "Active view selection is not evaluated.",
    "hu2025csfprrtdetr": "Detector-only comparison is outside the narrowed temporal paper.",
    "johns2016activemultiview": "Active multi-view recognition is not evaluated.",
    "ma2020frelu": "FReLU is cited only by the detector source file excluded from main.tex.",
    "naik2024bucktales": "BuckTales cross-video evaluation is outside the compiled temporal scope.",
    "sadeghibakhi2025comparison": "Detector survey/comparison does not support a compiled claim.",
    "yang2026uavdet": "Detector-only comparison is outside the narrowed temporal paper.",
    "zhang2024attention4align": "Cross-view alignment is outside within-stream post-linking.",
    "zhen2026gmt": "Global multi-camera identity assignment is not the evaluated task.",
}

FINAL_SOURCE_EXPECTED = PRE_REPAIR_SOURCE | set(ADDED)
FINAL_PDF_EXPECTED = FINAL_SOURCE_EXPECTED - SOURCE_ONLY_FINAL


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


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        match = re.search(r"(?<!\\)%", line)
        lines.append(line[:match.start()] if match else line)
    return "\n".join(lines)


def citations(text: str) -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(r"\\cite(?:t|p)?\{([^}]+)\}", text):
        keys.update(item.strip() for item in match.group(1).split(","))
    return keys


def source_tree_citations(root: Path) -> set[str]:
    return set().union(*(
        citations(strip_comments(path.read_text(errors="ignore")))
        for path in root.rglob("*.tex")
    ))


def compiled_citations(root: Path) -> set[str]:
    pending = [root / "main.tex"]
    visited: set[Path] = set()
    keys: set[str] = set()
    while pending:
        path = pending.pop().resolve()
        if path in visited:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"included TeX file missing: {path}")
        visited.add(path)
        text = strip_comments(path.read_text(encoding="utf-8"))
        keys.update(citations(text))
        for match in re.finditer(r"\\(?:input|include)\{([^}]+)\}", text):
            pending.append((root / match.group(1)).with_suffix(".tex"))
    return keys


def git_blob(root: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{revision}:{path}"],
        check=True, capture_output=True, text=True,
    )
    return result.stdout


def yn(value: bool) -> str:
    return "yes" if value else "no"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-root", type=Path, default=DEFAULT_PAPER)
    parser.add_argument(
        "--output", type=Path,
        default=ACE_ROOT / "results_raw/final/reference_audit.csv",
    )
    parser.add_argument(
        "--summary", type=Path,
        default=ACE_ROOT / "results_raw/final/reference_audit_summary.md",
    )
    args = parser.parse_args()

    current_bib_text = (args.paper_root / "main.bib").read_text(encoding="utf-8")
    old_bib_text = git_blob(args.paper_root, OLD_COMMIT, "main.bib")
    current_entries = entry_blocks(current_bib_text)
    old_entries = entry_blocks(old_bib_text)
    final_source = source_tree_citations(args.paper_root)
    final_pdf = compiled_citations(args.paper_root)
    if final_source != FINAL_SOURCE_EXPECTED:
        raise RuntimeError(
            "source citation mismatch: "
            f"missing={sorted(FINAL_SOURCE_EXPECTED - final_source)}, "
            f"unexpected={sorted(final_source - FINAL_SOURCE_EXPECTED)}"
        )
    if final_pdf != FINAL_PDF_EXPECTED:
        raise RuntimeError(
            "compiled citation mismatch: "
            f"missing={sorted(FINAL_PDF_EXPECTED - final_pdf)}, "
            f"unexpected={sorted(final_pdf - FINAL_PDF_EXPECTED)}"
        )

    duplicate_dois = [
        doi for doi, count in Counter(
            field(entry, "doi").lower()
            for entry in current_entries.values() if field(entry, "doi")
        ).items() if count > 1
    ]
    if duplicate_dois:
        raise RuntimeError(f"duplicate DOI entries: {duplicate_dois}")
    if any("\\nocite" in path.read_text(errors="ignore") for path in args.paper_root.rglob("*.tex")):
        raise RuntimeError("nocite found in manuscript source")

    rows = []
    for key in sorted(OLD_PDF_CITED | final_pdf):
        entry = current_entries.get(key) or old_entries.get(key, "")
        if key in RESTORED:
            section, claim, source = RESTORED[key]
            decision = "restore"
            reason = "Restored the dataset-source citation in the compiled Fig. 1 caption."
        elif key in ADDED:
            section, claim, source = ADDED[key]
            decision = "add"
            reason = "Added to support a specific temporal-refinement related-work claim."
        elif key in final_pdf:
            section, claim = KEEP[key]
            source = "compiled manuscript citation and verified main.bib entry"
            decision = "keep"
            reason = "Directly supports the narrowed compiled manuscript."
        else:
            section = "Prior 54-page scope"
            claim = "No claim in the compiled temporal-refinement manuscript."
            source = f"paper history at {OLD_COMMIT} and retained BibTeX metadata"
            decision = "remove"
            reason = REMOVED[key]
        rows.append({
            "key": key,
            "title": field(entry, "title"),
            "doi_or_url": field(entry, "doi") or field(entry, "url"),
            "old_20260913_pdf": yn(key in OLD_PDF_CITED),
            "pre_repair_20260915_pdf": yn(key in PRE_REPAIR_PDF),
            "final_pdf": yn(key in final_pdf),
            "final_source_tree": yn(key in final_source),
            "old_bib_entry": yn(key in old_entries),
            "current_bib_entry": yn(key in current_entries),
            "decision": decision,
            "reason": reason,
            "relevant_section": section,
            "citation_sentence_or_claim": claim,
            "metadata_source": source,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    decisions = Counter(row["decision"] for row in rows)
    old_hash = hashlib.sha256(old_bib_text.encode()).hexdigest()
    current_hash = hashlib.sha256(current_bib_text.encode()).hexdigest()
    physical_added = sorted(set(current_entries) - set(old_entries))
    physical_removed = sorted(set(old_entries) - set(current_entries))
    linked = [row for row in rows if row["decision"] in {"add", "restore"}]
    removed = [row for row in rows if row["decision"] == "remove"]

    summary = [
        "# Temporal-refinement bibliography audit",
        "",
        "This audit measures citation coverage; it does not assert a journal minimum.",
        "",
        "## Version reconciliation",
        "",
        "| Snapshot | Compiled references | Source-tree cite keys | Evidence |",
        "| --- | ---: | ---: | --- |",
        f"| 20260913 broad manuscript | {len(OLD_PDF_CITED)} | {len(OLD_PDF_CITED)} | `{OLD_COMMIT}` and reviewed PDF |",
        f"| 20260915 narrowed pre-repair | {len(PRE_REPAIR_PDF)} | {len(PRE_REPAIR_SOURCE)} | `{PRE_REPAIR_COMMIT}` source topology |",
        f"| Final temporal-refinement source | {len(final_pdf)} | {len(final_source)} | reachable inputs from `main.tex` |",
        "",
        "The 38-to-22 drop is therefore real at the compiled-PDF level. The four-key",
        "source/PDF gap in the pre-repair snapshot came from citations that existed only",
        "in TeX files not included by `main.tex`. The final gap is three keys because the",
        "VisDrone-DET2019 source citation is now reachable from the Fig. 1 caption.",
        "",
        "## Decisions",
        "",
        f"- Keep: {decisions['keep']}",
        f"- Restore: {decisions['restore']}",
        f"- Add: {decisions['add']}",
        f"- Remove from compiled scope: {decisions['remove']}",
        "- `nocite{*}` or bibliography-only padding: none",
        "- Duplicate DOI entries in current `main.bib`: none",
        "",
        "## Added and restored claim linkage",
        "",
        "| Key | Decision | Section | Supported claim | Metadata source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in linked:
        summary.append(
            f"| `{row['key']}` | {row['decision']} | {row['relevant_section']} | "
            f"{row['citation_sentence_or_claim']} | {row['metadata_source']} |"
        )
    summary.extend([
        "",
        "## Excluded prior-scope citations",
        "",
        "| Key | Title | Reason |",
        "| --- | --- | --- |",
    ])
    for row in removed:
        summary.append(f"| `{row['key']}` | {row['title']} | {row['reason']} |")
    summary.extend([
        "",
        "## BibTeX preservation",
        "",
        f"- Original `main.bib`: Git `{OLD_COMMIT}`, SHA-256 `{old_hash}`",
        f"- Current `main.bib`: SHA-256 `{current_hash}`",
        f"- Physical entries: old {len(old_entries)}, current {len(current_entries)}",
        f"- Physical keys added since old snapshot: {', '.join(physical_added) or 'none'}",
        f"- Physical keys removed since old snapshot: {', '.join(physical_removed) or 'none'}",
        "",
        "The original bibliography is preserved in Git history. Entries excluded from the",
        "compiled scope were not erased from the historical snapshot.",
        "",
    ])
    args.summary.write_text("\n".join(summary), encoding="utf-8")
    print(
        f"wrote {len(rows)} rows; final compiled={len(final_pdf)}, "
        f"source-tree={len(final_source)}, decisions={dict(decisions)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
