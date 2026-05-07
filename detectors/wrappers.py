"""Detector wrappers that produce EvidenceToken objects.

Heavy detector libraries are imported lazily so unit tests can run without GPU
or training dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from evidence import EvidenceToken
from evidence.uncertainty import class_entropy, max_softmax_confidence


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

    def predict(self, image_path: str | Path, metadata: dict[str, Any] | None = None) -> list[EvidenceToken]:
        metadata = metadata or {}
        results = self.model(str(image_path), verbose=False)
        tokens: list[EvidenceToken] = []
        for result_index, result in enumerate(results):
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for det_index, box in enumerate(boxes):
                xyxy = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                logits = metadata.get("class_logits") or [conf]
                x1, y1, x2, y2 = xyxy
                tokens.append(
                    EvidenceToken(
                        token_id=f"{metadata.get('image_id', Path(image_path).stem)}:{result_index}:{det_index}",
                        image_id=str(metadata.get("image_id", Path(image_path).stem)),
                        uav_id=str(metadata.get("uav_id", "uav_unknown")),
                        timestamp=float(metadata.get("timestamp", 0.0)),
                        bbox_2d=[float(x1), float(y1), float(x2 - x1), float(y2 - y1)],
                        class_logits=list(logits),
                        confidence=conf,
                        uncertainty=class_entropy(logits),
                        class_id=cls_id,
                        camera_intrinsic=metadata.get("camera_intrinsic", []),
                        camera_extrinsic=metadata.get("camera_extrinsic", []),
                        uav_pose=metadata.get("uav_pose", []),
                        depth_path=metadata.get("depth_path"),
                        camera_pose_path=metadata.get("camera_pose_path"),
                    )
                )
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

