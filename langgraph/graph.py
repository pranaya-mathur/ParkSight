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

def build_graph():
    """Builds a LangGraph orchestrator with Conditional Routing for parking alerts."""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        temperature=0,
        model_name="llama3-70b-8192", 
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
        """Urgent alert generator for safety issues."""
        scene = state["scene"]
        guidance = scene.get("guidance", {})
        system_msg = SystemMessage(content="You are ParkSight AI / EMERGENCY ALERT. Be direct and authoritative.")
        user_msg = HumanMessage(content=f"DANGER: {scene.get('hazards')}\nGuidance: {guidance.get('instruction', 'Stop immediately')}\nExplain the IMMEDIATE actions required.")
        response = llm.invoke([system_msg, user_msg])
        state["explanation"] = f"CRITICAL: {response.content}"
        return state

    # Add nodes
    workflow.add_node("classify", classifier)
    workflow.add_node("explain_standard", standard_explainer)
    workflow.add_node("explain_urgent", urgent_alerter)

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

    workflow.add_edge("explain_standard", END)
    workflow.add_edge("explain_urgent", END)

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
