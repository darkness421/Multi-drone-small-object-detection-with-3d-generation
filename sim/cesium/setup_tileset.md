# Cesium Tileset Setup

이 문서는 `Cesium for Omniverse`로 Busan Haeundae Marine City digital twin을 구성하기 위한 설정 메모입니다.

## Current Haeundae Coordinate Bookmark

- Viewer: `sim/cesium/haeundae_marinecity_viewer.html`
- MarineCity origin: `35.156900, 129.145600, 160 m`
- Haeundae Beach reference: `35.158700, 129.160400, 35 m`
- Local frame: WGS84 origin with ENU offsets for UAV/object placement.
- Token behavior: the viewer works with OpenStreetMap imagery without a token.
  If a Cesium ion token is supplied as `?ion_token=...` or
  `localStorage.CESIUM_ION_TOKEN`, OSM Buildings can be enabled.

## Local Preview

```bash
python3 -m http.server 8093 --bind 127.0.0.1 --directory sim/cesium
```

Open:

```text
http://127.0.0.1:8093/haeundae_marinecity_viewer.html
```

## TODO

- Cesium ion token 준비 for OSM Buildings / ion assets.
- Marine City 주변 3D Tiles 또는 terrain source 확인.
- Isaac Sim stage origin과 WGS84/ENU 변환 기준 정리.
- screenshot과 camera path를 paper figure 후보로 저장.
