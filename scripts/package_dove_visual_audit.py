#!/usr/bin/env python3
"""Package the DOVE renderer and visual-model audit from saved results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialised = list(rows)
    fields = list(dict.fromkeys(key for row in materialised for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(materialised)


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_bundle(source: Path, destination: Path, names: Iterable[str]) -> None:
    for name in names:
        _copy(source / name, destination / name)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def _model_rows(path: Path) -> dict[str, dict[str, str]]:
    return {row["method"]: row for row in _read_csv(path)}


def _capture_seconds(path: Path) -> float:
    matches = re.findall(
        r"\[([0-9.]+)s\] Simulation App Shutting Down",
        path.read_text(encoding="utf-8", errors="replace"),
    )
    if not matches:
        raise RuntimeError(f"capture shutdown timing missing from {path}")
    return float(matches[-1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT
        / "outputs/dove_wm/final_package/DOVE_RENDER_VISUAL_MODEL_AUDIT_20261016",
    )
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    uv = ROOT / "outputs/dove_wm/uv_camera_ab_20261016/audit"
    capture = ROOT / "outputs/dove_wm/visual_gt_balanced_20261016"
    evaluation = ROOT / "outputs/dove_wm/visual_gt_balanced_eval_final_20261016"
    compact = ROOT / "outputs/dove_wm/visual_world_model_balanced_final_r2_20261016"
    embeddings = ROOT / "outputs/dove_wm/visual_current_embeddings_balanced_20261016"
    embedding_model = (
        ROOT / "outputs/dove_wm/visual_world_model_detector_embedding_final_r2_20261016"
    )
    first_pilot = ROOT / "outputs/dove_wm/visual_world_model_pilot_20261016"
    figures = ROOT / "outputs/dove_wm/final_figures_final_r2_20261016"

    _copy_bundle(
        uv,
        output / "main",
        [
            "camera_calibration_audit.csv",
            "proxy_selection_tie_aware_summary.csv",
            "uv_detector_ab.csv",
            "uv_pixel_ab.csv",
        ],
    )
    _copy(
        evaluation / "detector_gt_per_view.csv",
        output / "main/balanced_detector_gt_per_view.csv",
    )
    _copy(
        evaluation / "view_selection.csv",
        output / "main/balanced_view_selection.csv",
    )
    _copy(
        compact / "model_summary.csv",
        output / "main/compact_visual_model_summary.csv",
    )
    _copy(
        embedding_model / "model_summary.csv",
        output / "main/detector_embedding_model_summary.csv",
    )
    _copy(
        embedding_model / "paired_scene_bootstrap.csv",
        output / "main/detector_embedding_paired_scene_bootstrap.csv",
    )
    for source in sorted(figures.iterdir()):
        if source.is_file():
            _copy(source, output / "main/figures" / source.name)

    complete_names = [
        "SUMMARY_KO.md",
        "gt_action_dataset.csv",
        "model_summary.csv",
        "oof_predictions.csv",
        "paired_scene_bootstrap.csv",
        "run.log",
        "selection_by_scene.csv",
        "summary.json",
    ]
    _copy_bundle(compact, output / "supplementary/compact_visual_model", complete_names)
    _copy_bundle(
        embedding_model,
        output / "supplementary/detector_embedding_visual_model",
        complete_names,
    )
    _copy_bundle(
        evaluation,
        output / "supplementary/balanced_gt_evaluation",
        [
            "SUMMARY_KO.md",
            "bbox_coordinate_audit.csv",
            "detector_gt_per_view.csv",
            "detector_predictions.csv",
            "run.log",
            "summary.json",
            "view_selection.csv",
        ],
    )
    _copy_bundle(
        uv,
        output / "supplementary/uv_and_tie_audit",
        [
            "camera_calibration_audit.csv",
            "manifest.json",
            "proxy_selection_tie_aware.csv",
            "proxy_selection_tie_aware_summary.csv",
            "uv_detector_ab.csv",
            "uv_pixel_ab.csv",
        ],
    )
    _copy_bundle(
        first_pilot,
        output / "supplementary/first_visual_pilot",
        [
            "SUMMARY_KO.md",
            "model_summary.csv",
            "paired_scene_bootstrap.csv",
            "selection_by_scene.csv",
            "summary.json",
        ],
    )

    _copy_bundle(
        capture,
        output / "raw/balanced_capture",
        [
            "capture.log",
            "capture_plan.json",
            "marinecity_proxy_stage.usda",
            "proxy_capture_summary.json",
        ],
    )
    _copy_bundle(
        embeddings,
        output / "raw/current_rgb_embeddings",
        ["current_visual_embeddings.csv", "run.log", "summary.json"],
    )

    code_paths = [
        "configs/sim/marinecity_isaac_stage1.yaml",
        "configs/sim/marinecity_visual_gt_balanced.yaml",
        "configs/sim/marinecity_visual_gt_pilot.yaml",
        "detectors/__init__.py",
        "scripts/audit_dove_uv_and_ties.py",
        "scripts/evaluate_dove_proxy_gt.py",
        "scripts/evaluate_dove_visual_world_models.py",
        "scripts/extract_dove_current_embeddings.py",
        "scripts/package_dove_visual_audit.py",
        "scripts/render_dove_visual_model_audit.py",
        "simulation/isaac/build_marinecity_stage.py",
        "simulation/isaac/capture_marinecity_proxy.py",
        "tests/test_dove_stage_calibration.py",
    ]
    for relative in code_paths:
        _copy(ROOT / relative, output / "code" / relative)

    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    remote = _git("remote", "get-url", "origin")
    (output / "code/git_head.txt").write_text(
        f"commit={head}\nbranch={branch}\nremote={remote}\n", encoding="utf-8"
    )
    (output / "code/git_status.txt").write_text(
        _git("status", "--short", "--branch") + "\n", encoding="utf-8"
    )
    (output / "code/latest_commit.patch").write_text(
        _git("show", "--format=fuller", "--stat", "--patch", "HEAD") + "\n",
        encoding="utf-8",
    )

    eval_summary = json.loads((evaluation / "summary.json").read_text())
    compact_summary = json.loads((compact / "summary.json").read_text())
    embedding_summary = json.loads((embeddings / "summary.json").read_text())
    embedding_model_summary = json.loads(
        (embedding_model / "summary.json").read_text()
    )
    model_rows = _model_rows(embedding_model / "model_summary.csv")
    boot_rows = _read_csv(embedding_model / "paired_scene_bootstrap.csv")
    direct_boot = next(
        row
        for row in boot_rows
        if row["left_method"] == "VISUAL_DIRECT_RIDGE"
        and row["right_method"] == "GEOMETRY_RIDGE"
    )
    uv_detector = _read_csv(uv / "uv_detector_ab.csv")
    uv_pixel = _read_csv(uv / "uv_pixel_ab.csv")
    proxy_rows = _model_rows(uv / "proxy_selection_tie_aware_summary.csv")
    geometry = model_rows["GEOMETRY_RIDGE"]
    visual = model_rows["VISUAL_DIRECT_RIDGE"]
    residual = model_rows["GEOMETRY_VISUAL_RESIDUAL_RIDGE"]
    oracle = model_rows["GT_RECALL_ORACLE"]
    random_expected = model_rows["UNIFORM_RANDOM_EXPECTATION"]
    uv_example = next(
        row
        for row in uv_pixel
        if row["uav_id"] == "uav_01" and row["region"] == "full_image"
    )

    runtime_rows = [
        {
            "stage": "Isaac balanced capture",
            "items": 48,
            "elapsed_seconds": _capture_seconds(capture / "capture.log"),
            "device": "RTX 5090 GPU 0",
            "cache": "none",
        },
        {
            "stage": "detector GT evaluation",
            "items": 48,
            "elapsed_seconds": eval_summary["elapsed_seconds"],
            "device": "RTX 5090 GPU 0",
            "cache": "saved RGB reused",
        },
        {
            "stage": "frozen current-RGB embedding",
            "items": 12,
            "elapsed_seconds": embedding_summary["elapsed_seconds"],
            "device": "RTX 5090 GPU 0",
            "cache": "saved RGB reused",
        },
        {
            "stage": "compact feature models plus 20k bootstrap",
            "items": 48,
            "elapsed_seconds": compact_summary[
                "feature_model_bootstrap_elapsed_seconds"
            ],
            "device": "CPU",
            "cache": "saved metrics reused",
        },
        {
            "stage": "detector-embedding models plus 20k bootstrap",
            "items": 48,
            "elapsed_seconds": embedding_model_summary[
                "feature_model_bootstrap_elapsed_seconds"
            ],
            "device": "CPU",
            "cache": "saved embeddings reused",
        },
    ]
    _write_csv(output / "main/runtime.csv", runtime_rows)

    status_rows = [
        {
            "item": "USD UV primvar wiring",
            "status": "COMPLETE",
            "evidence": "main/uv_pixel_ab.csv",
            "claim": "UV wiring materially changes rendered pixels.",
        },
        {
            "item": "camera and bbox evaluation repair",
            "status": "COMPLETE",
            "evidence": "main/camera_calibration_audit.csv; supplementary/balanced_gt_evaluation/bbox_coordinate_audit.csv",
            "claim": "Configured 780 px focal length and saved-image box bounds are audited.",
        },
        {
            "item": "tie-aware detector-proxy reanalysis",
            "status": "COMPLETE",
            "evidence": "main/proxy_selection_tie_aware_summary.csv",
            "claim": "The earlier 4/12 to 5/12 advantage disappears under tie-aware scoring.",
        },
        {
            "item": "GT-supervised visual direct and residual models",
            "status": "COMPLETE_NEGATIVE",
            "evidence": "main/detector_embedding_model_summary.csv; main/detector_embedding_paired_scene_bootstrap.csv",
            "claim": "The visual models were implemented but did not beat geometry.",
        },
        {
            "item": "independent real-scene validation",
            "status": "NOT_EXECUTED",
            "evidence": "",
            "claim": "No generalization claim is supported.",
        },
        {
            "item": "memory, discovery, closed-loop control",
            "status": "NOT_IMPLEMENTED",
            "evidence": "",
            "claim": "These modules cannot be claimed as validated contributions.",
        },
    ]
    _write_csv(output / "status.csv", status_rows)

    evidence_rows = [
        {
            "experiment_id": "DOVE_UV_AB_20261016",
            "question": "Does the missing UV connection alter the render?",
            "result_file": "main/uv_pixel_ab.csv",
            "result": (
                f"uav_01 changed pixels={uv_example['changed_pixel_count']}, "
                f"MAE={float(uv_example['mean_absolute_pixel_delta']):.6f}"
            ),
            "supported_claim": "The USD texture-coordinate path was missing and the repair changes pixels.",
            "unsupported_claim": "UV repair improves detector recall.",
        },
        {
            "experiment_id": "DOVE_UV_DETECTOR_AB_20261016",
            "question": "Does the UV repair create GT-matched detections?",
            "result_file": "main/uv_detector_ab.csv",
            "result": "TP=0 for UV off and on at confidence 0.01 and 0.001.",
            "supported_claim": "No detection improvement was established in this A/B.",
            "unsupported_claim": "UV was the sole cause of the previous zero-TP result.",
        },
        {
            "experiment_id": "DOVE_PROXY_TIE_AUDIT_20261016",
            "question": "Does residual proxy selection beat direct selection after ties?",
            "result_file": "main/proxy_selection_tie_aware_summary.csv",
            "result": (
                f"all learned methods match {proxy_rows['GEOMETRY_STRUCTURED_RESIDUAL']['tie_aware_oracle_matches']}/12; "
                f"residual mean={float(proxy_rows['GEOMETRY_STRUCTURED_RESIDUAL']['mean_selected_utility']):.6f}, "
                f"random expectation={float(proxy_rows['GEOMETRY_STRUCTURED_RESIDUAL']['mean_uniform_random_expected_utility']):.6f}"
            ),
            "supported_claim": "Tie-aware proxy analysis removes the reported residual advantage.",
            "unsupported_claim": "Residual selection improves AP or recall.",
        },
        {
            "experiment_id": "DOVE_BALANCED_GT_VISUAL_20261016",
            "question": "Do current-RGB visual models beat geometry on GT recall?",
            "result_file": "main/detector_embedding_model_summary.csv",
            "result": (
                f"geometry={float(geometry['mean_selected_recall_at_iou50']):.6f}; "
                f"visual={float(visual['mean_selected_recall_at_iou50']):.6f}; "
                f"delta={float(direct_boot['mean_recall_difference']):.6f}, "
                f"CI=[{float(direct_boot['ci95_low']):.6f}, {float(direct_boot['ci95_high']):.6f}]"
            ),
            "supported_claim": "The minimum visual world-model path runs without outcome-image leakage.",
            "unsupported_claim": "The visual model outperforms geometry or generalizes to real scenes.",
        },
    ]
    _write_csv(output / "evidence_map.csv", evidence_rows)

    readme = f"""# DOVE Renderer and Visual-Model Audit

