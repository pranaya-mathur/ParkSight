"""Static checks that deployment artifacts and layout stay consistent."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_docker_artifacts_exist():
    base = REPO_ROOT / "docker"
    for name in (
        "Dockerfile.api",
        "Dockerfile.edge",
        "Dockerfile.ui",
        "nginx-ui.conf",
    ):
        assert (base / name).is_file(), f"missing {base / name}"


def test_compose_declares_core_services():
    text = (REPO_ROOT / "docker-compose.yml").read_text()
    for svc in ("db:", "api:", "edge:", "ui:"):
        assert svc in text


def test_compose_api_database_url_uses_postgres():
    text = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "postgresql://" in text or "postgres" in text.lower()


def test_helm_chart_present():
    chart = REPO_ROOT / "infra" / "helm" / "Chart.yaml"
    assert chart.is_file()


def test_evaluation_package_present():
    base = REPO_ROOT / "evaluation"
    for name in ("evaluate_models.py", "generate_ground_truth.py", "metrics.py", "README.md"):
        assert (base / name).is_file(), f"missing {base / name}"
