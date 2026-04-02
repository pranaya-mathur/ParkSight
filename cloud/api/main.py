from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy import func
from dotenv import load_dotenv
from .policy_engine import PolicyEngine
from .telemetry import TelemetrySystem
from .reports import ReportGenerator
from .notifications import NotificationService
from .analytics_service import AnalyticsService
from .predictor_service import PredictorService
from brain.graph import build_graph
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables once
load_dotenv()

app = FastAPI(title="ParkSight API - Production")

# 0. Configure CORS for frontend stability
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shared components
policy_engine = PolicyEngine()
telemetry = TelemetrySystem()
notifier = NotificationService()
# graph = build_graph() # Note: Requires active GROQ_API_KEY
graph = None # Initialized on demand or in startup

class Slot(BaseModel):
    id: int
    status: str
    distance: float

class Scene(BaseModel):
    camera_id: str
    timestamp: float
    slots: List[dict] # Allow extra identity fields
    hazards: List[str]
    confidence: float

class ReservationRequest(BaseModel):
    slot_id: int
    vehicle_id: str

@app.get("/health")
def health():
    return {"status": "ok", "components": ["policy", "telemetry", "langgraph"]}

@app.post("/system/process")
async def process_scene(scene: Scene):
    """Core guidance endpoint: policy checks, telemetry logs, and LLM explanation."""
    
    # 1. Initialize State
    result = {}
    explanation = "System Operational: Analyzing scene..."
    best_slot = -1
    
    # 2. Identify best slot (deterministic)
    violations = policy_engine.evaluate_scene(scene.model_dump())
    
    # 3. Cognitive Brain (LangGraph + Groq)
    # Check for target identity and provide AI reasoning
    
    # Identify best slot (deterministic)
    free = [s for s in scene.slots if s.get("status") == "free"]
    if free:
        best_slot = sorted(free, key=lambda x: x.get("distance", 999))[0]["id"]
    
    # LLM Explanation (Simulation if API key is missing)
    if os.getenv("GROQ_API_KEY"):
        try:
            # Use real LangGraph with Groq
            global graph
            if not graph:
                graph = build_graph()
            
            # --- CRITICAL: Filter embeddings to avoid '413 Payload Too Large' ---
            lightweight_slots = []
            for s in scene.slots:
                s_copy = s.copy()
                s_copy.pop("embedding", None) # Embeddings are too large for LLM
                lightweight_slots.append(s_copy)
            
            lightweight_scene = scene.model_dump()
            lightweight_scene["slots"] = lightweight_slots
            
            result = graph.invoke({
                "scene": lightweight_scene,
                "violations": violations,
                "explanation": "",
                "best_slot": best_slot,
                "classification": "STANDARD" # Initial
            })
            explanation = result["explanation"]
            
        except Exception as e:
            explanation = f"AI Service error: {str(e)}"
    else:
        # High-quality mock explanation for local dev
        explanation = f"Slot {best_slot} is free and ready for use. No immediate hazards detected."
        # Use simple revenue logic for mock mode
        from .revenue_service import RevenueService
        occ_p = (len([s for s in scene.slots if s.get("status") == "occupied"]) / len(scene.slots) * 100) if scene.slots else 0
        result = {
            "broadcast": "SYSTEM OPERATIONAL - FALLBACK ACTIVE",
            "revenue_data": RevenueService().calculate_current_rate(occ_p),
            "violations": violations
        }

    # 4. Automated Ticketing Integration (Always Run)
    # Ensure active_violations uses AI results if available, otherwise deterministic fallback
    active_violations = result.get("violations", violations)
    
    for v in active_violations:
        if v.get("should_ticket"):
            # Find vehicle_id for this slot
            target_slot = next((s for s in scene.slots if s.get("id") == v.get("slot_id")), {})
            v_id = target_slot.get("vehicle_id")
            if v_id:
                telemetry.create_ticket(v_id, v["type"], amount=500.0)

    # 5. Build Final Response
    guidance_data = {
        "message": explanation,
        "broadcast": result.get("broadcast", "PROCEED WITH CAUTION"),
        "revenue": result.get("revenue_data", {})
    }
    
    # 6. Comprehensive Telemetry Log (Captures full processed state)
    full_data = scene.model_dump()
    full_data["guidance"] = guidance_data
    full_data["violations"] = active_violations
    telemetry.log_event("Scene Update (Identity Resolved)", full_data)

    return {
        "camera_id": scene.camera_id,
        "status": "success",
        "guidance": guidance_data,
        "violations": active_violations
    }

