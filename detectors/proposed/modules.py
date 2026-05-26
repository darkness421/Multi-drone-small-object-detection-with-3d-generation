"""Runtime patches for proposed small-object detector ablations.

These modules are intentionally attached after loading an Ultralytics YOLO
checkpoint. That keeps the baseline weights usable while letting us compare
attention/stem/neck variants without editing the installed Ultralytics package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class ProposedModuleConfig:
    backbone: str = "yolo11s"
    wavelet_stem: bool = False
    se_neck: bool = False
    cbam_neck: bool = False
    partial_deformable_neck: bool = False
    tiling_inference: bool = False
    tile_size: int = 1024
    tile_overlap: float = 0.2


class HighFrequencyStem(nn.Module):
    """Small high-frequency residual pre-filter before the first YOLO conv."""

    def __init__(self, initial_gain: float = 0.15) -> None:
        super().__init__()
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        self.blur = nn.AvgPool2d(kernel_size=3, stride=1, padding=1, count_include_pad=False)

    def forward(self, x: Tensor) -> Tensor:
        high = x - self.blur(x)
        return x + torch.tanh(self.gain) * high


class SEBlock(nn.Module):
    """Squeeze-and-excitation block with residual gating for stable fine-tuning."""

    def __init__(self, channels: int, reduction: int = 16, initial_gain: float = 0.05) -> None:
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Conv2d(channels, hidden, 1, bias=True),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, channels, 1, bias=True),
            nn.Sigmoid(),
        )
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))

    def forward(self, x: Tensor) -> Tensor:
        gate = self.fc(self.pool(x))
        return x * (1.0 + torch.tanh(self.gain) * (gate - 0.5))


class CBAMBlock(nn.Module):
    """Convolutional block attention module with residual channel/spatial gates."""

    def __init__(self, channels: int, reduction: int = 16, spatial_kernel: int = 7, initial_gain: float = 0.05) -> None:
        super().__init__()
        hidden = max(channels // reduction, 8)
        padding = spatial_kernel // 2
        self.channel_mlp = nn.Sequential(
            nn.Conv2d(channels, hidden, 1, bias=False),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, channels, 1, bias=False),
        )
        self.spatial = nn.Conv2d(2, 1, spatial_kernel, padding=padding, bias=False)
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))

    def forward(self, x: Tensor) -> Tensor:
        avg_gate = self.channel_mlp(torch.mean(x, dim=(2, 3), keepdim=True))
        max_gate = self.channel_mlp(torch.amax(x, dim=(2, 3), keepdim=True))
        channel_gate = torch.sigmoid(avg_gate + max_gate)
        channel_refined = x * (1.0 + torch.tanh(self.gain) * (channel_gate - 0.5))
        spatial_input = torch.cat(
            [torch.mean(channel_refined, dim=1, keepdim=True), torch.amax(channel_refined, dim=1, keepdim=True)],
            dim=1,
        )
        spatial_gate = torch.sigmoid(self.spatial(spatial_input))
        return channel_refined * (1.0 + torch.tanh(self.gain) * (spatial_gate - 0.5))


class PartialDeformableRefine(nn.Module):
    """Partial-channel deformable refinement for YOLO neck features."""

    def __init__(self, channels: int, partial_ratio: float = 0.5, kernel_size: int = 3, initial_gain: float = 0.05) -> None:
        super().__init__()
        try:
            from torchvision.ops import DeformConv2d
        except Exception as exc:  # pragma: no cover - depends on torchvision build
            raise RuntimeError("torchvision.ops.DeformConv2d is required for partial_deformable_neck") from exc
        partial_channels = max(8, int(channels * partial_ratio))
        partial_channels = min(channels, partial_channels)
        padding = kernel_size // 2
        self.partial_channels = partial_channels
        self.offset = nn.Conv2d(partial_channels, 2 * kernel_size * kernel_size, kernel_size=3, padding=1)
        self.deform = DeformConv2d(partial_channels, partial_channels, kernel_size=kernel_size, padding=padding)
        self.fuse = nn.Conv2d(channels, channels, kernel_size=1)
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        nn.init.zeros_(self.offset.weight)
        nn.init.zeros_(self.offset.bias)
        nn.init.zeros_(self.fuse.weight)
        nn.init.zeros_(self.fuse.bias)

    def forward(self, x: Tensor) -> Tensor:
        x_part = x[:, : self.partial_channels]
        x_rest = x[:, self.partial_channels :]
        offset = self.offset(x_part)
        refined = self.deform(x_part, offset)
        merged = torch.cat([refined, x_rest], dim=1) if x_rest.numel() else refined
        return x + torch.tanh(self.gain) * self.fuse(merged)


class PatchedLayer(nn.Module):
    """Wrap an existing Ultralytics layer while preserving routing metadata."""

    def __init__(self, base: nn.Module, patch: nn.Module, label: str, mode: str = "post", out_channels: int | None = None) -> None:
        super().__init__()
        self.base = base
        self.patch = patch
        self.patch_label = label
        self.patch_mode = mode
        if out_channels is not None:
            self.out_channels = int(out_channels)
        for attr in ("i", "f", "type", "np"):
            if hasattr(base, attr):
                setattr(self, attr, getattr(base, attr))
        self.type = f"{getattr(base, 'type', type(base).__name__)}+{label}"
        self.np = sum(param.numel() for param in self.parameters())

    def forward(self, x: Any) -> Any:
        if self.patch_mode == "pre":
            return self.base(self.patch(x))
        return self.patch(self.base(x))


FALLBACK_NECK_LAYER_INDICES = (16, 19, 22)


def infer_out_channels(module: nn.Module) -> int:
    """Infer output channels from common Ultralytics modules."""

    if hasattr(module, "out_channels"):
        return int(getattr(module, "out_channels"))
    for attr_path in (("conv",), ("cv2", "conv"), ("cv3", "conv")):
        current: Any = module
        for attr in attr_path:
            current = getattr(current, attr, None)
            if current is None:
                break
        if isinstance(current, nn.Conv2d):
            return int(current.out_channels)
    convs = [child for child in module.modules() if isinstance(child, nn.Conv2d)]
    if convs:
        return int(convs[-1].out_channels)
    raise ValueError(f"Could not infer output channels for {type(module).__name__}")


def parse_patch_spec(spec: str | None) -> list[str]:
    if not spec:
        return []
    tokens: list[str] = []
    for chunk in spec.replace("+", ",").split(","):
        token = chunk.strip().lower().replace("-", "_")
        if token and token not in {"none", "control", "baseline"}:
            tokens.append(token)
    return tokens


def detect_neck_layer_indices(model: nn.Module) -> tuple[int, ...]:
    """Return the feature layers consumed by the Ultralytics detection head."""

    layers = getattr(model, "model", None)
    if layers is None:
        raise ValueError("Expected an Ultralytics DetectionModel with a .model layer list")
    for index in range(len(layers) - 1, -1, -1):
        layer = layers[index]
        layer_type = str(getattr(layer, "type", type(layer).__name__)).lower()
        if "detect" not in layer_type:
            continue
        from_indices = getattr(layer, "f", None)
        if isinstance(from_indices, (list, tuple)) and from_indices:
            return tuple(int(item) for item in from_indices)
    return FALLBACK_NECK_LAYER_INDICES


def wrap_neck(model: nn.Module, patch_name: str, patch_factory: Any) -> list[str]:
    applied: list[str] = []
    layers = getattr(model, "model", None)
    if layers is None:
        raise ValueError("Expected an Ultralytics DetectionModel with a .model layer list")
    for index in detect_neck_layer_indices(model):
        base = layers[index]
        channels = infer_out_channels(base)
        layers[index] = PatchedLayer(base, patch_factory(channels), patch_name, out_channels=channels)
        applied.append(f"{patch_name}@{index}:{channels}ch")
    return applied


def apply_proposed_patches(model: nn.Module, patch_spec: str | None) -> list[str]:
    """Attach proposed ablation modules to an Ultralytics DetectionModel."""

    patches = parse_patch_spec(patch_spec)
    if not patches:
        return []
    applied: list[str] = []
    layers = getattr(model, "model", None)
    if layers is None:
        raise ValueError("Expected an Ultralytics DetectionModel with a .model layer list")

    for patch in patches:
        if patch == "wavelet_stem":
            layers[0] = PatchedLayer(layers[0], HighFrequencyStem(), patch, mode="pre", out_channels=infer_out_channels(layers[0]))
            applied.append("wavelet_stem@0")
        elif patch == "se_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: SEBlock(channels)))
        elif patch == "cbam_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: CBAMBlock(channels)))
        elif patch == "partial_deformable_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: PartialDeformableRefine(channels)))
        else:
            raise ValueError(f"Unknown proposed model patch: {patch}")
    return applied
