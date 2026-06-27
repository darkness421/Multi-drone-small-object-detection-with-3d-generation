# MarineCity Neural-3D Completion Result Table

Updated: `2026-06-27 17:15:53 KST`
Source CSV: `outputs/experiments/3d_generation_comparison.csv`
Verified rows: `2` / total rows `2`

Rows are admitted only when status is non-placeholder and PSNR, SSIM, and LPIPS are numeric.

| Method | PSNR | SSIM | LPIPS | FPS | Time min | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Nerfacto (torch smoke) | 22.73 | 0.938 | 0.072 | 0.59 | -- | complete_native_nerfacto_torch_split067_noapp_8k |
| 3D Gaussian Splatting | 19.68 | 0.807 | 0.170 | 4.56 | -- | complete_native_splatfacto_split067_5k |
