import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("camera-service")

class CameraService:
    """Mock Camera Service to simulate streaming frames from a parking lot."""
    
    def __init__(self, camera_id: str = "CAM-01"):
        self.camera_id = camera_id
        self.is_running = False

    def start(self):
        logger.info(f"Starting camera stream for {self.camera_id}...")
        self.is_running = True

    def get_frame(self):
        """Simulates capturing a frame with unique meta-data."""
        if not self.is_running:
            return None
        
        # In a real app, this would return a numpy array (image)
        # For our mock, we return a frame-id and timestamp
        frame_id = random.randint(1000, 9999)
        timestamp = time.time()
        logger.debug(f"Captured frame {frame_id} from {self.camera_id}")
        return {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "camera_id": self.camera_id
        }

if __name__ == "__main__":
    cam = CameraService()
    cam.start()
    while True:
        frame = cam.get_frame()
        time.sleep(1)
