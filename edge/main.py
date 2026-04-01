import time
import requests
import os
import logging
from .scene_builder import SceneBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-main")

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/system/process")
CAMERA_CONFIGS = [
    {"id": "CAM-01", "source": os.getenv("CAMERA_SOURCE", "MOCK")},
    {"id": "CAM-02", "source": os.getenv("CAMERA_SOURCE", "MOCK")}
]

def run_edge_node():
    """Main loop for the Edge Node: Orchestrate and Push to Cloud."""
    logger.info("🚀 ParkSight Edge Node Starting...")
    
    # Initialize multi-camera orchestrator
    sb = SceneBuilder(camera_configs=CAMERA_CONFIGS)
    
    while True:
        try:
            # 1. Build scenes for all cameras (Inference + Identity + Guidance)
            scenes = sb.build_scenes()
            
            # 2. Push each scene to Cloud API
            for scene in scenes:
                response = requests.post(API_URL, json=scene, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Telemetry Pushed: {scene['camera_id']} ({len(scene['slots'])} slots)")
                else:
                    logger.warning(f"⚠️ API Error: {response.status_code} for {scene['camera_id']}")
                    
        except Exception as e:
            logger.error(f"❌ Edge Loop Error: {e}")
            
        # 5-second interval for telemetry updates (Enterprise standard)
        time.sleep(5)

if __name__ == "__main__":
    run_edge_node()
