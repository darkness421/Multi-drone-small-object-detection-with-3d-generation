# MarineCity Neural-3D Completion Result Table

Updated: `2026-06-28 07:54:46 KST`
Source CSV: `outputs/experiments/3d_generation_comparison.csv`
Verified rows: `3` / total rows `3`

Rows are admitted only when status is non-placeholder and PSNR, SSIM, and LPIPS are numeric.

| Method | PSNR | SSIM | LPIPS | FPS | Time min | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Instant-NGP | 21.62 | 0.897 | 0.117 | 0.28 | -- | complete_native_instant_ngp_split067_5k |
| 3D Gaussian Splatting | 19.68 | 0.807 | 0.170 | 4.56 | -- | complete_native_splatfacto_split067_5k |
| Nerfacto (torch smoke) | 10.56 | 0.382 | 0.557 | 0.63 | -- | complete_native_marinecity_nerfacto_torch_split067_noapp_48k |
