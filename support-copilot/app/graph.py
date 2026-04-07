from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.state import CopilotState
from app.nodes import retrieve_context, classify_request, draft_response, select_tool
from app.approval import approval_gate, finalize_response
from app.tool_node import run_tool

builder = StateGraph(CopilotState)

builder.add_node("retrieve_context", retrieve_context)
builder.add_node("classify_request", classify_request)
builder.add_node("draft_response", draft_response)
builder.add_node("approval_gate", approval_gate)
builder.add_node("select_tool", select_tool)
builder.add_node("run_tool", run_tool)
builder.add_node("finalize_response", finalize_response)

builder.add_edge(START, "retrieve_context")
builder.add_edge("retrieve_context", "classify_request")
builder.add_edge("classify_request", "draft_response")
builder.add_edge("draft_response", "approval_gate")
builder.add_edge("approval_gate", "select_tool")
builder.add_edge("select_tool", "run_tool")
builder.add_edge("run_tool", "finalize_response")
builder.add_edge("finalize_response", END)

graph = builder.compile(checkpointer=InMemorySaver())