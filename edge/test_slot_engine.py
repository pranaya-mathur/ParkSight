from .slot_engine import SlotEngine
import pytest

def test_polygon_occupancy():
    engine = SlotEngine(num_slots=10)
    
    # Test case 1: Vehicle mostly in slot 0 (Trapezoidal: 1,25 -> 9,25 -> 10,45 -> 0,45)
    # Area approximately 180 (Base 10, Height 20)
    # Bbox: 2, 30, 8, 40 (Area 60)
    detections = [{"label": "car", "bbox": [2, 30, 8, 40]}] 
    occupancy = engine.update_occupancy(detections, iou_threshold=0.3)
    assert occupancy[0]["status"] == "occupied"
    assert occupancy[1]["status"] == "free"

    # Test case 2: Small detection, not enough to occupy (IoA < 0.3)
    detections = [{"label": "car", "bbox": [5, 30, 6, 31]}] # Area 1
    occupancy = engine.update_occupancy(detections, iou_threshold=0.3)
    assert occupancy[0]["status"] == "free"

    print("Polygon Slot Engine tests passed!")

if __name__ == "__main__":
    try:
        test_polygon_occupancy()
    except AssertionError as e:
        print(f"Tests failed: {e}")
