"""
Pilot-style API chain (mock camera data → edge-equivalent JSON → API → billing paths).
Uses in-memory DB from conftest; no real video.
"""
import pytest
from fastapi.testclient import TestClient

from cloud.api.main import app


@pytest.fixture(autouse=True)
def _disable_groq_for_speed(monkeypatch):
    """Avoid slow LLM calls during sequential stress posts."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def test_scene_process_and_revenue_shape():
    c = TestClient(app)
    scene = {
        "camera_id": "CAM-PILOT",
        "timestamp": 1.0,
        "slots": [
            {"id": 0, "status": "free", "distance": 1.0},
            {"id": 1, "status": "occupied", "distance": 2.0, "vehicle_id": "VEH-P1"},
        ],
        "hazards": [],
        "confidence": 0.95,
    }
    r = c.post("/system/process", json=scene)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "success"
    assert "guidance" in j
    assert "violations" in j

    rs = c.get("/revenue/summary")
    assert rs.status_code == 200
    body = rs.json()
    assert "total_revenue" in body and "billing_ar_open" in body


def test_reservation_and_billing_session_happy_path():
    c = TestClient(app)
    r = c.post("/reserve", json={"slot_id": 3, "vehicle_id": "VEH-PILOT-2"})
    assert r.status_code == 200

    s = c.post(
        "/billing/sessions/start",
        json={"vehicle_id": "VEH-PILOT-2", "slot_id": 3},
    )
    assert s.status_code == 200
    sid = s.json()["id"]
    cl = c.post(f"/billing/sessions/{sid}/close", json={})
    assert cl.status_code == 200


def test_stress_many_scene_posts():
    """Many sequential scene posts (light stress; no concurrency)."""
    c = TestClient(app)
    for i in range(40):
        scene = {
            "camera_id": "CAM-STRESS",
            "timestamp": float(i),
            "slots": [{"id": j % 5, "status": "free" if j % 3 else "occupied", "distance": float(j)} for j in range(8)],
            "hazards": [],
            "confidence": 0.9,
        }
        r = c.post("/system/process", json=scene)
        assert r.status_code == 200
