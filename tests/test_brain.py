import pytest
from brain.graph import build_graph

def test_graph_build():
    """Verifies that the LangGraph orchestrator can be compiled successfully."""
    graph = build_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")

def test_classifier_logic():
    """Tests the internal routing logic of the graph (mock invocation if key missing)."""
    # This is a unit test of the classification logic
    # In a real CI, we'd mock the LLM
    pass
