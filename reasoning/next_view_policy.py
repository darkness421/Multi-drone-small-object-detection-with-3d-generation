"""Evidence completion policy for selecting recommended next views.

TODO:
- Select next view from missing evidence.
- Consider UAV availability and altitude constraints.
- Produce active re-observation request.
"""

from __future__ import annotations


def recommend_view(ambiguity_type: str) -> str:
    """Return a simple next-view recommendation."""
    if ambiguity_type == "missing_side_view":
        return "right_oblique"
    if ambiguity_type == "heavy_occlusion":
        return "left_oblique"
    return "front_oblique"


if __name__ == "__main__":
    print(recommend_view("missing_side_view"))

