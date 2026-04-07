from langgraph.types import interrupt


def approval_gate(state):
    request_type = state.get("request_type", "requires_human")
    recommended_action = state.get("recommended_action", "escalate")

    if request_type == "safe" and recommended_action == "none":
        return {"approval_decision": "approved"}

    if request_type == "requires_human" or recommended_action == "escalate":
        return {"approval_decision": "rejected"}

    decision = interrupt(
        {
            "type": "approval_request",
            "question": state["user_query"],
            "request_type": state.get("request_type"),
            "classification_reason": state.get("classification_reason"),
            "draft_response": state["draft_response"],
            "answer_confidence": state.get("answer_confidence"),
            "answer_sources": state.get("answer_sources", []),
            "recommended_action": state.get("recommended_action"),
        }
    )
    return {"approval_decision": decision}


def finalize_response(state):
    decision = state.get("approval_decision")
    request_type = state.get("request_type")
    recommended_action = state.get("recommended_action", "escalate")
    tool_result = state.get("tool_result")

    if request_type == "requires_human" or recommended_action == "escalate":
        return {
            "final_response": "This request should be handled by a human support reviewer."
        }

    if decision == "rejected":
        return {
            "final_response": "Draft was rejected by human reviewer. Please revise manually."
        }

    if decision == "approved":
        answer = state["draft_response"]
        confidence = state.get("answer_confidence", "unknown")
        sources = ", ".join(state.get("answer_sources", [])) or "No sources"

        if tool_result:
            return {
                "final_response": (
                    f"{answer}\n\n"
                    f"Confidence: {confidence}\n"
                    f"Sources: {sources}\n\n"
                    f"Action Result:\n{tool_result}"
                )
            }

        return {
            "final_response": (
                f"{answer}\n\n"
                f"Confidence: {confidence}\n"
                f"Sources: {sources}"
            )
        }

    return {"final_response": f"Unexpected approval decision: {decision}"}