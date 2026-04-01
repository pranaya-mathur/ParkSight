import time
import os
import random
import logging
import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("camera-service")

class CameraService:
    """Production-ready Camera Service supporting Mock, RTSP, and CSI streams."""
    
    def __init__(self, source: str = "MOCK", camera_id: str = "CAM-01"):
        self.camera_id = camera_id
        self.source = os.getenv("CAMERA_SOURCE", source)
        self.cap = None
        self.is_running = False

    def start(self):
        """Initializes the connection to the camera source."""
        if self.source == "MOCK":
            logger.info(f"💾 Starting MOCK camera for {self.camera_id}...")
        else:
            logger.info(f"🔋 Connecting to RTSP/CSI Source: {self.source}...")
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                logger.error("🛑 Failed to open camera source!")
                return False
        
        self.is_running = True
        return True

    def get_frame(self):
        """Captures the latest frame from the source."""
        if not self.is_running:
            return None
        
        if self.source == "MOCK":
            # Deterministic ID for tracking
            mock_id = int(time.time() * 100) % 100000
            return {
                "frame_id": mock_id,
                "timestamp": time.time(),
                "camera_id": self.camera_id,
                "data": None # Mock data
            }
        
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("⚠️ Frame dropped from stream.")
            return None
            
        return {
            "frame_id": int(time.time()),
            "timestamp": time.time(),
            "camera_id": self.camera_id,
            "data": frame # Raw OpenCV frame (numpy array)
        }

    def stop(self):
        if self.cap:
            self.cap.release()
        self.is_running = False

if __name__ == "__main__":
    # Test with mock by default
    cam = CameraService()
    cam.start()
    while True:
        frame = cam.get_frame()
        time.sleep(1)
