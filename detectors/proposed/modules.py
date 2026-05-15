"""Skeleton modules for proposed lightweight small-object perception.

The production implementation will plug these ideas into the selected YOLO11n
or YOLO11s baseline after the server baseline sweep identifies the comparison
targets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposedModuleConfig:
    backbone: str = "yolo11n"
    wavelet_stem: bool = False
    partial_deformable_neck: bool = False
    tiling_inference: bool = False
    tile_size: int = 1024
    tile_overlap: float = 0.2


class WaveletStemPlaceholder:
    """Placeholder for a future wavelet-aware input stem."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled


class PartialDeformableNeckPlaceholder:
    """Placeholder for partial deformable convolution blocks in the neck."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled


class TilingInferencePlaceholder:
    """Configuration holder for patch/tiling inference experiments."""

    def __init__(self, tile_size: int = 1024, overlap: float = 0.2) -> None:
        self.tile_size = tile_size
        self.overlap = overlap
