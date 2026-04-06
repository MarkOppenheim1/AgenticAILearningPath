from langgraph.types import interrupt


def approval_gate(state):
    request_type = state.get("request_type", "requires_human")

    if request_type == "safe":
        return {"approval_decision": "approved"}

    if request_type == "requires_human":
        return {"approval_decision": "rejected"}

    decision = interrupt({
        "type": "approval_request",
        "question": state["user_query"],
        "request_type": state.get("request_type"),
        "classification_reason": state.get("classification_reason"),
        "draft_response": state["draft_response"],
    })
    return {"approval_decision": decision}


def finalize_response(state):
    decision = state.get("approval_decision")
    request_type = state.get("request_type")

    if request_type == "requires_human":
        return {
            "final_response": (
                "This request should be handled by a human support reviewer."
            )
        }

    if decision == "rejected":
        return {
            "final_response": (
                "Draft was rejected by human reviewer. Please revise manually."
            )
        }

    if decision == "approved":
        return {"final_response": state["draft_response"]}

    return {
        "final_response": f"Unexpected approval decision: {decision}"
    }