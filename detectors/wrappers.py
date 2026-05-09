"""Detector wrappers that produce EvidenceToken objects.

Heavy detector libraries are imported lazily so unit tests can run without GPU
or training dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from evidence import EvidenceToken, extract_crop, save_tokens_jsonl
from evidence.uncertainty import class_entropy, max_softmax_confidence, uncertainty_score


class DetectorWrapper:
    """Base interface for always-on detector front-ends."""

    def predict(self, image_path: str | Path, metadata: dict[str, Any] | None = None) -> list[EvidenceToken]:
        raise NotImplementedError


class UltralyticsWrapper(DetectorWrapper):
    """Wrapper for YOLOv8, YOLOv11, and Ultralytics RT-DETR models."""

    def __init__(self, model_name: str = "yolo11n.pt") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("Install ultralytics to use UltralyticsWrapper") from exc
            self._model = YOLO(self.model_name)
        return self._model

    def _pseudo_logits(self, class_id: int, confidence: float, num_classes: int) -> list[float]:
        num_classes = max(num_classes, class_id + 1, 1)
        base = max(1e-6, (1.0 - confidence) / max(num_classes - 1, 1))
        probs = [base for _ in range(num_classes)]
        probs[class_id] = max(confidence, 1e-6)
        return probs

    def predict(
        self,
        image_path: str | Path,
        metadata: dict[str, Any] | None = None,
        *,
        crop_dir: str | Path | None = None,
    ) -> list[EvidenceToken]:
        metadata = metadata or {}
        results = self.model(str(image_path), verbose=False)
        tokens: list[EvidenceToken] = []
        for result_index, result in enumerate(results):
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            names = getattr(result, "names", {}) or {}
            num_classes = len(names) if names else int(metadata.get("num_classes", 1))
            for det_index, box in enumerate(boxes):
                xyxy = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                logits = metadata.get("class_logits") or self._pseudo_logits(cls_id, conf, num_classes)
                x1, y1, x2, y2 = xyxy
                bbox = [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]
                token_id = f"{metadata.get('image_id', Path(image_path).stem)}:{result_index}:{det_index}"
                crop_path = None
                if crop_dir is not None:
                    crop_path = Path(crop_dir) / f"{token_id.replace(':', '_')}.jpg"
                    extract_crop(image_path, bbox, crop_path)
                token_metadata = {"crop_path": str(crop_path) if crop_path is not None else None, "image_path": str(Path(image_path).resolve())}
                if names and cls_id in names:
                    token_metadata["class_name"] = str(names[cls_id])
                tokens.append(
                    EvidenceToken(
                        token_id=token_id,
                        image_id=str(metadata.get("image_id", Path(image_path).stem)),
                        uav_id=str(metadata.get("uav_id", "uav_unknown")),
                        timestamp=float(metadata.get("timestamp", 0.0)),
                        bbox_2d=bbox,
                        class_logits=list(logits),
                        confidence=conf,
                        uncertainty=uncertainty_score(logits),
                        class_id=cls_id,
                        camera_intrinsic=metadata.get("camera_intrinsic", []),
                        camera_extrinsic=metadata.get("camera_extrinsic", []),
                        uav_pose=metadata.get("uav_pose", []),
                        depth_path=metadata.get("depth_path"),
                        camera_pose_path=metadata.get("camera_pose_path"),
                        metadata=token_metadata,
                    )
                )
        return tokens

    def infer_folder_to_jsonl(
        self,
        image_dir: str | Path,
        out_jsonl: str | Path,
        *,
        crop_dir: str | Path | None = None,
        patterns: tuple[str, ...] = ("*.jpg", "*.jpeg", "*.png", "*.bmp"),
    ) -> list[EvidenceToken]:
        image_dir = Path(image_dir)
        image_paths = sorted(path for pattern in patterns for path in image_dir.glob(pattern))
        tokens: list[EvidenceToken] = []
        for image_path in image_paths:
            tokens.extend(self.predict(image_path, {"image_id": image_path.stem}, crop_dir=crop_dir))
        save_tokens_jsonl(tokens, out_jsonl)
        return tokens


class YOLOv8Wrapper(UltralyticsWrapper):
    def __init__(self, model_name: str = "yolov8n.pt") -> None:
        super().__init__(model_name)


class YOLOv11Wrapper(UltralyticsWrapper):
    def __init__(self, model_name: str = "yolo11n.pt") -> None:
        super().__init__(model_name)


class RTDETRWrapper(UltralyticsWrapper):
    def __init__(self, model_name: str = "rtdetr-l.pt") -> None:
        super().__init__(model_name)


class DFINEWrapper(DetectorWrapper):
    """Placeholder D-FINE interface for later official-code integration."""

    def predict(self, image_path: str | Path, metadata: dict[str, Any] | None = None) -> list[EvidenceToken]:
        raise NotImplementedError("D-FINE wrapper requires the selected official implementation.")


class EvidenceGenerator:
    """Run a detector over frames and return evidence tokens."""

    def __init__(self, detector: DetectorWrapper) -> None:
        self.detector = detector

    def generate(self, frames: Iterable[dict[str, Any]]) -> list[EvidenceToken]:
        tokens: list[EvidenceToken] = []
        for frame in frames:
            tokens.extend(self.detector.predict(frame["image_path"], frame))
        return tokens
