# Table D.16 absolute results by tracker

IDF1 and AssA are equal-sequence means; IDSW is summed over the listed sequences. Deltas in parentheses are versus None, except H+V and P-G+V, whose second delta is versus their parent linker.

## M3OT / development / oracle-box tracker output; direct tracker-box BaseReID crops

Sequences (4): `M3OT/1/ir/val/1-08T;M3OT/1/rgb/val/1-08;M3OT/2/ir/val/2-08T;M3OT/2/rgb/val/2-08`

| Tracker | Method | IDF1 | AssA | IDSW | Delta IDF1 vs None | Delta IDF1 vs parent | Delta IDSW vs None | Delta IDSW vs parent |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bytetrack | None | 96.885 | 92.280 | 20 | +0.000 | +0.000 | +0 | +0 |
| bytetrack | v1 | 98.502 | 93.962 | 9 | +1.617 | +1.617 | -11 | -11 |
| bytetrack | H | 98.623 | 94.200 | 5 | +1.738 | +1.738 | -15 | -15 |
| bytetrack | H+V | 98.807 | 94.379 | 9 | +1.922 | +0.184 | -11 | +4 |
| bytetrack | P-G | 98.502 | 93.931 | 9 | +1.617 | +1.617 | -11 | -11 |
| bytetrack | P-G+V | 98.807 | 94.379 | 9 | +1.922 | +0.305 | -11 | +0 |
| ocsort | None | 96.097 | 94.548 | 21 | +0.000 | +0.000 | +0 | +0 |
| ocsort | v1 | 98.260 | 96.976 | 9 | +2.163 | +2.163 | -12 | -12 |
| ocsort | H | 98.326 | 97.102 | 6 | +2.228 | +2.228 | -15 | -15 |
| ocsort | H+V | 98.276 | 97.006 | 8 | +2.179 | -0.050 | -13 | +2 |
| ocsort | P-G | 98.244 | 96.917 | 10 | +2.146 | +2.146 | -11 | -11 |
| ocsort | P-G+V | 98.244 | 96.931 | 10 | +2.146 | +0.000 | -11 | +0 |

## M3OT / held_out / oracle-box tracker output; direct tracker-box BaseReID crops

Sequences (4): `M3OT/1/ir/test/1-03T;M3OT/1/rgb/test/1-03;M3OT/2/ir/test/2-03T;M3OT/2/rgb/test/2-03`

| Tracker | Method | IDF1 | AssA | IDSW | Delta IDF1 vs None | Delta IDF1 vs parent | Delta IDSW vs None | Delta IDSW vs parent |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bytetrack | None | 96.772 | 88.432 | 6 | +0.000 | +0.000 | +0 | +0 |
| bytetrack | v1 | 91.962 | 81.991 | 5 | -4.810 | -4.810 | -1 | -1 |
| bytetrack | H | 91.051 | 81.011 | 5 | -5.721 | -5.721 | -1 | -1 |
| bytetrack | H+V | 92.078 | 82.250 | 4 | -4.694 | +1.027 | -2 | -1 |
| bytetrack | P-G | 92.078 | 82.250 | 4 | -4.694 | -4.694 | -2 | -2 |
| bytetrack | P-G+V | 92.078 | 82.250 | 4 | -4.694 | +0.000 | -2 | +0 |
| ocsort | None | 95.393 | 92.768 | 5 | +0.000 | +0.000 | +0 | +0 |
| ocsort | v1 | 94.841 | 91.909 | 5 | -0.552 | -0.552 | +0 | +0 |
| ocsort | H | 93.956 | 90.820 | 5 | -1.437 | -1.437 | +0 | +0 |
| ocsort | H+V | 94.920 | 92.129 | 4 | -0.473 | +0.964 | -1 | -1 |
| ocsort | P-G | 94.920 | 92.129 | 4 | -0.473 | -0.473 | -1 | -1 |
| ocsort | P-G+V | 94.920 | 92.129 | 4 | -0.473 | +0.000 | -1 | +0 |

## MMOT / official_detector / official detector

Sequences (50): `data23-1;data24-1;data27-1;data28-1;data28-2;data28-3;data28-4;data28-5;data28-6;data30-10;data30-2;data30-3;data30-4;data30-5;data30-9;data31-1;data33-1;data34-1;data34-2;data34-3;data36-10;data36-11;data36-12;data36-13;data36-4;data36-5;data37-1;data37-10;data37-11;data37-12;data37-2;data39-1;data39-2;data39-3;data39-6;data40-3;data40-4;data40-5;data41-1;data42-1;data42-2;data42-3;data46-11;data46-12;data47-1;data47-2;data47-3;data47-4;data48-1;data49-2`

