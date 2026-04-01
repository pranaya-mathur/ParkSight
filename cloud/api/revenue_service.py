import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("revenue-service")

class RevenueService:
    """Dynamic pricing engine for occupancy-aware parking rates."""
    
    def __init__(self, base_rate: float = 100.0): # Default ₹100/hr
        self.base_rate = base_rate
        self.surge_threshold = 0.8 # 80% occupancy triggers surge

    def calculate_current_rate(self, current_occupancy_percent: float, vehicle_type: str = "STANDARD"):
        """Calculates the applicable rate based on load and vehicle profile."""
        rate = self.base_rate
        
        # 1. Surge Pricing (Load-based)
        if current_occupancy_percent >= (self.surge_threshold * 100):
            rate *= 1.5
            logger.info(f"⚡ SURGE ACTIVE: Facility at {current_occupancy_percent}% load.")
            
        # 2. Vehicle Discounts (Incentives)
        if vehicle_type == "EV":
            rate *= 0.8 # 20% Discount for EVs
            logger.info("🍃 EV DISCOUNT APPLIED.")
        elif vehicle_type == "VIP":
            rate *= 1.2 # 20% Premium for VIP priority spots
            
        return {
            "base_rate": self.base_rate,
            "final_rate": round(rate, 2),
            "currency": "INR",
            "is_surge": current_occupancy_percent >= (self.surge_threshold * 100),
            "vehicle_type": vehicle_type
        }

if __name__ == "__main__":
    rs = RevenueService()
    print(rs.calculate_current_rate(85, "EV"))