이 패키지는 DOVE의 렌더링·평가 오류를 수정하고, 논문의 핵심 가설인
시각 기반 viewpoint world model을 최소 형태로 실제 구현·평가한 결과입니다.
합성 proxy 한 장면의 12개 결정적 변형이므로 CVPR 성능 또는 독립 일반화
근거로 확대하면 안 됩니다.

## 실제로 완료한 것

- USD cutout shader에 `st` UV primvar reader를 연결했습니다.
- 780 px 초점거리를 USD의 mm 단위로 변환하고 1280x720 센서 종횡비를
  보존했습니다.
- bbox 좌표, 저장 영상 해상도, 전체 고정 class 집합, scene별 action grouping,
  oracle 동점 처리를 교정했습니다.
- 현재 RGB와 후보 카메라 행동만 입력하는 Visual Direct Ridge와
  Geometry + Visual Residual Ridge를 구현했습니다. 후보 결과 RGB는 입력으로
  쓰지 않았고, 한 scene variant 전체를 빼는 12-fold 평가를 사용했습니다.
- compact RGB 특징과 frozen detector 512차원 embedding을 각각 평가했습니다.

## 핵심 결과

### UV 및 기존 proxy 결과 감사

- UV on/off는 uav_01 전체 영상에서 {int(uv_example['changed_pixel_count']):,}개
  픽셀을 바꿨고 평균 절대 변화는
  {float(uv_example['mean_absolute_pixel_delta']):.6f}입니다.
