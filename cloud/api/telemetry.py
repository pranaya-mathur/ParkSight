import logging
import json
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import numpy as np

Base = declarative_base()

class TelemetryEvent(Base):
    __tablename__ = 'telemetry_events'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text) # JSON string

class VehicleIdentity(Base):
    __tablename__ = 'vehicle_identities'
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), unique=True)
    license_plate = Column(String(20))
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    embedding = Column(Text) # JSON-serialized 512-dim vector

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    slot_id = Column(Integer)
    vehicle_id = Column(String(50))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    expiry_time = Column(DateTime)
    status = Column(String(20), default="ACTIVE") # ACTIVE, EXPIRED, FULFILLED

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50))
    violation_type = Column(String(50))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="UNPAID") # UNPAID, PAID, VOIDED

class TelemetrySystem:
    """Enterprise-grade telemetry system with Vehicle Re-ID matching."""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./parksight.db")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("telemetry")

    def log_event(self, event_type: str, data: dict):
        """Persists a telemetry event and resolves vehicle identities."""
        try:
            session = self.Session()
            
            # Resolve vehicle identities for Scene Updates
            if event_type == "Scene Update":
                for slot in data.get("slots", []):
                    if slot.get("status") == "occupied" and "embedding" in slot:
                        identity = self.get_or_register_identity(
                            embedding=slot["embedding"], 
                            plate=slot.get("license_plate")
                        )
                        slot["vehicle_id"] = identity["vehicle_id"]
                        # We don't need to store the raw embedding in the event log 
                        # to save space, but keeping it for now for demo debugging
            
            event = TelemetryEvent(
                event_type=event_type,
                data=json.dumps(data)
            )
            session.add(event)
            session.commit()
            session.close()
            self.logger.info(f"📊 Event Logged: {event_type} (Identity Resolved)")
        except Exception as e:
            self.logger.error(f"❌ Failed to persist telemetry: {e}")

    def get_or_register_identity(self, embedding: list, plate: str = None):
        """Resolves a vehicle_id using Vector Re-ID matching."""
        session = self.Session()
        query = session.query(VehicleIdentity).all()
        
        target_vec = np.array(embedding)
        best_match = None
        highest_sim = 0
        
        for identity in query:
            db_vec = np.array(json.loads(identity.embedding))
            sim = self._cosine_similarity(target_vec, db_vec)
            if sim > highest_sim:
                highest_sim = sim
                best_match = identity
                
        # Re-ID Match threshold (0.9 is conservative)
        if best_match and highest_sim > 0.9:
            best_match.last_seen = datetime.datetime.utcnow()
            if plate: best_match.license_plate = plate
            v_id = best_match.vehicle_id
            session.commit()
        else:
            # Create new identity
            import uuid
            v_id = f"VEH-{uuid.uuid4().hex[:6].upper()}"
            new_identity = VehicleIdentity(
                vehicle_id=v_id,
                license_plate=plate or "UNKNOWN",
                embedding=json.dumps(embedding)
            )
            session.add(new_identity)
            session.commit()
            
        session.close()
        return {"vehicle_id": v_id, "similarity": highest_sim}

    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

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

    def create_ticket(self, vehicle_id: str, violation_type: str, amount: float = 500.0):
        """Creates a persistent violation ticket (E-Challan)."""
        session = self.Session()
        from .telemetry import Ticket
        ticket = Ticket(
            vehicle_id=vehicle_id,
            violation_type=violation_type,
            amount=amount
        )
        session.add(ticket)
        session.commit()
        session.close()
        self.logger.info(f"🎫 TICKET GENERATED: {violation_type} for {vehicle_id}")
        return ticket

if __name__ == "__main__":
    ts = TelemetrySystem()
    ts.log_event("Scene Update", {"camera_id": "CAM-01", "status": "ok"})
    print(f"Total events for CAM-01: {len(ts.get_history(camera_id='CAM-01'))}")
    print(ts.get_summary())
