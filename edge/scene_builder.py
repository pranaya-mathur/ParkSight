import time
import random
import logging
from .camera_service import CameraService
from .cv_inference import CVInference
from .slot_engine import SlotEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scene-builder")

class SceneBuilder:
    """Aggregates all detections and slot states into a structured JSON 'Scene' for the cloud."""
    
    def __init__(self):
        self.camera = CameraService()
        self.inference = CVInference()
        self.engine = SlotEngine()
        self.camera.start()
        logger.info("Initializing Scene Builder...")

    def build_scene(self):
        """Builds a complete snapshot of the parking lot."""
        frame = self.camera.get_frame()
        detections = self.inference.run_inference(frame)
        occupancy = self.engine.update_occupancy(detections)
        
        # Simulated hazards/incidents for the policy engine & LLM
        possible_hazards = ["Oil Leak", "Unauthorized Access", "Double Parked", "Blocked Fire Hydrant"]
        hazards = random.choices(possible_hazards, k=random.randint(0, 1)) if random.random() > 0.8 else []
        
        scene = {
            "camera_id": frame["camera_id"],
            "timestamp": frame["timestamp"],
            "slots": occupancy,
            "hazards": hazards,
            "confidence": 0.95 # Mock aggregate confidence
        }
        
        logger.info(f"Built Scene at {frame['timestamp']} with {len(occupancy)} slots.")
        return scene

if __name__ == "__main__":
    sb = SceneBuilder()
    while True:
        print(sb.build_scene())
        time.sleep(5)
