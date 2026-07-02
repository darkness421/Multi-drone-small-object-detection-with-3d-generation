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
import torch.nn.functional as F


@dataclass(frozen=True)
class ProposedModuleConfig:
    backbone: str = "yolo11s"
    wavelet_stem: bool = False
    dct_stem: bool = False
    se_neck: bool = False
    cbam_neck: bool = False
    lite_self_attention_neck: bool = False
    dynfreq_c3_neck: bool = False
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


class DCTHighFrequencyStem(nn.Module):
    """Local DCT high-frequency residual stem for tiny-object texture cues."""

    def __init__(self, kernel_size: int = 3, initial_gain: float = 0.08) -> None:
        super().__init__()
        if kernel_size < 3:
            raise ValueError("DCTHighFrequencyStem requires kernel_size >= 3")
        filters = self._build_high_frequency_filters(kernel_size)
        self.register_buffer("filters", filters)
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))

    @staticmethod
    def _alpha(index: int, size: int) -> float:
        return (1.0 / size) ** 0.5 if index == 0 else (2.0 / size) ** 0.5

    @classmethod
    def _build_high_frequency_filters(cls, size: int) -> Tensor:
        coords = torch.arange(size, dtype=torch.float32)
        bases: list[Tensor] = []
        for u in range(size):
            for v in range(size):
                if u + v < size - 1:
                    continue
                basis_u = cls._alpha(u, size) * torch.cos(torch.pi * (2 * coords + 1) * u / (2 * size))
                basis_v = cls._alpha(v, size) * torch.cos(torch.pi * (2 * coords + 1) * v / (2 * size))
                basis = torch.outer(basis_u, basis_v)
                basis = basis - basis.mean()
                norm = basis.abs().sum().clamp_min(1e-6)
                bases.append(basis / norm)
        return torch.stack(bases, dim=0).unsqueeze(1)

    def forward(self, x: Tensor) -> Tensor:
        batch, channels, height, width = x.shape
        flat = x.reshape(batch * channels, 1, height, width)
        coeffs = F.conv2d(flat, self.filters.to(dtype=x.dtype), padding=self.filters.shape[-1] // 2)
        high = coeffs.mean(dim=1, keepdim=True).reshape(batch, channels, height, width)
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


class TinySpatialFReLU(nn.Module):
    """FReLU-style spatial activation with a tiny-object high-frequency condition.

    The activation keeps the FReLU mechanism of max(x, spatial_condition(x)), but
    adds a small learnable high-frequency residual to preserve weak edges and
    texture cues that are easy to erase for UAV tiny objects.
    """

    def __init__(self, channels: int, initial_edge_gain: float = 0.05) -> None:
        super().__init__()
        self.condition = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1, groups=channels, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.blur = nn.AvgPool2d(kernel_size=3, stride=1, padding=1, count_include_pad=False)
        self.edge_gain = nn.Parameter(torch.tensor(float(initial_edge_gain)))

    def forward(self, x: Tensor) -> Tensor:
        edge = x - self.blur(x)
        condition = self.condition(x) + torch.tanh(self.edge_gain) * edge
        return torch.maximum(x, condition)


class PooledTokenSelfAttention(nn.Module):
    """Compact pooled-token self-attention for detection neck features.

    This borrows the global-context mechanism from ViT/DINO-style feature mixing
    without importing a large transformer backbone. Attention is computed on a
    small pooled grid, then upsampled as a residual context map.
    """

    def __init__(self, channels: int, token_size: int = 8, reduction: int = 8, initial_gain: float = 0.05) -> None:
        super().__init__()
        hidden = max(16, min(channels // reduction, 64))
        self.pool = nn.AdaptiveAvgPool2d((token_size, token_size))
        self.q = nn.Conv2d(channels, hidden, 1, bias=False)
        self.k = nn.Conv2d(channels, hidden, 1, bias=False)
        self.v = nn.Conv2d(channels, hidden, 1, bias=False)
        self.proj = nn.Conv2d(hidden, channels, 1, bias=False)
        self.scale = hidden**-0.5
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))

    def forward(self, x: Tensor) -> Tensor:
        pooled = self.pool(x)
        batch, _, token_h, token_w = pooled.shape
        q = self.q(pooled).flatten(2).transpose(1, 2)
        k = self.k(pooled).flatten(2)
        v = self.v(pooled).flatten(2).transpose(1, 2)
        attn = torch.softmax((q @ k) * self.scale, dim=-1)
        context = (attn @ v).transpose(1, 2).reshape(batch, -1, token_h, token_w)
        context = self.proj(context)
        context = F.interpolate(context, size=x.shape[-2:], mode="bilinear", align_corners=False)
        return x + torch.tanh(self.gain) * context


class DynFreqC3Refine(nn.Module):
    """Dynamic frequency refinement for C3/C3k2 neck features.

    The module splits a feature map into low- and high-frequency residuals,
    predicts channel-wise frequency gates from the current C3 output, and adds a
    small residual correction. It is intentionally lightweight so P2/P3 tiny
    object heads can receive frequency-aware refinement without exceeding the
    YOLOv11l parameter budget.
    """

    def __init__(self, channels: int, reduction: int = 32, initial_gain: float = 0.04) -> None:
        super().__init__()
        hidden = max(8, min(channels // reduction, 32))
        self.blur = nn.AvgPool2d(kernel_size=3, stride=1, padding=1, count_include_pad=False)
        self.high_filter = nn.Conv2d(channels, channels, kernel_size=3, padding=1, groups=channels, bias=False)
        self.low_filter = nn.Conv2d(channels, channels, kernel_size=3, padding=1, groups=channels, bias=False)
        self.gate = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels, hidden, kernel_size=1, bias=True),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, channels * 2, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        self._init_depthwise_identity()

    def _init_depthwise_identity(self) -> None:
        nn.init.zeros_(self.high_filter.weight)
        nn.init.zeros_(self.low_filter.weight)
        center = self.high_filter.weight.shape[-1] // 2
        with torch.no_grad():
            self.high_filter.weight[:, 0, center, center] = 1.0
            self.low_filter.weight[:, 0, center, center] = 1.0

    def forward(self, x: Tensor) -> Tensor:
        low = self.blur(x)
        high = x - low
        high_gate, low_gate = self.gate(x).chunk(2, dim=1)
        high_residual = high_gate * self.high_filter(high)
        low_residual = low_gate * (self.low_filter(low) - x)
        return x + torch.tanh(self.gain) * (high_residual + low_residual)


class DilatedRFRefine(nn.Module):
    """Lightweight receptive-field expansion for high-resolution neck features.

    This keeps the selected SelfAttnFR design intact while adding a small
    dilated-depthwise residual on the highest-resolution neck outputs. The
    branch is initialized near identity, so it can learn broader local context
    without immediately disturbing the pretrained detector.
    """

    def __init__(self, channels: int, reduction: int = 64, initial_gain: float = 0.03) -> None:
        super().__init__()
        hidden = max(8, min(channels // reduction, 24))
        self.dilated_2 = nn.Conv2d(channels, channels, kernel_size=3, padding=2, dilation=2, groups=channels, bias=False)
        self.dilated_3 = nn.Conv2d(channels, channels, kernel_size=3, padding=3, dilation=3, groups=channels, bias=False)
        self.gate = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels, hidden, kernel_size=1, bias=True),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, channels * 2, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        self._init_depthwise_identity()

    def _init_depthwise_identity(self) -> None:
        nn.init.zeros_(self.dilated_2.weight)
        nn.init.zeros_(self.dilated_3.weight)
        center = self.dilated_2.weight.shape[-1] // 2
        with torch.no_grad():
            self.dilated_2.weight[:, 0, center, center] = 1.0
            self.dilated_3.weight[:, 0, center, center] = 1.0

    def forward(self, x: Tensor) -> Tensor:
        gate_2, gate_3 = self.gate(x).chunk(2, dim=1)
        residual = gate_2 * (self.dilated_2(x) - x) + gate_3 * (self.dilated_3(x) - x)
        return x + torch.tanh(self.gain) * residual


class SimAMRefine(nn.Module):
    """Parameter-free SimAM-style attention used for YOLO11s-UAV module reproduction."""

    def __init__(self, channels: int | None = None, e_lambda: float = 1e-4, initial_gain: float = 0.05) -> None:
        super().__init__()
        self.e_lambda = float(e_lambda)
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))

    def forward(self, x: Tensor) -> Tensor:
        _, _, height, width = x.shape
        spatial_count = max(height * width - 1, 1)
        centered = (x - x.mean(dim=(2, 3), keepdim=True)).pow(2)
        energy = centered / (4 * (centered.sum(dim=(2, 3), keepdim=True) / spatial_count + self.e_lambda)) + 0.5
        attended = x * torch.sigmoid(energy)
        return x + torch.tanh(self.gain) * (attended - x)


class DWRRefine(nn.Module):
    """Shape-preserving DWR branch from YOLO11s-UAV's S2DResConv public module.

    The released S2DResConv block performs space-to-depth downsampling, which
    cannot be inserted post-neck without changing detection-head resolution.
    For a fair module-level reproduction, we reuse its multi-dilation DWR
    refinement while preserving feature-map shape.
    """

    def __init__(self, channels: int, initial_gain: float = 0.04) -> None:
        super().__init__()
        half = max(channels // 2, 8)
        self.reduce = nn.Conv2d(channels, half, kernel_size=3, padding=1, bias=False)
        self.bn_reduce = nn.BatchNorm2d(half)
        self.d1 = nn.Conv2d(half, channels, kernel_size=3, padding=1, dilation=1, bias=False)
        self.d3 = nn.Conv2d(half, half, kernel_size=3, padding=3, dilation=3, bias=False)
        self.d5 = nn.Conv2d(half, half, kernel_size=3, padding=5, dilation=5, bias=False)
        self.fuse = nn.Conv2d(channels * 2, channels, kernel_size=1, bias=False)
        self.bn_out = nn.BatchNorm2d(channels)
        self.act = nn.GELU()
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        nn.init.zeros_(self.fuse.weight)

    def forward(self, x: Tensor) -> Tensor:
        reduced = F.silu(self.bn_reduce(self.reduce(x)))
        mixed = torch.cat([self.d1(reduced), self.d3(reduced), self.d5(reduced)], dim=1)
        refined = self.act(self.bn_out(self.fuse(mixed)))
        return x + torch.tanh(self.gain) * refined


class LightweightSSMContextRefine(nn.Module):
    """Lightweight state-space-style context refinement for UAVDet reproduction.

    This is a paper-facing fallback when the official MMDetection/UAVDet stack
    is unavailable. It preserves the YOLO feature shape while adding directional
    long-range context over rows and columns, loosely matching the CNN-Mamba
    motivation without claiming to be the official UAVDet implementation.
    """

    def __init__(self, channels: int, reduction: int = 64, initial_gain: float = 0.03) -> None:
        super().__init__()
        hidden = max(8, min(channels // reduction, 32))
        self.local = nn.Conv2d(channels, channels, kernel_size=3, padding=1, groups=channels, bias=False)
        self.mix = nn.Conv2d(channels * 3, channels, kernel_size=1, bias=False)
        self.gate = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels, hidden, kernel_size=1, bias=True),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, channels, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )
        self.gain = nn.Parameter(torch.tensor(float(initial_gain)))
        nn.init.zeros_(self.mix.weight)
        self._init_depthwise_identity()

    def _init_depthwise_identity(self) -> None:
        nn.init.zeros_(self.local.weight)
        center = self.local.weight.shape[-1] // 2
        with torch.no_grad():
            self.local.weight[:, 0, center, center] = 1.0

    @staticmethod
    def _causal_average(x: Tensor, dim: int) -> Tensor:
        length = x.shape[dim]
        denom_shape = [1] * x.ndim
        denom_shape[dim] = length
        denom = torch.arange(1, length + 1, device=x.device, dtype=x.dtype).reshape(denom_shape)
        return torch.cumsum(x, dim=dim) / denom

    def forward(self, x: Tensor) -> Tensor:
        local = self.local(x)
        row_context = self._causal_average(x, dim=3)
        col_context = self._causal_average(x, dim=2)
        mixed = self.mix(torch.cat([local, row_context, col_context], dim=1))
        gate = self.gate(x)
        return x + torch.tanh(self.gain) * gate * (mixed - x)


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
    return wrap_neck_indices(model, detect_neck_layer_indices(model), patch_name, patch_factory)


def wrap_neck_indices(model: nn.Module, indices: tuple[int, ...], patch_name: str, patch_factory: Any) -> list[str]:
    applied: list[str] = []
    layers = getattr(model, "model", None)
    if layers is None:
        raise ValueError("Expected an Ultralytics DetectionModel with a .model layer list")
    for index in indices:
        base = layers[index]
        channels = infer_out_channels(base)
        layers[index] = PatchedLayer(base, patch_factory(channels), patch_name, out_channels=channels)
        applied.append(f"{patch_name}@{index}:{channels}ch")
    return applied


def select_high_resolution_neck_indices(model: nn.Module, limit: int) -> tuple[int, ...]:
    indices = detect_neck_layer_indices(model)
    return tuple(indices[: max(1, min(limit, len(indices)))])


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
        elif patch == "dct_stem":
            layers[0] = PatchedLayer(layers[0], DCTHighFrequencyStem(), patch, mode="pre", out_channels=infer_out_channels(layers[0]))
            applied.append("dct_stem@0")
        elif patch == "se_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: SEBlock(channels)))
        elif patch == "cbam_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: CBAMBlock(channels)))
        elif patch in {"lite_self_attention_neck", "self_attention_neck", "dino_context_neck"}:
            applied.extend(wrap_neck(model, patch, lambda channels: PooledTokenSelfAttention(channels)))
        elif patch == "dynfreq_c3_p2":
            indices = select_high_resolution_neck_indices(model, limit=1)
            applied.extend(wrap_neck_indices(model, indices, patch, lambda channels: DynFreqC3Refine(channels)))
        elif patch == "dynfreq_c3_small":
            indices = select_high_resolution_neck_indices(model, limit=2)
            applied.extend(wrap_neck_indices(model, indices, patch, lambda channels: DynFreqC3Refine(channels)))
        elif patch == "dynfreq_c3_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: DynFreqC3Refine(channels)))
        elif patch in {"rf_context_neck", "dilated_rf_neck"}:
            indices = select_high_resolution_neck_indices(model, limit=2)
            applied.extend(wrap_neck_indices(model, indices, patch, lambda channels: DilatedRFRefine(channels)))
        elif patch in {"simam_neck", "flexsimam_neck", "yolo11suav_simam_neck"}:
            applied.extend(wrap_neck(model, patch, lambda channels: SimAMRefine(channels)))
        elif patch in {"dwr_neck", "s2dresconv_repro_neck", "yolo11suav_dwr_neck"}:
            applied.extend(wrap_neck(model, patch, lambda channels: DWRRefine(channels)))
        elif patch in {"ssm_context_neck", "mamba_context_neck", "uavdet_mamba_neck"}:
            applied.extend(wrap_neck(model, patch, lambda channels: LightweightSSMContextRefine(channels)))
        elif patch in {"frelu_neck", "tiny_frelu_neck"}:
            applied.extend(wrap_neck(model, patch, lambda channels: TinySpatialFReLU(channels)))
        elif patch == "partial_deformable_neck":
            applied.extend(wrap_neck(model, patch, lambda channels: PartialDeformableRefine(channels)))
        else:
            raise ValueError(f"Unknown proposed model patch: {patch}")
    return applied
