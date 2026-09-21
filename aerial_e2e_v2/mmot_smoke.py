"""MMOT frame and annotation helpers for infrastructure smoke tests."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import Tensor

from .b2_scaffold import B2Targets


@dataclass(frozen=True)
class OrientedObject:
    frame: int
    identity: int
    class_id: int
    points: np.ndarray


def parse_annotation(path: Path) -> list[OrientedObject]:
    objects = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split(",")
        if len(fields) != 13:
            raise ValueError(f"expected 13 MMOT fields in {path}, received {len(fields)}")
        values = [float(value) for value in fields]
        objects.append(
            OrientedObject(
                frame=int(values[0]),
                identity=int(values[1]),
                points=np.asarray(values[2:10], dtype=np.float32).reshape(4, 2),
                class_id=int(values[11]),
            )
        )
    return objects


def canonical_long_axis(points: np.ndarray) -> tuple[float, float, float, float, float]:
    """Return center, long/short side, and long-axis angle modulo pi."""
    center = points.mean(axis=0)
    edges = np.roll(points, -1, axis=0) - points
    lengths = np.linalg.norm(edges, axis=1)
    longest = int(np.argmax(lengths))
    width = float(lengths[longest])
    height = float(lengths[(longest + 1) % 4])
    vector = edges[longest]
    theta = math.atan2(float(vector[1]), float(vector[0]))
    theta = (theta + math.pi / 2.0) % math.pi - math.pi / 2.0
    return float(center[0]), float(center[1]), width, height, theta


def load_sequence_pair(sequence_dir: Path, image_size: int) -> tuple[Tensor, list[list[OrientedObject]], list[str]]:
    frame_paths = sorted(sequence_dir.glob("*.npy"))
    selected = []
    for frame_path in frame_paths:
        label_path = frame_path.with_suffix(".txt")
        if label_path.exists() and parse_annotation(label_path):
            selected.append((frame_path, label_path))
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise RuntimeError(f"could not find two labeled frames in {sequence_dir}")

    images, labels, names = [], [], []
    for frame_path, label_path in selected:
        array = np.load(frame_path, mmap_mode="r")
        if array.ndim != 3 or array.shape[2] < 5:
            raise ValueError(f"unsupported MMOT image shape: {array.shape}")
        bgr = np.ascontiguousarray(array[:, :, [1, 2, 4]])
        resized = cv2.resize(bgr, (image_size, image_size), interpolation=cv2.INTER_AREA)
        rgb = resized[:, :, ::-1].copy()
        images.append(torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0)
        labels.append(parse_annotation(label_path))
        names.append(frame_path.name)
    return torch.stack(images).unsqueeze(0), labels, names


def build_dense_targets(
    labels: list[list[OrientedObject]],
    original_size: tuple[int, int],
    grid_size: tuple[int, int],
    num_classes: int,
) -> B2Targets:
    original_h, original_w = original_size
    grid_h, grid_w = grid_size
    objectness = torch.zeros((1, len(labels), 1, grid_h, grid_w), dtype=torch.float32)
    class_ids = torch.full((1, len(labels), grid_h, grid_w), -1, dtype=torch.long)
    box_state = torch.zeros((1, len(labels), grid_h, grid_w, 6), dtype=torch.float32)
    identity_ids = torch.full((1, len(labels), grid_h, grid_w), -1, dtype=torch.long)
    occupied_area = torch.zeros((len(labels), grid_h, grid_w), dtype=torch.float32)

    for time, frame_objects in enumerate(labels):
        for item in frame_objects:
            cx, cy, width, height, theta = canonical_long_axis(item.points)
            gx = min(grid_w - 1, max(0, int(cx / original_w * grid_w)))
            gy = min(grid_h - 1, max(0, int(cy / original_h * grid_h)))
            area = width * height
            if area <= float(occupied_area[time, gy, gx]):
                continue
            occupied_area[time, gy, gx] = area
            objectness[0, time, 0, gy, gx] = 1.0
            class_ids[0, time, gy, gx] = min(max(item.class_id, 0), num_classes - 1)
            identity_ids[0, time, gy, gx] = item.identity
            box_state[0, time, gy, gx] = torch.tensor(
                [
                    cx / original_w,
                    cy / original_h,
                    width / original_w,
                    height / original_h,
                    math.sin(2.0 * theta),
                    math.cos(2.0 * theta),
                ],
                dtype=torch.float32,
            )
    return B2Targets(objectness, class_ids, box_state, identity_ids)
