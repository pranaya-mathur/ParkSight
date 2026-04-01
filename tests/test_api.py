import pytest
from fastapi.testclient import TestClient
from cloud.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_process_scene_minimal():
    mock_scene = {
        "camera_id": "CAM-TEST",
        "timestamp": 123456789.0,
        "slots": [{"id": 0, "status": "free", "distance": 5.0}],
        "hazards": [],
        "confidence": 0.99
    }
    response = client.post("/system/process", json=mock_scene)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "guidance" in data
    assert data["guidance"]["best_slot"] == 0

def test_analytics_heatmap():
    response = client.get("/analytics/heatmap")
    assert response.status_code == 200
    # Even with empty DB, it should return a structured response (error or empty)
    assert "slots" in response.json() or "error" in response.json()
