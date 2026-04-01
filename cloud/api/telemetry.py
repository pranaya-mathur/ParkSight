import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telemetry")

class TelemetrySystem:
    """Telemetry system for logging and monitoring parking lot activity."""
    
    def __init__(self):
        # In a real system, this would push to a time-series database (e.g., InfluxDB, Prometheus)
        self.history = []
        logger.info("Initialized Telemetry System.")

    def log_event(self, event_type: str, data: dict):
        """Logs an event to the telemetry history."""
        timestamp = datetime.datetime.utcnow().isoformat()
        entry = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        }
        self.history.append(entry)
        
        # Limit history to 100 entries for this mock
        if len(self.history) > 100:
            self.history.pop(0)
            
        logger.debug(f"Logged {event_type} event.")
        return entry

    def get_summary(self):
        """Returns a summary of the telemetry history."""
        if not self.history:
            return {"status": "inactive"}
            
        latest = self.history[-1]
        return {
            "total_events": len(self.history),
            "latest_event_type": latest["type"],
            "latest_timestamp": latest["timestamp"]
        }

if __name__ == "__main__":
    ts = TelemetrySystem()
    ts.log_event("Heartbeat", {"camera_id": "CAM-01"})
    print(ts.get_summary())
