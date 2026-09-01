"""Vehicle segmentation for background replacement.

This is an optional ML-backed module. It returns None when no segmentation
engine is available so the processor degrades gracefully (non-destructive
copy) instead of altering the image incorrectly.
"""

from __future__ import annotations

from typing import Optional


def segment_vehicle(image_path: str):
    """Return a PIL mask of the vehicle, or None if unavailable.

    A real production deployment would wire up a segmentation model here
    (e.g. a self-hosted U2-Net / rembg / SAM checkpoint) and return a binary
    mask. We intentionally return None unless a configured engine is present,
    so we never produce a corrupt or wrong mask.
    """
    return None
