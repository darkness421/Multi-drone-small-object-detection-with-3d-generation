"""Baseline B2 shared-encoder scaffold without proposed V2 modules.

The module deliberately contains only a visual encoder, deterministic oriented
box head, class/objectness heads, and an identity embedding head. It has no
uncertainty model, temporal aggregation, ego-motion compensation, rollout,
reversible assignment, memory, or adaptive-compute path.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass
class B2Outputs:
    objectness_logits: Tensor
    class_logits: Tensor
    box_state: Tensor
    identity_embeddings: Tensor


@dataclass
class B2Targets:
    objectness: Tensor
    class_ids: Tensor
    box_state: Tensor
    identity_ids: Tensor


class ConvBlock(nn.Sequential):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1) -> None:
        super().__init__(
            nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True),
        )


class B2Scaffold(nn.Module):
    """Small deterministic OBB detector with a shared identity feature map.

    Input shape is ``[batch, time, channels, height, width]``. The six box
    channels are normalized ``cx, cy, w, h, sin(2 theta), cos(2 theta)``.
    Doubling the angle represents the 180-degree symmetry of an oriented box
    without introducing an uncertainty distribution.
    """

    def __init__(self, num_classes: int = 8, embedding_dim: int = 32) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.embedding_dim = embedding_dim
        self.encoder = nn.Sequential(
            ConvBlock(3, 24, stride=2),
            ConvBlock(24, 32, stride=2),
            ConvBlock(32, 64, stride=2),
            ConvBlock(64, 64),
        )
        self.objectness_head = nn.Conv2d(64, 1, 1)
        self.class_head = nn.Conv2d(64, num_classes, 1)
        self.box_head = nn.Conv2d(64, 6, 1)
        self.identity_head = nn.Conv2d(64, embedding_dim, 1)

    def forward(self, frames: Tensor) -> B2Outputs:
        if frames.ndim != 5:
            raise ValueError(f"expected [B,T,C,H,W], received {tuple(frames.shape)}")
        batch, time, channels, height, width = frames.shape
        features = self.encoder(frames.reshape(batch * time, channels, height, width))
        grid_h, grid_w = features.shape[-2:]

        def restore(value: Tensor) -> Tensor:
            return value.reshape(batch, time, value.shape[1], grid_h, grid_w)

        raw_box = restore(self.box_head(features))
        xywh = raw_box[:, :, :4].sigmoid()
        angle = F.normalize(raw_box[:, :, 4:6], dim=2, eps=1e-6)
        embeddings = F.normalize(restore(self.identity_head(features)), dim=2, eps=1e-6)
        return B2Outputs(
            objectness_logits=restore(self.objectness_head(features)),
            class_logits=restore(self.class_head(features)),
            box_state=torch.cat((xywh, angle), dim=2),
            identity_embeddings=embeddings,
        )


def _identity_loss(embeddings: Tensor, identity_ids: Tensor, positive_mask: Tensor) -> Tensor:
    vectors = embeddings.permute(0, 1, 3, 4, 2)[positive_mask]
    ids = identity_ids[positive_mask]
    if vectors.shape[0] < 2:
        return vectors.sum() * 0.0
    similarity = vectors @ vectors.T
    upper = torch.triu(torch.ones_like(similarity, dtype=torch.bool), diagonal=1)
    same = ids[:, None].eq(ids[None, :]) & upper
    different = ids[:, None].ne(ids[None, :]) & upper
    terms = []
    if same.any():
        terms.append((1.0 - similarity[same]).mean())
    if different.any():
        terms.append(F.relu(similarity[different] - 0.2).mean())
    return sum(terms) if terms else vectors.sum() * 0.0


def compute_b2_loss(outputs: B2Outputs, targets: B2Targets) -> dict[str, Tensor]:
    positive = targets.objectness.squeeze(2).bool()
    objectness = F.binary_cross_entropy_with_logits(outputs.objectness_logits, targets.objectness)
    class_map = outputs.class_logits.permute(0, 1, 3, 4, 2)
    box_map = outputs.box_state.permute(0, 1, 3, 4, 2)
    if positive.any():
        classification = F.cross_entropy(class_map[positive], targets.class_ids[positive])
        box = F.smooth_l1_loss(box_map[positive], targets.box_state[positive])
    else:
        classification = class_map.sum() * 0.0
        box = box_map.sum() * 0.0
    identity = _identity_loss(outputs.identity_embeddings, targets.identity_ids, positive)
    total = objectness + classification + 5.0 * box + 0.25 * identity
    return {
        "total": total,
        "objectness": objectness,
        "classification": classification,
        "box": box,
        "identity": identity,
    }
