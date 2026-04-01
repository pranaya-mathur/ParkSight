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

if __name__ == "__main__":
    mock_history = [
        {"type": "Scene Update", "data": {"slots": [{"id": 0, "status": "occupied"}, {"id": 1, "status": "free"}]}},
        {"type": "Scene Update", "data": {"slots": [{"id": 0, "status": "occupied"}, {"id": 1, "status": "occupied"}]}}
    ]
    ans = AnalyticsService(mock_history)
    print(ans.get_occupancy_heatmap())
