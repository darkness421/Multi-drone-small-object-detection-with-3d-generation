# Ours vs Comparison Gate

Generated: `2026-06-26T03:31:28+09:00`
Status: `overwhelmed`
Section: `main_1280_completed_3seed`

| Role | Method | AP | AP50 | F1 | Params(M) | Seeds |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Ours | Ours: P2P4-SelfAttnFR | 0.3822 | 0.6052 | 0.6273 | 20.82 | 42,123,2026 |
| Best overall comparison by AP | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55 | 42,123,2026 |
| Best overall comparison by AP50 | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55 | 42,123,2026 |
| Best overall comparison by F1 | YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 25.32 | 123,2026,42 |
| Best cited related work by AP | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55 | 42,123,2026 |
| Best cited related work by AP50 | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55 | 42,123,2026 |
| Best cited related work by F1 | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55 | 42,123,2026 |

## Deltas

- Vs best overall comparison per metric: AP `0.0010`, AP50 `0.0047`, F1 `0.0025`, Params vs best-AP model `-12.73M`.
- Vs best cited related work per metric: AP `0.0010`, AP50 `0.0047`, F1 `0.0069`, Params vs best-AP related model `-12.73M`.

## Checks

- `beats_best_overall_AP`: `True`
- `beats_best_overall_AP50`: `True`
- `beats_best_overall_F1`: `True`
- `beats_best_related_AP`: `True`
- `beats_best_related_AP50`: `True`
- `beats_best_related_F1`: `True`
