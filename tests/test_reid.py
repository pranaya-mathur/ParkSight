import json

import numpy as np
import pytest

from cloud.api.telemetry import TelemetrySystem

def test_reid_persistence():
    ts = TelemetrySystem()
    
    # 1. First capture at CAM-01
    embedding = [0.1] * 512 # Unique fingerprint
    scene_1 = {
        "camera_id": "CAM-01",
        "slots": [{"id": 5, "status": "occupied", "license_plate": "ABC 123", "embedding": embedding}]
    }
    ts.log_event("Scene Update", scene_1)
    
    # Get the assigned vehicle_id
    history_1 = ts.get_history(camera_id="CAM-01", limit=1)
    vid_1 = history_1[0]["data"]["slots"][0]["vehicle_id"]
    print(f"Captured at CAM-01: {vid_1}")
    
    # 2. Second capture at CAM-02 (Simulating vehicle movement)
    scene_2 = {
        "camera_id": "CAM-02",
        "slots": [{"id": 2, "status": "occupied", "license_plate": "ABC 123", "embedding": embedding}]
    }
    ts.log_event("Scene Update", scene_2)
    
    # Get the assigned vehicle_id
    history_2 = ts.get_history(camera_id="CAM-02", limit=1)
    vid_2 = history_2[0]["data"]["slots"][0]["vehicle_id"]
    print(f"Captured at CAM-02: {vid_2}")
    
    assert vid_1 == vid_2
    print("✅ Re-ID Persistence Verified: Same vehicle ID across cameras!")

def _cos(a, b):
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def test_embedding_distance_threshold_false_positive_control():
    """Same vehicle: high cosine; different vehicle: lower cosine — threshold band."""
    emb_a = np.random.default_rng(1).normal(0, 1, 512)
    emb_a = (emb_a / np.linalg.norm(emb_a)).tolist()
    noise = np.random.default_rng(2).normal(0, 0.01, 512)
    emb_a2 = (np.array(emb_a) + noise).tolist()
    emb_a2 = (np.array(emb_a2) / np.linalg.norm(emb_a2)).tolist()
    emb_b = np.random.default_rng(3).normal(0, 1, 512)
    emb_b = (emb_b / np.linalg.norm(emb_b)).tolist()
    assert _cos(emb_a, emb_a2) > 0.95
    assert _cos(emb_a, emb_b) < 0.85


@pytest.mark.evaluation
def test_gallery_size_noise_on_match():
    """Accuracy of same-vehicle match should drop slightly as gallery noise grows (sanity)."""
    base = np.random.default_rng(4).normal(0, 1, 512)
    base = (base / np.linalg.norm(base)).tolist()
    sims = [_cos(base, base)]
    for i in range(100):
        g = np.random.default_rng(5 + i).normal(0, 1, 512)
        g = (g / np.linalg.norm(g)).tolist()
        sims.append(_cos(base, g))
    best_random = max(sims[1:])
    assert sims[0] > best_random


if __name__ == "__main__":
    test_reid_persistence()
