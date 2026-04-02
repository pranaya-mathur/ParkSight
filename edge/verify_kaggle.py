import cv2
import os
import time
import logging
from .cv_inference import CVInference
from .slot_engine import SlotEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-kaggle")

def verify_single_frame(video_path: str, config_path: str):
    """Verifies slot occupancy on a single frame from a video file."""
    if not os.path.exists(video_path):
        logger.error(f"❌ Video not found: {video_path}")
        return
    
    if not os.path.exists(config_path):
        logger.error(f"❌ Config not found: {config_path}")
        return

    # 1. Load Slot Engine
    logger.info(f"📍 Loading polygons from {config_path}...")
    engine = SlotEngine.from_config(config_path)
    
    # 2. Load Frame
    logger.info(f"📹 Opening video: {video_path}...")
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        logger.error("❌ Failed to read frame from video.")
        return

    # 3. Run Inference
    logger.info("🧠 Running YOLO11 Inference...")
    detector = CVInference()
    detections = detector.run_inference({"data": frame})
    
    # 4. Process Occupancy
    logger.info("📐 Calculating Polygon Intersections...")
    occupancy = engine.update_occupancy(detections)
    
    # 5. Output Summary
    occupied = [s["id"] for s in occupancy if s["status"] == "occupied"]
    free = [s["id"] for s in occupancy if s["status"] == "free"]
    
    print("\n--- 🅿️ ParkSight Kaggle Verification Report ---")
    print(f"Video Source: {video_path}")
    print(f"Total Slots: {len(occupancy)}")
    print(f"Occupied: {len(occupied)} {occupied}")
    print(f"Free:     {len(free)} {free}")
    print("----------------------------------------------\n")
    
    logger.info("✅ Verification Complete.")

if __name__ == "__main__":
    # Default to first video
    v_path = "edge/data/kaggle/video1.mp4"
    c_path = "edge/configs/kaggle_config.json"
    verify_single_frame(v_path, c_path)
