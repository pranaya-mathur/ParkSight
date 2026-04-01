import json
import datetime
from typing import List

class ReportGenerator:
    """Smart Parking Management: Generates reports on parking lot utilization."""
    
    def __init__(self, history: List[dict]):
        self.history = history

    def generate_utilization_report(self):
        """Calculates average occupancy and identifies peak hours with temporal context."""
        if not self.history:
            return {"error": "No telemetry data available for reporting."}
            
        total_slots = 10
        occupancy_data = []
        hourly_map = {}
        
        for entry in self.history:
            if entry["type"] == "Scene Update":
                data = entry["data"]
                occupied_count = sum(1 for s in data["slots"] if s["status"] == "occupied")
                usage_pct = (occupied_count / total_slots) * 100
                
                # Parse hour for peak analysis
                ts = entry["timestamp"]
                from datetime import datetime
                dt = datetime.fromisoformat(ts) if isinstance(ts, str) else datetime.fromtimestamp(ts)
                hour_key = dt.strftime("%H:00")
                
                hourly_map.setdefault(hour_key, []).append(usage_pct)
                
                occupancy_data.append({
                    "timestamp": ts,
                    "usage_percent": usage_pct
                })
        
        if not occupancy_data:
            return {"error": "No occupancy updates found in history."}
            
        # Analytics
        avg_usage = sum(d["usage_percent"] for d in occupancy_data) / len(occupancy_data)
        peak_hour = max(hourly_map, key=lambda k: sum(hourly_map[k])/len(hourly_map[k]))
        peak_val = round(sum(hourly_map[peak_hour])/len(hourly_map[peak_hour]), 1)
        
        return {
            "report_generated_at": datetime.datetime.utcnow().isoformat(),
            "summary": {
                "average_utilization": f"{round(avg_usage, 1)}%",
                "peak_utilization_average": f"{peak_val}%",
                "peak_hour": peak_hour,
                "status": "Underutilized" if avg_usage < 30 else "Optimal" if avg_usage < 80 else "Overcrowded"
            },
            "recommendation": "Consider dynamic pricing for peak hours" if peak_val > 80 else "Normal operations",
            "raw_trends": occupancy_data[-10:] 
        }

if __name__ == "__main__":
    # Test stub
    mock_history = [
        {"type": "Scene Update", "timestamp": "2026-04-01T10:00:00", "data": {"slots": [{"status": "occupied"}] * 5}},
        {"type": "Scene Update", "timestamp": "2026-04-01T11:00:00", "data": {"slots": [{"status": "occupied"}] * 8}}
    ]
    rg = ReportGenerator(mock_history)
    print(json.dumps(rg.generate_utilization_report(), indent=2))
