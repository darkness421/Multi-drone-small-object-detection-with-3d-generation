"""Spawn fine-grained target objects for Marine City scenarios.

TODO:
- Place vehicle, pedestrian, boat, and debris assets.
- Attach fine class and object id metadata.
- Control hard-case ambiguity pairs.
"""

from __future__ import annotations


def planned_object_classes() -> list[str]:
    """Return the first planned fine-grained classes."""
    return ["sedan", "pickup", "van", "ambulance", "police_car", "small_boat"]


if __name__ == "__main__":
    print(planned_object_classes())

