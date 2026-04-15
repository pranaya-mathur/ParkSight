"""Slot engine and homography helpers (replaces stale edge/test_slot_engine.py)."""
from pathlib import Path

import pytest

from edge.slot_engine import HomographyTransformer, SlotEngine

REPO_ROOT = Path(__file__).resolve().parents[1]
KAGGLE_CONFIG = REPO_ROOT / "edge" / "configs" / "kaggle_config.json"


def test_default_grid_occupancy():
    engine = SlotEngine()
    assert len(engine.slots) == 10

    detections = [{"label": "car", "bbox": [2, 30, 8, 40]}]
    occupancy = engine.update_occupancy(detections, iou_threshold=0.3)
    assert occupancy[0]["status"] == "occupied"
    assert occupancy[1]["status"] == "free"

    detections = [{"label": "car", "bbox": [5, 30, 6, 31]}]
    occupancy = engine.update_occupancy(detections, iou_threshold=0.3)
    assert occupancy[0]["status"] == "free"


def test_reserved_slot_without_vehicle():
    engine = SlotEngine()
    detections = []
    occ = engine.update_occupancy(detections, reserved_slots={0})
    assert occ[0]["status"] == "reserved"
    assert occ[1]["status"] == "free"


@pytest.mark.skipif(not KAGGLE_CONFIG.exists(), reason="kaggle_config.json missing")
def test_from_config_loads_slots():
    engine = SlotEngine.from_config(str(KAGGLE_CONFIG))
    assert len(engine.slots) >= 10
    assert all("polygon" in s for s in engine.slots)


def test_homography_identity():
    ht = HomographyTransformer()
    assert ht.transform_point(1.0, 2.0) == pytest.approx((1.0, 2.0))


def test_homography_skew():
    tilt_h = [[1.2, 0.1, 0], [0.1, 1.1, 0], [0, 0, 1]]
    ht = HomographyTransformer(tilt_h)
    x, y = ht.transform_point(10.0, 20.0)
    assert isinstance(x, float) and isinstance(y, float)
