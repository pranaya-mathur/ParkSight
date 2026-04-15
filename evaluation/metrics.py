"""Shared metrics for evaluation scripts and tests."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple


def levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings (O(nm), fine for short plates)."""
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ca = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ca == b[j - 1] else 1
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def plate_metrics(pred: str, gt: str) -> Dict[str, Any]:
    """ALPR breakdown: detection assumed if pred non-empty; OCR via edit distance; full match."""
    pred = (pred or "").strip()
    gt = (gt or "").strip()
    detected = bool(pred) and pred.upper() != "UNREAD"
    full_match = pred == gt if gt else False
    ed = levenshtein(pred, gt) if gt else (0 if not pred else len(pred))
    char_acc = 1.0 - ed / max(len(gt), 1) if gt else (1.0 if not pred else 0.0)
    return {
        "detection_hit": float(detected),
        "full_plate_match": float(full_match),
        "levenshtein": ed,
        "char_accuracy_approx": max(0.0, min(1.0, char_acc)),
    }


def slot_status_accuracy(
    pred_slots: Sequence[Dict[str, Any]],
    gt_slots: Sequence[Dict[str, Any]],
) -> float:
    """
    Per-slot-id status match rate in [0,1].
    pred_slots / gt_slots: list of dicts with 'id' and 'status' (free|occupied|reserved).
    """
    gt_by_id = {int(s["id"]): str(s.get("status", "")).lower() for s in gt_slots}
    if not gt_by_id:
        return 0.0
    correct = 0
    for s in pred_slots:
        sid = int(s["id"])
        if sid not in gt_by_id:
            continue
        if str(s.get("status", "")).lower() == gt_by_id[sid]:
            correct += 1
    return correct / len(gt_by_id)


def detection_class_histogram(detections: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Count YOLO-style detections by label (car, motorcycle, …)."""
    h: Dict[str, int] = defaultdict(int)
    for d in detections:
        lab = str(d.get("label", "unknown")).lower()
        h[lab] += 1
    return dict(h)


def two_wheeler_ratio(hist: Dict[str, int]) -> float:
    total = sum(hist.values()) or 1
    tw = sum(hist.get(k, 0) for k in ("motorcycle", "bicycle"))
    return tw / total


def collect_ioa_values(
    slot_engine,
    detections: List[Dict[str, Any]],
    iou_threshold: float = 0.0,
) -> List[Tuple[int, float]]:
    """
    For each detection–slot pair that intersects, record (slot_id, IOA).
    Uses same geometry as SlotEngine.update_occupancy (IOA = intersection/slot_area).
    """
    from shapely.geometry import box

    out: List[Tuple[int, float]] = []
    for det in detections:
        bbox = det["bbox"]
        tx1, ty1, tx2, ty2 = slot_engine.transformer.transform_bbox(bbox)
        det_poly = box(tx1, ty1, tx2, ty2)
        for slot in slot_engine.slots:
            slot_poly = slot["polygon"]
            if not slot_poly.intersects(det_poly):
                continue
            inter = slot_poly.intersection(det_poly).area
            ioa = inter / max(slot_poly.area, 1e-9)
            if ioa >= iou_threshold:
                out.append((int(slot["id"]), float(ioa)))
    return out


def flag_borderline_ioa(ioa_values: Sequence[Tuple[int, float]], low: float = 0.4, high: float = 0.6) -> List[int]:
    """Slot ids with IOA in [low, high] — occupancy decision is fragile."""
    return sorted({sid for sid, ioa in ioa_values if low <= ioa <= high})


def weighted_system_score(
    slot_acc: float,
    alpr_char_acc: float,
    reid_stability: float,
    w_slot: float = 0.5,
    w_alpr: float = 0.3,
    w_reid: float = 0.2,
) -> float:
    """Pilot-style single number (all inputs in [0,1])."""
    return w_slot * slot_acc + w_alpr * alpr_char_acc + w_reid * reid_stability


def homography_reprojection_max_error(
    H: Sequence[Sequence[float]],
    src_pts: Sequence[Sequence[float]],
    dst_pts: Sequence[Sequence[float]],
) -> float:
    """Max L2 pixel error after applying 3×3 H to src vs expected dst (inhomogeneous)."""
    import numpy as np

    Hm = np.array(H, dtype=np.float64).reshape(3, 3)
    errs = []
    for (sx, sy), (ex, ey) in zip(src_pts, dst_pts):
        v = Hm @ np.array([sx, sy, 1.0], dtype=np.float64)
        if abs(v[2]) < 1e-12:
            return 1e9
        px, py = float(v[0] / v[2]), float(v[1] / v[2])
        errs.append(((px - ex) ** 2 + (py - ey) ** 2) ** 0.5)
    return max(errs) if errs else 0.0
