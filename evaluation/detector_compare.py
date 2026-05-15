"""2D detector comparison table helpers."""

from __future__ import annotations


DETECTOR_METHODS = [
    "YOLOv8n",
    "YOLOv11n",
    "YOLOv8n+P2",
    "RT-DETR-R18",
    "D-FINE-S",
    "UAVDet or LRDS-YOLO",
    "Ours AEG",
]


DETECTOR_COLUMNS = [
    "Method",
    "Dataset",
    "AP",
    "AP50",
    "AP75",
    "APsmall",
    "ROC-AUC",
    "FPS",
    "Params",
    "GFLOPs",
]


def empty_detector_table(datasets: list[str] | None = None) -> list[dict[str, str]]:
    """Return an empty 2D detector comparison table template."""

    datasets = datasets or ["VisDrone2019-DET", "UAVDT"]
    return [
        {
            "Method": method,
            "Dataset": dataset,
            "AP": "",
            "AP50": "",
            "AP75": "",
            "APsmall": "",
            "ROC-AUC": "",
            "FPS": "",
            "Params": "",
            "GFLOPs": "",
        }
        for dataset in datasets
        for method in DETECTOR_METHODS
    ]
