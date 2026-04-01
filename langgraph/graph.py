import os
from typing import TypedDict, List
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

def build_graph():
    """Builds a LangGraph orchestrator using Groq for parking explanations."""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        temperature=0,
        model_name="llama3-70b-8192", # Excellent for complex reasoning
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    workflow = StateGraph(PlanState)

    def orchestrator(state: PlanState):
        """Orchestrates the guidance message based on the scene and violations."""
        scene = state["scene"]
        violations = state["violations"]
        
        # Analyze scene for the user
        free_slots = [s["id"] for s in scene["slots"] if s["status"] == "free"]
        
        system_msg = SystemMessage(content=(
            "You are ParkSight AI, an intelligent parking guidance system. "
            "Explain the current parking situation concisely to the user. "
            "Address any safety hazards or policy violations immediately. "
            "Mention the best available slot based on distance if applicable."
        ))
        
        user_msg = HumanMessage(content=(
            f"Scene Data: {scene}\n"
            f"Violations: {violations}\n"
            f"Free Slots: {free_slots}\n"
            "Please provide a 2-sentence explanation of the status."
        ))
        
        response = llm.invoke([system_msg, user_msg])
        state["explanation"] = response.content
        return state

    workflow.add_node("explain", orchestrator)
    workflow.set_entry_point("explain")
    workflow.add_edge("explain", END)

    return workflow.compile()

if __name__ == "__main__":
    # Test stub
    graph = build_graph()
    mock_state = {
        "scene": {"slots": [{"id": 0, "status": "free", "distance": 1.0}]},
        "violations": [],
        "explanation": "",
        "best_slot": -1
    }
    # print(graph.invoke(mock_state))
