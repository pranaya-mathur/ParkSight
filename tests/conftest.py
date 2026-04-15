"""Ensure test env is set before any module imports `cloud.api.main` (telemetry DB + auth)."""
import os
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PARKSIGHT_REQUIRE_AUTH", "0")
os.environ.setdefault("PARKSIGHT_JWT_SECRET", "pytest-jwt-secret-key-min-32-chars!!")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def sample_bgr_frame():
    """Synthetic 480p frame (day-like)."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def night_augmented_frame(sample_bgr_frame):
    """Slightly darker frame (night-ish) without OpenCV dependency in conftest."""
    x = sample_bgr_frame.astype(np.int16) - 40
    return np.clip(x, 0, 255).astype(np.uint8)


@pytest.fixture(scope="session")
def yolo_weights_present(repo_root) -> bool:
    p = repo_root / "edge" / "yolo11n.pt"
    return p.is_file()


@pytest.fixture(scope="session")
def onnx_identity_bundle_present(repo_root) -> bool:
    d = repo_root / "edge" / "models"
    return all((d / f).is_file() for f in ("vehicle_reid_osnet.onnx", "lprnet.onnx"))


@pytest.fixture(scope="session", autouse=True)
def _prime_api_lifespan():
    """Run FastAPI lifespan (DB bootstrap users) once; TestClient may defer startup until first request."""
    from fastapi.testclient import TestClient

    from cloud.api.main import app

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
