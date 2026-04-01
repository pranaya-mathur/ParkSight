from .slot_engine import SlotEngine

def test_slot_occupancy():
    engine = SlotEngine(num_slots=10)
    
    # Test case 1: Vehicle in slot 0
    detections = [{"label": "car", "bbox": [5, 30, 8, 40]}] # Center (6.5, 35) is in Slot 0 (0-10, 25-45)
    occupancy = engine.update_occupancy(detections)
    assert occupancy[0]["status"] == "occupied"
    assert occupancy[1]["status"] == "free"

    # Test case 2: Vehicle in slot 5
    detections = [{"label": "car", "bbox": [52, 30, 58, 40]}] # Center (55, 35) is in Slot 5 (50-60, 25-45)
    occupancy = engine.update_occupancy(detections)
    assert occupancy[5]["status"] == "occupied"
    assert occupancy[4]["status"] == "free"

    print("Slot Engine tests passed!")

if __name__ == "__main__":
    try:
        test_slot_occupancy()
    except AssertionError as e:
        print(f"Tests failed: {e}")
