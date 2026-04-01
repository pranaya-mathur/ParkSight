import logging
import json
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class TelemetryEvent(Base):
    __tablename__ = 'telemetry_events'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text) # JSON string

class TelemetrySystem:
    """Enterprise-grade telemetry system with SQLAlchemy persistence."""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./parksight.db")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("telemetry")

    def log_event(self, event_type: str, data: dict):
        """Persists a telemetry event to the database."""
        try:
            session = self.Session()
            event = TelemetryEvent(
                event_type=event_type,
                data=json.dumps(data)
            )
            session.add(event)
            session.commit()
            session.close()
            self.logger.info(f"📊 Event Logged: {event_type} (DB Persisted)")
        except Exception as e:
            self.logger.error(f"❌ Failed to persist telemetry: {e}")

    def get_history(self, camera_id: str = None, limit: int = 100):
        """Fetches telemetry history from DB, with optional filtering by camera."""
        session = self.Session()
        query = session.query(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc())
        
        results = []
        for event in query.all():
            event_data = json.loads(event.data)
            # Filter by camera_id if provided
            if camera_id and event_data.get("camera_id") != camera_id:
                continue
            
            results.append({
                "type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event_data
            })
            if len(results) >= limit:
                break
                
        session.close()
        return results

    def get_summary(self):
        """Returns the last 50 events."""
        return self.get_history(limit=50)

if __name__ == "__main__":
    ts = TelemetrySystem()
    ts.log_event("Scene Update", {"camera_id": "CAM-01", "status": "ok"})
    print(f"Total events for CAM-01: {len(ts.get_history(camera_id='CAM-01'))}")
    print(ts.get_summary())
