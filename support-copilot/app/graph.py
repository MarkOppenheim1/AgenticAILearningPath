# app/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.state import CopilotState
from app.nodes import retrieve_context, classify_request, draft_response
from app.approval import approval_gate, finalize_response

builder = StateGraph(CopilotState)

builder.add_node("retrieve_context", retrieve_context)
builder.add_node("classify_request", classify_request)
builder.add_node("draft_response", draft_response)
builder.add_node("approval_gate", approval_gate)
builder.add_node("finalize_response", finalize_response)

builder.add_edge(START, "retrieve_context")
builder.add_edge("retrieve_context", "classify_request")
builder.add_edge("classify_request", "draft_response")
builder.add_edge("draft_response", "approval_gate")
builder.add_edge("approval_gate", "finalize_response")
builder.add_edge("finalize_response", END)

graph = builder.compile(checkpointer=InMemorySaver())