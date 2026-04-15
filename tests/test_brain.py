import os
from unittest.mock import MagicMock

import pytest

from brain.graph import build_graph


def test_graph_build():
    """Verifies that the LangGraph orchestrator can be compiled successfully."""
    graph = build_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")


def test_graph_invoke_standard_path_mocked(monkeypatch):
    """Full graph run with ChatGroq mocked — no network or API key."""
    mock_llm = MagicMock()

    def fake_invoke(_messages):
        r = MagicMock()
        r.content = "Parking is clear; proceed to the nearest free slot."
        return r

    mock_llm.invoke.side_effect = fake_invoke
    monkeypatch.setattr("brain.graph.ChatGroq", lambda **kwargs: mock_llm)

    graph = build_graph()
    result = graph.invoke(
        {
            "scene": {
                "slots": [{"id": 0, "status": "free", "distance": 5.0}],
                "hazards": [],
            },
            "violations": [],
            "explanation": "",
            "best_slot": 0,
            "classification": "STANDARD",
        }
    )

    assert result["classification"] == "STANDARD"
    assert "explanation" in result and result["explanation"]
    assert "revenue_data" in result
    assert mock_llm.invoke.call_count >= 1


def test_graph_invoke_urgent_path_mocked(monkeypatch):
    """URGENT branch when hazards are present."""
    mock_llm = MagicMock()

    def fake_invoke(_messages):
        r = MagicMock()
        r.content = "Oil leak reported; halt traffic in zone A."
        return r

    mock_llm.invoke.side_effect = fake_invoke
    monkeypatch.setattr("brain.graph.ChatGroq", lambda **kwargs: mock_llm)

    graph = build_graph()
    result = graph.invoke(
        {
            "scene": {"slots": [], "hazards": ["Oil leak"]},
            "violations": [],
            "explanation": "",
            "best_slot": -1,
            "classification": "STANDARD",
        }
    )

    assert result["classification"] == "URGENT"
    assert "ALERT" in result["explanation"] or "Oil leak" in result["explanation"]


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set (live LLM smoke)")
def test_graph_invoke_live_groq_smoke():
    """Optional: one real Groq round-trip when key is present (run locally or in CI with secret)."""
    graph = build_graph()
    result = graph.invoke(
        {
            "scene": {
                "slots": [{"id": 1, "status": "free", "distance": 3.0}],
                "hazards": [],
            },
            "violations": [],
            "explanation": "",
            "best_slot": 1,
            "classification": "STANDARD",
        }
    )
    assert result.get("explanation")
    assert result.get("revenue_data") is not None


def test_graph_surge_pricing_data_present_when_high_occupancy_mocked(monkeypatch):
    """High occupancy scene should still yield structured revenue_data from graph."""
    mock_llm = MagicMock()

    def fake_invoke(_messages):
        r = MagicMock()
        r.content = "Occupancy elevated; surge pricing may apply."
        return r

    mock_llm.invoke.side_effect = fake_invoke
    monkeypatch.setattr("brain.graph.ChatGroq", lambda **kwargs: mock_llm)

    graph = build_graph()
    slots = [{"id": i, "status": "occupied" if i < 18 else "free", "distance": float(i)} for i in range(20)]
    result = graph.invoke(
        {
            "scene": {"slots": slots, "hazards": []},
            "violations": [],
            "explanation": "",
            "best_slot": 19,
            "classification": "STANDARD",
        }
    )
    assert result.get("revenue_data") is not None


def test_graph_offline_when_groq_construct_fails(monkeypatch):
    """If ChatGroq cannot be constructed, document graceful failure (skip if graph still builds)."""
    def boom(**kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("brain.graph.ChatGroq", boom)
    with pytest.raises(RuntimeError):
        build_graph()
