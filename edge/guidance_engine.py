import math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("guidance-engine")

class GuidanceEngine:
    """Calculates steering vectors and maneuvers for automated parking guidance."""
    
    def __init__(self):
        # Target calibration: Assume vehicle is at (50, 95) - bottom center
        self.vehicle_pos = (50, 95) 

    def calculate_maneuver(self, target_poly_center: tuple, maneuver_type: str = "PERPENDICULAR"):
        """Calculates distance, angle, and instruction based on target center."""
        target_x, target_y = target_poly_center
        curr_x, curr_y = self.vehicle_pos
        
        # 1. Delta calculation
        dx = target_x - curr_x
        dy = target_y - curr_y
        
        distance = math.sqrt(dx**2 + dy**2)
        angle = math.degrees(math.atan2(dx, -dy)) # Angle relative to 'Forward'
        
        # 2. Instruction mapping
        instruction = "Proceed Forward"
        if angle < -10:
            instruction = f"Turn Left {abs(round(angle))}°"
        elif angle > 10:
            instruction = f"Turn Right {abs(round(angle))}°"
            
        if distance < 10:
            instruction = "Stop / Maneuver Complete"
            
        # 3. Path generation (Points for UI visualization)
        path = [
            {"x": curr_x, "y": curr_y},
            {"x": curr_x, "y": target_y + (dy/2)}, # Intermediate point
            {"x": target_x, "y": target_y}
        ]
        
        return {
            "distance": round(distance, 1),
            "angle": round(angle, 1),
            "instruction": instruction,
            "maneuver_type": maneuver_type,
            "path_points": path
        }

if __name__ == "__main__":
    ge = GuidanceEngine()
    # Test: Target at Slot 0 (approx 5, 35)
    print(ge.calculate_maneuver((5, 35)))
