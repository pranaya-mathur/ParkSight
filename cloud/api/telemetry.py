import logging
import json
import datetime
import os
from sqlalchemy import create_all, create_engine, Column, Integer, String, Float, DateTime, Text
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
    """Enterprise-grade telemetry system with PostgreSQL persistence."""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.history = [] # Keep in-memory cache for quick reports
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
            
            # Cache locally
            self.history.append({
                "type": event_type,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "data": data
            })
            self.logger.info(f"📊 Event Logged: {event_type} (DB Persisted)")
        except Exception as e:
            self.logger.error(f"❌ Failed to persist telemetry: {e}")

    def get_summary(self):
        """Returns the last 50 events."""
        return self.history[-50:]

if __name__ == "__main__":
    ts = TelemetrySystem()
    ts.log_event("Test", {"status": "ok"})
    print(ts.get_summary())
