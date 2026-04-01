import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slot-engine")

class SlotEngine:
    """Slot occupancy detection engine (Deterministic fallback).
    Maps raw CV detections to pre-defined parking slot polygons.
    """
    
    def __init__(self, num_slots: int = 10):
        # Define 10 static slots as rectangles: [x, y, w, h] in 0-100 coordinate space
        self.slots = []
        for i in range(num_slots):
            self.slots.append({
                "id": i,
                "x_range": (i * 10, i * 10 + 10),
                "y_range": (25, 45)
            })
        logger.info(f"Initialized SlotEngine with {num_slots} predefined slots.")

    def update_occupancy(self, detections: list):
        """Calculates which slots are occupied based on detections."""
        occupancy = []
        occupied_slots = set()
        
        for det in detections:
            bbox = det["bbox"] # [x1, y1, x2, y2]
            # Center of the bounding box
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            
            for slot in self.slots:
                if (slot["x_range"][0] <= cx <= slot["x_range"][1]) and \
                   (slot["y_range"][0] <= cy <= slot["y_range"][1]):
                    occupied_slots.add(slot["id"])
                    
        for slot in self.slots:
            status = "occupied" if slot["id"] in occupied_slots else "free"
            occupancy.append({
                "id": slot["id"],
                "status": status,
                # Random mock distance for guidance logic
                "distance": round(slot["id"] * 5.5, 1) 
            })
            
        logger.debug(f"Occupancy Map: {occupancy}")
        return occupancy

if __name__ == "__main__":
    se = SlotEngine()
    test_det = [{"label": "car", "bbox": [5, 30, 15, 40]}] # Overlaps with Slot 0/1
    print(se.update_occupancy(test_det))
