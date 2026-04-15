import numpy as np
import pytest
from fastapi.testclient import TestClient

from cloud.api.calibration_routes import _homography_from_four_pairs
from cloud.api.main import app
from cloud.api.security import AuthError, create_access_token, parse_authorization_header
from evaluation.metrics import homography_reprojection_max_error


def test_homography_numpy_four_points():
    src = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=float)
    dst = np.array([[0, 0], [200, 0], [200, 200], [0, 200]], dtype=float)
    h = _homography_from_four_pairs(src, dst)
    assert h.shape == (3, 3)
    p = h @ np.array([50.0, 50.0, 1.0])
    p = p / p[2]
    assert abs(p[0] - 100) < 2 and abs(p[1] - 100) < 2


def test_parse_service_bearer(monkeypatch):
    monkeypatch.setenv("PARKSIGHT_SERVICE_BEARER", "edge-secret-token")
    u = parse_authorization_header("Bearer edge-secret-token")
    assert u.role == "operator"
    assert u.email == "service@edge"


def test_parse_jwt_roundtrip():
    tok = create_access_token(sub="u@test.local", role="admin")
    u = parse_authorization_header(f"Bearer {tok}")
    assert u.email == "u@test.local"
    assert u.role == "admin"


def test_parse_invalid_raises():
    with pytest.raises(AuthError):
        parse_authorization_header("Bearer not-a-jwt")


def test_calibration_homography_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("PARKSIGHT_CALIBRATION_PATH", str(tmp_path / "kaggle_config.json"))
    client = TestClient(app)
    body = {
        "src": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 100}, {"x": 0, "y": 100}],
        "dst": [{"x": 0, "y": 0}, {"x": 200, "y": 0}, {"x": 200, "y": 200}, {"x": 0, "y": 200}],
    }
    r = client.post("/calibration/homography", json=body)
    assert r.status_code == 200
    h = r.json()["homography"]
    assert len(h) == 3 and len(h[0]) == 3


def test_calibration_save_and_roundtrip(tmp_path, monkeypatch):
    cfg_path = tmp_path / "kaggle_config.json"
    monkeypatch.setenv("PARKSIGHT_CALIBRATION_PATH", str(cfg_path))
    client = TestClient(app)
    payload = {
        "camera_id": "CAM-TEST",
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "slots": [{"id": 0, "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]], "distance": 1.0}],
    }
    r = client.post("/calibration/slot-config", json=payload)
    assert r.status_code == 200
    assert cfg_path.is_file()
    r2 = client.get("/calibration/slot-config")
    assert r2.status_code == 200
    assert r2.json()["camera_id"] == "CAM-TEST"


def test_homography_reprojection_error_under_five_pixels():
    src = [[10, 20], [110, 20], [110, 120], [10, 120]]
    dst = [[12, 18], [108, 22], [112, 118], [8, 122]]
    h = _homography_from_four_pairs(
        np.array(src, dtype=float),
        np.array(dst, dtype=float),
    )
    err = homography_reprojection_max_error(h, src, dst)
    assert err < 5.0


def test_calibration_rejects_short_polygon(tmp_path, monkeypatch):
    monkeypatch.setenv("PARKSIGHT_CALIBRATION_PATH", str(tmp_path / "kaggle_config.json"))
    client = TestClient(app)
    payload = {
        "camera_id": "CAM-BAD",
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "slots": [{"id": 0, "polygon": [[0, 0], [1, 0]], "distance": 1.0}],
    }
    r = client.post("/calibration/slot-config", json=payload)
    assert r.status_code == 400


def test_auth_login_json():
    client = TestClient(app)
    r = client.post(
        "/auth/login",
        json={"email": "admin@parksight.local", "password": "ChangeMeInProduction!"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@parksight.local"
