"""Sentry (optional), Prometheus metrics, edge heartbeat."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from prometheus_client import Gauge

from .security import require_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

_edge_heartbeat_ts: Dict[str, float] = {}
_edge_fps: Dict[str, float] = {}

EDGE_LAST_BEAT = Gauge(
    "parksight_edge_last_heartbeat_timestamp",
    "Unix time of last edge heartbeat",
    ["camera_id"],
)
EDGE_FPS = Gauge("parksight_edge_reported_fps", "Last reported inference FPS", ["camera_id"])


class HeartbeatBody(BaseModel):
    camera_id: str = "CAM-01"
    fps: Optional[float] = None
    uptime_sec: Optional[float] = None
    note: Optional[str] = Field(None, max_length=500)


def init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        )
    except ImportError:
        pass


@router.post("/heartbeat")
def edge_heartbeat(body: HeartbeatBody, _user=Depends(require_user)):
    now = time.time()
    _edge_heartbeat_ts[body.camera_id] = now
    EDGE_LAST_BEAT.labels(camera_id=body.camera_id).set(now)
    if body.fps is not None:
        _edge_fps[body.camera_id] = float(body.fps)
        EDGE_FPS.labels(camera_id=body.camera_id).set(float(body.fps))
    return {"status": "ok", "camera_id": body.camera_id, "server_time": now}


@router.get("/edge-status")
def edge_status(_user=Depends(require_user)) -> Dict[str, Any]:
    out = {}
    for cam, ts in _edge_heartbeat_ts.items():
        out[cam] = {
            "last_heartbeat_age_sec": round(time.time() - ts, 2),
            "fps": _edge_fps.get(cam),
        }
    return {"edges": out}