| Tracker | Method | IDF1 | AssA | IDSW | Delta IDF1 vs None | Delta IDF1 vs parent | Delta IDSW vs None | Delta IDSW vs parent |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bytetrack | None | 38.316 | 42.288 | 10324 | +0.000 | +0.000 | +0 | +0 |
| bytetrack | v1 | 39.967 | 43.755 | 8935 | +1.651 | +1.651 | -1389 | -1389 |
| bytetrack | H | 40.563 | 44.105 | 8405 | +2.247 | +2.247 | -1919 | -1919 |
| bytetrack | H+V | 40.462 | 44.057 | 8466 | +2.146 | -0.101 | -1858 | +61 |
| bytetrack | P-G | 40.529 | 44.087 | 8371 | +2.213 | +2.213 | -1953 | -1953 |
| bytetrack | P-G+V | 40.462 | 44.055 | 8464 | +2.146 | -0.067 | -1860 | +93 |
| deepocsort | None | 63.085 | 67.004 | 1370 | +0.000 | +0.000 | +0 | +0 |
| deepocsort | v1 | 64.083 | 67.837 | 1046 | +0.998 | +0.998 | -324 | -324 |
| deepocsort | H | 64.172 | 67.951 | 957 | +1.087 | +1.087 | -413 | -413 |
| deepocsort | H+V | 64.222 | 67.979 | 984 | +1.137 | +0.050 | -386 | +27 |
| deepocsort | P-G | 64.172 | 67.956 | 963 | +1.087 | +1.087 | -407 | -407 |
| deepocsort | P-G+V | 64.222 | 67.980 | 989 | +1.136 | +0.049 | -381 | +26 |
| ocsort | None | 36.462 | 47.620 | 4263 | +0.000 | +0.000 | +0 | +0 |
| ocsort | v1 | 38.085 | 49.240 | 3204 | +1.623 | +1.623 | -1059 | -1059 |
| ocsort | H | 38.742 | 49.968 | 2668 | +2.280 | +2.280 | -1595 | -1595 |
| ocsort | H+V | 38.593 | 49.789 | 2805 | +2.132 | -0.148 | -1458 | +137 |
| ocsort | P-G | 38.625 | 49.855 | 2729 | +2.163 | +2.163 | -1534 | -1534 |
| ocsort | P-G+V | 38.582 | 49.778 | 2814 | +2.120 | -0.043 | -1449 | +85 |

## MMOT / oracle_aabb / oracle AABB

Sequences (50): `data23-1;data24-1;data27-1;data28-1;data28-2;data28-3;data28-4;data28-5;data28-6;data30-10;data30-2;data30-3;data30-4;data30-5;data30-9;data31-1;data33-1;data34-1;data34-2;data34-3;data36-10;data36-11;data36-12;data36-13;data36-4;data36-5;data37-1;data37-10;data37-11;data37-12;data37-2;data39-1;data39-2;data39-3;data39-6;data40-3;data40-4;data40-5;data41-1;data42-1;data42-2;data42-3;data46-11;data46-12;data47-1;data47-2;data47-3;data47-4;data48-1;data49-2`

| Tracker | Method | IDF1 | AssA | IDSW | Delta IDF1 vs None | Delta IDF1 vs parent | Delta IDSW vs None | Delta IDSW vs parent |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bytetrack | None | 47.437 | 44.690 | 20056 | +0.000 | +0.000 | +0 | +0 |
| bytetrack | v1 | 49.717 | 46.337 | 17511 | +2.279 | +2.279 | -2545 | -2545 |
| bytetrack | H | 50.784 | 46.905 | 16462 | +3.346 | +3.346 | -3594 | -3594 |
| bytetrack | H+V | 50.452 | 46.744 | 16636 | +3.015 | -0.332 | -3420 | +174 |
| bytetrack | P-G | 50.659 | 46.844 | 16437 | +3.222 | +3.222 | -3619 | -3619 |
| bytetrack | P-G+V | 50.391 | 46.714 | 16650 | +2.954 | -0.268 | -3406 | +213 |
| deepocsort | None | 81.486 | 82.063 | 1962 | +0.000 | +0.000 | +0 | +0 |
| deepocsort | v1 | 83.670 | 84.538 | 1377 | +2.184 | +2.184 | -585 | -585 |
| deepocsort | H | 84.002 | 84.928 | 1174 | +2.515 | +2.515 | -788 | -788 |
| deepocsort | H+V | 83.959 | 84.916 | 1257 | +2.473 | -0.043 | -705 | +83 |
| deepocsort | P-G | 84.004 | 84.930 | 1198 | +2.518 | +2.518 | -764 | -764 |
| deepocsort | P-G+V | 83.955 | 84.911 | 1260 | +2.469 | -0.049 | -702 | +62 |
| ocsort | None | 42.964 | 51.431 | 6119 | +0.000 | +0.000 | +0 | +0 |
| ocsort | v1 | 45.254 | 53.639 | 4441 | +2.290 | +2.290 | -1678 | -1678 |
| ocsort | H | 46.185 | 54.445 | 3547 | +3.222 | +3.222 | -2572 | -2572 |
| ocsort | H+V | 45.931 | 54.254 | 3812 | +2.967 | -0.254 | -2307 | +265 |
| ocsort | P-G | 46.093 | 54.385 | 3659 | +3.129 | +3.129 | -2460 | -2460 |
| ocsort | P-G+V | 45.929 | 54.257 | 3817 | +2.966 | -0.163 | -2302 | +158 |
