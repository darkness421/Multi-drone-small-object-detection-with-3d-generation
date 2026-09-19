# Third-Party Notices

No third-party repository, dataset, or model checkpoint is bundled. Optional
full-evaluation workflows use the following externally obtained components,
which retain their own copyright and license terms.

| Component | Recorded revision | Purpose | Official source |
| --- | --- | --- | --- |
| BoxMOT | `6edfa8ad7dc2f24b19a41c0058fc53d8d2c4e8ec` | ByteTrack, OC-SORT, Deep OC-SORT | https://github.com/mikel-brostrom/boxmot |
| TrackEval | `12c8791b303e0a0b50f753af204249e622d0281a` | HOTA, CLEAR, identity metrics | https://github.com/JonathonLuiten/TrackEval |
| OpenMMLab MOT17 ResNet-50 ReID | SHA-256 `4bf6b63d49235973033c47f77bc9b94a54bdd222bd3f484b4e484aba580254c1` | Frozen 128-D tracklet descriptors | https://download.openmmlab.com/mmtracking/mot/reid/reid_r50_6e_mot17-4bf6b63d.pth |

The package links to but does not redistribute MMOT, M3OT, images, tracker
caches, pretrained weights, or simulator assets. Users must obtain each asset
from its official source and comply with its current terms.

This notice does not grant a project-level license. See the License section in
`README.md` for the current release status.
