# app/approval.py
from langgraph.types import interrupt

def approval_gate(state):
    if not state.get("needs_approval", False):
        return {"approval_decision": "approved"}

    decision = interrupt({
        "type": "approval_request",
        "question": state["user_query"],
        "draft_response": state["draft_response"],
    })
    return {"approval_decision": decision}

def finalize_response(state):
    decision = state.get("approval_decision")

    if decision == "rejected":
        return {
            "final_response": "Draft was rejected by human reviewer. Please revise manually."
        }

    if decision == "approved":
        return {"final_response": state["draft_response"]}

    return {
        "final_response": f"Unexpected approval decision: {decision}"
    }