"""Model-heavy checks; run with: pytest tests/test_model_evaluation.py -m evaluation -q"""
import json
from pathlib import Path

import pytest
from edge.cv_inference import CVInference
from edge.slot_engine import SlotEngine
from evaluation.metrics import collect_ioa_values, flag_borderline_ioa, slot_status_accuracy


@pytest.mark.evaluation
def test_cv_yolo_fps_baseline(sample_bgr_frame, yolo_weights_present):
    """Rough FPS on synthetic frame (skipped if YOLO weights missing)."""
    if not yolo_weights_present:
        pytest.skip("edge/yolo11n.pt not present")
    import time

    cv = CVInference()
    n = 8
    t0 = time.perf_counter()
    for _ in range(n):
        cv.run_inference({"data": sample_bgr_frame})
    dt = time.perf_counter() - t0
    fps = n / max(dt, 1e-6)
    assert fps > 0.5  # very loose; CI CPUs vary


@pytest.mark.evaluation
def test_slot_accuracy_on_simulated_detections():
    """Slot engine + synthetic GT-like occupancy (no video file)."""
    eng = SlotEngine()
    dets = [{"label": "car", "bbox": [2, 30, 8, 40]}]
    occ = eng.update_occupancy(dets, iou_threshold=0.3)
    gt = [{"id": 0, "status": "occupied"}] + [
        {"id": i, "status": "free"} for i in range(1, 10)
    ]
    assert slot_status_accuracy(occ, gt) >= 0.88


@pytest.mark.evaluation
def test_ioa_borderline_detection():
    eng = SlotEngine()
    dets = [{"label": "car", "bbox": [5, 30, 6, 31]}]
    pairs = collect_ioa_values(eng, dets, iou_threshold=0.0)
    flagged = flag_borderline_ioa(pairs, low=0.0, high=1.0)
    assert isinstance(flagged, list)
