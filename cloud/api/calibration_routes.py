"""Slot geometry + homography: compute and persist edge `kaggle_config`-style JSON."""
from __future__ import annotations

import json
import os
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .security import require_admin

router = APIRouter(prefix="/calibration", tags=["calibration"])


def _default_config_path() -> str:
    return os.getenv(
        "PARKSIGHT_CALIBRATION_PATH",
        os.path.join(os.getcwd(), "edge", "configs", "kaggle_config.json"),
    )


class Point(BaseModel):
    x: float
    y: float


class HomographyRequest(BaseModel):
    """Four point correspondences (image plane → target plane), same convention as OpenCV getPerspectiveTransform."""
    src: List[Point] = Field(..., min_length=4, max_length=4)
    dst: List[Point] = Field(..., min_length=4, max_length=4)


class SlotPolygon(BaseModel):
    id: int
    polygon: List[List[float]]
    distance: float = 0.0


class SlotConfigPayload(BaseModel):
    camera_id: str = "CAM-01"
    homography: Optional[List[List[float]]] = None
    slots: List[SlotPolygon]


def _homography_from_four_pairs(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """DLT homography (3×3), numpy only."""
    if src.shape != (4, 2) or dst.shape != (4, 2):
        raise ValueError("src and dst must be 4×2")
    a = []
    for i in range(4):
        sx, sy = src[i]
        dx, dy = dst[i]
        a.append([-sx, -sy, -1, 0, 0, 0, dx * sx, dx * sy, dx])
        a.append([0, 0, 0, -sx, -sy, -1, dy * sx, dy * sy, dy])
    a = np.asarray(a, dtype=np.float64)
    _, _, vt = np.linalg.svd(a)
    h = vt[-1].reshape(3, 3)
    if abs(h[2, 2]) < 1e-12:
        raise ValueError("Degenerate homography")
    h = h / h[2, 2]
    return h


@router.post("/homography", response_model=dict)
def compute_homography(body: HomographyRequest, _admin=Depends(require_admin)):
    src = np.array([[p.x, p.y] for p in body.src], dtype=np.float64)
    dst = np.array([[p.x, p.y] for p in body.dst], dtype=np.float64)
    try:
        h = _homography_from_four_pairs(src, dst)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    mat = h.tolist()
    return {"homography": mat}


@router.post("/slot-config", response_model=dict)
def save_slot_config(body: SlotConfigPayload, _admin=Depends(require_admin)):
    """Write JSON consumed by `edge/main.py` (`SlotEngine.from_config`)."""
    path = _default_config_path()
    if not body.slots:
        raise HTTPException(status_code=400, detail="At least one slot polygon is required")
    for s in body.slots:
        if len(s.polygon) < 3:
            raise HTTPException(status_code=400, detail=f"Slot {s.id}: polygon needs ≥3 points")
    homography = body.homography
    if homography is None:
        homography = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    out = {
        "camera_id": body.camera_id,
        "homography": homography,
        "slots": [{"id": s.id, "polygon": s.polygon, "distance": s.distance} for s in body.slots],
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return {"status": "saved", "path": path, "slots": len(body.slots)}


@router.get("/slot-config")
def get_slot_config(_admin=Depends(require_admin)):
    path = _default_config_path()
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No calibration file on server")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
