import json
import datetime
from typing import List

class ReportGenerator:
    """Smart Parking Management: Generates reports on parking lot utilization."""
    
    def __init__(self, history: List[dict]):
        self.history = history

    def generate_utilization_report(self):
        """Calculates average occupancy and identifies peak hours."""
        if not self.history:
            return {"error": "No telemetry data available for reporting."}
            
        total_slots = 10
        occupancy_data = []
        
        for entry in self.history:
            if entry["type"] == "Scene Update":
                data = entry["data"]
                occupied_count = sum(1 for s in data["slots"] if s["status"] == "occupied")
                occupancy_data.append({
                    "timestamp": entry["timestamp"],
                    "usage_percent": (occupied_count / total_slots) * 100
                })
        
        if not occupancy_data:
            return {"error": "No occupancy updates found in history."}
            
        # Analytics
        avg_usage = sum(d["usage_percent"] for d in occupancy_data) / len(occupancy_data)
        peak_usage = max(d["usage_percent"] for d in occupancy_data)
        
        return {
            "report_generated_at": datetime.datetime.utcnow().isoformat(),
            "summary": {
                "average_utilization": f"{round(avg_usage, 1)}%",
                "peak_utilization": f"{round(peak_usage, 1)}%",
                "status": "Underutilized" if avg_usage < 30 else "Optimal" if avg_usage < 80 else "Overcrowded"
            },
            "raw_trends": occupancy_data[-24:] # Last 24 points
        }

if __name__ == "__main__":
    # Test stub
    mock_history = [
        {"type": "Scene Update", "timestamp": "2026-04-01T10:00:00", "data": {"slots": [{"status": "occupied"}] * 5}},
        {"type": "Scene Update", "timestamp": "2026-04-01T11:00:00", "data": {"slots": [{"status": "occupied"}] * 8}}
    ]
    rg = ReportGenerator(mock_history)
    print(json.dumps(rg.generate_utilization_report(), indent=2))