- 하지만 confidence 0.01과 0.001에서 UV on/off 모두 TP=0입니다. 따라서
  UV 수정은 필수 렌더링 교정이지만 검출 개선으로 입증되지는 않았습니다.
- tie-aware oracle match는 Direct, Geometry, Residual 모두 7/12입니다.
  residual 평균 confidence {float(proxy_rows['GEOMETRY_STRUCTURED_RESIDUAL']['mean_selected_utility']):.6f}는
  균등 무작위 기대값 {float(proxy_rows['GEOMETRY_STRUCTURED_RESIDUAL']['mean_uniform_random_expected_utility']):.6f}보다 낮습니다.

### 균형 action GT 파일럿

| Method | Recall@0.5 | F1@0.5 | Recall regret | Mean movement (m) |
| --- | ---: | ---: | ---: | ---: |
| Geometry Ridge | {float(geometry['mean_selected_recall_at_iou50']):.6f} | {float(geometry['mean_selected_f1_at_iou50']):.6f} | {float(geometry['mean_recall_regret']):.6f} | {float(geometry['mean_movement_from_current_m']):.3f} |
| Visual Direct Ridge | {float(visual['mean_selected_recall_at_iou50']):.6f} | {float(visual['mean_selected_f1_at_iou50']):.6f} | {float(visual['mean_recall_regret']):.6f} | {float(visual['mean_movement_from_current_m']):.3f} |
| Geometry + Visual Residual | {float(residual['mean_selected_recall_at_iou50']):.6f} | {float(residual['mean_selected_f1_at_iou50']):.6f} | {float(residual['mean_recall_regret']):.6f} | {float(residual['mean_movement_from_current_m']):.3f} |
| Uniform random expectation | {float(random_expected['mean_selected_recall_at_iou50']):.6f} | {float(random_expected['mean_selected_f1_at_iou50']):.6f} | {float(random_expected['mean_recall_regret']):.6f} | {float(random_expected['mean_movement_from_current_m']):.3f} |
| GT oracle | {float(oracle['mean_selected_recall_at_iou50']):.6f} | {float(oracle['mean_selected_f1_at_iou50']):.6f} | 0.000000 | {float(oracle['mean_movement_from_current_m']):.3f} |

