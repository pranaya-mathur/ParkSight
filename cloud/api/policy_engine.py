import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("policy-engine")

class PolicyEngine:
    """Enterprise policy engine for parking management.
    Handles rules such as time-limits, authorized zones, and safety violations.
    """
    
    def __init__(self):
        # Sample rules: Slot ID -> Allowed Category
        self.rules = {
            0: "Handicap Only",
            1: "Emergency Vehicle Only",
            2: "Standard",
            3: "Standard",
            4: "Electric Vehicle Only",
            5: "Standard",
            6: "Standard",
            7: "Standard",
            8: "Standard",
            9: "Standard",
        }
        logger.info("Initialized Policy Engine with enterprise rules.")

    def evaluate_scene(self, scene: dict):
        """Checks the entire scene for policy violations and ticketing triggers."""
        violations = []
        slots = scene.get("slots", [])
        
        # 1. Safety & Infrastructure Hazards
        if scene.get("hazards"):
            for hazard in scene["hazards"]:
                violations.append({
                    "type": "Safety Incident",
                    "description": hazard,
                    "severity": "High",
                    "should_ticket": False # Safety is an alert, not a fine
                })
        
        # 2. Overcrowding Detection
        occupied_count = sum(1 for s in slots if s.get("status") == "occupied")
        if len(slots) > 0 and (occupied_count / len(slots)) > 0.8:
            violations.append({
                "type": "Usage Anomaly",
                "description": "Parking lot is reaching critical capacity (Overcrowding).",
                "severity": "Medium",
                "should_ticket": False
            })
            
        # 3. Deterministic Slot Violations
        for slot in slots:
            slot_id = slot["id"]
            status = slot.get("status")
            duration = slot.get("occupancy_duration", 0)
            
            if status == "occupied":
                # A. Overstay Policy (> 10 mins)
                if duration > 600:
                    violations.append({
                        "type": "Policy Violation",
                        "slot_id": slot_id,
                        "rule": "Time Limit (600s)",
                        "description": "Vehicle has exceeded the maximum stay duration.",
                        "severity": "High",
                        "should_ticket": duration > 900 # 5-min grace after limit
                    })
                
                # B. Restricted Zone Check
                rule = self.rules.get(slot_id, "Standard")
                if rule != "Standard":
                    # Simulated: We check if the vehicle identity lacks authorization
                    # For this V4.0 model, we flag it if it's there for > 30s
                    if duration > 30:
                        violations.append({
                            "type": "Policy Violation",
                            "slot_id": slot_id,
                            "rule": rule,
                            "description": f"Unauthorized occupancy in {rule} zone.",
                            "severity": "High",
                            "should_ticket": duration > 300 # 5-min grace period
                        })
                        
        logger.info(f"Evaluated scene: {len(violations)} violations found.")
        return violations

if __name__ == "__main__":
    pb = PolicyEngine()
    test_scene = {"slots": [{"id": 0, "status": "occupied"}], "hazards": ["Oil Leak"]}
    print(pb.evaluate_scene(test_scene))
