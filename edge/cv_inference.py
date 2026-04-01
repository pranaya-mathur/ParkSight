import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cv-inference")

class CVInference:
    """Mock CV Inference using model YOLO26-N (Nano).
    Simulates vehicle detection within a camera frame.
    """
    
    def __init__(self, model_version: str = "YOLO26-N"):
        self.model_version = model_version
        logger.info(f"Initialized CV Inferencer with {self.model_version}")

    def run_inference(self, frame):
        """Simulates object detection in a frame. Returns a list of bounding boxes."""
        if not frame:
            return []
        
        # Real-time simulation of parking lot activity:
        # We simulate multiple vehicles with (x1, y1, x2, y2) coordinates in (0-100) range.
        detections = []
        
        # Randomly generate 4-7 vehicles
        num_vehicles = random.randint(4, 7)
        for i in range(num_vehicles):
            # Slots are at (x: 10*i, y: 30) approximately.
            # We place vehicles partially based on slot-id to simulate occupancy.
            slot_id = random.randint(0, 9)
            x_base = slot_id * 10
            x1 = x_base + random.randint(0, 2)
            y1 = 25 + random.randint(0, 2)
            x2 = x1 + 8
            y2 = y1 + 10
            
            detections.append({
                "label": "car",
                "confidence": random.uniform(0.85, 0.99),
                "bbox": [x1, y1, x2, y2]
            })
            
        return detections

if __name__ == "__main__":
    cv = CVInference()
    print(cv.run_inference({"frame_id": 1}))
