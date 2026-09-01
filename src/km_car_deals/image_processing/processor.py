"""AI image processing.

Requirements:
- KEEP ORIGINAL UNCHANGED (always).
- Create processed/web/social/thumbnail variants.
- Never alter vehicle identity, model, color, body, wheels, condition.
- Never invent accessories or fake specs.
- Never remove genuine damage.

Background replacement uses a pluggable segmenter. Without a paid/ML service it
degrades gracefully to a light cleanup pass that preserves the original pixels.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger

logger = get_logger(__name__)

BACKGROUNDS = {
    "premium_showroom": {
        "label": "Premium Showroom",
        "color": (245, 245, 250),
        "description": "Clean premium showroom backdrop",
    },
    "dealership": {
        "label": "Professional Dealership",
        "color": (235, 238, 245),
        "description": "Professional dealership backdrop",
    },
    "neutral_studio": {
        "label": "Neutral Studio",
        "color": (240, 240, 240),
        "description": "Neutral studio grey",
    },
    "outdoor_road": {
        "label": "Clean Outdoor Road",
        "color": (200, 210, 220),
        "description": "Clean outdoor road backdrop",
    },
    "km_branded": {
        "label": "KM Car Deals Branded Showroom",
        "color": (18, 24, 38),
        "description": "KM Car Deals branded showroom",
    },
}


def available_backgrounds() -> dict:
    return {name: meta for name, meta in BACKGROUNDS.items()}


def replace_background(
    input_path: str, background: str, output_path: str
) -> bool:
    """Attempt background replacement.

    Full replacement requires an ML segmentation backend. If not available this
    returns False so callers fall back to a non-destructive copy.
    """
    try:
        from km_car_deals.image_processing.segmentation import segment_vehicle

        mask = segment_vehicle(input_path)
        if mask is None:
            return False
        from PIL import Image

        img = Image.open(input_path).convert("RGBA")
        bg_color = BACKGROUNDS.get(background, BACKGROUNDS["neutral_studio"])["color"]
        bg = Image.new("RGBA", img.size, bg_color + (255,))
        from PIL import Image, ImageOps

        result = Image.composite(img, bg, mask.convert("L"))
        out = ImageOps.expand(result.convert("RGB"), border=0)
        out.save(output_path, quality=92)
        return True
    except Exception:
        logger.exception("Background replacement failed for %s", input_path)
        return False


def _ensure_dimension(img, max_size: int):
    from PIL import Image

    w, h = img.size
    if max(w, h) <= max_size:
        return img
    scale = max_size / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def make_thumbnail(img, size: int = 400):
    from PIL import Image

    return _make_thumb_pil(img, size)


def _make_thumb_pil(img, size: int):
    from PIL import Image

    img = img.convert("RGB")
    img.thumbnail((size, size), Image.LANCZOS)
    return img


def _variant_name(fname: str, suffix: str) -> str:
    p = Path(fname)
    return f"{p.stem}_{suffix}{p.suffix.lower()}"


def generate_variants(
    original_path: str,
    out_dir: str,
    background: Optional[str] = None,
    brand: bool = True,
) -> dict:
    """Generate the full set of image variants for one original photo.

    original/  - byte-for-byte copy of the original (never modified).
    processed/ - cleaned (background replaced if segmenter available).
    web/       - resized for website.
    social/    - resized for social.
    thumbnail/ - small thumb.

    Returns mapping of variant name -> output path.
    """
    from PIL import Image

    src = Path(original_path)
    root = Path(out_dir)
    variants = {}

    # 1. Original - keep unchanged
    orig_dir = root / "original"
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_out = orig_dir / src.name
    shutil.copyfile(src, orig_out)
    variants["original"] = str(orig_out)

    img = Image.open(src)

    # 2. Processed
    processed_dir = root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_out = processed_dir / _variant_name(src.name, "processed")
    replaced = False
    if background is not None:
        replaced = replace_background(src, background, str(processed_out))
    if not replaced:
        img.convert("RGB").save(str(processed_out), quality=92)
    variants["processed"] = str(processed_out)

    # 3. Web (1600px)
    web_dir = root / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    web_out = web_dir / _variant_name(src.name, "web")
    _ensure_dimension(img, 1600).convert("RGB").save(str(web_out), quality=90)
    variants["web"] = str(web_out)

    # 4. Social (1080px)
    social_dir = root / "social"
    social_dir.mkdir(parents=True, exist_ok=True)
    social_out = social_dir / _variant_name(src.name, "social")
    _ensure_dimension(img, 1080).convert("RGB").save(str(social_out), quality=90)
    variants["social"] = str(social_out)

    # 5. Thumbnail (400px)
    thumb_dir = root / "thumbnail"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_out = thumb_dir / _variant_name(src.name, "thumb")
    _make_thumb_pil(img, 400).save(str(thumb_out), quality=85)
    variants["thumbnail"] = str(thumb_out)

    return variants
