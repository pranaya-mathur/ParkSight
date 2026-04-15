"""Ensure test env is set before any module imports `cloud.api.main` (telemetry DB + auth)."""
import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PARKSIGHT_REQUIRE_AUTH", "0")
os.environ.setdefault("PARKSIGHT_JWT_SECRET", "pytest-jwt-secret-key-min-32-chars!!")


@pytest.fixture(scope="session", autouse=True)
def _prime_api_lifespan():
    """Run FastAPI lifespan (DB bootstrap users) once; TestClient may defer startup until first request."""
    from fastapi.testclient import TestClient

    from cloud.api.main import app

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