@app.get("/telemetry/summary")
def get_summary(camera_id: Optional[str] = None):
    return telemetry.get_history(camera_id=camera_id, limit=50)

@app.get("/reports/generate")
def generate_report(camera_id: Optional[str] = None):
    """Generates a utilization report from database history."""
    history = telemetry.get_history(camera_id=camera_id, limit=1000)
    report_gen = ReportGenerator(history)
    return report_gen.generate_utilization_report()

@app.get("/analytics/heatmap")
def get_heatmap(camera_id: Optional[str] = None):
    """Generates an occupancy heatmap from database history."""
    history = telemetry.get_history(camera_id=camera_id, limit=500)
    analyzer = AnalyticsService(history)
    return analyzer.get_occupancy_heatmap()

@app.get("/analytics/violations")
def get_violations(camera_id: Optional[str] = None):
    """Generates a violation report from database history."""
    history = telemetry.get_history(camera_id=camera_id, limit=500)
    analyzer = AnalyticsService(history)
    return analyzer.get_violation_report()

@app.get("/analytics/forecast")
def get_forecast(camera_id: Optional[str] = None):
    """Generates a 60-minute occupancy forecast."""
    predictor = PredictorService(telemetry)
    return predictor.get_occupancy_forecast(camera_id=camera_id)

@app.post("/reserve")
async def reserve_slot(request: ReservationRequest):
    """Creates a 30-minute reservation for a specific slot."""
    import datetime
    session = telemetry.Session()
    # Check if slot exists
    # Create reservation
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    from .telemetry import Reservation
    res = Reservation(
        slot_id=request.slot_id,
        vehicle_id=request.vehicle_id,
        expiry_time=expiry
    )
    session.add(res)
    session.commit()
    session.close()
    return {"status": "reserved", "slot_id": request.slot_id}

@app.get("/vehicles/{vehicle_id}/guidance")
def get_driver_guidance(vehicle_id: str):
    """Personalized guidance for a specific recognized driver."""
    # Check for active reservations
    session = telemetry.Session()
    from .telemetry import Reservation
    res = session.query(Reservation).filter(
        Reservation.vehicle_id == vehicle_id,
        Reservation.status == "ACTIVE"
    ).first()
    session.close()

    if res:
        return {
            "welcome": f"Welcome back, {vehicle_id}!",
            "instruction": f"Proceed to your reserved Slot #{res.slot_id}.",
            "target_slot": res.slot_id
        }
    
    return {
        "welcome": f"Hello, {vehicle_id}!",
        "instruction": "Please follow the neon path to the nearest available slot.",
        "target_slot": -1
    }

@app.get("/reservations/active")
def get_active_reservations():
    """Fetches all active slot reservations for Edge node synchronization."""
    session = telemetry.Session()
    from .telemetry import Reservation
    res = session.query(Reservation).filter(Reservation.status == "ACTIVE").all()
    out = [{"slot_id": r.slot_id, "vehicle_id": r.vehicle_id} for r in res]
    session.close()
    return out

@app.get("/revenue/summary")
def get_revenue_summary():
    """Summarizes facility-wide earnings and tickets."""
    session = telemetry.Session()
    from .telemetry import Ticket
    total_revenue = session.query(func.sum(Ticket.amount)).filter(Ticket.status == 'PAID').scalar() or 0
    pending_revenue = session.query(func.sum(Ticket.amount)).filter(Ticket.status == 'UNPAID').scalar() or 0
    active_tickets = session.query(Ticket).filter(Ticket.status == 'UNPAID').count()
    session.close()
    return {
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "active_tickets": active_tickets,
        "currency": "INR"
    }

@app.get("/revenue/tickets")
def get_all_tickets():
    """Returns a log of all violation tickets."""
    session = telemetry.Session()
    from .telemetry import Ticket
    tickets = session.query(Ticket).order_by(Ticket.timestamp.desc()).all()
    out = [{
        "id": t.id,
        "vehicle_id": t.vehicle_id,
        "violation": t.violation_type,
        "amount": t.amount,
        "status": t.status,
        "timestamp": t.timestamp.isoformat()
    } for t in tickets]
    session.close()
    return out

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
