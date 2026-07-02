"""Geospatial helpers for WGS84 and local ENU scene coordinates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoOrigin:
    latitude_deg: float
    longitude_deg: float
    height_m: float


@dataclass(frozen=True)
class EnuPose:
    east_m: float
    north_m: float
    up_m: float
    yaw_deg: float
    pitch_deg: float
    roll_deg: float


MARINE_CITY_ORIGIN = GeoOrigin(
    latitude_deg=35.1569,
    longitude_deg=129.1456,
    height_m=80.0,
)
