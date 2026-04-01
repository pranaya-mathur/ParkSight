import time
import random
import logging
from .camera_service import CameraService
from .cv_inference import CVInference
from .slot_engine import SlotEngine
from .guidance_engine import GuidanceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scene-builder")

class SceneBuilder:
    """Aggregates all detections and slot states into a structured JSON 'Scene' for the cloud."""
    
    def __init__(self):
        self.camera = CameraService()
        self.inference = CVInference()
        self.engine = SlotEngine()
        self.guidance_engine = GuidanceEngine()
        self.camera.start()
        logger.info("Initializing Scene Builder...")

    def _detect_hazards(self, detections: list, occupancy: list):
        """Rule-based anomaly detection for hazards and violations."""
        hazards = []
        
        # 1. Overstay Violation (> 60s for demo)
        for slot in occupancy:
            if slot["status"] == "occupied" and slot.get("occupancy_duration", 0) > 60:
                hazards.append(f"Overstay Violation: Slot {slot['id']}")
        
        # 2. Obstacle Detection (Pedestrians/Bicycles in car slots)
        for det in detections:
            if det["label"] in ["person", "bicycle"]:
                hazards.append(f"Safety Hazard: {det['label']} detected in parking area")
            if det["label"] == "fire hydrant":
                hazards.append("Infrastructure: Fire Hydrant Detected")
                
        # 3. Double Parking (Very basic check - overlapping detections)
        if len(detections) > len([s for s in occupancy if s["status"] == "occupied"]):
            hazards.append("Potential Double Parking Detected")
            
        return list(set(hazards)) # Deduplicate

    def build_scene(self):
        """Builds a complete snapshot of the parking lot."""
        frame = self.camera.get_frame()
        detections = self.inference.run_inference(frame)
        occupancy = self.engine.update_occupancy(detections)
        
        # Rule-based hazards instead of pure randomization
        hazards = self._detect_hazards(detections, occupancy)
        
        # Calculate Guidance
        target_slot = occupancy[0] if occupancy else None
        guidance = {}
        if target_slot:
            center_x = (target_slot.get('id', 0) * 10) + 5
            guidance = self.guidance_engine.calculate_maneuver((center_x, 35))
        
        scene = {
            "camera_id": frame["camera_id"],
            "timestamp": frame["timestamp"],
            "slots": occupancy,
            "hazards": hazards,
            "guidance": guidance,
            "confidence": 0.98 if detections else 0.5 
        }
        
        logger.info(f"Built Scene at {frame['timestamp']} with {len(occupancy)} slots.")
        return scene

if __name__ == "__main__":
    sb = SceneBuilder()
    while True:
        print(sb.build_scene())
        time.sleep(5)
