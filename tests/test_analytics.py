import pytest
from cloud.api.analytics_service import AnalyticsService

def test_heatmap_calculation():
    mock_history = [
        {
            "type": "Scene Update",
            "timestamp": "2026-04-01T10:00:00",
            "data": {"slots": [{"id": 0, "status": "occupied"}, {"id": 1, "status": "free"}]}
        },
        {
            "type": "Scene Update",
            "timestamp": "2026-04-01T11:00:00",
            "data": {"slots": [{"id": 0, "status": "occupied"}, {"id": 1, "status": "occupied"}]}
        }
    ]
    analyzer = AnalyticsService(mock_history)
    heatmap = analyzer.get_occupancy_heatmap()
    
    # Slot 0 should have 100% (2/2) utilization
    assert heatmap["slots"][0]["utilization_percent"] == 100.0
    # Slot 1 should have 50.0% (1/2) utilization
    assert heatmap["slots"][1]["utilization_percent"] == 50.0

def test_usage_trends():
    mock_history = [
        {"type": "Scene Update", "timestamp": "2026-04-01T10:00:00", "data": {"slots": [{"status": "occupied"}]}},
        {"type": "Scene Update", "timestamp": "2026-04-01T10:10:00", "data": {"slots": [{"status": "occupied"}, {"status": "occupied"}]}}
    ]
    analyzer = AnalyticsService(mock_history)
    trends = analyzer.get_usage_trends()
    # Average for 10:00 hour should be 1.5
    assert trends[0]["avg_occupied"] == 1.5