Visual Direct - Geometry의 Recall 차이는
{float(direct_boot['mean_recall_difference']):+.6f},
20,000회 paired bootstrap 95% CI
[{float(direct_boot['ci95_low']):+.6f}, {float(direct_boot['ci95_high']):+.6f}]입니다.
즉 시각 모델은 이 파일럿에서 geometry를 이기지 못했으며 채택하지 않습니다.

## 결론

렌더러와 GT 기반 평가, 실제 visual-model 코드 경로는 복구되었습니다.
그러나 현재 증거는 DOVE의 visual world model 우위를 뒷받침하지 않습니다.
Memory, discovery, closed-loop control도 아직 구현·제거 실험이 없습니다.
따라서 현 상태는 정직하게 `implementation-complete pilot, method claim not
validated`로 분류해야 합니다.

## 폴더

- `main/`: 핵심 표, 비용표, 논문 편집용 그림
- `supplementary/`: per-scene 예측, OOF 결과, bootstrap, 실패 자료
- `raw/`: capture manifest·USD·로그와 frozen embedding
- `code/`: 실행 코드·설정·테스트·Git 기록
- `status.csv`: 완료·부정 결과·미구현 상태
- `evidence_map.csv`: 각 주장과 근거 파일 및 금지할 주장
- `reproduction_commands.md`: 재현 명령
- `SHA256SUMS`: 패키지 무결성
"""
    (output / "README.md").write_text(readme, encoding="utf-8")

    checkpoint = embedding_summary["checkpoint"]
    commands = rf"""# Reproduction commands

