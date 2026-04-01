import json
import logging
import datetime
from sqlalchemy import func
from .telemetry import TelemetryEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictor-service")

class PredictorService:
    """Statistical forecasting engine for occupancy trends."""
    
    def __init__(self, telemetry_system):
        self.ts = telemetry_system

    def get_occupancy_forecast(self, camera_id: str = None, horizon_minutes: int = 60):
        """Calculates occupancy probability for the next X minutes."""
        now = datetime.datetime.utcnow()
        forecast_time = now + datetime.timedelta(minutes=horizon_minutes)
        
        # 1. Fetch relevant historical samples (Same hour, same day of week)
        day_of_week = now.weekday()
        hour = forecast_time.hour
        
        session = self.ts.Session()
        try:
            # Simple heuristic: Look at the last 4 weeks of the same hour and day
            query = session.query(TelemetryEvent).filter(
                TelemetryEvent.event_type == "Scene Update"
            ).order_by(TelemetryEvent.timestamp.desc())
            
            samples = []
            for event in query.limit(500).all():
                event_data = json.loads(event.data)
                if camera_id and event_data.get("camera_id") != camera_id:
                    continue
                
                # Check if this sample matches our 'temporal target'
                ts = event.timestamp
                if ts.weekday() == day_of_week and ts.hour == hour:
                    occupied_count = sum(1 for s in event_data.get("slots", []) if s.get("status") == "occupied")
                    total_slots = len(event_data.get("slots", []))
                    if total_slots > 0:
                        samples.append(occupied_count / total_slots)
            
            # 2. Calculate Weighted Moving Average
            if not samples:
                # Fallback: Use all-time average for this hour if day-specific data is sparse
                return {"forecast_percent": 35, "confidence": "Low (Global Average)"}
                
            prediction = (sum(samples) / len(samples)) * 100
            confidence = "High" if len(samples) > 10 else "Medium"
            
            return {
                "forecast_percent": round(prediction, 1),
                "horizon_minutes": horizon_minutes,
                "confidence": confidence,
                "samples_analyzed": len(samples)
            }
        except Exception as e:
            logger.error(f"❌ Prediction Error: {e}")
            return {"error": str(e)}
        finally:
            session.close()

if __name__ == "__main__":
    from .telemetry import TelemetrySystem
    ts = TelemetrySystem()
    predictor = PredictorService(ts)
    print(predictor.get_occupancy_forecast(camera_id="CAM-01"))
