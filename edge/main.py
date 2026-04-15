import time
import requests
import os
import logging
from .scene_builder import SceneBuilder
from .slot_engine import SlotEngine
from .camera_service import CameraService
from .cv_inference import CVInference
from .identity_engine import IdentityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-main")

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/system/process")
RESERVE_URL = os.getenv("RESERVE_URL", "http://localhost:8000/reservations/active")


def _cloud_headers():
    """Bearer for JWT or PARKSIGHT_SERVICE_BEARER when API auth is enabled."""
    t = os.getenv("PARKSIGHT_SERVICE_BEARER", "").strip()
    if t:
        return {"Authorization": f"Bearer {t}"}
    return {}


HEARTBEAT_URL = os.getenv("PARKSIGHT_HEARTBEAT_URL", "").strip()
_EWMA_ALPHA = float(os.getenv("PARKSIGHT_EWMA_ALPHA", "0.15"))
_ewma_fps = None

CAMERA_CONFIGS = [
    {"id": "CAM-01", "source": os.getenv("CAMERA_SOURCE", "MOCK")}
]

def run_edge_node():
    """Main loop for the Edge Node: Orchestrate and Push to Cloud."""
    source = os.getenv("CAMERA_SOURCE", "MOCK")
    config_path = "edge/configs/kaggle_config.json"
    
    # 1. Dynamic Engine & Config Initialization
    if source.lower().endswith((".mp4", ".avi", ".mkv", ".mov")) and os.path.exists(config_path):
        import json
        with open(config_path, 'r') as f:
            cfg_data = json.load(f)
        
        c_id = "CAM-01" # Force match with UI default
        slot_engine = SlotEngine.from_config(config_path)
        is_test_mode = True
        logger.info(f"🧪 TEST MODE: Processing local file with Kaggle Config ({c_id})")
    else:
        c_id = "CAM-01"
        slot_engine = SlotEngine()
        is_test_mode = False
        logger.info(f"📡 PRODUCTION MODE: Using {source}")

    camera_configs = [{"id": c_id, "source": source}]
    detector = CVInference()
    identity_engine = IdentityEngine()
    
    # Initialize multi-camera orchestrator
    sb = SceneBuilder(camera_configs=camera_configs, engine=slot_engine)
    
    global _ewma_fps

    while True:
        loop_t0 = time.time()
        try:
            # 2. Fetch active reservations from Cloud
            reserved_slots = set()
            try:
                res_resp = requests.get(RESERVE_URL, timeout=1, headers=_cloud_headers())
                if res_resp.status_code == 200:
                    reserved_slots = {r["slot_id"] for r in res_resp.json()}
            except:
                pass # Silent fallback for offline testing

            # 3. Build scenes
            scenes = sb.build_scenes(reserved_slots=reserved_slots)
            
            # 4. Push to Cloud API
            for scene in scenes:
                try:
                    response = requests.post(API_URL, json=scene, timeout=5, headers=_cloud_headers())
                    if response.status_code == 200:
                        logger.info(f"✅ Telemetry Pushed: {scene['camera_id']} ({len(scene['slots'])} slots)")
                    else:
                        logger.warning(f"⚠️ API Error: {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ Cloud Connection Failed: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Edge Loop Error: {e}")

        # EWMA FPS (loop body + network); optional push to API Prometheus path via heartbeat
        dt = max(time.time() - loop_t0, 1e-3)
        inst_fps = 1.0 / dt
        if _ewma_fps is None:
            _ewma_fps = inst_fps
        else:
            _ewma_fps = _EWMA_ALPHA * inst_fps + (1.0 - _EWMA_ALPHA) * _ewma_fps
        if HEARTBEAT_URL:
            try:
                requests.post(
                    HEARTBEAT_URL,
                    json={"camera_id": c_id, "fps": float(_ewma_fps)},
                    timeout=2,
                    headers={**_cloud_headers(), "Content-Type": "application/json"},
                )
            except Exception:
                pass

        # 5. Dynamic Interval: 1s for local files, 15s for live streams (to save Groq tokens)
        interval = 1 if is_test_mode else 15
        time.sleep(interval)

if __name__ == "__main__":
    run_edge_node()
