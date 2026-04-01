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
        """Checks the entire scene for policy violations."""
        violations = []
        
        # Check for slot-specific hazards first
        if scene.get("hazards"):
            for hazard in scene["hazards"]:
                violations.append({
                    "type": "Safety Incident",
                    "description": hazard,
                    "severity": "High"
                })
        
        # Check slots for rule compliance
        occupied_count = sum(1 for s in scene["slots"] if s["status"] == "occupied")
        
        # 1. Overcrowding Detection (e.g. > 80% capacity)
        if occupied_count / len(scene["slots"]) > 0.8:
            violations.append({
                "type": "Usage Anomaly",
                "description": "Parking lot is reaching critical capacity (Overcrowding).",
                "severity": "Medium"
            })
            
        for i, slot in enumerate(scene["slots"]):
            slot_id = slot["id"]
            status = slot["status"]
            
            if status == "occupied":
                # 2. Potential Double Parking Detection
                # (If two adjacent slots are occupied by the same 'large' vehicle detection)
                # For this mock, we simulate it based on a random factor.
                import random
                if random.random() > 0.95:
                    violations.append({
                        "type": "Policy Violation",
                        "slot_id": slot_id,
                        "rule": "Single Slot Usage",
                        "description": "Possible Double Parking detected.",
                        "severity": "High"
                    })
                
                rule = self.rules.get(slot_id, "Standard")
                if rule != "Standard":
                    # Simulate a 10% chance of a violation for demo purposes
                    import random
                    if random.random() > 0.9:
                        violations.append({
                            "type": "Policy Violation",
                            "slot_id": slot_id,
                            "rule": rule,
                            "description": f"Occupied without {rule} authorization.",
                            "severity": "Medium"
                        })
                        
        logger.info(f"Evaluated scene: {len(violations)} violations found.")
        return violations

if __name__ == "__main__":
    pb = PolicyEngine()
    test_scene = {"slots": [{"id": 0, "status": "occupied"}], "hazards": ["Oil Leak"]}
    print(pb.evaluate_scene(test_scene))