Repository: `{ROOT}`
Branch: `{branch}`
Commit at packaging: `{head}`
GPU: NVIDIA RTX 5090; driver 580.65.06
Isaac image: `nvcr.io/nvidia/isaac-sim:5.1.0`
Detector checkpoint: `{checkpoint}`
Detector SHA256: `{embedding_summary['checkpoint_sha256']}`

## Balanced capture (GPU 0)

```bash
docker run --rm --gpus device=0 \
  --entrypoint /isaac-sim/python.sh \
  -v "$PWD:/workspace/dove" -w /workspace/dove \
  nvcr.io/nvidia/isaac-sim:5.1.0 \
  simulation/isaac/capture_marinecity_proxy.py \
  --config configs/sim/marinecity_visual_gt_balanced.yaml \
  --out-dir outputs/dove_wm/visual_gt_balanced_20261016 \
  --scene-variants 12 --scene-variant-strategy balanced \
  --connect-uv on --active-gpu 0
```

## Detector evaluation and current-RGB embedding (GPU 0)

```bash
CUDA_VISIBLE_DEVICES=0 /home/oem/anaconda3/envs/com3d-ace/bin/python \
  scripts/evaluate_dove_proxy_gt.py \
  --capture-dir outputs/dove_wm/visual_gt_balanced_20261016 \
  --checkpoint "{checkpoint}" \
  --output-dir outputs/dove_wm/visual_gt_balanced_eval_final_20261016 \
  --device 0 --imgsz 1280 --confidence 0.01 --iou-threshold 0.5 \
  --seed 20261016

CUDA_VISIBLE_DEVICES=0 /home/oem/anaconda3/envs/com3d-ace/bin/python \
  scripts/extract_dove_current_embeddings.py \
  --capture-dir outputs/dove_wm/visual_gt_balanced_20261016 \
  --checkpoint "{checkpoint}" \
  --output-dir outputs/dove_wm/visual_current_embeddings_balanced_20261016 \
  --current-uav-id uav_01 --device 0 --imgsz 1280
```

