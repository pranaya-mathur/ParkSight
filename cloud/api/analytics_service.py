import json
from typing import List
import numpy as np

class AnalyticsService:
    """Smart Parking Management: Advanced Heatmaps and Historical Trends."""
    
    def __init__(self, history: List[dict]):
        self.history = history

    def get_occupancy_heatmap(self):
        """Generates a 1D heatmap of slot utilization over time."""
        if not self.history:
            return {"error": "No history available."}
            
        slot_usage = {}
        total_samples = 0
        
        for entry in self.history:
            if entry["type"] == "Scene Update":
                total_samples += 1
                for slot in entry["data"]["slots"]:
                    slot_id = slot["id"]
                    if slot["status"] == "occupied":
                        slot_usage[slot_id] = slot_usage.get(slot_id, 0) + 1
                        
        if total_samples == 0:
            return {"error": "No occupancy data samples found."}
            
        heatmap = []
        for i in range(10): # Assuming 10 slots
            count = slot_usage.get(i, 0)
            intensity = round((count / total_samples) * 100, 1)
            heatmap.append({
                "slot_id": i,
                "utilization_percent": intensity,
                "label": "High" if intensity > 70 else "Medium" if intensity > 30 else "Low"
            })
            
        return {
            "title": "Historical Occupancy Heatmap",
            "slots": heatmap,
            "total_samples": total_samples
        }

    def get_usage_trends(self):
        """Groups occupancy by 'hour of day' to identify peak usage trends."""
        from datetime import datetime
        hourly_usage = {i: [] for i in range(24)}
        
        for entry in self.history:
            if entry["type"] == "Scene Update":
                ts = entry["timestamp"]
                # Handle both float (epoch) and string (ISO) timestamps
                dt = datetime.fromisoformat(ts) if isinstance(ts, str) else datetime.fromtimestamp(ts)
                hour = dt.hour
                
                occupied_count = sum(1 for s in entry["data"]["slots"] if s["status"] == "occupied")
                hourly_usage[hour].append(occupied_count)
        
        trends = []
        for hour, counts in hourly_usage.items():
            if counts:
                avg = round(sum(counts) / len(counts), 1)
                trends.append({"hour": f"{hour:02d}:00", "avg_occupied": avg})
        
        return sorted(trends, key=lambda x: x["hour"])

    def get_violation_report(self):
        """Aggregates all hazards and overstay violations into a summary report."""
        violations = {}
        total_violations = 0
        
        for entry in self.history:
            if entry["type"] == "Scene Update":
                hazards = entry["data"].get("hazards", [])
                for h in hazards:
                    violations[h] = violations.get(h, 0) + 1
                    total_violations += 1
                    
        return {
            "total_incidents": total_violations,
            "breakdown": violations,
            "status": "Critical" if total_violations > 10 else "Normal"
        }

if __name__ == "__main__":
    # Test stub with multi-type data
    mock_history = [
        {
            "type": "Scene Update", 
            "timestamp": "2026-04-01T10:00:00", 
            "data": {
                "slots": [{"id": 0, "status": "occupied"}],
                "hazards": ["Safety Hazard: person detected"]
            }
        },
        {
            "type": "Scene Update", 
            "timestamp": "2026-04-01T11:00:00", 
            "data": {
                "slots": [{"id": 0, "status": "occupied"}, {"id": 1, "status": "occupied"}],
                "hazards": ["Overstay Violation: Slot 0"]
            }
        }
    ]
    ans = AnalyticsService(mock_history)
    print("--- Heatmap ---")
    print(ans.get_occupancy_heatmap())
    print("\n--- Usage Trends ---")
    print(ans.get_usage_trends())
    print("\n--- Violation Report ---")
    print(ans.get_violation_report())
