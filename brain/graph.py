import os
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

class PlanState(TypedDict):
    scene: dict
    explanation: str
    violations: List[dict]
    best_slot: int
    classification: Literal["STANDARD", "URGENT"]
    guidance: dict
    broadcast: str
    revenue_data: dict
    session_costs: List[dict]

def build_graph():
    """Builds a LangGraph orchestrator with Conditional Routing for parking alerts."""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.3-70b-versatile", 
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    workflow = StateGraph(PlanState)

    def classifier(state: PlanState):
        """Classifies the scene as STANDARD or URGENT based on violations."""
        violations = state["violations"]
        hazards = state["scene"].get("hazards", [])
        
        # Any high-severity violation or non-empty hazard list triggers URGENT
        is_urgent = any(v.get("severity") == "High" for v in violations) or len(hazards) > 0
        state["classification"] = "URGENT" if is_urgent else "STANDARD"
        return state

    def standard_explainer(state: PlanState):
        """Standard guidance explainer."""
        scene = state["scene"]
        violations = state["violations"]
        free_slots = scene.get("slots", [])
        
        system_msg = SystemMessage(content=(
            "You are ParkSight AI, an intelligent parking guidance system. "
            "Explain the current parking situation concisely to the user. "
            "Provide natural language steering guidance if a target slot is identified."
            "Address any safety hazards or policy violations immediately."
        ))
        
        guidance = scene.get("guidance", {})
        guidance_text = f"Guidance: {guidance.get('instruction', 'None')}. Distance: {guidance.get('distance', 0)}m." if guidance else ""

        user_msg = HumanMessage(content=(
            f"Scene Data: {scene}\n"
            f"Violations: {violations}\n"
            f"Free Slots: {free_slots}\n"
            f"{guidance_text}\n"
            "Please provide a 2-sentence explanation of the status including steering advice."
        ))
        response = llm.invoke([system_msg, user_msg])
        state["explanation"] = response.content
        return state

    def urgent_alerter(state: PlanState):
        """Urgent alert generator for safety issues and policy violations."""
        scene = state["scene"]
        hazards = scene.get("hazards", [])
        guidance = scene.get("guidance", {})
        
        system_msg = SystemMessage(content=(
            "You are ParkSight AI / EMERGENCY ALERT. "
            "Identify the specific hazard (e.g., Safety Hazard, Overstay, Infrastructure) and provide IMMEDIATE corrective actions."
            "Keep it authoritative and brief."
        ))
        
        user_msg = HumanMessage(content=(
            f"URGENT DANGER/VIOLATION: {hazards}\n"
            f"Scene Context: {scene}\n"
            f"Guidance: {guidance.get('instruction', 'Stop immediately')}\n"
            "Explain the specific risk and the required action."
        ))
        
        response = llm.invoke([system_msg, user_msg])
        state["explanation"] = f"🔴 ALERT: {response.content}"
        return state

    def signage_broadcast(state: PlanState):
        """Generates a 3-5 word public announcement for signage."""
        explanation = state.get("explanation", "System Operational")
        is_urgent = state.get("classification") == "URGENT"
        
        system_msg = SystemMessage(content=(
            "You are a public address system. Summarize the status into a 3-5 word HIGH IMPACT announcement. "
            "If URGENT, make it a warning. If STANDARD, make it a helpful guidance."
        ))
        
        user_msg = HumanMessage(content=f"Status: {explanation}")
        
        # Use LLM for concise broadcast
        try:
            response = llm.invoke([system_msg, user_msg])
            state["broadcast"] = response.content.strip().upper()
        except:
            state["broadcast"] = "PROCEED WITH CAUTION" if is_urgent else "WELCOME TO PARKSIGHT"
            
        return state

    def revenue_analyst(state: PlanState):
        """Calculates session costs and earnings for the scene."""
        from cloud.api.revenue_service import RevenueService
        rs = RevenueService()
        
        # Get occupancy % for surge calculation
        slots = state["scene"].get("slots", [])
        occ_count = sum(1 for s in slots if s.get("status") == "occupied")
        occ_p = (occ_count / len(slots) * 100) if slots else 0
        
        # Current Rate Data
        rev_data = rs.calculate_current_rate(occ_p)
        state["revenue_data"] = rev_data
        
        # Calculate costs for active sessions
        costs = []
        for slot in slots:
            if slot.get("status") == "occupied":
                # Rate per second (approx)
                rate_per_sec = rev_data["final_rate"] / 3600
                duration = slot.get("occupancy_duration", 0)
                costs.append({
                    "slot_id": slot["id"],
                    "cost": round(duration * rate_per_sec, 2),
                    "vehicle_id": slot.get("vehicle_id", "Unknown")
                })
        
        state["session_costs"] = costs
        return state

    # Add nodes
    workflow.add_node("classify", classifier)
    workflow.add_node("explain_standard", standard_explainer)
    workflow.add_node("explain_urgent", urgent_alerter)
    workflow.add_node("revenue", revenue_analyst)
    workflow.add_node("broadcast", signage_broadcast)

    # Entry and routing
    workflow.set_entry_point("classify")

    # Conditional Routing
    def route_decision(state: PlanState):
        return state["classification"]

    workflow.add_conditional_edges(
        "classify",
        route_decision,
        {
            "STANDARD": "explain_standard",
            "URGENT": "explain_urgent"
        }
    )

    workflow.add_edge("explain_standard", "revenue")
    workflow.add_edge("explain_urgent", "revenue")
    workflow.add_edge("revenue", "broadcast")
    workflow.add_edge("broadcast", END)

    return workflow.compile()

if __name__ == "__main__":
    # Test stub
    graph = build_graph()
    mock_state = {
        "scene": {"slots": [], "hazards": ["Oil Leak"]},
        "violations": [],
        "explanation": "",
        "best_slot": -1
    }
    # result = graph.invoke(mock_state)
    # print(result["explanation"])
