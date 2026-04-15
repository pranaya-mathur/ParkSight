import logging
import time
from typing import List, Optional

import numpy as np
from shapely.geometry import Point, Polygon

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

    def _vehicle_crop_for_slot(
        self, frame_data: dict, detections: list, slot: dict
    ) -> Optional[np.ndarray]:
        """Crop vehicle from frame using detection bbox whose center lies in the slot polygon."""
        img = frame_data.get("data")
        if img is None or not isinstance(img, np.ndarray) or img.ndim < 2:
            return None
        pts = slot.get("polygon_points")
        if not pts or len(pts) < 3:
            return None
        try:
            poly = Polygon(pts)
        except Exception:
            return None
        best_bbox = None
        best_conf = -1.0
        for det in detections:
            if det.get("label") not in ("car", "truck", "bus", "motorcycle"):
                continue
            bbox = det.get("bbox")
            if not bbox or len(bbox) < 4:
                continue
            x1, y1, x2, y2 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            if not poly.contains(Point(cx, cy)):
                continue
            conf = float(det.get("confidence", 0))
            if conf > best_conf:
                best_conf = conf
                best_bbox = (x1, y1, x2, y2)
        if best_bbox is None:
            return None
        x1, y1, x2, y2 = best_bbox
        h, w = img.shape[:2]
        xi1, yi1 = max(0, int(x1)), max(0, int(y1))
        xi2, yi2 = min(w, int(x2)), min(h, int(y2))
        if xi2 <= xi1 or yi2 <= yi1:
            return None
        crop = img[yi1:yi2, xi1:xi2]
        return crop if crop.size else None

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
                        crop = self._vehicle_crop_for_slot(frame, detections, slot)
                        identity = self.identity_engine.extract_identity(
                            crop, vehicle_id_seed=slot["id"]
                        )
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
