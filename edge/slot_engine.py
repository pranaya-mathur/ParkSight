import time
import logging
import numpy as np
from shapely.geometry import Polygon, box

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slot-engine")

class HomographyTransformer:
    """Corrects camera perspective using a 3x3 homography matrix."""
    
    def __init__(self, matrix=None):
        # Default Identity Matrix (no change)
        self.H = np.array(matrix) if matrix else np.eye(3)

    def transform_point(self, x, y):
        """Applies homography to a single (x, y) point."""
        point = np.array([x, y, 1.0]).reshape(3, 1)
        new_point = self.H @ point
        new_point /= new_point[2] # Normalize (z-axis)
        return float(new_point[0]), float(new_point[1])

    def transform_bbox(self, bbox):
        """Transforms a bounding box [x1, y1, x2, y2]."""
        x1, y1 = self.transform_point(bbox[0], bbox[1])
        x2, y2 = self.transform_point(bbox[2], bbox[3])
        return [x1, y1, x2, y2]

class SlotEngine:
    """Advanced Slot occupancy detection engine with Homography support."""
    
    def __init__(self, num_slots: int = 10, homography_matrix=None):
        self.transformer = HomographyTransformer(homography_matrix)
        self.slots = []
        for i in range(num_slots):
            x_start = i * 10
            x_end = x_start + 10
            # Slot Polygon (Defined in real-world / top-down space)
            poly = Polygon([
                (x_start + 0.5, 20), (x_end - 0.5, 20),
                (x_end, 40), (x_start, 40)
            ])
            self.slots.append({
                "id": i,
                "polygon": poly,
                "distance": round(i * 5.2, 1)
            })
        self.slot_timers = {} # Tracks {slot_id: start_timestamp}
        logger.info(f"Initialized SlotEngine with Homography and Overstay tracking.")

    def update_occupancy(self, detections: list, iou_threshold: float = 0.3):
        """Calculates occupancy after perspective correction."""
        occupancy = []
        occupied_slots = set()
        
        for det in detections:
            bbox = det["bbox"] 
            # 1. Transform detector bbox to Slot coordinate space
            tx1, ty1, tx2, ty2 = self.transformer.transform_bbox(bbox)
            det_poly = box(tx1, ty1, tx2, ty2)
            
            for slot in self.slots:
                slot_poly = slot["polygon"]
                if slot_poly.intersects(det_poly):
                    intersection_area = slot_poly.intersection(det_poly).area
                    ioa = intersection_area / slot_poly.area
                    if ioa >= iou_threshold:
                        occupied_slots.add(slot["id"])
                    
        for slot in self.slots:
            is_occupied = slot["id"] in occupied_slots
            status = "occupied" if is_occupied else "free"
            
            # Timer management
            duration = 0
            if is_occupied:
                if slot["id"] not in self.slot_timers:
                    self.slot_timers[slot["id"]] = time.time()
                duration = time.time() - self.slot_timers[slot["id"]]
            else:
                self.slot_timers.pop(slot["id"], None)

            occupancy.append({
                "id": slot["id"],
                "status": status,
                "distance": slot["distance"],
                "occupancy_duration": round(duration, 1)
            })
            
        return occupancy

if __name__ == "__main__":
    # Test with tilted matrix simulating 30% perspective shift
    tilt_H = [[1.2, 0.1, 0], [0.1, 1.1, 0], [0, 0, 1]]
    se = SlotEngine(homography_matrix=tilt_H)
    test_det = [{"label": "car", "bbox": [5, 30, 25, 50]}]
    print(se.update_occupancy(test_det))
