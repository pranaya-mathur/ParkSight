"""Prometheus /metrics smoke (default CI path — not marked evaluation)."""

from fastapi.testclient import TestClient

from cloud.api.main import app


def test_metrics_endpoint_available():
    c = TestClient(app)
    r = c.get("/metrics")
    if r.status_code == 404:
        return  # optional dependency path
    assert r.status_code == 200
    assert len(r.text) > 10