The first Ultralytics load attempted an automatic PyPI dependency install in
the conda environment. The project-local `detectors/__init__.py` now resolves
the checkpoint's custom module before similarly named third-party packages.

## World models, statistics, and figures

```bash
/home/oem/anaconda3/envs/com3d-ace/bin/python \
  scripts/evaluate_dove_visual_world_models.py \
  --capture-dir outputs/dove_wm/visual_gt_balanced_20261016 \
  --evaluation-dir outputs/dove_wm/visual_gt_balanced_eval_final_20261016 \
  --ridge-alpha 1.0 --bootstrap-repeats 20000 --seed 20261016 \
  --output-dir outputs/dove_wm/visual_world_model_balanced_final_r2_20261016

/home/oem/anaconda3/envs/com3d-ace/bin/python \
  scripts/evaluate_dove_visual_world_models.py \
  --capture-dir outputs/dove_wm/visual_gt_balanced_20261016 \
  --evaluation-dir outputs/dove_wm/visual_gt_balanced_eval_final_20261016 \
  --visual-embedding-csv outputs/dove_wm/visual_current_embeddings_balanced_20261016/current_visual_embeddings.csv \
  --visual-pca-components 8 --ridge-alpha 1.0 \
  --bootstrap-repeats 20000 --seed 20261016 \
  --output-dir outputs/dove_wm/visual_world_model_detector_embedding_final_r2_20261016

/home/oem/anaconda3/envs/com3d-ace/bin/python \
  scripts/render_dove_visual_model_audit.py \
  --summary-csv outputs/dove_wm/visual_world_model_detector_embedding_final_r2_20261016/model_summary.csv \
  --evaluation-dir outputs/dove_wm/visual_gt_balanced_eval_final_20261016 \
  --output-dir outputs/dove_wm/final_figures_final_r2_20261016

python -m unittest discover tests
```
"""
    (output / "reproduction_commands.md").write_text(commands, encoding="utf-8")
    source_paths = {
        "repository": str(ROOT),
        "uv_audit": str(uv),
        "balanced_capture": str(capture),
        "balanced_evaluation": str(evaluation),
        "compact_visual_model": str(compact),
        "detector_embeddings": str(embeddings),
        "detector_embedding_model": str(embedding_model),
        "figures": str(figures),
    }
    (output / "raw/source_paths.json").write_text(
        json.dumps(source_paths, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksum_rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            checksum_rows.append(f"{_sha256(path)}  {path.relative_to(output)}")
    (output / "SHA256SUMS").write_text(
        "\n".join(checksum_rows) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "COMPLETE",
                "output_dir": str(output),
                "file_count": len(checksum_rows) + 1,
                "git_head": head,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
