import logging
from shapely.geometry import Polygon, box

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slot-engine")

class SlotEngine:
    """Advanced Slot occupancy detection engine using Shapely Polygons.
    Supports complex perspective-transformed parking slots.
    """
    
    def __init__(self, num_slots: int = 10):
        # Define 10 slots as Polygons (4 coordinates each) 
        # to handle camera perspective/slanting.
        self.slots = []
        for i in range(num_slots):
            x_start = i * 10
            x_end = x_start + 10
            # Define a slightly trapezoidal slot to simulate perspective
            poly = Polygon([
                (x_start + 1, 25), # Top Left
                (x_end - 1, 25),   # Top Right
                (x_end, 45),       # Bottom Right
                (x_start, 45)      # Bottom Left
            ])
            self.slots.append({
                "id": i,
                "polygon": poly,
                "distance": round(i * 5.2, 1)
            })
        logger.info(f"Initialized Advanced SlotEngine with {num_slots} polygons.")

    def update_occupancy(self, detections: list, iou_threshold: float = 0.3):
        """Calculates occupancy based on Intersection over Area (IoA)."""
        occupancy = []
        occupied_slots = set()
        
        for det in detections:
            bbox = det["bbox"] # [x1, y1, x2, y2]
            det_poly = box(bbox[0], bbox[1], bbox[2], bbox[3])
            
            for slot in self.slots:
                slot_poly = slot["polygon"]
                # Calculate Intersection over Slot Area
                if slot_poly.intersects(det_poly):
                    intersection_area = slot_poly.intersection(det_poly).area
                    ioa = intersection_area / slot_poly.area
                    
                    if ioa >= iou_threshold:
                        occupied_slots.add(slot["id"])
                    
        for slot in self.slots:
            status = "occupied" if slot["id"] in occupied_slots else "free"
            occupancy.append({
                "id": slot["id"],
                "status": status,
                "distance": slot["distance"]
            })
            
        logger.debug(f"Polygon Occupancy Map: {occupancy}")
        return occupancy

if __name__ == "__main__":
    se = SlotEngine()
    # Test collision with a slanting polygon
    test_det = [{"label": "car", "bbox": [2, 30, 8, 40]}] # Mostly overlaps Slot 0
    print(se.update_occupancy(test_det))
