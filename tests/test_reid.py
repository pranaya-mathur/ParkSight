import json
from cloud.api.telemetry import TelemetrySystem

def test_reid_persistence():
    ts = TelemetrySystem()
    
    # 1. First capture at CAM-01
    embedding = [0.1] * 512 # Unique fingerprint
    scene_1 = {
        "camera_id": "CAM-01",
        "slots": [{"id": 5, "status": "occupied", "license_plate": "ABC 123", "embedding": embedding}]
    }
    ts.log_event("Scene Update", scene_1)
    
    # Get the assigned vehicle_id
    history_1 = ts.get_history(camera_id="CAM-01", limit=1)
    vid_1 = history_1[0]["data"]["slots"][0]["vehicle_id"]
    print(f"Captured at CAM-01: {vid_1}")
    
    # 2. Second capture at CAM-02 (Simulating vehicle movement)
    scene_2 = {
        "camera_id": "CAM-02",
        "slots": [{"id": 2, "status": "occupied", "license_plate": "ABC 123", "embedding": embedding}]
    }
    ts.log_event("Scene Update", scene_2)
    
    # Get the assigned vehicle_id
    history_2 = ts.get_history(camera_id="CAM-02", limit=1)
    vid_2 = history_2[0]["data"]["slots"][0]["vehicle_id"]
    print(f"Captured at CAM-02: {vid_2}")
    
    assert vid_1 == vid_2
    print("✅ Re-ID Persistence Verified: Same vehicle ID across cameras!")

if __name__ == "__main__":
    test_reid_persistence()
