import json
import tempfile
import unittest
from pathlib import Path

from dove_wm.proxy_gt import load_deduplicated_gt


class ProxyGroundTruthTests(unittest.TestCase):
    def test_mesh_and_cutout_components_are_merged_by_object_path(self) -> None:
        payload = {
            "data": [
                {"semanticId": 0, "x_min": 10, "y_min": 20, "x_max": 30, "y_max": 40},
                {"semanticId": 1, "x_min": 8, "y_min": 18, "x_max": 34, "y_max": 44},
                {"semanticId": 2, "x_min": 50, "y_min": 60, "x_max": 55, "y_max": 80},
            ],
            "info": {
                "bboxIds": [7, 12, 99],
                "idToLabels": {
                    "0": {"class": "sedan"},
                    "1": {"class": "car"},
                    "2": {"class": "worker"},
                },
                "primPaths": [
                    "/World/Objects/obj_0001_sedan",
                    "/World/CutoutOverlays/obj_0001_car/Plane",
                    "/World/Objects/obj_0008_worker",
                ],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bbox.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            rows = load_deduplicated_gt(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["object_id"], "obj_0001")
        self.assertEqual(rows[0]["canonical"], "car")
        self.assertEqual(rows[0]["xyxy"], [8.0, 18.0, 34.0, 44.0])
        self.assertEqual(rows[0]["component_count"], 2)
        self.assertEqual(rows[1]["object_id"], "obj_0008")
        self.assertEqual(rows[1]["canonical"], "pedestrian")


if __name__ == "__main__":
    unittest.main()
