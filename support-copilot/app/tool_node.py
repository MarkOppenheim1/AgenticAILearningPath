from app.tools import create_refund_ticket, create_escalation_case


def run_tool(state):
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input", {})

    if not tool_name:
        return {"tool_result": None}

    if tool_name == "create_refund_ticket":
        result = create_refund_ticket(**tool_input)
        return {"tool_result": result}

    if tool_name == "create_escalation_case":
        result = create_escalation_case(**tool_input)
        return {"tool_result": result}

    return {"tool_result": f"Unknown tool: {tool_name}"}