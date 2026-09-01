"""Phase 1 tests: photo storage, variant generation (original unchanged), vision."""

import hashlib
from pathlib import Path

from PIL import Image

from km_car_deals.agents.vision_agent import VehicleVisionAgent, compute_sha256_photo
from km_car_deals.image_processing.processor import generate_variants
from km_car_deals.models.enums import PhotoVariant
from km_car_deals.models.vehicle import VehiclePhoto


def _make_image(path: Path, color=(120, 40, 200), size=(320, 200)):
    img = Image.new("RGB", size, color)
    img.save(str(path))
    return color


def test_generate_variants_keeps_original_unchanged(tmp_path):
    src = tmp_path / "front.jpg"
    _make_image(src)
    before = hashlib.sha256(src.read_bytes()).hexdigest()

    out_dir = tmp_path / "out"
    variants = generate_variants(str(src), str(out_dir))

    expected = {"original", "processed", "web", "social", "thumbnail"}
    assert expected.issubset(variants.keys())
    # original is a byte-for-byte copy of the untouched source
    assert hashlib.sha256(Path(variants["original"]).read_bytes()).hexdigest() == before
    # variants are real files that exist
    for path in variants.values():
        assert Path(path).exists()
    # thumbnails are smaller than the original dimensions
    thumb = Image.open(variants["thumbnail"])
    assert max(thumb.size) <= 400


def test_vision_deterministic_analysis_when_disabled(db, tmp_storage):
    path = tmp_storage / "pic.jpg"
    _make_image(path)
    photo = VehiclePhoto(
        photo_id="p1",
        vehicle_id="v1",
        variant=PhotoVariant.ORIGINAL.value,
        category="other",
        file_path=str(path),
    )
    db.add(photo)
    agent = VehicleVisionAgent(db)
    agent.analyze_photo(photo)
    db.refresh(photo)
    # with AI disabled we still store deterministic dimensions and never crash
    assert photo.width == 320
    assert photo.height == 200
    assert photo.analysis_notes  # a note was recorded


def test_vision_duplicate_detection(db, tmp_storage):
    a = tmp_storage / "a.png"
    b = tmp_storage / "b.png"
    _make_image(a, color=(10, 20, 30))
    _make_image(b, color=(10, 20, 30))  # identical content -> duplicate

    pa = VehiclePhoto(photo_id="pa", vehicle_id="v1", variant="original", file_path=str(a))
    pb = VehiclePhoto(photo_id="pb", vehicle_id="v1", variant="original", file_path=str(b))
    for p in (pa, pb):
        db.add(p)
    db.flush()

    agent = VehicleVisionAgent(db)
    dups = agent.detect_duplicates([pa, pb])
    assert len(dups) == 1  # one of them flagged as a duplicate of the other


def test_compute_sha256_photo(tmp_storage):
    path = tmp_storage / "x.jpg"
    _make_image(path)
    digest = compute_sha256_photo(str(path))
    assert len(digest) == 64
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()