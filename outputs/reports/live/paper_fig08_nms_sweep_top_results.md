# NMS Sweep Snapshot

Reference YOLOv11l mean: AP 0.3777, AP50 0.5981, P 0.6666, R 0.5881, F1 0.6248, Params 25.32M.
Strict pass threshold: AP >= 0.3833 and AP50 >= 0.6071.

| Rank | Method | NMS | AP | AP50 | P | R | F1 | Params | Delta AP | Strict pass |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | P2BalV2-FR-s42 | conf=0.001, iou=0.55, classaware | 0.3856 | 0.6119 | 0.6626 | 0.6013 | 0.6305 | 24.41M | +0.0080 | yes |
| 2 | P2BalV2-FR-s42 | conf=0.001, iou=0.65, classaware | 0.3849 | 0.6080 | 0.6690 | 0.5963 | 0.6306 | 24.41M | +0.0073 | yes |
| 3 | P2BalV2-FR-s42 | conf=0.001, iou=0.45, classaware | 0.3849 | 0.6118 | 0.6611 | 0.6032 | 0.6308 | 24.41M | +0.0073 | yes |
| 4 | P2BalV2-FR-s42 | conf=0.01, iou=0.55, classaware | 0.3839 | 0.6086 | 0.6626 | 0.6013 | 0.6305 | 24.41M | +0.0063 | yes |
| 5 | P2BalV2-FR-s42 | conf=0.01, iou=0.65, classaware | 0.3836 | 0.6056 | 0.6690 | 0.5963 | 0.6306 | 24.41M | +0.0060 | no |
| 6 | P2BalV2-FR-s42 | conf=0.01, iou=0.45, classaware | 0.3831 | 0.6080 | 0.6611 | 0.6032 | 0.6308 | 24.41M | +0.0055 | no |
| 7 | P2BalV2-FR-s42 | conf=0.001, iou=0.75, classaware | 0.3825 | 0.5990 | 0.6690 | 0.5900 | 0.6270 | 24.41M | +0.0049 | no |
| 8 | P2BalV2-FR-s42 | conf=0.01, iou=0.75, classaware | 0.3817 | 0.5979 | 0.6690 | 0.5900 | 0.6270 | 24.41M | +0.0041 | no |
