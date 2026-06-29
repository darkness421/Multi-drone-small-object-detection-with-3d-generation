"""Build a real-Cesium MarineCity cross-view evidence graph smoke artifact.

This script reads detector EvidenceTokens exported from the verified MarineCity
real-Cesium captures. It does not create or modify an Isaac/Cesium stage, and it
does not claim a completed NeRF/3DGS reconstruction benchmark. The graph is a
camera-metadata-backed association smoke test for the 3D evidence layer.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evidence import EvidenceToken, load_tokens_jsonl


DEFAULT_TOKENS = REPO_ROOT / "outputs/evidence/marinecity_real_capture_detector_smoke/evidence_tokens.jsonl"
DEFAULT_OUT = REPO_ROOT / "outputs/graphs/marinecity_crossview_evidence_graph"
DEFAULT_LIVE = REPO_ROOT / "outputs/reports/live"
DEFAULT_PAPER_FIG_DIR = REPO_ROOT / "paper/figures/results/marinecity_system"
DEFAULT_PAPER_TABLE = REPO_ROOT / "paper/tables/marinecity_crossview_evidence_graph_table.tex"
UAV_IDS = ["uav_01", "uav_02", "uav_03"]


def vec_sub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def vec_add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def vec_scale(a: list[float], scale: float) -> list[float]:
    return [a[i] * scale for i in range(3)]


def dot(a: list[float], b: list[float]) -> float:
    return sum(a[i] * b[i] for i in range(3))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(max(dot(a, a), 0.0))


def normalize(a: list[float], fallback: list[float] | None = None) -> list[float]:
    length = norm(a)
    if length < 1e-9:
        return list(fallback or [0.0, 0.0, 1.0])
    return [value / length for value in a]


def distance_xy(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def class_name(token: EvidenceToken) -> str:
    if token.metadata.get("class_name"):
        return str(token.metadata["class_name"])
    if token.class_id is not None:
        return f"class_{token.class_id}"
    return "unknown"


def scenario_id(token: EvidenceToken) -> str:
    return str(token.metadata.get("scenario_id") or "unknown_scenario")


def short_scenario(value: str) -> str:
    if "_s0_" in value:
        return "S0"
    if "_s1_" in value:
        return "S1"
    if "_s2_" in value:
        return "S2"
    return value.replace("uavmarine_", "").replace("_viewer160_session_recapture", "")


def image_size(token: EvidenceToken) -> tuple[int, int]:
    path = token.metadata.get("image_path")
    if path:
        try:
            from PIL import Image

            with Image.open(path) as image:
                return int(image.width), int(image.height)
        except Exception:
            pass
    return 1280, 720


def project_token(
    token: EvidenceToken,
    *,
    hfov_deg: float,
    ground_z: float,
) -> dict[str, Any]:
    """Approximate a token's ground-plane point from camera metadata.

    The output is used only for association smoke testing. It is not a calibrated
    metric 3D reconstruction.
    """

    extrinsic = token.camera_extrinsic or []
    eye = [float(v) for v in token.metadata.get("camera_position") or []]
    if len(eye) != 3 and token.uav_pose and len(token.uav_pose) >= 3:
        eye = [float(v) for v in token.uav_pose[:3]]
    if len(eye) != 3 and len(extrinsic) == 4 and len(extrinsic[3]) >= 3:
        eye = [float(v) for v in extrinsic[3][:3]]

    target = [float(v) for v in token.metadata.get("look_at_target") or []]
    if len(eye) != 3:
        return {
            "token_id": token.token_id,
            "valid": False,
            "reason": "missing_camera_metadata",
            "association_point": [0.0, 0.0, 0.0],
        }

    width, height = image_size(token)
    cx, cy = token.bbox_center
    x_norm = 2.0 * (cx / max(width, 1) - 0.5)
    y_norm = 2.0 * (0.5 - cy / max(height, 1))

    htan = math.tan(math.radians(hfov_deg) / 2.0)
    vtan = htan * height / max(width, 1)
    if len(target) == 3:
        forward = normalize(vec_sub(target, eye), fallback=[0.0, 0.0, -1.0])
        world_up = [0.0, 0.0, 1.0]
        right = normalize(cross(forward, world_up), fallback=[1.0, 0.0, 0.0])
        up = normalize(cross(right, forward), fallback=[0.0, 1.0, 0.0])
        ray = normalize(vec_add(forward, vec_add(vec_scale(right, x_norm * htan), vec_scale(up, y_norm * vtan))))
        camera_model = "look_at"
    elif len(extrinsic) == 4 and all(len(row) >= 3 for row in extrinsic[:3]):
        local_ray = normalize([x_norm * htan, y_norm * vtan, -1.0], fallback=[0.0, 0.0, -1.0])
        rotation = [[float(extrinsic[row][col]) for col in range(3)] for row in range(3)]
        # Isaac/Omniverse transform matrices commonly store translation in the
        # final row. Treat the detector export as a row-vector transform.
        ray = normalize(
            [
                sum(local_ray[j] * rotation[j][0] for j in range(3)),
                sum(local_ray[j] * rotation[j][1] for j in range(3)),
                sum(local_ray[j] * rotation[j][2] for j in range(3)),
            ],
            fallback=[0.0, 0.0, -1.0],
        )
        camera_model = "camera_extrinsic"
    else:
        ray = [0.0, 0.0, -1.0]
        camera_model = "vertical_fallback"

    ground_point: list[float] | None = None
    if ray[2] < -1e-8:
        t = (ground_z - eye[2]) / ray[2]
        if 0.0 < t < 5000.0:
            ground_point = vec_add(eye, vec_scale(ray, t))

    depth_point: list[float] | None = None
    if token.depth_value is not None and math.isfinite(float(token.depth_value)) and float(token.depth_value) > 0:
        depth_point = vec_add(eye, vec_scale(ray, float(token.depth_value)))

    association_point = ground_point or depth_point or target
    source = "ground_plane_intersection" if ground_point else ("depth_ray_point" if depth_point else "look_at_target_fallback")
    return {
        "token_id": token.token_id,
        "valid": bool(ground_point or depth_point),
        "projection_source": source,
        "association_point": [float(v) for v in association_point],
        "ground_point": ground_point,
        "depth_point": depth_point,
        "image_size": [width, height],
        "bbox_center": [cx, cy],
        "hfov_deg": hfov_deg,
        "ground_z": ground_z,
        "camera_model": camera_model,
    }


def representative_point(points: list[list[float]]) -> list[float]:
    if not points:
        return [0.0, 0.0, 0.0]
    return [sum(point[i] for point in points) / len(points) for i in range(3)]


def point_spread(points: list[list[float]], center: list[float]) -> float:
    if not points:
        return 0.0
    return sum(distance_xy(point, center) for point in points) / len(points)


def route_action(
    *,
    view_count: int,
    ambiguity: float,
    mean_confidence: float,
    projection_valid_ratio: float,
) -> str:
    """Assign the graph-level routing action used by the smoke protocol.

    The action is intentionally conservative: only multi-view, low-ambiguity
    hypotheses are finalized directly. Moderate multi-view ambiguity is kept
    under monitoring, severe ambiguity or missing-view evidence triggers
    targeted re-observation, and very weak single-view hypotheses are rejected
    from automatic acceptance.
    """

    if view_count < 2 and mean_confidence < 0.03:
        return "reject"
    if view_count >= 2 and ambiguity < 0.55:
        return "finalize"
    if view_count >= 2 and ambiguity < 0.75:
        return "monitor"
    return "targeted_reobserve"


def cluster_tokens(
    tokens: list[EvidenceToken],
    projections: dict[str, dict[str, Any]],
    *,
    threshold: float,
) -> list[list[EvidenceToken]]:
    clusters: list[list[EvidenceToken]] = []
    centers: list[list[float]] = []
    for token in sorted(tokens, key=lambda row: float(row.confidence), reverse=True):
        point = projections[token.token_id]["association_point"]
        best_idx = None
        best_dist = float("inf")
        for idx, center in enumerate(centers):
            dist = distance_xy(point, center)
            if dist < best_dist:
                best_dist = dist
                best_idx = idx
        if best_idx is not None and best_dist <= threshold:
            clusters[best_idx].append(token)
            centers[best_idx] = representative_point([projections[row.token_id]["association_point"] for row in clusters[best_idx]])
        else:
            clusters.append([token])
            centers.append(point)
    return clusters


def build_graph(tokens: list[EvidenceToken], args: argparse.Namespace) -> dict[str, Any]:
    projections = {token.token_id: project_token(token, hfov_deg=args.hfov_deg, ground_z=args.ground_z) for token in tokens}
    grouped: dict[tuple[str, str], list[EvidenceToken]] = defaultdict(list)
    for token in tokens:
        grouped[(scenario_id(token), class_name(token))].append(token)

    hypotheses: list[dict[str, Any]] = []
    support_edges: list[dict[str, Any]] = []
    observation_nodes: list[dict[str, Any]] = []
    hypothesis_index = 0

    for token in tokens:
        meta = token.metadata or {}
        observation_nodes.append(
            {
                "node_id": f"obs::{token.token_id}",
                "node_type": "observation",
                "token_id": token.token_id,
                "scenario_id": scenario_id(token),
                "uav_id": token.uav_id,
                "class_name": class_name(token),
                "confidence": token.confidence,
                "uncertainty": token.uncertainty,
                "bbox_2d": token.bbox_2d,
                "projection": projections[token.token_id],
                "rgb_black_ratio": meta.get("rgb_black_ratio"),
                "depth_finite_ratio": meta.get("depth_finite_ratio"),
            }
        )

    for (scenario, cls), group in sorted(grouped.items()):
        for cluster in cluster_tokens(group, projections, threshold=args.cluster_threshold):
            points = [projections[token.token_id]["association_point"] for token in cluster]
            center = representative_point(points)
            uavs = sorted({token.uav_id for token in cluster})
            classes = Counter(class_name(token) for token in cluster)
            conf_values = [float(token.confidence) for token in cluster]
            unc_values = [float(token.uncertainty) for token in cluster]
            black_values = [float(token.metadata.get("rgb_black_ratio") or 0.0) for token in cluster]
            valid_projection_count = sum(1 for token in cluster if projections[token.token_id].get("valid"))
            projection_valid_ratio = valid_projection_count / max(1, len(cluster))
            spread = point_spread(points, center)
            missing_uavs = [uav for uav in UAV_IDS if uav not in uavs]
            view_count = len(uavs)
            mean_confidence = sum(conf_values) / max(1, len(conf_values))
            mean_uncertainty = sum(unc_values) / max(1, len(unc_values))
            ambiguity = min(
                1.0,
                mean_uncertainty
                + (0.18 if view_count < 2 else 0.0)
                + (0.08 if spread > args.cluster_threshold * 0.5 else 0.0)
                + (0.06 if max(black_values or [0.0]) > 0.15 else 0.0),
            )
            action = route_action(
                view_count=view_count,
                ambiguity=ambiguity,
                mean_confidence=mean_confidence,
                projection_valid_ratio=projection_valid_ratio,
            )
            hypothesis_id = f"{short_scenario(scenario)}_H{hypothesis_index:03d}"
            hypothesis_index += 1
            hypothesis = {
                "hypothesis_id": hypothesis_id,
                "scenario_id": scenario,
                "scenario_short": short_scenario(scenario),
                "class_name": cls,
                "token_ids": [token.token_id for token in cluster],
                "uav_ids": uavs,
                "missing_uav_ids": missing_uavs,
                "token_count": len(cluster),
                "view_count": view_count,
                "class_votes": dict(classes),
                "mean_confidence": mean_confidence,
                "mean_uncertainty": mean_uncertainty,
                "max_rgb_black_ratio": max(black_values or [0.0]),
                "projection_valid_ratio": projection_valid_ratio,
                "center_scene_units": center,
                "association_spread_xy": spread,
                "ambiguity_score": ambiguity,
                "association_quality": "multi_view_support" if view_count >= 2 else "single_view_candidate",
                "recommended_action": action,
                "claim_level": "real_cesium_crossview_association_smoke",
            }
            hypotheses.append(hypothesis)
            for token in cluster:
                support_edges.append(
                    {
                        "edge_type": "support",
                        "source": f"obs::{token.token_id}",
                        "target": f"hyp::{hypothesis_id}",
                        "token_id": token.token_id,
                        "uav_id": token.uav_id,
                        "confidence": token.confidence,
                    }
                )

    conflict_edges: list[dict[str, Any]] = []
    weak_edges: list[dict[str, Any]] = []
    missing_edges: list[dict[str, Any]] = []
    for idx, left in enumerate(hypotheses):
        if left["view_count"] < 2 or left["ambiguity_score"] >= 0.62:
            weak_edges.append(
                {
                    "edge_type": "weak_or_uncertain",
                    "source": f"hyp::{left['hypothesis_id']}",
                    "target": "verifier::reobserve_policy",
                    "reason": "single_view_or_high_ambiguity",
                    "ambiguity_score": left["ambiguity_score"],
                }
            )
        for uav_id in left["missing_uav_ids"]:
            missing_edges.append(
                {
                    "edge_type": "missing_evidence",
                    "source": f"hyp::{left['hypothesis_id']}",
                    "target": f"uav::{uav_id}",
                    "reason": "no_supporting_token_from_view",
                }
            )
        for right in hypotheses[idx + 1 :]:
            if left["scenario_id"] != right["scenario_id"] or left["class_name"] == right["class_name"]:
                continue
            dist = distance_xy(left["center_scene_units"], right["center_scene_units"])
            if dist <= args.conflict_threshold:
                conflict_edges.append(
                    {
                        "edge_type": "conflict_or_class_ambiguity",
                        "source": f"hyp::{left['hypothesis_id']}",
                        "target": f"hyp::{right['hypothesis_id']}",
                        "distance_xy": dist,
                        "reason": "nearby_different_class_hypotheses",
                    }
                )

    hypothesis_nodes = [
        {
            "node_id": f"hyp::{row['hypothesis_id']}",
            "node_type": "object_hypothesis",
            **row,
        }
        for row in hypotheses
    ]
    edges = support_edges + conflict_edges + weak_edges + missing_edges
    summary = {
        "status": "marinecity_crossview_evidence_graph_smoke_ready",
        "claim_level": "real_cesium_crossview_association_smoke_not_final_3d_reconstruction",
        "source_tokens": str(args.tokens),
        "token_count": len(tokens),
        "scenario_count": len({scenario_id(token) for token in tokens}),
        "uav_count": len({token.uav_id for token in tokens}),
        "hypothesis_count": len(hypotheses),
        "multi_view_hypothesis_count": sum(1 for row in hypotheses if row["view_count"] >= 2),
        "single_view_hypothesis_count": sum(1 for row in hypotheses if row["view_count"] < 2),
        "support_edge_count": len(support_edges),
        "conflict_edge_count": len(conflict_edges),
        "weak_edge_count": len(weak_edges),
        "missing_evidence_edge_count": len(missing_edges),
        "action_counts": dict(Counter(row["recommended_action"] for row in hypotheses)),
        "mean_ambiguity": sum(float(row["ambiguity_score"]) for row in hypotheses) / max(1, len(hypotheses)),
        "class_counts": dict(Counter(class_name(token) for token in tokens)),
        "scenario_token_counts": dict(Counter(short_scenario(scenario_id(token)) for token in tokens)),
        "parameters": {
            "hfov_deg": args.hfov_deg,
            "ground_z": args.ground_z,
            "cluster_threshold": args.cluster_threshold,
            "conflict_threshold": args.conflict_threshold,
            "finalize_rule": "view_count>=2 and ambiguity<0.55",
            "monitor_rule": "view_count>=2 and 0.55<=ambiguity<0.75",
            "reject_rule": "view_count<2 and mean_confidence<0.03",
            "reobserve_rule": "remaining high-ambiguity, missing-view, or low-projection-confidence cases",
        },
        "claiming_rule": "Use as real-Cesium evidence-graph smoke/protocol result. Do not claim completed metric 3D reconstruction or external-provider LLM validation.",
    }
    return {
        "summary": summary,
        "nodes": observation_nodes + hypothesis_nodes,
        "hypotheses": hypotheses,
        "edges": edges,
        "projections": projections,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_hypothesis_csv(path: Path, hypotheses: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "hypothesis_id",
        "scenario_short",
        "class_name",
        "token_count",
        "view_count",
        "uav_ids",
        "mean_confidence",
        "mean_uncertainty",
        "association_spread_xy",
        "projection_valid_ratio",
        "ambiguity_score",
        "association_quality",
        "recommended_action",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in hypotheses:
            writer.writerow(
                {
                    **{field: row.get(field, "") for field in fields},
                    "uav_ids": ",".join(row.get("uav_ids", [])),
                    "mean_confidence": f"{row.get('mean_confidence', 0.0):.4f}",
                    "mean_uncertainty": f"{row.get('mean_uncertainty', 0.0):.4f}",
                    "association_spread_xy": f"{row.get('association_spread_xy', 0.0):.2f}",
                    "projection_valid_ratio": f"{row.get('projection_valid_ratio', 0.0):.2f}",
                    "ambiguity_score": f"{row.get('ambiguity_score', 0.0):.4f}",
                }
            )


def tex_escape(value: Any) -> str:
    return str(value).replace("_", r"\_").replace("%", r"\%")


def write_latex_table(path: Path, hypotheses: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(hypotheses, key=lambda row: (row["scenario_short"], -row["view_count"], -row["mean_confidence"]))
    lines = [
        r"\begin{tabular}{lllrrrl}",
        r"\toprule",
        r"Scenario & Hyp. & Class & Tokens & Views & Amb. & Action \\",
        r"\midrule",
    ]
    for row in ranked:
        lines.append(
            " & ".join(
                [
                    tex_escape(row["scenario_short"]),
                    tex_escape(row["hypothesis_id"]),
                    tex_escape(row["class_name"]),
                    str(row["token_count"]),
                    str(row["view_count"]),
                    f"{row['ambiguity_score']:.3f}",
                    tex_escape(row["recommended_action"].replace("_", " ")),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_md(path: Path, graph: dict[str, Any], figure_path: Path, table_path: Path) -> None:
    summary = graph["summary"]
    hypotheses = sorted(graph["hypotheses"], key=lambda row: (row["scenario_short"], row["hypothesis_id"]))
    lines = [
        "# MarineCity Cross-View Evidence Graph Smoke",
        "",
        f"- Status: `{summary['status']}`",
        f"- Claim level: `{summary['claim_level']}`",
        f"- Source tokens: `{summary['source_tokens']}`",
        f"- Tokens / hypotheses: `{summary['token_count']}` / `{summary['hypothesis_count']}`",
        f"- Multi-view hypotheses: `{summary['multi_view_hypothesis_count']}`",
        f"- Support/conflict/missing edges: `{summary['support_edge_count']}` / `{summary['conflict_edge_count']}` / `{summary['missing_evidence_edge_count']}`",
        f"- Figure: `{figure_path}`",
        f"- Paper table: `{table_path}`",
        "",
        "Claiming rule: this is real-Cesium detector-token evidence graph smoke evidence. It is not a completed metric 3D reconstruction, NeRF/3DGS result, or external-provider LLM validation.",
        "",
        "| Scenario | Hypothesis | Class | Tokens | Views | Mean conf. | Ambiguity | Action |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in hypotheses:
        lines.append(
            f"| {row['scenario_short']} | {row['hypothesis_id']} | {row['class_name']} | "
            f"{row['token_count']} | {row['view_count']} | {row['mean_confidence']:.3f} | "
            f"{row['ambiguity_score']:.3f} | {row['recommended_action']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def draw_graph_figure(path: Path, graph: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hypotheses = graph["hypotheses"]
    scenarios = sorted({row["scenario_short"] for row in hypotheses})
    if not scenarios:
        scenarios = ["S0"]
    fig, axes = plt.subplots(1, len(scenarios), figsize=(5.3 * len(scenarios), 4.7), dpi=180, squeeze=False)
    colors = {"car": "#2563eb", "bus": "#f97316", "pedestrian": "#16a34a", "person": "#16a34a", "unknown": "#64748b"}
    for ax, scenario in zip(axes[0], scenarios):
        rows = [row for row in hypotheses if row["scenario_short"] == scenario]
        ax.set_facecolor("#f8fafc")
        ax.grid(color="#e2e8f0", linewidth=0.8)
        ax.set_title(f"{scenario} evidence hypotheses", fontsize=11, weight="bold")
        ax.set_xlabel("scene x (heuristic)")
        ax.set_ylabel("scene y (heuristic)")
        if not rows:
            ax.text(0.5, 0.5, "no hypotheses", transform=ax.transAxes, ha="center", va="center")
            continue
        for row in rows:
            point = row["center_scene_units"]
            color = colors.get(row["class_name"], "#64748b")
            marker = "o" if row["view_count"] >= 2 else "s"
            size = 85 + 35 * row["token_count"]
            ax.scatter([point[0]], [point[1]], s=size, c=color, marker=marker, edgecolors="#0f172a", linewidths=0.8, alpha=0.86)
            label = f"{row['hypothesis_id']}\n{row['class_name']} v{row['view_count']} t{row['token_count']}"
            ax.annotate(label, (point[0], point[1]), textcoords="offset points", xytext=(7, 5), fontsize=7.5)
        xs = [row["center_scene_units"][0] for row in rows]
        ys = [row["center_scene_units"][1] for row in rows]
        pad_x = max(10.0, (max(xs) - min(xs)) * 0.15)
        pad_y = max(10.0, (max(ys) - min(ys)) * 0.15)
        ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
        ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)
    fig.text(
        0.01,
        0.01,
        "Real-Cesium detector-token association smoke. Coordinates are heuristic camera-ray projections, not metric reconstruction ground truth.",
        fontsize=8.5,
        color="#475569",
    )
    fig.savefig(path, bbox_inches="tight", facecolor="#f8fafc")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity real-Cesium cross-view evidence graph smoke artifacts.")
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--live-dir", type=Path, default=DEFAULT_LIVE)
    parser.add_argument("--paper-figure-dir", type=Path, default=DEFAULT_PAPER_FIG_DIR)
    parser.add_argument("--paper-table", type=Path, default=DEFAULT_PAPER_TABLE)
    parser.add_argument("--hfov-deg", type=float, default=60.0)
    parser.add_argument("--ground-z", type=float, default=0.0)
    parser.add_argument("--cluster-threshold", type=float, default=55.0)
    parser.add_argument("--conflict-threshold", type=float, default=38.0)
    args = parser.parse_args()

    tokens = load_tokens_jsonl(args.tokens)
    graph = build_graph(tokens, args)

    out_dir = args.out_dir
    write_json(out_dir / "summary.json", graph["summary"])
    write_json(out_dir / "nodes.json", graph["nodes"])
    write_json(out_dir / "hypotheses.json", graph["hypotheses"])
    write_json(out_dir / "edges.json", graph["edges"])
    write_json(out_dir / "projections.json", graph["projections"])
    write_hypothesis_csv(out_dir / "hypothesis_table.csv", graph["hypotheses"])
    write_latex_table(args.paper_table, graph["hypotheses"])

    live_fig = args.live_dir / "marinecity_crossview_evidence_graph.png"
    paper_fig = args.paper_figure_dir / "marinecity_crossview_evidence_graph.png"
    draw_graph_figure(live_fig, graph)
    draw_graph_figure(paper_fig, graph)

    summary_md = out_dir / "summary.md"
    live_md = args.live_dir / "marinecity_crossview_evidence_graph.md"
    write_summary_md(summary_md, graph, live_fig, args.paper_table)
    write_summary_md(live_md, graph, live_fig, args.paper_table)

    print(json.dumps({"summary": str(out_dir / "summary.json"), "live_md": str(live_md), "paper_table": str(args.paper_table), "paper_figure": str(paper_fig)}, indent=2))


if __name__ == "__main__":
    main()
