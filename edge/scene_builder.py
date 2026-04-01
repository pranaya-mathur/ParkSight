import time
import random
import logging
from typing import List, Optional
from .camera_service import CameraService
from .cv_inference import CVInference
from .slot_engine import SlotEngine
from .guidance_engine import GuidanceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scene-builder")

class SceneBuilder:
    """Multi-Camera Orchestrator: Aggregates scenes from multiple edge sensors."""
    
    def __init__(self, camera_configs: List[dict] = None):
        # Default to a single mock camera if none provided
        if not camera_configs:
            camera_configs = [{"id": "CAM-01", "source": "MOCK"}]
            
        self.cameras = [CameraService(source=cfg["source"], camera_id=cfg["id"]) for cfg in camera_configs]
        self.inference = CVInference()
        self.engine = SlotEngine()
        self.guidance_engine = GuidanceEngine()
        
        for cam in self.cameras:
            cam.start()
        logger.info(f"Initialized SceneBuilder with {len(self.cameras)} cameras.")

    def _detect_hazards(self, detections: list, occupancy: list):
        """Rule-based anomaly detection for hazards and violations."""
        hazards = []
        for slot in occupancy:
            if slot["status"] == "occupied" and slot.get("occupancy_duration", 0) > 60:
                hazards.append(f"Overstay Violation: Slot {slot['id']}")
        for det in detections:
            if det["label"] in ["person", "bicycle"]:
                hazards.append(f"Safety Hazard: {det['label']} detected in parking area")
            if det["label"] == "fire hydrant":
                hazards.append("Infrastructure: Fire Hydrant Detected")
        if len(detections) > len([s for s in occupancy if s["status"] == "occupied"]):
            hazards.append("Potential Double Parking Detected")
        return list(set(hazards))

    def build_scenes(self):
        """Builds snapshots for ALL connected cameras."""
        scenes = []
        for cam in self.cameras:
            frame = cam.get_frame()
            if not frame:
                continue
                
            detections = self.inference.run_inference(frame)
            occupancy = self.engine.update_occupancy(detections)
            hazards = self._detect_hazards(detections, occupancy)
            
            # Simplified guidance for demo
            target_slot = occupancy[0] if occupancy else None
            guidance = {}
            if target_slot:
                center_x = (target_slot.get('id', 0) * 10) + 5
                guidance = self.guidance_engine.calculate_maneuver((center_x, 35))
            
            scenes.append({
                "camera_id": cam.camera_id,
                "timestamp": frame["timestamp"],
                "slots": occupancy,
                "hazards": hazards,
                "guidance": guidance,
                "confidence": 0.98 if detections else 0.5 
            })
        return scenes

if __name__ == "__main__":
    # Test with Multi-Camera setup
    configs = [
        {"id": "CAM-01", "source": "MOCK"},
        {"id": "CAM-02", "source": "MOCK"}
    ]
    sb = SceneBuilder(camera_configs=configs)
    while True:
        scenes = sb.build_scenes()
        for s in scenes:
            print(f"Captured {s['camera_id']} at {s['timestamp']}")
        time.sleep(5)
