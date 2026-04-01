import time
import random
import logging
from typing import List, Optional
from .camera_service import CameraService
from .cv_inference import CVInference
from .slot_engine import SlotEngine
from .guidance_engine import GuidanceEngine
from .identity_engine import IdentityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scene-builder")

class SceneBuilder:
    """Multi-Camera Orchestrator: Aggregates scenes and identities from multiple sensors."""
    
    def __init__(self, camera_configs: List[dict] = None, engine: SlotEngine = None):
        # Default to a single mock camera if none provided
        if not camera_configs:
            camera_configs = [{"id": "CAM-01", "source": "MOCK"}]
            
        self.cameras = [CameraService(source=cfg["source"], camera_id=cfg["id"]) for cfg in camera_configs]
        self.inference = CVInference()
        self.engine = engine or SlotEngine()
        self.guidance_engine = GuidanceEngine()
        self.identity_engine = IdentityEngine()
        
        for cam in self.cameras:
            cam.start()
        logger.info(f"Initialized SceneBuilder with IDENTITY orchestration.")

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
        
        # Identity-based hazard (simulation)
        # If a plate is missing or "blocked", we could flag it
        return list(set(hazards))

    def build_scenes(self, reserved_slots: set = None):
        """Builds snapshots for ALL connected cameras with ALPR, Re-ID, and Reservations."""
        scenes = []
        for cam in self.cameras:
            try:
                frame = cam.get_frame()
                if not frame:
                    continue
                    
                detections = self.inference.run_inference(frame)
                occupancy = self.engine.update_occupancy(detections, reserved_slots=reserved_slots)
                
                # Enrich occupancy with Identity (ALPR + Re-ID)
                for slot in occupancy:
                    if slot["status"] == "occupied":
                        # Simulate crop and extraction
                        identity = self.identity_engine.extract_identity(None, vehicle_id_seed=slot["id"])
                        slot["license_plate"] = identity["license_plate"]
                        slot["embedding"] = identity["embedding"]
                
                hazards = self._detect_hazards(detections, occupancy)
                
                # Deterministic Steering via Guidance Engine
                target_slot = next((s for s in occupancy if s["status"] == "free"), None)
                guidance = {}
                if target_slot:
                    # Map slot ID to 2D coordinates for the guidance engine
                    center_x = (target_slot["id"] * 10) + 5
                    guidance = self.guidance_engine.calculate_maneuver((center_x, 35))
                
                scenes.append({
                    "camera_id": cam.camera_id,
                    "timestamp": frame["timestamp"],
                    "slots": occupancy,
                    "hazards": hazards,
                    "guidance": guidance,
                    "confidence": 0.98 if detections else 0.5 
                })
            except Exception as e:
                logger.error(f"❌ Scene Build Error for {cam.camera_id}: {e}")
                
        return scenes

if __name__ == "__main__":
    # Internal component check
    sb = SceneBuilder()
    print(f"Orchestration check: {len(sb.build_scenes())} cameras active.")
