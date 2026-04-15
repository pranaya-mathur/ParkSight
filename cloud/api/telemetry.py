import logging
import json
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

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


class Invoice(Base):
    __tablename__ = "billing_invoices"
    id = Column(Integer, primary_key=True)
    number = Column(String(40), unique=True, nullable=False)
    vehicle_id = Column(String(50), nullable=False)
    status = Column(String(24), default="DRAFT")  # DRAFT, OPEN, PARTIALLY_PAID, PAID, VOID
    currency = Column(String(8), default="INR")
    subtotal = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    issue_date = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class ParkingSession(Base):
    """Metered parking session (billable)."""
    __tablename__ = "parking_sessions"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), nullable=False)
    slot_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    hourly_rate = Column(Float, default=100.0)
    vehicle_type = Column(String(20), default="STANDARD")
    status = Column(String(20), default="ACTIVE")  # ACTIVE, CLOSED, BILLED
    invoice_id = Column(Integer, ForeignKey("billing_invoices.id"), nullable=True)


class InvoiceLine(Base):
    __tablename__ = "billing_invoice_lines"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("billing_invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    line_type = Column(String(32), default="OTHER")  # VIOLATION, PARKING, DISCOUNT, OTHER
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    parking_session_id = Column(Integer, ForeignKey("parking_sessions.id"), nullable=True)


class APIUser(Base):
    """Dashboard / API auth (JWT). Distinct from vehicle identities."""
    __tablename__ = "api_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="operator")  # operator | admin
    is_active = Column(Integer, default=1)  # 1 = active


class Payment(Base):
    __tablename__ = "billing_payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("billing_invoices.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(24), default="UPI")  # UPI, CARD, CASH, WALLET, BANK_TRANSFER
    reference = Column(String(120), nullable=True)
    status = Column(String(20), default="COMPLETED")  # PENDING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TelemetrySystem:
    """Enterprise-grade telemetry system with Vehicle Re-ID matching."""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./parksight.db")
        eng_kw = {}
        if self.db_url.startswith("sqlite") and ":memory:" in self.db_url:
            eng_kw["connect_args"] = {"check_same_thread": False}
            eng_kw["poolclass"] = StaticPool
        self.engine = create_engine(self.db_url, **eng_kw)
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
