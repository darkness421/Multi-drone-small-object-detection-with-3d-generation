"""Registry for Marine City 3D generative reconstruction baselines."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """A comparable 3D reconstruction / novel-view synthesis method."""

    key: str
    display_name: str
    family: str
    representation: str
    expected_strengths: list[str]
    expected_weaknesses: list[str]
    default_train_command: str
    default_render_command: str
    metrics: list[str] = field(default_factory=lambda: ["PSNR", "SSIM", "LPIPS", "FPS", "train_time_min", "VRAM_GB"])
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_model_specs() -> list[ModelSpec]:
    """Return the 4-method comparison set for the Marine City benchmark."""

    return [
        ModelSpec(
            key="nerf",
            display_name="NeRF",
            family="radiance_field",
            representation="MLP continuous 5D radiance field with volume rendering",
            expected_strengths=["canonical quality baseline", "clean conceptual comparison"],
            expected_weaknesses=["slow training", "slow rendering", "hard to scale to large outdoor scenes"],
            default_train_command="ns-train nerfacto --data {data}",
            default_render_command="ns-render camera-path --load-config {checkpoint} --output-path {scene}_nerf_renders",
            notes="Use as the classic reference baseline, not as the expected fastest method.",
        ),
        ModelSpec(
            key="instant_ngp",
            display_name="Instant-NGP",
            family="hash_encoded_radiance_field",
            representation="multiresolution hash-grid encoding with compact neural field",
            expected_strengths=["very fast convergence", "practical single-scene iteration"],
            expected_weaknesses=["CUDA/tiny-cuda-nn dependency", "quality can vary with camera coverage"],
            default_train_command="<instant-ngp-upstream-train> --scene {scene} --data {data}",
            default_render_command="<instant-ngp-upstream-render> --checkpoint {checkpoint}",
            notes="Good speed/quality baseline for iterative Marine City scene capture.",
        ),
        ModelSpec(
            key="mip_nerf_360",
            display_name="Mip-NeRF 360",
            family="anti_aliased_radiance_field",
            representation="anti-aliased unbounded-scene radiance field",
            expected_strengths=["outdoor/unbounded-scene quality", "strong novel-view synthesis reference"],
            expected_weaknesses=["high compute cost", "not real-time", "heavier implementation"],
            default_train_command="<mip-nerf-360-upstream-train> --scene {scene} --data {data}",
            default_render_command="<mip-nerf-360-upstream-render> --checkpoint {checkpoint}",
            notes="Use when Marine City viewpoints include wide outdoor trajectories.",
        ),
        ModelSpec(
            key="gaussian_splatting",
            display_name="3D Gaussian Splatting",
            family="explicit_splatting",
            representation="optimized anisotropic 3D Gaussians with visibility-aware splat rendering",
            expected_strengths=["real-time rendering", "strong visual quality", "fast interactive inspection"],
            expected_weaknesses=["memory footprint", "floaters under sparse views", "less natural uncertainty output"],
            default_train_command="<3dgs-upstream-train> --scene {scene} --source_path {data}",
            default_render_command="<3dgs-upstream-render> --model_path {checkpoint}",
            notes="Likely best qualitative renderer for same-scene visual inspection.",
        ),
    ]


def specs_by_key() -> dict[str, ModelSpec]:
    return {spec.key: spec for spec in default_model_specs()}
