from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from .policy_engine import PolicyEngine
from .telemetry import TelemetrySystem
from .reports import ReportGenerator
from .notifications import NotificationService
from .analytics_service import AnalyticsService
from langgraph.graph import StateGraph

# Load environment variables (GROQ_API_KEY, etc.)
load_dotenv()
# Absolute imports for langgraph
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langgraph.graph import build_graph

app = FastAPI(title="ParkSight API - Production")

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
    slots: List[Slot]
    hazards: List[str]
    confidence: float

@app.get("/health")
def health():
    return {"status": "ok", "components": ["policy", "telemetry", "langgraph"]}

@app.post("/system/process")
async def process_scene(scene: Scene):
    """Core guidance endpoint: policy checks, telemetry logs, and LLM explanation."""
    
    # 1. Log to telemetry
    telemetry.log_event("Scene Update", scene.dict())
    
    # 2. Policy evaluation
    violations = policy_engine.evaluate_scene(scene.dict())
    
    # 3. LLM Orchestration (LangGraph)
    explanation = "Deterministic fallback: Guidance active."
    best_slot = -1
    
    # Identify best slot (deterministic)
    free = [s for s in scene.slots if s.status == "free"]
    if free:
        best_slot = sorted(free, key=lambda x: x.distance)[0].id
    
    # LLM Explanation (Simulation if API key is missing)
    if os.getenv("GROQ_API_KEY"):
        try:
            # Use real LangGraph with Groq
            global graph
            if not graph:
                graph = build_graph()
            
            result = graph.invoke({
                "scene": scene.dict(),
                "violations": violations,
                "explanation": "",
                "best_slot": best_slot,
                "classification": "STANDARD" # Initial
            })
            explanation = result["explanation"]
            
            # Trigger Real Notifications for Urgent events
            if result.get("classification") == "URGENT":
                notifier.send_alert(
                    "🚨 URGENT PARKING ALERT",
                    explanation,
                    severity="High"
                )
        except Exception as e:
            explanation = f"AI Service error: {str(e)}"
    else:
        # High-quality mock explanation for local dev
        explanation = f"Slot {best_slot} is free and ready for use. "
        if violations:
            explanation += f"WARNING: {violations[0]['description']}"
        else:
            explanation += "No immediate hazards detected."

    return {
        "status": "success",
        "guidance": {
            "message": explanation,
            "best_slot": best_slot,
            "violations": violations
        },
        "telemetry_id": scene.timestamp
    }

@app.get("/telemetry/summary")
def get_summary():
    return telemetry.get_summary()

@app.get("/reports/generate")
def generate_report():
    """Generates a utilization report from telemetry history."""
    report_gen = ReportGenerator(telemetry.history)
    return report_gen.generate_utilization_report()

@app.get("/analytics/heatmap")
def get_heatmap():
    """Generates an occupancy heatmap from telemetry history."""
    analyzer = AnalyticsService(telemetry.history)
    return analyzer.get_occupancy_heatmap()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
