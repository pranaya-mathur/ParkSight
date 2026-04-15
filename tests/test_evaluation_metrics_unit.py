"""Fast unit tests for evaluation.metrics (no heavy models)."""
from evaluation.metrics import (
    homography_reprojection_max_error,
    levenshtein,
    plate_metrics,
    slot_status_accuracy,
    weighted_system_score,
)


def test_levenshtein_plate_variants():
    assert levenshtein("京A12345", "京A12345") == 0
    assert levenshtein("京A12345", "京A12346") == 1
    assert levenshtein("", "X") == 1


def test_plate_metrics_indian_style_dirty():
    m = plate_metrics("皖HAM12", "皖HAM11")
    assert m["levenshtein"] >= 1
    assert 0.0 <= m["char_accuracy_approx"] <= 1.0


def test_slot_status_accuracy_partial():
    pred = [{"id": 0, "status": "free"}, {"id": 1, "status": "occupied"}]
    gt = [{"id": 0, "status": "free"}, {"id": 1, "status": "free"}]
    acc = slot_status_accuracy(pred, gt)
    assert acc == 0.5


def test_weighted_system_score():
    s = weighted_system_score(0.9, 0.85, 0.8)
    assert 0.85 < s < 0.9


def test_homography_reprojection_identity():
    h = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    src = [[0, 0], [100, 0], [100, 100], [0, 100]]
    dst = [[0, 0], [100, 0], [100, 100], [0, 100]]
    err = homography_reprojection_max_error(h, src, dst)
    assert err < 1e-6
