# app/state.py
from typing import TypedDict, List, Optional

class CopilotState(TypedDict, total=False):
    user_query: str
    retrieved_chunks: List[str]
    request_type: str
    draft_response: str
    needs_approval: bool
    approval_decision: Optional[str]
    final_response: str